<?php
header('Content-Type: application/json');
date_default_timezone_set('UTC');

try {
    // Force absolute path for SQLite to prevent pathing issues on different servers
    $db = new PDO('sqlite:' . __DIR__ . '/database.sqlite');
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    // Ensure the table structure is always correct
    $db->exec("CREATE TABLE IF NOT EXISTS pastes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_code TEXT UNIQUE,
        content TEXT,
        is_encrypted INTEGER DEFAULT 0,
        expires_at DATETIME
    )");

    // MIGRATION: Auto-add column if missing from previous versions
    $cols = $db->query("PRAGMA table_info(pastes)")->fetchAll(PDO::FETCH_ASSOC);
    $hasEnc = false;
    foreach ($cols as $col) if ($col['name'] === 'is_encrypted') $hasEnc = true;
    if (!$hasEnc) $db->exec("ALTER TABLE pastes ADD COLUMN is_encrypted INTEGER DEFAULT 0");

    // EFFICIENCY: Auto-delete expired entries on every request
    $db->exec("DELETE FROM pastes WHERE expires_at < DATETIME('now')");

    $action = $_GET['action'] ?? '';

    if ($action == 'save' && $_SERVER['REQUEST_METHOD'] == 'POST') {
        $content = $_POST['content'] ?? '';
        $code = $_POST['code'] ?? ''; 
        $enc = isset($_POST['encrypted']) ? 1 : 0;
        
        if (empty($content) || empty($code)) {
            echo json_encode(["success" => false, "message" => "Missing content or code"]);
            exit;
        }

        $expires_at = date("Y-m-d H:i:s", strtotime('+10 minutes'));
        
        // Use REPLACE instead of INSERT to allow re-using codes if they exist (though rare with 10k range)
        $stmt = $db->prepare("INSERT OR REPLACE INTO pastes (room_code, content, is_encrypted, expires_at) VALUES (?, ?, ?, ?)");
        if ($stmt->execute([$code, $content, $enc, $expires_at])) {
            echo json_encode(["success" => true, "code" => $code]);
        }
    }

    if ($action == 'fetch') {
        $code = $_GET['code'] ?? '';
        $stmt = $db->prepare("SELECT content, is_encrypted FROM pastes WHERE room_code = ? AND expires_at > DATETIME('now')");
        $stmt->execute([$code]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);

        if ($row) {
            echo json_encode([
                "success" => true, 
                "content" => $row['content'],
                "is_encrypted" => (bool)$row['is_encrypted']
            ]);
        } else {
            echo json_encode(["success" => false, "message" => "Code expired or not found."]);
        }
    }
} catch (Exception $e) {
    echo json_encode(["success" => false, "message" => "Server Error: " . $e->getMessage()]);
}
?>