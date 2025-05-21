<?php
// run_webtoon_download.php

// 오류 표시 설정 (개발 중에만 활성화)
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

session_start(); // 세션 시작
header('Content-Type: application/json');

// POST 데이터 가져오기
$S_N = isset($_POST['S_N']) ? $_POST['S_N'] : '';
$startEpisode = isset($_POST['startEpisode']) ? $_POST['startEpisode'] : '';
$endEpisode = isset($_POST['endEpisode']) ? $_POST['endEpisode'] : '';

if (!$S_N || !$startEpisode || !$endEpisode) {
    echo json_encode(['success' => false, 'message' => '필수 매개변수가 누락되었습니다.']);
    exit;
}

// 입력값 검증
if (!is_numeric($S_N) || !is_numeric($startEpisode) || !is_numeric($endEpisode)) {
    echo json_encode(['success' => false, 'message' => '잘못된 입력값입니다. 숫자를 입력해주세요.']);
    exit;
}

// $titleId를 $S_N으로 설정
$titleId = $S_N;

// 세션 초기화
$_SESSION['progress'] = 0;
$_SESSION['complete'] = false;

// 세션 ID 가져오기
$sessionId = session_id();
$escapedSessionId = escapeshellarg($sessionId);

// 명령어 생성
$pythonScript = '/var/www/html/Python/webtoon_download.py';

// 매개변수 이스케이프 처리
$escapedTitleId = escapeshellarg($titleId);
$escapedStart = escapeshellarg($startEpisode);
$escapedEnd = escapeshellarg($endEpisode);

// Python 실행 경로 확인 (절대 경로 사용)
$pythonExecutable = '/usr/bin/python3'; // 실제 python3의 경로 확인 필요

// 백그라운드에서 Python 스크립트 실행
$command = "$pythonExecutable $pythonScript $escapedTitleId $escapedStart $escapedEnd $escapedSessionId > /dev/null 2>/dev/null &";

// 명령어 실행
exec($command);

// 즉시 응답 반환
echo json_encode(['success' => true, 'message' => '작업이 시작되었습니다.']);
?>
