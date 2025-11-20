import os
import re
import time
import pymysql
import ast
from urllib.parse import urljoin, parse_qs, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def crawl_and_update():
    # === 크롬 드라이버 설정 및 네이버 웹툰 크롤링 ===
    driver_path = '/usr/bin/chromedriver'
    service = Service(driver_path)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # 브라우저 창 없이 실행
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=service, options=options)
    
    base_url = "https://comic.naver.com/webtoon"
    driver.get(base_url)
    
    # 웹툰 링크 로드 대기
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'Poster__link--sopnC'))
        )
    except Exception as e:
        print("페이지 요소 로드 실패:", e)
        driver.quit()
        return

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    poster_links = soup.find_all('a', class_='Poster__link--sopnC')
    hrefs = [link.get('href') for link in poster_links if link.get('href')]
    print(f"총 {len(hrefs)}개의 링크 추출됨.")

    # 웹툰 데이터를 저장할 딕셔너리
    webtoon_data = {}

    # 각 웹툰 링크에 대해 데이터 수집
    for index, href in enumerate(hrefs):
        # 전체 URL 구성 및 웹툰 코드(titleId) 추출
        full_url = urljoin(base_url, href)
        parsed_url = urlparse(href)
        query_params = parse_qs(parsed_url.query)
        title_id = query_params.get('titleId', [None])[0]

        # 각 웹툰 페이지 접속 및 HTML 파싱
        driver.get(full_url)
        time.sleep(1)  # 페이지 로드 대기
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # 웹툰 제목 추출 (불필요한 자식 태그 제거 후 텍스트만 남김)
        title_element = soup.find('h2', class_='EpisodeListInfo__title--mYLjC')
        if title_element:
            for child in title_element.find_all(['i', 'span']):
                child.decompose()
            webtoon_title = title_element.get_text(strip=True).replace(" ", "")
        else:
            webtoon_title = full_url

        # 태그 정보 추출
        tag_elements = soup.find_all('a', class_='TagGroup__tag--xu0OH')
        tags = [tag.get_text(strip=True).lstrip('#') for tag in tag_elements]

        # 요약 정보 추출 (separator 매개변수를 사용하여 전체 텍스트를 가져옴)
        summary_element = soup.find('p', class_='EpisodeListInfo__summary--Jd1WG')
        summary = summary_element.get_text(separator=" ", strip=True) if summary_element else "요약 정보 없음"

        # 요일 정보 추출 (영어 약어 대신 한글 그대로 저장)
        day_element = soup.find('em', class_='ContentMetaInfo__info_item--utGrf')
        day = []
        if day_element:
            day_text = day_element.get_text(strip=True)
            if "웹툰" in day_text:
                day_part = day_text.split("웹툰")[0]
            elif "연재" in day_text:
                day_part = day_text.split("연재")[0]
            else:
                day_part = day_text
            # 추출된 한글 요일 그대로 사용
            day_candidates = re.findall(r'([월화수목금토일])', day_part)
            day = day_candidates

        # 추가: last 정보 크롤링 (예: <div class="EpisodeListView__count--fTMc5"> "총 4화" </div>)
        last_element = soup.find('div', class_='EpisodeListView__count--fTMc5')
        last = None
        if last_element:
            last_text = last_element.get_text(strip=True)
            # "총 4화" 형식의 문자열에서 숫자 추출
            last_match = re.search(r'총\s*(\d+)\s*화', last_text)
            if last_match:
                last = int(last_match.group(1))

        # 수집한 데이터를 딕셔너리에 저장 (웹툰 코드는 S_N으로 사용)
        webtoon_data[webtoon_title] = {
            'S_N': int(title_id) if title_id and title_id.isdigit() else None,
            'title': webtoon_title,
            'tags': ', '.join(tags),
            'summary': summary,
            'day': str(day),  # 예: "['월']"와 같이 문자열로 저장
            'last': last
        }
        print(f"[{index+1}/{len(hrefs)}] '{webtoon_title}' 데이터 수집 완료.")

    # 수집된 데이터를 텍스트 파일에 저장
    base_path = "/var/www/html/Python/databases/"
    output_file_path = os.path.join(base_path, 'webtoon_data.txt')

    if webtoon_data:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            for title, data in webtoon_data.items():
                f.write(f'웹툰: {data["title"]}\n')
                f.write(f'웹툰 코드: {data["S_N"]}\n')
                f.write(f'요일: {data["day"]}\n')
                f.write(f'last: {data["last"]}\n')
                f.write(f'태그: {data["tags"]}\n')
                f.write(f'요약: {data["summary"]}\n')
                f.write('---\n')
        print(f"데이터가 '{output_file_path}'에 저장됨.")
    else:
        print("저장할 데이터가 없음.")

    driver.quit()

    # === 저장된 파일을 읽어 MySQL에 데이터 저장 ===
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='123',
        database='webtoon',
        charset='utf8mb4'
    )

    parsed_webtoon_data = {}
    if os.path.isfile(output_file_path):
        with open(output_file_path, 'r', encoding='utf-8') as file:
            record = {}
            for line in file:
                line = line.strip()
                if line.startswith("웹툰:"):
                    if record:
                        cleaned_title = re.sub(r'[\s-]', '', record.get('title', ''))
                        if cleaned_title and 'S_N' in record:
                            parsed_webtoon_data[cleaned_title] = record
                        record = {}
                    record['title'] = line.replace("웹툰:", "").strip()
                elif line.startswith("웹툰 코드:"):
                    sn_str = line.replace("웹툰 코드:", "").strip()
                    try:
                        record['S_N'] = int(sn_str)
                    except:
                        record['S_N'] = None
                elif line.startswith("태그:"):
                    record['tags'] = line.replace("태그:", "").strip()
                elif line.startswith("요약:"):
                    record['summary'] = line.replace("요약:", "").strip() + " "
                elif line.startswith("요일:"):
                    day_str = line.replace("요일:", "").strip()
                    try:
                        day_val = ast.literal_eval(day_str)
                        if isinstance(day_val, list):
                            record['day'] = ','.join(day_val)
                        else:
                            record['day'] = str(day_val)
                    except Exception as e:
                        record['day'] = day_str
                elif line.startswith("last:"):
                    last_str = line.replace("last:", "").strip()
                    try:
                        record['last'] = int(last_str) if last_str.isdigit() else None
                    except:
                        record['last'] = None
                elif line == '---':
                    if record and record.get('S_N') is not None:
                        cleaned_title = re.sub(r'[\s-]', '', record.get('title', ''))
                        parsed_webtoon_data[cleaned_title] = record
                    record = {}
            if record and record.get('S_N') is not None:
                cleaned_title = re.sub(r'[\s-]', '', record.get('title', ''))
                parsed_webtoon_data[cleaned_title] = record

    try:
        with connection.cursor() as cursor:
            # 테이블이 없으면 생성 (last 열 추가 및 컬럼 순서 변경)
            create_table_query = """
            CREATE TABLE IF NOT EXISTS webtoon_info (
                S_N INT PRIMARY KEY,
                title VARCHAR(255) NOT NULL UNIQUE,
                day VARCHAR(255),
                last INT,
                tag VARCHAR(255),
                summary TEXT
            ) CHARSET=utf8mb4;
            """
            cursor.execute(create_table_query)

            # ON DUPLICATE KEY UPDATE를 사용해 기존 데이터가 있어도 last(및 기타 변경 가능 열)를 업데이트
            insert_query = """
            INSERT INTO webtoon_info (S_N, title, day, last, tag, summary)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                day = VALUES(day),
                last = VALUES(last),
                tag = VALUES(tag),
                summary = VALUES(summary);
            """
            for key, data in parsed_webtoon_data.items():
                # 웹툰 제목이 URL("https://comic.naver.com")로 시작하면 건너뜀
                if data.get('title', '').startswith("https://comic.naver.com"):
                    continue
                if data.get('S_N') is None:
                    continue
                cursor.execute(insert_query, (
                    data['S_N'],
                    data['title'],
                    data.get('day', ''),
                    data.get('last'),
                    data.get('tags', ''),
                    data.get('summary', '')
                ))
            connection.commit()
            print("MySQL 데이터베이스 업데이트 완료.")
    finally:
        connection.close()

if __name__ == "__main__":
    crawl_and_update()
