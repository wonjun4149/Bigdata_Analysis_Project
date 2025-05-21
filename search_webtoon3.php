<?php
// MySQL 데이터베이스 연결 설정
$host = 'localhost';
$db = 'webtoon';
$user = 'webtoon_user';
$pass = '1234';

// 제목으로 웹툰을 검색하여 S_N 번호를 반환하는 코드
if (isset($_GET['title'])) {
    $title = $_GET['title'];

    // DB 연결
    $conn = new mysqli($host, $user, $pass, $db);
    if ($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error);
    }

    $sql = "SELECT S_N, title FROM webtoon_info WHERE title LIKE ?";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param('s', $title);
    $stmt->execute();
    $stmt->store_result();

    if ($stmt->num_rows > 0) {
        $stmt->bind_result($S_N, $title);
        $stmt->fetch();
        echo json_encode(['S_N' => $S_N, 'title' => $title]);
    } else {
        echo json_encode(['error' => '웹툰을 찾을 수 없습니다.']);
    }

    $stmt->close();
    $conn->close();
}
?>
