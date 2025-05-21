<?php
// 오류 로깅을 설정 (에러 로그 파일에 기록)
ini_set('log_errors', 1);
ini_set('error_log', '/path/to/php-error.log');

// POST로 받은 데이터 처리
$sn = isset($_POST['sn']) ? $_POST['sn'] : null;
$start_episode = isset($_POST['start_episode']) ? $_POST['start_episode'] : null;
$end_episode = isset($_POST['end_episode']) ? $_POST['end_episode'] : null;

// 필수 값이 누락된 경우
if (empty($sn) || empty($start_episode) || empty($end_episode)) {
    echo json_encode([
        'error' => '필수 값이 누락되었습니다. SN, 시작 화, 끝 화를 확인해주세요.'
    ]);
    exit;
}

// 인자들을 안전하게 처리하기 위해 escapeshellarg() 사용
$sn = escapeshellarg($sn);
$start_episode = escapeshellarg($start_episode);
$end_episode = escapeshellarg($end_episode);

// Python 스크립트 경로
$python_script = '/var/www/html/python_api/api2.py'; // 실제 경로로 수정 필요

// Python 스크립트 실행 명령어 작성
$command = "python3 $python_script $sn $start_episode $end_episode";

// 명령어 실행
$output = shell_exec($command . " 2>&1");  // 표준 오류도 함께 캡처

// Python 스크립트 실행 오류가 발생했을 경우
if ($output === null) {
    echo json_encode([
        'error' => 'Python 스크립트 실행 중 오류가 발생했습니다.'
    ]);
    exit;
}

// 정상적으로 처리된 경우 JSON 응답 반환
echo json_encode([
    'result' => $output,  // 처리된 결과 (웹툰 요약 등)
    'message' => '처리가 완료되었습니다.'
]);
?>
