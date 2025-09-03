<?php
/**
 * Telegram Bot интеграция для Homelab VPS
 * ТОЛЬКО отправка уведомлений - никаких команд!
 */

/**
 * Отправляет сообщение в Telegram
 */
function sendToTelegram($message) {
    if (empty(TELEGRAM_BOT_TOKEN) || empty(TELEGRAM_CHAT_ID)) {
        throw new Exception('Telegram bot not configured');
    }
    
    $url = "https://api.telegram.org/bot" . TELEGRAM_BOT_TOKEN . "/sendMessage";
    
    $data = [
        'chat_id' => TELEGRAM_CHAT_ID,
        'text' => $message,
        'parse_mode' => 'Markdown',
        'disable_web_page_preview' => true,
        'disable_notification' => false // Уведомления включены
    ];
    
    $options = [
        'http' => [
            'method' => 'POST',
            'header' => 'Content-Type: application/x-www-form-urlencoded',
            'content' => http_build_query($data),
            'timeout' => REQUEST_TIMEOUT
        ]
    ];
    
    $context = stream_context_create($options);
    $result = file_get_contents($url, false, $context);
    
    if ($result === false) {
        throw new Exception('Failed to send message to Telegram');
    }
    
    $response = json_decode($result, true);
    
    if (!$response['ok']) {
        throw new Exception('Telegram API error: ' . ($response['description'] ?? 'Unknown error'));
    }
    
    return [
        'message_id' => $response['result']['message_id'],
        'chat_id' => $response['result']['chat']['id'],
        'date' => $response['result']['date']
    ];
}

/**
 * Проверяет статус бота (только для диагностики)
 */
function checkBotStatus() {
    if (empty(TELEGRAM_BOT_TOKEN)) {
        return ['status' => 'error', 'message' => 'Bot token not configured'];
    }
    
    $url = "https://api.telegram.org/bot" . TELEGRAM_BOT_TOKEN . "/getMe";
    
    $result = file_get_contents($url);
    if ($result === false) {
        return ['status' => 'error', 'message' => 'Failed to connect to Telegram API'];
    }
    
    $response = json_decode($result, true);
    
    if (!$response['ok']) {
        return ['status' => 'error', 'message' => 'Telegram API error: ' . ($response['description'] ?? 'Unknown error')];
    }
    
    return [
        'status' => 'success',
        'bot_info' => [
            'id' => $response['result']['id'],
            'name' => $response['result']['first_name'],
            'username' => $response['result']['username']
        ]
    ];
}

/**
 * Отправляет тестовое сообщение (только для проверки настройки)
 */
function sendTestMessage() {
    try {
        $testMessage = "🧪 **TEST MESSAGE** 🧪\n\n";
        $testMessage .= "**Service:** Homelab VPS\n";
        $testMessage .= "**Status:** Test\n";
        $testMessage .= "**Host:** VPS Server\n";
        $testMessage .= "**Time:** " . date('Y-m-d H:i:s T') . "\n\n";
        $testMessage .= "Если вы видите это сообщение, значит интеграция работает! ✅";
        
        $result = sendToTelegram($testMessage);
        
        return [
            'status' => 'success',
            'message' => 'Test message sent successfully',
            'telegram_response' => $result
        ];
        
    } catch (Exception $e) {
        return [
            'status' => 'error',
            'message' => 'Failed to send test message: ' . $e->getMessage()
        ];
    }
}
