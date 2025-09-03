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
    // Получаем JSON данные
    $input = file_get_contents('php://input');
    $data = json_decode($input, true);
    
    if (json_last_error() !== JSON_ERROR_NONE) {
        throw new Exception('Invalid JSON data');
    }
    
    // Логируем входящий запрос
    logMessage('INFO', 'Received webhook', $data);
    
    // Валидируем данные
    if (empty($data['source']) || empty($data['service']) || empty($data['status'])) {
        throw new Exception('Missing required fields: source, service, status');
    }
    
    // Формируем сообщение для Telegram
    $message = formatTelegramMessage($data);
    
    // Отправляем в Telegram
    $telegramResponse = sendToTelegram($message);
    
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
function formatTelegramMessage($data) {
    $emoji = getStatusEmoji($data['status']);
    $status = ucfirst($data['status']);
    $service = $data['service'];
    $host = $data['host'] ?? 'Unknown';
    $timestamp = $data['timestamp'] ?? date('c');
    
    $message = "{$emoji} **HOMELAB ALERT** {$emoji}\n\n";
    $message .= "**Service:** {$service}\n";
    $message .= "**Status:** {$status}\n";
    $message .= "**Host:** {$host}\n";
    $message .= "**Time:** " . formatTimestamp($timestamp) . "\n";
    
    // Добавляем детали если есть
    if (!empty($data['details'])) {
        $message .= "\n**Details:**\n";
        foreach ($data['details'] as $key => $value) {
            if (is_string($value) && !empty($value)) {
                $message .= "• {$key}: {$value}\n";
            }
        }
    }
    
    return $message;
}

/**
 * Возвращает emoji для статуса
 */
function getStatusEmoji($status) {
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
function logMessage($level, $message, $context = []) {
    $logFile = __DIR__ . '/../logs/homelab-vps.log';
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
