import pymysql
import os
import sys
import time  # 세션 ID에 타임스탬프 추가
from webtoon_download import NWebtoon

# MySQL 연결 설정
db_config = {
    "host": "localhost",
    "user": "webtoon_user",
    "password": "1234",
    "database": "webtoon",
    "charset": "utf8mb4"
}

def get_connection():
    """MySQL 연결 생성"""
    return pymysql.connect(**db_config, ssl_disabled=True)

def update_webtoon_data(S_N, start_episode, end_episode):
    """웹툰 데이터를 업데이트하고 데이터베이스에 삽입"""
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            for episode in range(start_episode, end_episode + 1):
                # 중복 확인
                cursor.execute(
                    "SELECT COUNT(*) FROM webtoon_text WHERE S_N = %s AND episode = %s",
                    (S_N, episode)
                )
                if cursor.fetchone()[0] > 0:
                    print(f"Episode {episode} already exists. Skipping.")
                    continue

                # 고유한 session_id 생성
                session_id = f"session_{S_N}_{episode}_{int(time.time())}"
                print(f"Processing S_N: {S_N}, Episode: {episode}, Session: {session_id}")

                # 웹툰 데이터 다운로드
                webtoon = NWebtoon(title_id=str(S_N), session_id=session_id)
                webtoon.multi_download(start_index=episode, end_index=episode)

                # 텍스트 추출 후 데이터베이스 삽입
                output_file_path = os.path.join(NWebtoon.OUTPUT_PATH, "extracted_texts.txt")
                if os.path.exists(output_file_path):
                    with open(output_file_path, "r", encoding="utf-8") as f:
                        line_data = f.read()

                    # 데이터 삽입
                    cursor.execute(
                        "INSERT INTO webtoon_text (S_N, episode, line) VALUES (%s, %s, %s)",
                        (S_N, episode, line_data)
                    )
                    connection.commit()
                    print(f"Inserted data for S_N: {S_N}, Episode: {episode}")
                else:
                    print(f"Text extraction failed for Episode: {episode}")
    except Exception as e:
        print(f"Error occurred: {e}")
        raise
    finally:
        connection.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python auto_update.py <S_N> <start_episode> <end_episode>")
        sys.exit(1)

    S_N = int(sys.argv[1])
    start_episode = int(sys.argv[2])
    end_episode = int(sys.argv[3])

    update_webtoon_data(S_N, start_episode, end_episode)
