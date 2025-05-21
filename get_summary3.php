<?php
// MySQL 데이터베이스 연결 설정
$host = 'localhost';
$db = 'webtoon';
$user = 'webtoon_user';
$pass = '1234';

// S_N과 화수 범위를 받아서 처리
if (isset($_GET['S_N'], $_GET['start'], $_GET['end'])) {
    $S_N = $_GET['S_N'];
    $start = $_GET['start'];
    $end = $_GET['end'];

    // DB 연결
    $conn = new mysqli($host, $user, $pass, $db);
    if ($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error);
    }

    // 데이터베이스에서 해당 화수 데이터 확인
    $sql = "SELECT episode, line FROM webtoon_text WHERE S_N = ? AND episode BETWEEN ? AND ?";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param('iii', $S_N, $start, $end);
    $stmt->execute();
    $stmt->store_result();

    $episodes = [];
    $stmt->bind_result($episode, $line);
    while ($stmt->fetch()) {
        $episodes[] = "화 {$episode}: {$line}";
    }

    if (count($episodes) > 0) {
        // GPT API 호출하여 요약 결과 반환
        $input_text = implode("\n", $episodes);
        $summary = get_gpt_summary($input_text);
        echo json_encode(['result' => $summary]);
    } else {
        // 데이터가 없으면 auto_update.py 호출
        $auto_update_script = '/var/www/html/Python/auto_update.py';  // 경로 수정
        $command = escapeshellcmd("python3 $auto_update_script $S_N $start $end");
        $output = shell_exec($command . " 2>&1"); // Python 출력 확인
        error_log("Auto update script output: " . $output);

        // 데이터베이스 다시 확인
        $stmt->execute();
        $stmt->store_result();

        $episodes = [];
        $stmt->bind_result($episode, $line);
        while ($stmt->fetch()) {
            $episodes[] = "화 {$episode}: {$line}";
        }

        if (count($episodes) > 0) {
            $input_text = implode("\n", $episodes);
            $summary = get_gpt_summary($input_text);
            echo json_encode(['result' => $summary]);
        } else {
            error_log("No data added to the database after running Python script.");
            echo json_encode(['error' => '데이터를 추가했지만 요약에 실패했습니다.']);
        }
    }

    $stmt->close();
    $conn->close();
}

// GPT 요약 호출 함수
function get_gpt_summary($text) {
    $api_script = '/var/www/html/python_api/api3.py'; // 경로 수정
    $encoded_text = escapeshellarg($text);
    $command = "python3 $api_script $encoded_text";
    $result = shell_exec($command . " 2>&1");
    error_log("Python script output: " . $result);

    $response = json_decode($result, true);
    return $response['result'] ?? 'GPT API 호출 오류';
}
?>
