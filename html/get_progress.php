<?php
// get_progress.php
session_start();
header('Content-Type: application/json');

// 세션 ID 가져오기
$sessionId = session_id();
$progressFile = '/tmp/progress_' . $sessionId . '.txt';

$progress = 0;
$complete = false;

if (file_exists($progressFile)) {
    $data = file_get_contents($progressFile);
    $progressData = json_decode($data, true);
    if ($progressData !== null) {
        $progress = $progressData['progress'] ?? 0;
        $complete = $progressData['complete'] ?? false;
    }
}

echo json_encode([
    'progress' => $progress,
    'complete' => $complete,
]);
?>
