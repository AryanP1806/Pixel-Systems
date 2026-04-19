<?php
/**
 * FlashPaste Pro API - Redesigned
 * Enforces 4-digit codes & Comprehensive Logging
 */

$DATA_DIR = __DIR__ . '/rooms';
$LOG_FILE = __DIR__ . '/logs/app.log';

if (!file_exists($DATA_DIR)) mkdir($DATA_DIR, 0777, true);
if (!file_exists(dirname($LOG_FILE))) mkdir(dirname($LOG_FILE), 0777, true);

function log_event($status, $message, $code = "0000") {
    global $LOG_FILE;
    $time = date('Y-m-d H:i:s');
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
    $entry = "[$time] [$status] [CODE:$code] [IP:$ip] $message" . PHP_EOL;
    file_put_contents($LOG_FILE, $entry, FILE_APPEND);
}

header('Content-Type: application/json');
$action = $_GET['action'] ?? '';

if ($action === 'save') {
    $code = preg_replace('/[^0-9]/', '', $_POST['code'] ?? '');
    $content = $_POST['content'] ?? '';
    $is_encrypted = ($_POST['encrypted'] === 'true');

    if (strlen($code) !== 4 || empty($content)) {
        log_event("ERROR", "Save failed: Code not 4 digits or empty content", $code);
        echo json_encode(['success' => false, 'message' => 'Invalid Request']);
        exit;
    }

    $file = "$DATA_DIR/$code.txt";
    $payload = json_encode([
        'content' => $content,
        'encrypted' => $is_encrypted,
        'created_at' => time()
    ]);

    if (file_put_contents($file, $payload)) {
        log_event("SUCCESS", "Data saved successfully (" . strlen($content) . " bytes)", $code);
        echo json_encode(['success' => true, 'code' => $code]);
    } else {
        log_event("CRITICAL", "Failed to write file to storage", $code);
        echo json_encode(['success' => false, 'message' => 'Storage Error']);
    }
    exit;
}

if ($action === 'fetch') {
    $code = preg_replace('/[^0-9]/', '', $_GET['code'] ?? '');

    if (strlen($code) !== 4) {
        log_event("ERROR", "Fetch attempt with invalid code format", $code);
        echo json_encode(['success' => false, 'message' => 'Enter 4 digits']);
        exit;
    }

    $file = "$DATA_DIR/$code.txt";
    if (!file_exists($file)) {
        log_event("NOT_FOUND", "Attempted to fetch non-existent room", $code);
        echo json_encode(['success' => false, 'message' => 'Room not found']);
        exit;
    }

    $data = json_decode(file_get_contents($file), true);
    log_event("SUCCESS", "Room fetched successfully", $code);
    echo json_encode([
        'success' => true,
        'content' => $data['content'],
        'encrypted' => $data['encrypted'] ?? false
    ]);
    exit;
}

log_event("INVALID", "Invalid action requested: $action");
echo json_encode(['success' => false, 'message' => 'Invalid action']);