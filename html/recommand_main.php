<?php
$tags = [
    '장르' => [
        'SF', 'SF액션', '개그', '느와르', '다크판타지', '드라마', '로맨스', '리얼로맨스', '미스터리', '무협/사극', '병맛', '스포츠', '스릴러', '시대물', '시리어스', '액션', '액션아포칼립스', '액션판타지', '오컬트', '오컬트판타지', '일상', '일상개그힐링', '중세판타지액션', '청춘', '판무', '판타지', '판타지개그', '학원로맨스', '학원액션', '하이틴', '현대판타지'
    ],
    '소재' => [
        '4차원', '감염', '게임', '게임판타지', '격투기', '괴담', '과거', '군림녀', '궁중로맨스', '귀족', '농구', '농사', '던전물', '데스게임', '동물', '동양', '두뇌싸움', '라이벌', '머니게임', '모험', '미래', '밀리터리', '배틀', '뱀파이어', '범죄', '법정드라마', '복수극', '빙의', '사이비종교', '사내연애', '사회고발', '상태창', '생존', '서바이벌', '서양', '성장드라마', '성장물', '소년물', '소년왕도물', '스포츠성장', '시대물', '신화', '아카데미물', '아포칼립스', '아이돌', '연예계', '오피스', '요리', '용사', '우정', '육아물', '음악', '의학', '이능력', '이능력배틀물', '이세계', '이세계요리', '인생역전', '인외존재', '전쟁', '정치', '정통무협', '좀비', '직업드라마', '차원이동', '참교육', '최강자전', '축구', '캠퍼스', '크리처', '타임슬립', '판타지', '학원물', '해외작품', '헌터물', '현대', '환골탈태', '환생', '회귀', '역사', '역사물'
    ],
    '캐릭터' => [
        '집착남', '집착녀', '직진남', '직진녀', '중년', '인플루언서', '걸크러시', '가벼운', '계략남', '계략녀', '고인물', '공식미남', '공식미녀', '까칠남', '까칠녀', '나쁜남자', '낮져밤이', '능글남', '능력남', '능력녀', '다정남', '다정녀', '다크히어로', '대형견남', '먼치킨', '명랑녀', '무심남', '무심녀', '무해한', '문란남', '문란녀', '빌런', '사연남', '사연녀', '소심남', '소심녀', '순정남', '순정녀', '순진남', '순진녀', '악녀', '악역이주인공', '아방녀', '얼빠녀', '연상녀', '연하남', '왕족', '외유내강녀', '유혹남', '유혹녀', '재벌', '재벌남', '재벌녀', '절망적인', '짐승남', '짝사랑남', '짝사랑녀', '철벽녀', '치명적인', '평범남', '평범녀', '폭스남', '햇살남', '햇살녀', '햇살캐', '헌신남', '혐관', '후회남', '후회물', '힘숨찐', '히어로'
    ],
    '관계/로맨스' => [
        '역하렘', '감성드라마', '결혼생활', '계약연애', '고자극로맨스', '궁중로맨스', '동양풍로맨스', '로맨스 코미디', '로맨틱코미디', '로판', '비밀연애', '삼각관계', '선결혼후연애', '소꿉친구', '아이돌연애', '연애/결혼공감', '연예계로맨스', '연상연하', '오피스로맨스', '재회', '전남친', '집착물', '짝사랑', '첫사랑', '청춘로맨스', '캠퍼스로맨스', '하렘', '학원로맨스', '할리퀸', '혐관로맨스'
    ],
    '분위기/기타' => [
        '서스펜스', '성장로판', '퓨전사극', '동양풍판타지', '중세', '예술', '공포', '음식&요리', '캠퍼스', '동아리', '4컷만화', '감성', '감성적인', '공감', '공감성수치', '구원서사', '눈물샘자극', '드라마&영화', '레드스트링', '레드아이스', '레트로', '러브코미디', '러블리', '명작', '미친작화', '블랙코미디', '블루스트링', '사이다', '세계관', '설렘폭발', '소설원작', '스튜디오', '스핀오프', '슈퍼스트링', '옴니버스', '요즘핫한추천작', '원작웹툰', '인소감성', '자본주의', '자극적인', '지금추천작', '지상최대공모전', '프리퀄', '피카레스크', '하이퍼리얼리즘', '해외작품', '힐링'
    ]
];
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['description'])) {
    header('Content-Type: application/json');

    $description = $_POST['description'] ?? '';

    if (empty($description)) {
        echo json_encode(['status' => 'error', 'message' => '내용이 비어있습니다.']);
        exit;
    }

    $pythonScriptPath = "/var/www/html/Python/gemini_tag_extractor_test.py"; // 실제 경로 확인
    $pythonExecutable = "python3";

    $command = $pythonExecutable . " " . escapeshellcmd($pythonScriptPath) . " " . escapeshellarg($description);
    $output = shell_exec($command . " 2>&1");

    if ($output === null) {
        echo json_encode(['status' => 'error', 'message' => '태그 추출 스크립트 실행에 실패했습니다.']);
        exit;
    }

    echo $output;
    exit;
}
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['tags_data'])) {
    header('Content-Type: application/json');

    ini_set('display_errors', 1);
    error_reporting(E_ALL);

    $tagsDataJson = $_POST['tags_data'] ?? '';

    if (empty($tagsDataJson)) {
        echo json_encode(['error' => '태그를 하나 이상 선택해주세요.']);
        exit;
    }

    $pythonScriptPath = "/var/www/html/Python/recommand_test.py";
    $pythonExecutable = "python3";

    $command = $pythonExecutable . " " . escapeshellcmd($pythonScriptPath) . " " . escapeshellarg($tagsDataJson);
    
    $output = shell_exec($command . " 2>&1");

    if ($output === null) {
        error_log("Python script execution failed. Command: " . $command);
        echo json_encode(['error' => '추천 시스템 실행에 실패했습니다.']);
        exit;
    }

    $decodedOutput = json_decode($output, true);

    if (json_last_error() !== JSON_ERROR_NONE) {
        error_log("Failed to decode Python JSON. Raw output: " . $output);
        echo json_encode(['error' => '추천 결과를 처리할 수 없습니다.', 'raw_output' => htmlspecialchars($output)]);
        exit;
    }
    
    if (isset($decodedOutput['error'])) {
        echo json_encode(['error' => 'Python 내부 오류: ' . htmlspecialchars($decodedOutput['error'])]);
        exit;
    }

    $snListFromPython = $decodedOutput['recommended'] ?? [];
    
    if (empty($snListFromPython) || !ctype_digit((string)($snListFromPython[0] ?? ''))) {
        $message = empty($snListFromPython) ? '추천 웹툰을 찾지 못했습니다.' : ($snListFromPython[0] ?? '알 수 없는 오류');
        echo json_encode(['error' => $message]);
        exit;
    }
    
    $db_host = "localhost";
    $db_user = "root";
    $db_pass = "123";
    $db_name = "webtoon";
    $connection = new mysqli($db_host, $db_user, $db_pass, $db_name);

    if ($connection->connect_error) {
        error_log("DB Connection Error: " . $connection->connect_error);
        echo json_encode(['error' => '데이터베이스 연결 오류']);
        exit;
    }
    $connection->set_charset("utf8mb4");

    $placeholders = implode(',', array_fill(0, count($snListFromPython), '?'));
    $types = str_repeat('s', count($snListFromPython));
    
    $fieldOrder = implode(',', array_map('intval', $snListFromPython));
    $query = "SELECT title, tag, summary, S_N FROM webtoon_info WHERE S_N IN ($placeholders) ORDER BY FIELD(S_N, $fieldOrder)";

    $stmt = $connection->prepare($query);
    if ($stmt === false) {
        error_log("DB Prepare Error: " . $connection->error);
        echo json_encode(['error' => '데이터베이스 쿼리 준비 오류']);
        exit;
    }
    
    $stmt->bind_param($types, ...$snListFromPython);
    $stmt->execute();
    $result = $stmt->get_result();
    
    $webtoonInfo = [];
    while ($row = $result->fetch_assoc()) {
        $webtoonInfo[] = $row;
    }
    
    $stmt->close();
    $connection->close();

    echo json_encode(['recommended' => $webtoonInfo]);
    exit;
}
?>
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>웹툰추천소</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/CSS/recommand_main.css">
    <link rel="apple-touch-icon" sizes="57x57" href="/favicon/apple-icon-57x57.png">
    <link rel="apple-touch-icon" sizes="60x60" href="/favicon/apple-icon-60x60.png">
    <link rel="apple-touch-icon" sizes="72x72" href="/favicon/apple-icon-72x72.png">
    <link rel="apple-touch-icon" sizes="76x76" href="/favicon/apple-icon-76x76.png">
    <link rel="apple-touch-icon" sizes="114x114" href="/favicon/apple-icon-114x114.png">
    <link rel="apple-touch-icon" sizes="120x120" href="/favicon/apple-icon-120x120.png">
    <link rel="apple-touch-icon" sizes="144x144" href="/favicon/apple-icon-144x144.png">
    <link rel="apple-touch-icon" sizes="152x152" href="/favicon/apple-icon-152x152.png">
    <link rel="apple-touch-icon" sizes="180x180" href="/favicon/apple-icon-180x180.png">
    <link rel="icon" type="image/png" sizes="192x192"  href="/favicon/android-icon-192x192.png">
    <link rel="icon" type="image/png" sizes="32x32" href="/favicon/favicon-32x32.png">
    <link rel="icon" type="image/png" sizes="96x96" href="/favicon/favicon-96x96.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/favicon/favicon-16x16.png">
    <link rel="manifest" href="/favicon/manifest.json">
    <meta name="msapplication-TileColor" content="#ffffff">
    <meta name="msapplication-TileImage" content="/favicon/ms-icon-144x144.png">
    <meta name="theme-color" content="#ffffff">
</head>
</head>
<body>
    <header>
      <nav class="logo-group">
          <a href="/index.html" class="logo-image"> <img src="/logo.png" alt="웹툰세상 로고">
          </a>
          <a href="/html/summary_main.html" class="text-logo">웹툰요약소</a> </nav>
    </header>

    <main>
        <h1>웹툰추천소</h1>
        
        <div class="search-container">
            <textarea 
                id="webtoon-description" 
                placeholder="원하는 웹툰 스토리를 자유롭게 입력해보세요!&#10;예: 가난했지만 복권 당첨으로 재벌이 된 남주가 짝사랑하던 여자와 만나는 로맨스 웹툰" 
                rows="4"
            ></textarea>
            <button class="gemini-btn" onclick="getTagsFromGemini()">
                AI로 태그 추출하기
            </button>
        </div>

        <div id="selected-tags-area"></div>

        <details class="tag-details">
            <summary>태그 수정</summary>
            <div class="tag-container" id="tag-source-container">
                
                <?php foreach ($tags as $category => $tag_list): ?>
                <div class="tag-category">
                    <h3><?= htmlspecialchars($category) ?></h3>
                    <div class="tag-group">
                        <?php foreach ($tag_list as $tag): ?>
                            <button class="tag-btn">#<?= htmlspecialchars($tag) ?></button>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endforeach; ?>

            </div>
        </details>
        
        <button class="recommend-btn" onclick="handleSearch()">
            이 태그들로 웹툰 추천받기
        </button>
        
        <div id="result"></div>
    </main>

    <script>
    const tagSourceContainer = document.getElementById('tag-source-container');
    const selectedTagsArea = document.getElementById('selected-tags-area');

    tagSourceContainer.addEventListener('click', function(e) {
        if (e.target.classList.contains('tag-btn') && !e.target.disabled) {
            const tagText = e.target.textContent;
            addTagToSelectedArea(tagText, 'manual');
            e.target.disabled = true;
            
            e.target.style.transform = 'scale(0.95)';
            setTimeout(() => { e.target.style.transform = ''; }, 150);
        }
    });

    selectedTagsArea.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-tag')) {
            const tagButtonToRemove = e.target.parentElement;
            const tagText = tagButtonToRemove.dataset.tag;
            
            tagButtonToRemove.style.transform = 'scale(0)';
            tagButtonToRemove.style.opacity = '0';
            
            setTimeout(() => { tagButtonToRemove.remove(); }, 300);

            const originalTagButton = Array.from(tagSourceContainer.querySelectorAll('.tag-btn'))
                                        .find(btn => btn.textContent === tagText);
            if (originalTagButton) {
                originalTagButton.disabled = false;
            }
        }
    });
    
    function escapeHTML(str) {
        const p = document.createElement('p');
        p.textContent = str;
        return p.innerHTML;
    }

    function addTagToSelectedArea(tagText, source) {
        const newTagButton = document.createElement('button');
        newTagButton.className = 'selected-tag';
        newTagButton.textContent = tagText;
        newTagButton.dataset.tag = tagText;
        newTagButton.dataset.source = source;
        newTagButton.style.transform = 'scale(0)';
        newTagButton.style.opacity = '0';

        const removeSpan = document.createElement('span');
        removeSpan.className = 'remove-tag';
        removeSpan.textContent = '×';
        
        newTagButton.appendChild(removeSpan);
        selectedTagsArea.appendChild(newTagButton);
        
        requestAnimationFrame(() => {
            newTagButton.style.transform = 'scale(1)';
            newTagButton.style.opacity = '1';
        });
    }

    async function getTagsFromGemini() {
        const description = document.getElementById('webtoon-description').value;
        const selectedTagsArea = document.getElementById('selected-tags-area');

        if (!description.trim()) {
            alert('웹툰 스토리를 입력해주세요.');
            return;
        }

        document.querySelectorAll('#selected-tags-area .selected-tag[data-source="ai"]').forEach(tag => {
            const tagText = tag.dataset.tag;
            const originalTagButton = Array.from(tagSourceContainer.querySelectorAll('.tag-btn'))
                                        .find(btn => btn.textContent === tagText);
            if (originalTagButton) {
                originalTagButton.disabled = false;
            }
            tag.remove();
        });

        selectedTagsArea.innerHTML = `
            <div style="width: 100%; text-align: center;">
                <p class="loading">AI가 태그를 추출하고 있습니다...</p>
                <div class="progress-bar-container">
                    <div id="gemini-progress-bar" class="progress-bar"></div>
                </div>
            </div>
        `;
        const progressBar = document.getElementById('gemini-progress-bar');
        
        progressBar.style.width = '0%';
        progressBar.style.transition = 'none';
        progressBar.getBoundingClientRect(); // Reflow
        progressBar.style.transition = 'width 20s linear';
        progressBar.style.width = '100%';

        try {
            const formData = new FormData();
            formData.append('description', description);
            
            const response = await fetch('recommand_main.php', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error(`서버 응답 오류: ${response.status}`);

            const data = await response.json();
            selectedTagsArea.innerHTML = ''; 

            if (data.status === 'success' && data.tags && data.tags.length > 0) {
                data.tags.forEach((tagText, index) => {
                    setTimeout(() => {
                        const fullTagText = `#${tagText}`;
                        const isAlreadySelected = !!document.querySelector(`#selected-tags-area .selected-tag[data-tag="${fullTagText}"]`);
                        
                        if (!isAlreadySelected) {
                            addTagToSelectedArea(fullTagText, 'ai');
                            const originalTagButton = Array.from(document.querySelectorAll('.tag-btn')).find(btn => btn.textContent === fullTagText);
                            if (originalTagButton) {
                                originalTagButton.disabled = true;
                            }
                        }
                    }, index * 100);
                });
            } else {
                const errorMessage = data.message || '입력한 내용에서 태그를 추출하지 못했습니다.';
                alert(`오류: ${errorMessage}`);
            }
        } catch (error) {
            console.error('Gemini 태그 추출 오류:', error);
            selectedTagsArea.innerHTML = '';
            alert('AI 태그 추출 중 오류가 발생했습니다. 개발자 콘솔(F12)을 확인해주세요.');
        }
    }

    async function handleSearch() {
        const selectedTagButtons = selectedTagsArea.querySelectorAll('.selected-tag');
        const resultDiv = document.getElementById('result');

        if (selectedTagButtons.length === 0) {
            alert('태그를 하나 이상 선택해주세요.');
            return;
        }

        resultDiv.innerHTML = '<p class="loading">취향에 맞는 웹툰을 찾고 있습니다...</p>';

        const manual_tags = [];
        const ai_tags = [];
        selectedTagButtons.forEach(tagButton => {
            const tagValue = tagButton.dataset.tag.replace('#', '');
            if (tagButton.dataset.source === 'manual') {
                manual_tags.push(tagValue);
            } else {
                ai_tags.push(tagValue);
            }
        });

        const tagsData = {
            manual_tags: manual_tags,
            ai_tags: ai_tags
        };

        try {
            const formData = new FormData();
            formData.append('tags_data', JSON.stringify(tagsData));
            
            const response = await fetch('recommand_main.php', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error(`서버 응답 오류: ${response.status}`);
            
            const data = await response.json();

            if (data.error) {
                resultDiv.innerHTML = `<p class="error-message">오류: ${escapeHTML(data.error)}</p>`;
                if (data.raw_output) {
                    resultDiv.innerHTML += `<pre class="debug-output">${escapeHTML(data.raw_output)}</pre>`;
                }
            } else if (data.recommended && data.recommended.length > 0) {
                let resultHTML = '<div class="webtoon-cards-container">';
                const allSelectedTags = [...manual_tags, ...ai_tags];

                data.recommended.forEach((webtoon, index) => {
                    const webtoonUrl = `https://comic.naver.com/webtoon/list?titleId=${encodeURIComponent(webtoon.S_N)}`;
                    
                    const title = escapeHTML(webtoon.title || '제목 없음');
                    const summary = escapeHTML(webtoon.summary || '요약 없음');
                    
                    const allWebtoonTags = (webtoon.tag || '').split(',').map(t => t.trim());
                    const highlightedTags = allWebtoonTags.map(tag => {
                        if (allSelectedTags.includes(tag)) {
                            return `<span class="highlight-tag">#${escapeHTML(tag)}</span>`;
                        } else {
                            return `<span class="normal-tag">#${escapeHTML(tag)}</span>`;
                        }
                    }).join(' ');

                    resultHTML += `
                        <div class="webtoon-card" onclick="window.open('${webtoonUrl}', '_blank')" style="animation-delay: ${index * 0.1}s">
                            <h3 class="webtoon-title">${title}</h3>
                            <div class="webtoon-tag">
                                <strong>태그:</strong><br> 
                                ${highlightedTags}
                            </div>
                            <div class="webtoon-summary">
                                <strong>요약:</strong><br> 
                                ${summary}
                            </div>
                        </div>
                    `;
                });
                resultHTML += '</div>';
                resultDiv.innerHTML = resultHTML;
            } else {
                resultDiv.innerHTML = '<p class="no-results">추천할 웹툰을 찾을 수 없습니다. 다른 태그를 선택해보세요!</p>';
            }
        } catch (error) {
            console.error('Fetch/JavaScript Error:', error);
            resultDiv.innerHTML = '<p class="error-message">추천 처리 중 오류가 발생했습니다.</p>';
        }
    }
    
    document.addEventListener('DOMContentLoaded', function() {
        const elements = document.querySelectorAll('main > *');
        elements.forEach((el, index) => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            setTimeout(() => {
                el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }, index * 100);
        });
    });
    document.addEventListener('DOMContentLoaded', function() {
        document.getElementById('webtoon-description').focus();
    });
    </script>
</body>
</html>