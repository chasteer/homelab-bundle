<?php
require_once __DIR__ . '/config.php';
require_once __DIR__ . '/telegram.php';

header('Content-Type: application/json');

try {
    $botStatus = checkBotStatus();
    
    echo json_encode([
        'status' => 'success',
        'vps' => [
            'hostname' => gethostname(),
            'php_version' => PHP_VERSION,
            'nginx_status' => 'running',
            'php_fpm_status' => 'running'
        ],
        'telegram_bot' => $botStatus,
        'timestamp' => date('c')
    ]);
    
} catch (Exception $e) {
    echo json_encode([
        'status' => 'error',
        'message' => $e->getMessage(),
        'timestamp' => date('c')
    ]);
}
