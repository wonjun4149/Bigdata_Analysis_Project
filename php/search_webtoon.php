<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);
header('Content-Type: application/json');

$host = 'localhost';
$db = 'webtoon';
$user = 'root';
$pass = '123';

if (isset($_GET['title'])) {
    $title = $_GET['title'];

    $conn = new mysqli($host, $user, $pass, $db);
    if ($conn->connect_error) {
        echo json_encode(['error' => '데이터베이스 연결 실패: ' . $conn->connect_error]);
        exit;
    }
    $sql = "SELECT S_N, title, day, last FROM webtoon_info WHERE REPLACE(title, ' ', '') LIKE ? ORDER BY LENGTH(REPLACE(title, ' ', '')) ASC LIMIT 1";
    $stmt = $conn->prepare($sql);
    
    $searchTerm = '%' . str_replace(' ', '', $title) . '%';
    $stmt->bind_param('s', $searchTerm);
    $stmt->execute();
    $stmt->store_result();

    if ($stmt->num_rows > 0) {
        $stmt->bind_result($S_N, $title, $day, $last);
        $stmt->fetch();
        echo json_encode(['S_N' => $S_N, 'title' => $title, 'day' => $day, 'last' => $last]);
    } else {
        echo json_encode(['error' => '웹툰을 찾을 수 없습니다.']);
    }

    $stmt->close();
    $conn->close();
} else {
    echo json_encode(['error' => '검색어가 제공되지 않았습니다.']);
}
?>