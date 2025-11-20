import pymysql
import os
import sys
user_home = '/home/issi' 
python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
site_packages_path = os.path.join(user_home, '.local', 'lib', python_version, 'site-packages')

if os.path.exists(site_packages_path) and site_packages_path not in sys.path:
    sys.path.insert(0, site_packages_path)

import time
from paddleocr import PaddleOCR
import uuid
import shutil

try:
    from webtoon_download import NWebtoon
except ImportError:
    print("CRITICAL: webtoon_download_copy.py 파일을 찾을 수 없습니다.")
    sys.exit(1)

db_config = {
    "host": "localhost", "user": "root", "password": "123",
    "database": "webtoon", "charset": "utf8mb4",
}

def get_connection():
    return pymysql.connect(**db_config)

def get_existing_episodes(S_N, start_episode, end_episode):
    """데이터베이스에 이미 존재하는 에피소드 목록을 반환"""
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT episode FROM webtoon_text WHERE S_N = %s AND episode BETWEEN %s AND %s"
            cursor.execute(sql, (S_N, start_episode, end_episode))
            existing_episodes = {row[0] for row in cursor.fetchall()}
            return existing_episodes
    finally:
        connection.close()

def download_and_store_webtoon_data(S_N, start_episode, end_episode, ocr_reader):
    # 먼저 이미 존재하는 에피소드들을 확인
    existing_episodes = get_existing_episodes(S_N, start_episode, end_episode)
    
    # 처리해야 할 에피소드들만 필터링
    episodes_to_process = []
    for ep in range(start_episode, end_episode + 1):
        if ep not in existing_episodes:
            episodes_to_process.append(ep)
        else:
            print(f"에피소드 {ep}는 이미 DB에 존재합니다. 건너뜁니다.")
    
    if not episodes_to_process:
        print(f"웹툰 {S_N}: 모든 에피소드가 이미 DB에 존재합니다. 작업을 건너뜁니다.")
        return

    print(f"웹툰 {S_N}: {len(episodes_to_process)}개 에피소드를 처리합니다: {episodes_to_process}")

    base_tmp_dir = "/var/www/html/Python/image/jobs" # 'tmp' 대신 'jobs' 사용
    job_id = str(uuid.uuid4())
    tmp_job_path = os.path.join(base_tmp_dir, job_id)

    try:
        os.makedirs(tmp_job_path, exist_ok=True)
        print(f"임시 작업 폴더 생성: {tmp_job_path}")

        # 필터링된 에피소드들만 다운로드 및 처리
        webtoon = NWebtoon(title_id=str(S_N), ocr_reader=ocr_reader, tmp_download_path=tmp_job_path)
        extracted_data = webtoon.multi_download_filtered(episodes_to_process)
        
        if not extracted_data:
            print("추출된 데이터가 없습니다.")
            return

        connection = get_connection()
        with connection.cursor() as cursor:
            data_to_insert = []
            for episode, line_data in extracted_data.items():
                # 이중 체크: 혹시 다운로드 중에 다른 프로세스가 추가했을 수도 있으니
                cursor.execute("SELECT COUNT(*) FROM webtoon_text WHERE S_N = %s AND episode = %s", (S_N, episode))
                if cursor.fetchone()[0] == 0:
                    data_to_insert.append((S_N, episode, line_data))
                else:
                    print(f"에피소드 {episode}가 이미 다른 프로세스에 의해 추가되었습니다.")

            if data_to_insert:
                sql = "INSERT INTO webtoon_text (S_N, episode, line) VALUES (%s, %s, %s)"
                cursor.executemany(sql, data_to_insert)
                connection.commit()
                print(f"{len(data_to_insert)}개의 데이터가 DB에 저장되었습니다.")
            else:
                print("저장할 새로운 데이터가 없습니다.")
        connection.close()
    
    except Exception as e:
        print(f"작업 처리 중 오류 발생: {e}")
    finally:
        if os.path.exists(tmp_job_path):
            shutil.rmtree(tmp_job_path)
            print(f"임시 작업 폴더 삭제: {tmp_job_path}")

def update_all_webtoons_in_batches(start_episode, end_episode, ocr_reader):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT S_N FROM webtoon_info")
            webtoons_info = cursor.fetchall()
            if not webtoons_info:
                print("데이터베이스에 웹툰 정보가 없습니다.")
                return

            for row in webtoons_info:
                S_N = row[0]
                print(f"\n--- [{S_N}] 웹툰 업데이트 작업 시작 ---")
                download_and_store_webtoon_data(S_N, start_episode, end_episode, ocr_reader)
                time.sleep(1)
    finally:
        if connection: connection.close()

if __name__ == "__main__":
    ocr_reader = None
    try:
        print("Initializing OCR Reader...")
        # rec_model_path = "/var/www/html/Python/models/korean_PP-OCRv4_rec_infer/"
        # det_model_path = "/var/www/html/Python/models/ch_PP-OCRv4_det_infer/"
        # ocr_reader = PaddleOCR(use_angle_cls=True, lang='korean', show_log=False, rec_model_dir=rec_model_path, det_model_dir=det_model_path)
        ocr_reader = PaddleOCR(use_textline_orientation=True, lang='korean')
        print("PaddleOCR initialized successfully.")
    except Exception as e:
        print(f"CRITICAL: Failed to initialize PaddleOCR. Exiting. Error: {e}")
        sys.exit(1)

    if len(sys.argv) == 4:
        S_N, start_ep, end_ep = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
        download_and_store_webtoon_data(S_N, start_ep, end_ep, ocr_reader)
    
    elif len(sys.argv) == 1:
        start_ep = int(input("업데이트 시작 화: ").strip())
        end_ep = int(input("업데이트 종료 화: ").strip())
        update_all_webtoons_in_batches(start_ep, end_ep, ocr_reader)
    
    else:
        print("사용법: python3 auto_update.py [S_N] [시작] [종료] or python3 auto_update.py")
        sys.exit(1)

    print("\n모든 작업이 완료되었습니다.")