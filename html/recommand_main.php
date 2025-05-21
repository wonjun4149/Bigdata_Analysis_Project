<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $userInput = $_POST['text'] ?? '';

    if (empty($userInput)) {
        // 사용자가 검색어를 입력하지 않았을 때 오류 반환
        echo json_encode(['error' => '검색어를 입력해주세요.']);
        exit;
    }

    // MySQL 연결
    $connection = new mysqli('localhost', 'webtoon_user', '1234', 'webtoon');

    if ($connection->connect_error) {
        echo json_encode(['error' => '데이터베이스 연결 오류: ' . $connection->connect_error]);
        exit;
    }

    // Python 스크립트 실행
    $pythonScript = escapeshellcmd("python3 /var/www/html/Python/recommand.py '" . addslashes($userInput) . "'");
    $output = shell_exec($pythonScript);
    

    if ($output === null) {
        // Python 스크립트 실행 오류 처리
        echo json_encode(['error' => '추천 처리 중 오류가 발생했습니다.']);
        exit;
    }

    // Python 출력 결과를 JSON으로 반환
    $decodedOutput = json_decode($output, true);

    if (isset($decodedOutput['error'])) {
        echo json_encode(['error' => $decodedOutput['error']]);
        exit;
    }

    // 추천된 웹툰의 S_N 추출
    $snList = $decodedOutput['recommended'];
    if (empty($snList)) {
        echo json_encode(['error' => '추천할 웹툰을 찾을 수 없습니다.']);
        exit;
    }

    // S_N을 이용한 쿼리 준비
    $placeholders = implode(',', array_fill(0, count($snList), '?'));
    $query = "SELECT title, tag, summary, S_N FROM webtoon_info WHERE S_N IN ($placeholders)";
    
    // SQL 쿼리 실행
    if ($stmt = $connection->prepare($query)) {
        $stmt->bind_param(str_repeat('i', count($snList)), ...$snList); // S_N 바인딩
        $stmt->execute();
        $result = $stmt->get_result();

        if ($result->num_rows === 0) {
            echo json_encode(['error' => '해당하는 웹툰을 찾을 수 없습니다.']);
            exit;
        }

        // 결과 처리
        $webtoonInfo = [];
        while ($row = $result->fetch_assoc()) {
            $webtoonInfo[] = [
                'title' => $row['title'],
                'tag' => $row['tag'],
                'summary' => $row['summary'],
                'S_N' => $row['S_N']
            ];
        }

        // 추천 결과 반환
        echo json_encode(['recommended' => $webtoonInfo]);
    } else {
        echo json_encode(['error' => '쿼리 준비 중 오류가 발생했습니다.']);
    }

    // MySQL 연결 종료
    $connection->close();
    exit;
}
?>

<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>원준이의 웹툰추천소</title>
    <link rel="stylesheet" href="/CSS/summary_main.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Jua&display=swap" rel="stylesheet">
    <script>
async function handleSearch() {
    const userInput = document.getElementById('search-input').value;

    if (!userInput) {
        alert('검색어를 입력해주세요.');
        return;
    }

    try {
        // PHP로 입력값 전달
        const response = await fetch('/html/recommand_main.php', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `text=${encodeURIComponent(userInput)}`
        });

        const data = await response.json();

        // 서버에서 오류 메시지가 반환되면 처리
        if (data.error) {
            alert(data.error);
        } else {
            let resultHTML = '<div class="webtoon-cards-container">'; // 카드 컨테이너 시작
            data.recommended.forEach((webtoon) => {
                // S_N을 URL 뒤에 그대로 추가
                const webtoonUrl = `https://comic.naver.com/webtoon/list?titleId=${webtoon.S_N}`;

                // 웹툰 카드 생성, 클릭 시 해당 URL로 이동
                resultHTML += `
                    <div class="webtoon-card" onclick="window.location.href='${webtoonUrl}'">
                        <h3 class="webtoon-title">${webtoon.title}</h3>
                        <p class="webtoon-tag"><strong>태그:</strong><br> ${webtoon.tag}</p>
                        <p class="webtoon-summary"><strong>요약:</strong><br> ${webtoon.summary}</p>
                    </div>
                `;
            });
            resultHTML += '</div>'; // 카드 컨테이너 종료
            document.getElementById('result').innerHTML = resultHTML;
        }
    } catch (error) {
        console.error('Error:', error);
        alert('추천 처리 중 오류가 발생했습니다.');
    }
}
</script>

<style>
    .webtoon-cards-container {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 20px;
        margin-top: 20px;
    }
    .webtoon-card {
        background-color: #f9f9f9;
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        text-align: left;
    }
    .webtoon-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .webtoon-tag, .webtoon-summary, .webtoon-serial-number {
        font-size: 1.1rem;
        margin-bottom: 10px;
    }
    .webtoon-tag strong, .webtoon-summary strong, .webtoon-serial-number strong {
        display: inline-block;
        margin-bottom: 5px;
    }
    .webtoon-tag, .webtoon-summary, .webtoon-serial-number {
        white-space: pre-line; /* 줄바꿈 허용 */
    }
    body {
        font-family: 'Jua', sans-serif;
        margin: 0;
        padding: 0;
        text-align: center;
    }
    header {
        background-color: #f4f4f4;
        padding: 10px;
        border-bottom: 1px solid #ccc;
    }
    .logo-group {
        display: flex;
        justify-content: center;
        gap: 20px;
    }
    .logo {
        text-decoration: none;
        font-size: 1.5rem;
        color: #333;
    }
    main {
        padding: 50px 20px;
        position: absolute; 
        left: 50%; 
        top: 50%; 
        transform: translate(-50%, -50%);
    }
    h1 {
        margin-bottom: 30px;
        font-size: 2.5rem;
        color: #333;
    }
    .search-container {
        position: relative;
        width: 600px;
        margin: 0 auto;
    }
    .search-container input[type="text"] {
        width: 100%;
        padding: 15px 60px 15px 20px; /* 버튼 공간 확보 */
        font-size: 1.2rem;
        border: 2px solid #ccc;
        border-radius: 50px;
        outline: none;
        box-sizing: border-box;
    }
    .search-container button {
        position: absolute;
        right: 10px; /* 버튼이 입력창 오른쪽 끝에 붙음 */
        top: 50%;
        transform: translateY(-50%);
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        cursor: pointer;
    }
    .search-container button:hover {
        background-color: #45a049;
    }
    #result {
        margin-top: 20px;
        font-size: 1.2rem;
        color: #333;
        text-align: left; /* 결과를 왼쪽 정렬로 */
    }
</style>
</head>
<body>

<header>
    <div class="logo-group">
        <a href="/index.php" class="logo">원준이의 웹툰세상</a>
        <a href="/html/test3.php" class="logo">원준이의 웹툰요약소</a>
    </div>
</header>

<main>
    <h1>원준이의 웹툰추천소</h1> 
    <div class="search-container">
        <input id="search-input" type="text" placeholder="원하는 스타일의 웹툰을 입력하세요">
        <button onclick="handleSearch()">&#128269;</button>
    </div>
    <p id="result"></p>
</main>

</body>
</html>
