from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from urllib.parse import urljoin, parse_qs, urlparse
import time
import os

# ChromeDriver 경로 설정
driver_path = '/usr/local/bin/chromedriver'
service = Service(driver_path)

# Chrome 옵션 설정
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # 화면 없이 실행
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Chrome WebDriver 시작
driver = webdriver.Chrome(service=service, options=options)

# 네이버 웹툰 메인 URL
base_url = "https://comic.naver.com/webtoon"
driver.get(base_url)

# 페이지가 완전히 로드될 때까지 기다리기
try:
    # 특정 요소가 로드될 때까지 기다리기 (10초 타임아웃)
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'Poster__link--sopnC'))
    )
except Exception as e:
    print("페이지 요소를 로드하지 못했습니다:", e)
    driver.quit()
    exit()

# BeautifulSoup으로 HTML 파싱
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

# Poster__link--sopnC 클래스의 링크를 모두 찾기
poster_links = soup.find_all('a', class_='Poster__link--sopnC')

# href 속성 추출
hrefs = [link.get('href') for link in poster_links if link.get('href')]

# 모든 링크를 사용하도록 변경
print(f"총 {len(hrefs)}개의 링크를 추출했습니다.")

# 웹툰별 데이터를 저장할 딕셔너리
webtoon_data = {}

# 각 웹툰 링크에 접근하여 데이터 수집
for index, href in enumerate(hrefs):
    # 전체 URL 구성
    full_url = urljoin(base_url, href)

    # titleId 추출
    parsed_url = urlparse(href)
    query_params = parse_qs(parsed_url.query)
    title_id = query_params.get('titleId', [None])[0]

    # 웹툰 페이지로 이동
    driver.get(full_url)
    time.sleep(1)  # 페이지가 로드될 시간을 기다림

    # 웹툰 페이지의 HTML 파싱
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # 웹툰 제목 추출 (새로운 클래스명으로 수정)
    title_element = soup.find('h2', class_='EpisodeListInfo__title--mYLjC')
    if title_element:
        # 자식 태그들을 모두 제거하여 제목만 남기기
        for child in title_element.find_all(['i', 'span']):
            child.decompose()  # 필요 없는 태그 제거
        webtoon_title = title_element.get_text(strip=True).replace(" ", "")  # 공백 제거
    else:
        webtoon_title = full_url  # 제목을 찾지 못한 경우 URL을 대신 사용

    # 태그 추출
    tag_elements = soup.find_all('a', class_='TagGroup__tag--xu0OH')
    tags = [tag.get_text(strip=True).lstrip('#') for tag in tag_elements]  # 앞의 '#' 제거

    # 요약 추출
    summary_element = soup.find('p', class_='EpisodeListInfo__summary--Jd1WG')
    summary = summary_element.get_text(strip=True) if summary_element else "요약 정보 없음"

    # 딕셔너리에 전체 정보 저장
    webtoon_data[webtoon_title] = {
        'title_id': title_id,
        'tags': tags,
        'summary': summary
    }

    # 진행 상태 출력 (디버깅 및 확인 용도)
    print(f"[{index + 1}/{len(hrefs)}] '{webtoon_title}'의 데이터를 추출했습니다.")

# 결과를 텍스트 파일로 저장 (홈 디렉토리에 저장)
base_path = "/var/www/html/Python/databases/"
output_file_path = os.path.join(base_path, 'webtoon_data.txt')

if webtoon_data:
    with open(output_file_path, 'w', encoding='utf-8') as f:
        for title, data in webtoon_data.items():
            f.write(f'웹툰: {title}\n')
            f.write(f'웹툰 코드: {data["title_id"]}\n')
            f.write('태그: ' + ', '.join(data['tags']) + '\n')
            f.write(f'요약: {data["summary"]}\n')
            f.write('---\n')

    print(f'데이터가 {output_file_path}에 저장되었습니다.')
else:
    print("저장할 데이터가 없습니다. 웹사이트 구조를 확인해주세요.")

# 드라이버 종료
driver.quit()
