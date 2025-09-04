<?php
/**
 * Тестирование Telegram API
 * Запускайте: php test_telegram.php
 */

require_once __DIR__ . '/api/config.php';
require_once __DIR__ . '/api/telegram.php';

echo "🧪 Тестирование Telegram API\n";
echo "==========================\n\n";

// Проверяем конфигурацию
echo "📋 Проверка конфигурации:\n";
echo "TELEGRAM_BOT_TOKEN: " . (empty(TELEGRAM_BOT_TOKEN) ? "❌ НЕ НАСТРОЕН" : "✅ Настроен") . "\n";
echo "TELEGRAM_CHAT_ID: " . (empty(TELEGRAM_CHAT_ID) ? "❌ НЕ НАСТРОЕН" : TELEGRAM_CHAT_ID) . "\n\n";

if (empty(TELEGRAM_BOT_TOKEN) || empty(TELEGRAM_CHAT_ID)) {
    echo "❌ Ошибка: Telegram бот не настроен!\n";
    echo "Создайте файл .env и заполните TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID\n";
    exit(1);
}

// Тестируем статус бота
echo "🤖 Проверка статуса бота:\n";
try {
    $botStatus = checkBotStatus();
    if ($botStatus['status'] === 'success') {
        echo "✅ Бот активен: " . $botStatus['bot_info']['name'] . " (@" . $botStatus['bot_info']['username'] . ")\n";
    } else {
        echo "❌ Ошибка бота: " . $botStatus['message'] . "\n";
        exit(1);
    }
} catch (Exception $e) {
    echo "❌ Ошибка проверки бота: " . $e->getMessage() . "\n";
    exit(1);
}

echo "\n";

// Тестируем отправку сообщения
echo "📤 Тестирование отправки сообщения:\n";
try {
    $testResult = sendTestMessage();
    if ($testResult['status'] === 'success') {
        echo "✅ Тестовое сообщение отправлено успешно!\n";
        echo "Message ID: " . $testResult['telegram_response']['message_id'] . "\n";
        echo "Chat ID: " . $testResult['telegram_response']['chat_id'] . "\n";
        echo "Date: " . date('Y-m-d H:i:s', $testResult['telegram_response']['date']) . "\n";
    } else {
        echo "❌ Ошибка отправки: " . $testResult['message'] . "\n";
    }
} catch (Exception $e) {
    echo "❌ Исключение при отправке: " . $e->getMessage() . "\n";
}

echo "\n";

// Тестируем API endpoint
echo "🌐 Тестирование API endpoint:\n";
$testData = [
    'source' => 'test-script',
    'service' => 'test-service',
    'status' => 'up',
    'host' => 'test-host',
    'timestamp' => date('c'),
    'details' => [
        'test' => 'true',
        'script' => 'test_telegram.php'
    ]
];

echo "Отправляю тестовые данные:\n";
echo json_encode($testData, JSON_PRETTY_PRINT) . "\n\n";

try {
    $message = formatTelegramMessage($testData);
    echo "Сформированное сообщение:\n";
    echo "---\n" . $message . "\n---\n\n";
    
    $telegramResponse = sendToTelegram($message);
    echo "✅ Сообщение отправлено через API!\n";
    echo "Message ID: " . $telegramResponse['message_id'] . "\n";
} catch (Exception $e) {
    echo "❌ Ошибка API: " . $e->getMessage() . "\n";
}

echo "\n🎉 Тестирование завершено!\n";
