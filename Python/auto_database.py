import os
import pymysql
import re
from urllib.parse import urlparse

# 데이터베이스 연결 정보
connection = pymysql.connect(
    host='localhost',
    user='webtoon_server',
    password='1234',
    database='webtoon',
    charset='utf8mb4'
)

# 파일 경로 및 요일 매핑
base_path = "/var/www/html/Python/databases"
day_map = {
    "월요웹툰.txt": "mon",
    "화요웹툰.txt": "tue",
    "수요웹툰.txt": "wed",
    "목요웹툰.txt": "thu",
    "금요웹툰.txt": "fri",
    "토요웹툰.txt": "sat",
    "일요웹툰.txt": "sun"
}

# 추가 파일 경로
webtoon_data_path = '/var/www/html/Python/databases/webtoon_data.txt'

# URL 체크 함수 정의
def is_url(string):
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

try:
    # 커서 생성
    with connection.cursor() as cursor:
        # 테이블이 이미 존재할 경우 삭제
        cursor.execute("DROP TABLE IF EXISTS webtoon_info")
        
        # 테이블 생성 쿼리 실행
        create_table_query = """
        CREATE TABLE webtoon_info (
            S_N INT PRIMARY KEY,
            title VARCHAR(255) NOT NULL UNIQUE,
            day VARCHAR(255),
            tag VARCHAR(255),
            summary TEXT
        ) CHARSET=utf8mb4;
        """
        cursor.execute(create_table_query)

        # 웹툰 데이터를 저장할 딕셔너리 초기화
        webtoon_data = {}

        # 추가 파일(webtoon_data.txt) 읽어서 데이터 저장
        if os.path.isfile(webtoon_data_path):
            with open(webtoon_data_path, 'r', encoding='utf-8') as file:
                webtoon_title = None
                S_N = None
                tags = None
                summary = ''

                for line in file:
                    line = line.strip()
                    if line.startswith("웹툰:"):
                        # 기존에 저장된 정보가 있으면 딕셔너리에 저장
                        if webtoon_title and S_N:
                            # 웹툰 제목이 URL인지 체크
                            if is_url(webtoon_title):
                                # URL인 경우 해당 웹툰 무시
                                webtoon_title = None
                                S_N = None
                                tags = None
                                summary = ''
                                continue
                            cleaned_title = re.sub(r'[\s-]', '', webtoon_title)
                            webtoon_data[cleaned_title] = {
                                'S_N': int(S_N),
                                'title': webtoon_title,
                                'tags': tags,
                                'summary': summary.strip(),
                                'day': ''
                            }
                        # 새로운 웹툰 정보 초기화
                        webtoon_title = line.replace("웹툰:", "").strip()
                        S_N = None
                        tags = None
                        summary = ''
                    elif line.startswith("웹툰 코드:"):
                        S_N = line.replace("웹툰 코드:", "").strip()
                    elif line.startswith("태그:"):
                        tags = line.replace("태그:", "").strip()
                    elif line.startswith("요약:"):
                        summary = line.replace("요약:", "").strip()
                    elif line == '---':
                        # 웹툰 정보의 끝, 저장
                        if webtoon_title and S_N:
                            # 웹툰 제목이 URL인지 체크
                            if is_url(webtoon_title):
                                # URL인 경우 해당 웹툰 무시
                                webtoon_title = None
                                S_N = None
                                tags = None
                                summary = ''
                                continue
                            cleaned_title = re.sub(r'[\s-]', '', webtoon_title)
                            webtoon_data[cleaned_title] = {
                                'S_N': int(S_N),
                                'title': webtoon_title,
                                'tags': tags,
                                'summary': summary.strip(),
                                'day': ''
                            }
                            webtoon_title = None
                            S_N = None
                            tags = None
                            summary = ''
                    else:
                        # 요약이 여러 줄인 경우
                        summary += line + ' '

                # 마지막 웹툰 정보 저장
                if webtoon_title and S_N:
                    # 웹툰 제목이 URL인지 체크
                    if not is_url(webtoon_title):
                        cleaned_title = re.sub(r'[\s-]', '', webtoon_title)
                        webtoon_data[cleaned_title] = {
                            'S_N': int(S_N),
                            'title': webtoon_title,
                            'tags': tags,
                            'summary': summary.strip(),
                            'day': ''
                        }

        # 각 파일을 읽어서 day 정보 업데이트
        for file_name, day in day_map.items():
            file_path = os.path.join(base_path, file_name)
            if os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    for line in file:
                        title = line.strip()
                        if title:  # 빈 줄 무시
                            # 웹툰 제목이 URL인지 체크
                            if is_url(title):
                                continue  # URL인 경우 무시
                            # 공백과 '-' 기호 제거
                            cleaned_title = re.sub(r'[\s-]', '', title)
                            if cleaned_title in webtoon_data:
                                # 이미 존재하는 경우 day 업데이트
                                existing_day = webtoon_data[cleaned_title]['day']
                                if existing_day:
                                    if day not in existing_day.split(','):
                                        webtoon_data[cleaned_title]['day'] = existing_day + ',' + day
                                else:
                                    webtoon_data[cleaned_title]['day'] = day
                            else:
                                # webtoon_data에 없는 경우, S_N이 없으므로 건너뜀
                                continue

        # 데이터베이스에 데이터 삽입
        for cleaned_title, data in webtoon_data.items():
            S_N = data['S_N']
            title = data['title']
            day = data['day']
            tags = data['tags']
            summary = data['summary']

            if S_N is not None:
                # S_N이 있는 경우, S_N을 지정하여 삽입
                insert_query = """
                INSERT INTO webtoon_info (S_N, title, day, tag, summary)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    day = VALUES(day),
                    tag = VALUES(tag),
                    summary = VALUES(summary);
                """
                cursor.execute(insert_query, (S_N, title, day, tags, summary))
            else:
                # S_N이 없는 경우, 해당 웹툰을 건너뜀
                continue

        # 변경 사항 커밋
        connection.commit()

finally:
    # 연결 종료
    connection.close()

print("데이터베이스 업데이트 완료.")
