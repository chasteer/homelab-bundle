<?php
/**
 * Telegram Bot интеграция для Homelab VPS
 * ТОЛЬКО отправка уведомлений - никаких команд!
 */

/**
 * Отправляет сообщение в Telegram
 * @throws Exception
 */
function sendToTelegram($message): array
{
    if (empty(TELEGRAM_BOT_TOKEN) || empty(TELEGRAM_CHAT_ID)) {
        throw new Exception('Telegram bot not configured');
    }
    
    // Логируем детали запроса (без токена)
    error_log("Telegram API request - Chat ID: " . TELEGRAM_CHAT_ID . ", Message length: " . strlen($message));
    
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
        $error = error_get_last();
        $errorMsg = $error ? $error['message'] : 'Unknown error';
        throw new Exception('Failed to send message to Telegram: ' . $errorMsg);
    }
    
    $response = json_decode($result, true);
    
    if (!$response['ok']) {
        $errorCode = $response['error_code'] ?? 'Unknown';
        $errorDescription = $response['description'] ?? 'Unknown error';
        throw new Exception("Telegram API error [{$errorCode}]: {$errorDescription}");
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
function checkBotStatus(): array
{
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
 * Отправляет длинное сообщение частями с задержкой
 */
function sendLongMessage($message, $maxLength = 4000): array
{
    if (strlen($message) <= $maxLength) {
        return sendToTelegram($message);
    }
    
    // Разбиваем сообщение на части
    $parts = [];
    $lines = explode("\n", $message);
    $currentPart = '';
    
    foreach ($lines as $line) {
        if (strlen($currentPart . $line . "\n") > $maxLength) {
            if (!empty($currentPart)) {
                $parts[] = trim($currentPart);
                $currentPart = $line . "\n";
            } else {
                // Если одна строка слишком длинная, обрезаем её
                $parts[] = substr($line, 0, $maxLength - 3) . '...';
            }
        } else {
            $currentPart .= $line . "\n";
        }
    }
    
    if (!empty($currentPart)) {
        $parts[] = trim($currentPart);
    }
    
    $results = [];
    $totalParts = count($parts);
    
    foreach ($parts as $index => $part) {
        $partMessage = $part;
        if ($totalParts > 1) {
            $partMessage = "📄 **Часть " . ($index + 1) . "/" . $totalParts . "**\n\n" . $part;
        }
        
        // Отправляем часть
        $results[] = sendToTelegram($partMessage);
        
        // Добавляем задержку между частями (кроме последней)
        if ($index < $totalParts - 1) {
            sleep(1); // 1 секунда задержки
        }
    }
    
    return $results;
}

/**
 * Отправляет длинное сообщение с умной разбивкой по смысловым блокам
 */
function sendSmartLongMessage($message, $maxLength = 4000): array
{
    if (strlen($message) <= $maxLength) {
        return sendToTelegram($message);
    }
    
    // Разбиваем сообщение по смысловым блокам
    $parts = [];
    $sections = preg_split('/(\n\*\*[^*]+\*\*:?\n)/', $message, -1, PREG_SPLIT_DELIM_CAPTURE);
    
    $currentPart = '';
    $sectionIndex = 0;
    
    while ($sectionIndex < count($sections)) {
        $section = $sections[$sectionIndex];
        
        // Если это заголовок секции
        if (preg_match('/\n\*\*[^*]+\*\*:?\n/', $section)) {
            // Проверяем, поместится ли заголовок + следующий контент
            $nextContent = isset($sections[$sectionIndex + 1]) ? $sections[$sectionIndex + 1] : '';
            
            if (strlen($currentPart . $section . $nextContent) > $maxLength) {
                if (!empty($currentPart)) {
                    $parts[] = trim($currentPart);
                    $currentPart = $section . $nextContent;
                } else {
                    $currentPart = $section . $nextContent;
                }
                $sectionIndex += 2; // Пропускаем заголовок и контент
            } else {
                $currentPart .= $section . $nextContent;
                $sectionIndex += 2; // Пропускаем заголовок и контент
            }
        } else {
            $currentPart .= $section;
            $sectionIndex++;
        }
        
        // Если текущая часть слишком длинная, обрезаем её
        if (strlen($currentPart) > $maxLength) {
            $parts[] = substr($currentPart, 0, $maxLength - 3) . '...';
            $currentPart = '';
        }
    }
    
    if (!empty($currentPart)) {
        $parts[] = trim($currentPart);
    }
    
    $results = [];
    $totalParts = count($parts);
    
    foreach ($parts as $index => $part) {
        $partMessage = $part;
        if ($totalParts > 1) {
            $partMessage = "📄 **Часть " . ($index + 1) . "/" . $totalParts . "**\n\n" . $part;
        }
        
        // Отправляем часть
        $results[] = sendToTelegram($partMessage);
        
        // Добавляем задержку между частями (кроме последней)
        if ($index < $totalParts - 1) {
            sleep(1); // 1 секунда задержки
        }
    }
    
    return $results;
}

/**
 * Отправляет тестовое сообщение (только для проверки настройки)
 */
function sendTestMessage(): array
{
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
