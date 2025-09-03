<?php
/**
 * Конфигурация Homelab VPS API
 */

// Загружаем переменные окружения из .env файла
$envFile = __DIR__ . '/../.env';
if (file_exists($envFile)) {
    $lines = file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos($line, '=') !== false && strpos($line, '#') !== 0) {
            list($key, $value) = explode('=', $line, 2);
            $_ENV[trim($key)] = trim($value);
            putenv(trim($key) . '=' . trim($value));
        }
    }
}

// Основные настройки
define('TELEGRAM_BOT_TOKEN', $_ENV['TELEGRAM_BOT_TOKEN'] ?? '');
define('TELEGRAM_CHAT_ID', $_ENV['TELEGRAM_CHAT_ID'] ?? '');
define('API_SECRET_KEY', $_ENV['API_SECRET_KEY'] ?? '');
define('LOG_LEVEL', $_ENV['LOG_LEVEL'] ?? 'INFO');
define('ENVIRONMENT', $_ENV['ENVIRONMENT'] ?? 'production');

// Проверяем обязательные настройки
if (empty(TELEGRAM_BOT_TOKEN)) {
    error_log('TELEGRAM_BOT_TOKEN не настроен');
}

if (empty(TELEGRAM_CHAT_ID)) {
    error_log('TELEGRAM_CHAT_ID не настроен');
}

// Настройки безопасности
define('ALLOWED_ORIGINS', [
    'http://localhost',
    'http://127.0.0.1',
    'https://your-homelab-domain.com', // Замените на ваш домен
    'http://192.168.1.200', // Ваш локальный IP
]);

// Настройки логирования
define('LOG_FILE', __DIR__ . '/../logs/homelab-vps.log');
define('MAX_LOG_SIZE', 10 * 1024 * 1024); // 10 MB
define('LOG_RETENTION_DAYS', 30);

// Настройки API
define('MAX_REQUEST_SIZE', 1024 * 1024); // 1 MB
define('REQUEST_TIMEOUT', 30); // секунды

// Функция для проверки безопасности
function validateRequest() {
    // Проверяем размер запроса
    if ($_SERVER['CONTENT_LENGTH'] > MAX_REQUEST_SIZE) {
        throw new Exception('Request too large');
    }
    
    // Проверяем origin (если настроен)
    if (!empty($_SERVER['HTTP_ORIGIN'])) {
        $origin = $_SERVER['HTTP_ORIGIN'];
        if (!in_array($origin, ALLOWED_ORIGINS)) {
            logMessage('WARNING', 'Blocked request from unauthorized origin', ['origin' => $origin]);
            // В продакшене можно заблокировать, в разработке - только логируем
            if (ENVIRONMENT === 'production') {
                throw new Exception('Unauthorized origin');
            }
        }
    }
    
    // Проверяем API ключ если настроен
    if (!empty(API_SECRET_KEY)) {
        $authHeader = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
        if (strpos($authHeader, 'Bearer ' . API_SECRET_KEY) !== 0) {
            throw new Exception('Invalid API key');
        }
    }
    
    return true;
}

// Функция для очистки старых логов
function cleanupOldLogs() {
    if (file_exists(LOG_FILE) && filesize(LOG_FILE) > MAX_LOG_SIZE) {
        $backupFile = LOG_FILE . '.' . date('Y-m-d-H-i-s') . '.bak';
        rename(LOG_FILE, $backupFile);
        
        // Удаляем старые backup файлы
        $logDir = dirname(LOG_FILE);
        $files = glob($logDir . '/*.bak');
        $cutoff = time() - (LOG_RETENTION_DAYS * 24 * 60 * 60);
        
        foreach ($files as $file) {
            if (filemtime($file) < $cutoff) {
                unlink($file);
            }
        }
    }
}

// Автоматическая очистка логов
if (rand(1, 100) === 1) { // 1% шанс на каждом запросе
    cleanupOldLogs();
}
