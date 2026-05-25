<?php
/**
 * Homelab VPS API - Основной endpoint для приема уведомлений
 *
 * Принимает уведомления от Homelab Agent и пересылает их в Telegram
 */

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/telegram.php';

// Устанавливаем заголовки
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Обрабатываем preflight запросы
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Проверяем метод запроса
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit();
}

try {
    // Проверяем конфигурацию Telegram
    if (empty(TELEGRAM_BOT_TOKEN) || empty(TELEGRAM_CHAT_ID)) {
        throw new Exception('Telegram bot not configured. Please check .env file and TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID settings.');
    }
    
    // Получаем JSON данные
    $input = file_get_contents('php://input');
    $data = json_decode($input, true);

    if (json_last_error() !== JSON_ERROR_NONE) {
        throw new Exception('Invalid JSON data');
    }

    // Логируем входящий запрос
    logMessage('INFO', 'Received webhook', $data);
    
    // Логируем конфигурацию (без токена)
    logMessage('INFO', 'Telegram configuration', [
        'bot_token_set' => !empty(TELEGRAM_BOT_TOKEN),
        'chat_id_set' => !empty(TELEGRAM_CHAT_ID),
        'chat_id' => TELEGRAM_CHAT_ID
    ]);

    // Валидируем данные
    if (empty($data['source']) || empty($data['service']) || empty($data['status'])) {
        throw new Exception('Missing required fields: source, service, status');
    }

    // Формируем сообщение для Telegram
    $message = formatTelegramMessage($data);
    
    // Проверяем, что сообщение не пустое
    if (empty(trim($message))) {
        throw new Exception('Generated message is empty. Check input data and configuration.');
    }
    
    // Логируем длину сообщения
    logMessage('INFO', 'Message prepared for Telegram', [
        'message_length' => strlen($message),
        'message_preview' => substr($message, 0, 200) . (strlen($message) > 200 ? '...' : '')
    ]);

    // Отправляем в Telegram (используем sendSmartLongMessage для сообщений с анализом или длинных)
    if (strlen($message) > 4000 || !empty($data['incident_analysis'])) {
        $telegramResponse = sendSmartLongMessage($message);
    } else {
        $telegramResponse = sendToTelegram($message);
    }

    // Логируем результат
    logMessage('INFO', 'Telegram response', $telegramResponse);

    // Возвращаем успешный ответ
    http_response_code(200);
    echo json_encode([
        'success' => true,
        'message' => 'Notification sent to Telegram',
        'telegram_response' => $telegramResponse,
        'timestamp' => date('c')
    ]);

} catch (Exception $e) {
    // Логируем ошибку
    logMessage('ERROR', 'Webhook processing failed', [
        'error' => $e->getMessage(),
        'data' => $data ?? null
    ]);

    // Возвращаем ошибку
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage(),
        'timestamp' => date('c')
    ]);
}

/**
 * Форматирует сообщение для Telegram
 */
function formatTelegramMessage($data): string
{
    // Проверяем обязательные поля
    if (empty($data['status']) || empty($data['service'])) {
        throw new Exception('Missing required fields for message formatting');
    }
    
    $emoji = getStatusEmoji($data['status']);
    $status = ucfirst($data['status']);
    $service = $data['service'];
    $host = $data['host'] ?? 'Unknown';
    $timestamp = $data['timestamp'] ?? date('c');

    // Основное сообщение
    $message = "{$emoji} **HOMELAB ALERT** {$emoji}\n\n";
    $message .= "**Service:** {$service}\n";
    $message .= "**Status:** {$status}\n";
    $message .= "**Host:** {$host}\n";
    $message .= "**Time:** " . formatTimestamp($timestamp) . "\n";

    // Добавляем важные детали (ограниченно)
    if (!empty($data['details'])) {
        $message .= "\n**Details:**\n";
        $importantKeys = ['monitor_url', 'monitor_type', 'message'];
        foreach ($importantKeys as $key) {
            if (isset($data['details'][$key]) && !empty($data['details'][$key])) {
                $value = $data['details'][$key];
                if (strlen($value) > 100) {
                    $value = substr($value, 0, 97) . '...';
                }
                $message .= "• {$key}: {$value}\n";
            }
        }
    }

    // Источник анализа (cursor_cli / basic / recovery)
    if (!empty($data['analysis_type'])) {
        $src = $data['analysis_type'] === 'cursor_cli' ? 'Cursor CLI' : $data['analysis_type'];
        $message .= "\n**Analysis source:** {$src}\n";
    }
    if (!empty($data['cursor_report_path'])) {
        $message .= "**Report file:** {$data['cursor_report_path']}\n";
    }

    // Анализ (уже сжат агентом; доп. лимит для Telegram)
    if (!empty($data['incident_analysis'])) {
        $analysis = $data['incident_analysis'];
        $maxAnalysis = 1600;
        if (function_exists('mb_strlen') && mb_strlen($analysis) > $maxAnalysis) {
            $analysis = mb_substr($analysis, 0, $maxAnalysis - 20) . "\n…";
        } elseif (strlen($analysis) > $maxAnalysis) {
            $analysis = substr($analysis, 0, $maxAnalysis - 20) . "\n…";
        }
        $message .= "\n**Analysis:**\n{$analysis}";
    }

    // НЕ обрезаем сообщение здесь - это сделает sendLongMessage если нужно

    return $message;
}

/**
 * Возвращает emoji для статуса
 */
function getStatusEmoji($status): string
{
    $emojis = [
        'up' => '✅',
        'down' => '🚨',
        'maintenance' => '🔧',
        'paused' => '⏸️',
        'unknown' => '❓'
    ];

    return $emojis[strtolower($status)] ?? '❓';
}

/**
 * Форматирует временную метку
 */
function formatTimestamp($timestamp) {
    try {
        $date = new DateTime($timestamp);
        return $date->format('Y-m-d H:i:s T');
    } catch (Exception $e) {
        return $timestamp;
    }
}

/**
 * Логирует сообщения
 */
function logMessage($level, $message, $context = []): void
{
    $logFile = __DIR__ . '/../../logs/homelab-vps.log';
    $timestamp = date('Y-m-d H:i:s');
    $contextStr = !empty($context) ? ' ' . json_encode($context) : '';

    $logEntry = "[{$timestamp}] [{$level}] {$message}{$contextStr}\n";

    // Создаем директорию для логов если её нет
    $logDir = dirname($logFile);
    if (!is_dir($logDir)) {
        mkdir($logDir, 0755, true);
    }

    file_put_contents($logFile, $logEntry, FILE_APPEND | LOCK_EX);
}
