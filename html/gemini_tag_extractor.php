<?php
header('Content-Type: application/json');

ini_set('display_errors', 1);
error_reporting(E_ALL);

$description = $_POST['description'] ?? '';

if (empty($description)) {
    echo json_encode(['error' => '내용이 비어있습니다.']);
    exit;
}

$pythonScriptPath = "/var/www/html/Python/gemini_tag_extractor_test.py";
$pythonExecutable = "python3";

$command = $pythonExecutable . " " . escapeshellcmd($pythonScriptPath) . " " . escapeshellarg($description);

$output = shell_exec($command . " 2>&1");

if ($output === null) {
    echo json_encode(['error' => '태그 추출 스크립트 실행에 실패했습니다.']);
    exit;
}

echo $output;