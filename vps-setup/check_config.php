<?php
/**
 * Проверка конфигурации Telegram
 * Запускайте: php check_config.php
 */

require_once __DIR__ . '/api/config.php';

echo "🔍 Проверка конфигурации Telegram\n";
echo "================================\n\n";

// Проверяем переменные окружения
echo "📋 Переменные окружения:\n";
echo "TELEGRAM_BOT_TOKEN: " . (empty(TELEGRAM_BOT_TOKEN) ? "❌ НЕ НАСТРОЕН" : "✅ " . substr(TELEGRAM_BOT_TOKEN, 0, 10) . "...") . "\n";
echo "TELEGRAM_CHAT_ID: " . (empty(TELEGRAM_CHAT_ID) ? "❌ НЕ НАСТРОЕН" : "✅ " . TELEGRAM_CHAT_ID) . "\n";
echo "ENVIRONMENT: " . (defined('ENVIRONMENT') ? ENVIRONMENT : '❌ НЕ ОПРЕДЕЛЕН') . "\n\n";

// Проверяем типы данных
if (!empty(TELEGRAM_CHAT_ID)) {
    echo "🔢 Анализ TELEGRAM_CHAT_ID:\n";
    echo "Тип: " . gettype(TELEGRAM_CHAT_ID) . "\n";
    echo "Длина: " . strlen(TELEGRAM_CHAT_ID) . "\n";
    echo "Значение: '" . TELEGRAM_CHAT_ID . "'\n";
    
    // Проверяем на кавычки
    if (strpos(TELEGRAM_CHAT_ID, '"') !== false) {
        echo "⚠️  ВНИМАНИЕ: Обнаружены кавычки в TELEGRAM_CHAT_ID!\n";
        echo "   Это может вызывать ошибки. Используйте fix_quotes.sh\n";
    }
    
    // Проверяем на числовое значение
    if (is_numeric(TELEGRAM_CHAT_ID)) {
        echo "✅ TELEGRAM_CHAT_ID является числом\n";
    } else {
        echo "❌ TELEGRAM_CHAT_ID не является числом\n";
    }
}

echo "\n";

// Проверяем доступность Telegram API
echo "🌐 Проверка доступности Telegram API:\n";
$testUrl = "https://api.telegram.org/bot" . TELEGRAM_BOT_TOKEN . "/getMe";

$context = stream_context_create([
    'http' => [
        'timeout' => 10,
        'method' => 'GET'
    ]
]);

$result = @file_get_contents($testUrl, false, $context);

if ($result === false) {
    echo "❌ Не удается подключиться к Telegram API\n";
    $error = error_get_last();
    if ($error) {
        echo "   Ошибка: " . $error['message'] . "\n";
    }
} else {
    $response = json_decode($result, true);
    if ($response && isset($response['ok']) && $response['ok']) {
        echo "✅ Telegram API доступен\n";
        echo "   Бот: " . $response['result']['first_name'] . " (@" . $response['result']['username'] . ")\n";
    } else {
        echo "❌ Ошибка Telegram API: " . ($response['description'] ?? 'Unknown error') . "\n";
    }
}

echo "\n";

// Проверяем права доступа
echo "🔐 Проверка прав доступа:\n";
$envFile = __DIR__ . '/.env';
if (file_exists($envFile)) {
    echo ".env файл: " . (is_readable($envFile) ? "✅ Читаемый" : "❌ Не читаемый") . "\n";
    echo "Права: " . substr(sprintf('%o', fileperms($envFile)), -4) . "\n";
    echo "Владелец: " . posix_getpwuid(fileowner($envFile))['name'] . "\n";
} else {
    echo ".env файл: ❌ Не найден\n";
}

$logsDir = __DIR__ . '/logs';
if (is_dir($logsDir)) {
    echo "Директория logs: " . (is_writable($logsDir) ? "✅ Записываемая" : "❌ Не записываемая") . "\n";
} else {
    echo "Директория logs: ❌ Не найдена\n";
}

echo "\n";

// Рекомендации
echo "📋 Рекомендации:\n";
if (empty(TELEGRAM_BOT_TOKEN) || empty(TELEGRAM_CHAT_ID)) {
    echo "1. Создайте файл .env из env.example\n";
    echo "2. Заполните TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID\n";
    echo "3. НЕ ставьте кавычки вокруг значений!\n";
} else {
    if (strpos(TELEGRAM_CHAT_ID, '"') !== false) {
        echo "1. Запустите: ./fix_quotes.sh\n";
    } else {
        echo "1. Конфигурация выглядит корректно\n";
        echo "2. Протестируйте: php test_telegram.php\n";
    }
}

echo "\n🎉 Проверка завершена!\n";
