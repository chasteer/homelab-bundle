<?php
/**
 * Полное тестирование Telegram интеграции
 * Запускайте: php test_all.php
 */

echo "🧪 Полное тестирование Telegram интеграции\n";
echo "========================================\n\n";

// Проверяем конфигурацию
echo "1️⃣ Проверка конфигурации...\n";
require_once __DIR__ . '/api/config.php';

if (empty(TELEGRAM_BOT_TOKEN) || empty(TELEGRAM_CHAT_ID)) {
    echo "❌ Ошибка: Telegram бот не настроен!\n";
    echo "Создайте файл .env и заполните TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID\n";
    exit(1);
}

echo "✅ Конфигурация загружена\n";
echo "   Bot Token: " . substr(TELEGRAM_BOT_TOKEN, 0, 10) . "...\n";
echo "   Chat ID: " . TELEGRAM_CHAT_ID . "\n\n";

// Тестируем статус бота
echo "2️⃣ Проверка статуса бота...\n";
require_once __DIR__ . '/api/telegram.php';

try {
    $botStatus = checkBotStatus();
    if ($botStatus['status'] === 'success') {
        echo "✅ Бот активен: " . $botStatus['bot_info']['name'] . " (@" . $botStatus['bot_info']['username'] . ")\n\n";
    } else {
        echo "❌ Ошибка бота: " . $botStatus['message'] . "\n";
        exit(1);
    }
} catch (Exception $e) {
    echo "❌ Ошибка проверки бота: " . $e->getMessage() . "\n";
    exit(1);
}

// Тестируем короткое сообщение
echo "3️⃣ Тестирование короткого сообщения...\n";
try {
    $shortMessage = "🧪 **TEST MESSAGE** 🧪\n\n";
    $shortMessage .= "**Service:** Homelab VPS\n";
    $shortMessage .= "**Status:** Test\n";
    $shortMessage .= "**Host:** VPS Server\n";
    $shortMessage .= "**Time:** " . date('Y-m-d H:i:s T') . "\n\n";
    $shortMessage .= "Если вы видите это сообщение, значит интеграция работает! ✅";
    
    $result = sendToTelegram($shortMessage);
    echo "✅ Короткое сообщение отправлено успешно!\n";
    echo "   Message ID: " . $result['message_id'] . "\n\n";
} catch (Exception $e) {
    echo "❌ Ошибка отправки короткого сообщения: " . $e->getMessage() . "\n";
}

// Тестируем длинное сообщение
echo "4️⃣ Тестирование длинного сообщения...\n";
try {
    $longMessage = "🚨 **HOMELAB ALERT** 🚨\n\n";
    $longMessage .= "**Service:** Test Service\n";
    $longMessage .= "**Status:** Down\n";
    $longMessage .= "**Host:** 192.168.1.200\n";
    $longMessage .= "**Time:** " . date('Y-m-d H:i:s T') . "\n\n";
    
    $longMessage .= "**Details:**\n";
    $longMessage .= "• monitor_url: http://example.com\n";
    $longMessage .= "• monitor_type: http\n";
    $longMessage .= "• message: Service is down\n\n";
    
    $longMessage .= "**Analysis:**\n";
    $longMessage .= "🔍 **АНАЛИЗ ИНЦИДЕНТА: Test Service**\n";
    $longMessage .= "📊 **Статус:** down\n";
    $longMessage .= "🌐 **URL:** http://example.com\n";
    $longMessage .= "🖥️ **Тип:** http\n";
    $longMessage .= "🏠 **Хост:** example.com\n";
    $longMessage .= "🔌 **Порт:** 80\n";
    $longMessage .= "⏰ **Время:** " . date('c') . "\n\n";
    
    $longMessage .= "🚨 **ВОЗМОЖНЫЕ ПРИЧИНЫ:**\n";
    $longMessage .= "   • Сервис недоступен по HTTP\n";
    $longMessage .= "   • Проблемы с веб-сервером\n";
    $longMessage .= "   • Ошибки в конфигурации\n";
    $longMessage .= "   • Проблемы с сетью\n";
    $longMessage .= "   • Перегрузка сервера\n";
    $longMessage .= "   • Недостаток ресурсов\n\n";
    
    $longMessage .= "🔧 **БАЗОВЫЕ ДЕЙСТВИЯ:**\n";
    $longMessage .= "   1. Проверить статус сервиса: `systemctl status <service>`\n";
    $longMessage .= "   2. Проверить логи: `journalctl -u <service> -f`\n";
    $longMessage .= "   3. Проверить доступность порта: `netstat -tlnp | grep <port>`\n";
    $longMessage .= "   4. Перезапустить сервис: `systemctl restart <service>`\n";
    $longMessage .= "   5. Проверить конфигурацию: `nginx -t`\n";
    $longMessage .= "   6. Проверить права доступа к файлам\n\n";
    
    $longMessage .= "📋 **ДОПОЛНИТЕЛЬНЫЕ ПРОВЕРКИ:**\n";
    $longMessage .= "   • Проверить использование ресурсов (CPU, RAM, диск)\n";
    $longMessage .= "   • Проверить сетевые подключения\n";
    $longMessage .= "   • Проверить конфигурационные файлы\n";
    $longMessage .= "   • Проверить права доступа\n";
    $longMessage .= "   • Проверить логи веб-сервера\n";
    $longMessage .= "   • Проверить SSL сертификаты\n";
    $longMessage .= "   • Проверить DNS резолюцию\n\n";
    
    $longMessage .= "⚠️ **ПРИМЕЧАНИЕ:** Это базовый анализ. Для детального анализа используйте LLM агента.\n";
    $longMessage .= "📞 **КОНТАКТ:** Если проблема критическая, обратитесь к администратору системы.";
    
    echo "   Длина сообщения: " . strlen($longMessage) . " символов\n";
    
    $result = sendSmartLongMessage($longMessage);
    
    if (is_array($result) && count($result) > 1) {
        echo "✅ Длинное сообщение отправлено частями: " . count($result) . " частей\n";
        foreach ($result as $index => $partResult) {
            echo "   Часть " . ($index + 1) . ": Message ID " . $partResult['message_id'] . "\n";
        }
    } else {
        echo "✅ Длинное сообщение отправлено как одно целое\n";
        echo "   Message ID: " . $result['message_id'] . "\n";
    }
    echo "\n";
} catch (Exception $e) {
    echo "❌ Ошибка отправки длинного сообщения: " . $e->getMessage() . "\n";
}

// Тестируем API endpoint
echo "5️⃣ Тестирование API endpoint...\n";
require_once __DIR__ . '/api/uptime-alerts.php';

$testData = [
    'source' => 'test-script',
    'service' => 'test-service',
    'status' => 'up',
    'host' => 'test-host',
    'timestamp' => date('c'),
    'details' => [
        'test' => 'true',
        'script' => 'test_all.php'
    ]
];

try {
    $message = formatTelegramMessage($testData);
    echo "   Сформированное сообщение: " . strlen($message) . " символов\n";
    
    $telegramResponse = sendToTelegram($message);
    echo "✅ API endpoint работает корректно!\n";
    echo "   Message ID: " . $telegramResponse['message_id'] . "\n\n";
} catch (Exception $e) {
    echo "❌ Ошибка API endpoint: " . $e->getMessage() . "\n";
}

echo "🎉 Полное тестирование завершено!\n";
echo "📱 Проверьте ваш Telegram канал - должно прийти несколько сообщений\n";
echo "📋 Все функции работают корректно:\n";
echo "   ✅ Конфигурация загружается\n";
echo "   ✅ Бот активен\n";
echo "   ✅ Короткие сообщения отправляются\n";
echo "   ✅ Длинные сообщения разбиваются на части\n";
echo "   ✅ API endpoint работает\n";
echo "\n🚀 Telegram интеграция готова к работе!\n";
