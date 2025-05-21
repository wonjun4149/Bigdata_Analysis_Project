<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>원준이의 웹툰요약소</title>
    <link href="https://fonts.googleapis.com/css2?family=Jua&display=swap" rel="stylesheet">
    <style>
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
            justify-content: flex-start; /* 왼쪽 정렬 */
            align-items: center;
            gap: 40px;
        }
        .logo {
            text-decoration: none;
            font-size: 1.5rem;
            color: #333;
            font-family: 'Jua', sans-serif; /* 웹툰 추천소와 동일한 폰트 */
            font-weight: bold; /* 강조 */
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
        .popup {
            display: none;
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 400px;
            background: white;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            z-index: 1000;
        }
        .popup-header {
            background: #333;
            color: white;
            padding: 10px;
            border-radius: 8px 8px 0 0;
            font-size: 18px;
            text-align: center;
        }
        .popup-content {
            padding: 20px;
        }
        .popup-footer {
            text-align: right;
            padding: 10px;
            border-top: 1px solid #ddd;
        }
        .popup-footer button {
            padding: 5px 10px;
            background: #333;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .popup-footer button:hover {
            background: #555;
        }
        #progress-container {
            margin-top: 20px;
            width: 100%;
            background: #ddd;
            border-radius: 8px;
            overflow: hidden;
        }
        #progress-bar {
            width: 0;
            height: 30px;
            background: #4CAF50;
        }
        #progress-text {
            margin-top: 10px;
            font-size: 1.2rem;
        }
    </style>
</head>
<body>
<header>
    <div class="logo-group">
        <a href="/index.php" class="logo">원준이의 웹툰세상</a>
        <a href="/html/recommand_main.php" class="logo">원준이의 웹툰추천소</a>
    </div>
</header>
<main>
    <h1>원준이의 웹툰요약소</h1>
    <div class="search-container">
        <form id="search-form">
            <input type="text" id="search-query" placeholder="검색어를 입력하세요">
            <button type="submit">&#128269;</button>
        </form>
    </div>
</main>

<div class="popup" id="search-popup">
    <div class="popup-header">검색 결과</div>
    <div class="popup-content">
        <p><strong>웹툰 제목:</strong> <span id="webtoon-title"></span></p>
        <div>
            <label>시작 화:</label>
            <input type="number" id="start-episode" placeholder="예: 1">
        </div>
        <div>
            <label>마지막 화:</label>
            <input type="number" id="end-episode" placeholder="예: 10">
        </div>
    </div>
    <div class="popup-footer">
        <button id="submit-request">요약 요청</button>
        <button onclick="closePopup()">닫기</button>
    </div>
</div>

<div class="popup" id="progress-popup">
    <div class="popup-header">진행률</div>
    <div class="popup-content">
        <div id="progress-container">
            <div id="progress-bar"></div>
        </div>
        <p id="progress-text">진행률: 0%</p>
    </div>
</div>

<div class="popup" id="result-popup">
    <div class="popup-header">요약 결과</div>
    <div class="popup-content">
        <p id="summary-text"></p>
    </div>
    <div class="popup-footer">
        <button onclick="closePopup()">닫기</button>
    </div>
</div>

<script>
let currentWebtoonId = null;

function openPopup(popupId) {
    document.querySelectorAll('.popup').forEach(popup => popup.style.display = 'none');
    document.getElementById(popupId).style.display = 'block';
}

function closePopup() {
    document.querySelectorAll('.popup').forEach(popup => popup.style.display = 'none');
}

document.getElementById('search-form').addEventListener('submit', function (e) {
    e.preventDefault();
    const query = document.getElementById('search-query').value.trim();

    if (!query) {
        alert('검색어를 입력하세요.');
        return;
    }

    fetch(`/search_webtoon3.php?title=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }

            document.getElementById('webtoon-title').textContent = data.title || '제목 없음';
            currentWebtoonId = data.S_N;
            openPopup('search-popup');
        })
        .catch(error => {
            console.error('검색 중 오류 발생:', error);
            alert('검색 중 문제가 발생했습니다.');
        });
});

document.getElementById('submit-request').addEventListener('click', function () {
    const startEpisode = document.getElementById('start-episode').value;
    const endEpisode = document.getElementById('end-episode').value;

    if (!startEpisode || !endEpisode) {
        alert('시작 화와 마지막 화를 입력하세요.');
        return;
    }

    openPopup('progress-popup');
    checkProgress();

    fetch(`/get_summary3.php?S_N=${currentWebtoonId}&start=${startEpisode}&end=${endEpisode}`)
        .then(response => response.json())
        .then(data => {
            if (data.result) {
                document.getElementById('summary-text').textContent = data.result;
                openPopup('result-popup');
            } else {
                alert("요약 실패: " + data.error);
            }
        })
        .catch(error => {
            console.error('요약 요청 중 오류 발생:', error);
            alert('요약 요청 중 문제가 발생했습니다.');
        });
});

function checkProgress() {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');

    function fetchProgress() {
        fetch(`/progress.php?S_N=${currentWebtoonId}`)
            .then(response => response.json())
            .then(data => {
                const progress = data.progress || 0;
                progressBar.style.width = progress + '%';
                progressText.textContent = `진행률: ${progress}%`;

                if (progress < 100) {
                    setTimeout(fetchProgress, 1000);
                }
            })
            .catch(error => console.error('진행률 확인 중 오류 발생:', error));
    }

    fetchProgress();
}
</script>
</body>
</html>
