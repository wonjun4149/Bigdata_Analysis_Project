<?php
putenv("AIzaSyCYs36VA-vB75FoP8zkjC_PAEjvEubn02U");

$host = 'localhost';
$db   = 'webtoon';
$user = 'root';
$pass = '123';

if (isset($_GET['S_N'], $_GET['start'], $_GET['end'])) {
    $S_N   = $_GET['S_N'];
    $start = $_GET['start'];
    $end   = $_GET['end'];

    $conn = new mysqli($host, $user, $pass, $db);
    if ($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error);
    }

    $sql  = "SELECT episode, line FROM webtoon_text WHERE S_N = ? AND episode BETWEEN ? AND ?";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param('iii', $S_N, $start, $end);
    $stmt->execute();
    $stmt->store_result();

    $expectedCount = $end - $start + 1;
    $numFound = $stmt->num_rows;

    if ($numFound < $expectedCount) {
        $auto_update_script = '/var/www/html/Python/auto_update.py';  // 절대 경로 사용
        $command = escapeshellcmd("python3 $auto_update_script $S_N $start $end");
        $output  = shell_exec($command . " 2>&1");
        error_log("Auto update script output: " . $output);

        $stmt->execute();
        $stmt->store_result();
    }

    $episodes = [];
    $stmt->bind_result($episode, $line);
    while ($stmt->fetch()) {
        $episodes[] = "화 {$episode}: {$line}";
    }

    if (count($episodes) > 0) {
        $input_text = implode("\n", $episodes);
        $summary = get_gemini_summary($input_text);
        echo json_encode(['result' => $summary]);
    } else {
        error_log("No data added to the database after running auto_update.py.");
        echo json_encode(['error' => '데이터를 추가했지만 요약에 실패했습니다.']);
    }

    $stmt->close();
    $conn->close();
} else {
    echo json_encode(['error' => '필요한 매개변수가 제공되지 않았습니다.']);
}

function get_gemini_summary($text) {
    $api_script   = '/var/www/html/Python/summary_api.py';
    $encoded_text = escapeshellarg($text);
    $task_type    = escapeshellarg("summary");  // summary 작업 명시
    $command      = "python3 $api_script $encoded_text $task_type";
    $result       = shell_exec($command . " 2>&1");
    error_log("Python script output: " . $result);
    $response     = json_decode($result, true);
    return $response['result'] ?? 'Gemini API 호출 오류';
}
?>