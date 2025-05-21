import errno
import json
import os
import re
import requests
from bs4 import BeautifulSoup
from typing import Literal
import concurrent.futures
import cv2
import numpy as np
import natsort
import glob
import easyocr
from PIL import Image, ImageEnhance, ImageFilter
import sys
# 헤더 파일 불러오기
from Headers import headers, image_headers

# EasyOCR Reader 생성 (GPU 사용 여부 확인 후 CPU 사용)
try:
    reader = easyocr.Reader(['ko', 'en'], gpu=True)  # 한국어와 영어를 지원, GPU 사용
except:
    print("Neither CUDA nor MPS are available - defaulting to CPU. Note: This module is much faster with a GPU.")
    reader = easyocr.Reader(['ko', 'en'], gpu=False)

import time

class ImageMerger:
    def __init__(self, dir_path, episode_number):
        """
        특정 화의 이미지를 병합하기 위한 클래스
        :param dir_path: 이미지들이 저장된 디렉토리 경로
        :param episode_number: 병합할 화 번호
        """
        self.dir_path = dir_path
        self.episode_number = episode_number
        self.output_filename = f"output_{self.episode_number}.png"

    def vconcat_resize_min(self, im_list, interpolation=cv2.INTER_CUBIC):
        w_min = min(im.shape[1] for im in im_list)
        im_list_resize = [
            cv2.resize(im, (w_min, int(im.shape[0] * w_min / im.shape[1])), interpolation=interpolation)
            for im in im_list
        ]
        return cv2.vconcat(im_list_resize)

    def merge_images(self):
        """
        지정된 화의 이미지를 병합하고, 병합된 이미지를 저장한 후 병합된 이미지만 자릅니다.
        """
        try:
            # 디렉토리 내 모든 이미지 파일 목록 가져오기
            file_pattern = os.path.join(self.dir_path, f"{self.episode_number}_*.jpg")
            file_lst = glob.glob(file_pattern)
            file_lst = natsort.natsorted(file_lst)

            if not file_lst:
                print(f"화 번호 {self.episode_number}에 해당하는 이미지가 없습니다.")
                return

            img_lst = []
            for image_file in file_lst:
                img = cv2.imread(image_file)
                if img is not None:
                    img_lst.append(img)
                else:
                    print(f"이미지를 읽을 수 없습니다: {image_file}")

            if not img_lst:
                print(f"화 번호 {self.episode_number}에 해당하는 유효한 이미지가 없습니다.")
                return

            # 이미지 병합 전에 크기를 동일하게 맞추기
            try:
                merged_image = self.vconcat_resize_min(img_lst)
            except Exception as e:
                print(f"이미지 병합 중 오류 발생 (크기 조정 중 문제 발생): {e}")
                return

            # 병합된 이미지 저장
            output_path = os.path.join(self.dir_path, self.output_filename)
            cv2.imwrite(output_path, merged_image)
            print(f"병합 완료: {output_path}")

            # 병합 후 이미지 처리 수행 (병합된 이미지에 대해서만 수행)
            self.process_image(output_path)

            # 병합에 사용된 개별 이미지 삭제
            for image_file in file_lst:
                os.remove(image_file)
                print(f"삭제 완료: {image_file}")

        except cv2.error as e:
            print(f"이미지 병합 중 오류 발생: {e}")
        except Exception as e:
            print(f"알 수 없는 오류 발생: {e}")

    def process_image(self, image_path):
        """
        병합된 이미지를 자르는 작업을 수행합니다.
        :param image_path: 병합된 이미지 경로
        """
        try:
            # 결과 이미지를 저장할 폴더 경로
            output_folder = NWebtoon.OUTPUT_PATH  # 수정된 경로 사용
            os.makedirs(output_folder, exist_ok=True)

            # 이미지 로드
            image = cv2.imread(image_path)
            if image is None:
                print(f"이미지를 불러올 수 없습니다: {image_path}")
                return

            # 이미지를 그레이스케일로 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 대비 향상을 위해 CLAHE 적용
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray_clahe = clahe.apply(gray)

            # 조명 보정
            gaussian = cv2.GaussianBlur(gray_clahe, (0, 0), sigmaX=15, sigmaY=15)
            divided = cv2.divide(gray_clahe, gaussian, scale=255)

            # 이진화 적용 (적응형 이진화)
            thresh = cv2.adaptiveThreshold(
                divided, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 10
            )

            # 노이즈 제거를 위한 모폴로지 연산 (커널 크기 및 반복 횟수 증가)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            clean = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=3)

            # 연결 요소 분석
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(clean)

            # 각 연결 요소에 대해 바운딩 박스 추출
            regions = []
            for i in range(1, num_labels):  # 레이블 0은 배경이므로 제외
                x, y, w, h, area = stats[i]

                # 너무 작은 영역은 무시 (노이즈 제거)
                if area < 1000:
                    continue

                # 영역의 높이나 너비가 너무 작으면 무시
                if h < 100 or w < 100:
                    continue

                regions.append([x, y, w, h])

            # 영역 병합 함수 정의
            def merge_overlapping_regions(regions):
                merged = True
                while merged:
                    merged = False
                    new_regions = []
                    used = [False] * len(regions)

                    for i in range(len(regions)):
                        if used[i]:
                            continue
                        x1, y1, w1, h1 = regions[i]
                        rect1 = [x1, y1, x1 + w1, y1 + h1]
                        for j in range(i + 1, len(regions)):
                            if used[j]:
                                continue
                            x2, y2, w2, h2 = regions[j]
                            rect2 = [x2, y2, x2 + w2, y2 + h2]

                            # 두 영역이 겹치는지 확인
                            dx = min(rect1[2], rect2[2]) - max(rect1[0], rect2[0])
                            dy = min(rect1[3], rect2[3]) - max(rect1[1], rect2[1])
                            if dx >= 0 and dy >= 0:
                                # 겹치면 병합
                                new_x1 = min(rect1[0], rect2[0])
                                new_y1 = min(rect1[1], rect2[1])
                                new_x2 = max(rect1[2], rect2[2])
                                new_y2 = max(rect1[3], rect2[3])
                                regions[i] = [new_x1, new_y1, new_x2 - new_x1, new_y2 - new_y1]
                                used[j] = True
                                merged = True
                        if not used[i]:
                            new_regions.append(regions[i])
                    regions = new_regions
                return regions

            # 영역 병합 수행
            regions = merge_overlapping_regions(regions)

            # 병합된 영역을 y 좌표 기준으로 정렬
            regions = sorted(regions, key=lambda r: r[1])

            # 이미지 자르기 및 저장
            for i, (x, y, w, h) in enumerate(regions):
                # 가로 크기를 이미지 전체로 설정
                x = 0
                w = image.shape[1]

                # 패딩 적용 (필요에 따라 조절)
                padding = 10
                y_padded = max(y - padding, 0)
                h_padded = min(h + 2 * padding, image.shape[0] - y_padded)

                cropped_image = image[y_padded: y_padded + h_padded, x: x + w]
                output_path = os.path.join(output_folder, f'cropped_image_{i + 1}.jpg')
                cv2.imwrite(output_path, cropped_image)
                print(f"이미지 자르기 완료: {output_path}")

            # 자른 이미지들에 대해 텍스트 인식 수행
            self.extract_text_from_images(output_folder)

            # 병합된 이미지 삭제
            os.remove(image_path)
            print(f"병합된 이미지 삭제 완료: {image_path}")

        except cv2.error as e:
            print(f"이미지 처리 중 오류 발생: {e}")
        except Exception as e:
            print(f"알 수 없는 오류 발생: {e}")
        finally:
            print("이미지 처리가 완료되었습니다.")

    def extract_text_from_images(self, folder_path):
        """
        폴더 내 모든 이미지에 대해 텍스트 인식을 수행하고 텍스트 파일만 남기고 이미지 파일을 삭제합니다.
        :param folder_path: 이미지들이 저장된 디렉토리 경로
        """
        # 출력 파일 경로의 디렉토리가 없으면 생성합니다.
        output_file_path = os.path.join(folder_path, "extracted_texts.txt")

        # 하나의 텍스트 파일로 모든 이미지의 텍스트를 저장
        with open(output_file_path, 'w', encoding='utf-8') as f:
            # 파일 이름에서 숫자를 기준으로 정렬
            for filename in sorted(os.listdir(folder_path), key=self.numerical_sort):
                if filename.endswith('.jpg'):
                    image_path = os.path.join(folder_path, filename)
                    print(f'{filename} 처리 중...')
                    extracted_text = self.process_ocr_image(image_path)
                    print(f'추출된 텍스트: {extracted_text}')

                    # 파일에 이미지 이름과 추출된 텍스트를 저장
                    f.write(f"{extracted_text}\n")

        # 이미지 파일 삭제
        for filename in os.listdir(folder_path):
            if filename.endswith('.jpg'):
                file_path = os.path.join(folder_path, filename)
                os.remove(file_path)
                print(f"삭제 완료: {file_path}")

        print(f"모든 추출된 텍스트가 {output_file_path}에 저장되었습니다.")

    def process_ocr_image(self, image_path):
        """
        이미지에서 텍스트를 추출합니다.
        :param image_path: 이미지 경로
        :return: 추출된 텍스트
        """
        # 이미지 로드
        image = Image.open(image_path)

        # 이미지 전처리
        # 그레이스케일 변환
        image = image.convert('L')

        # 대비 향상
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.5)  # 대비를 더 높게 설정

        # 샤프닝 필터 적용
        image = image.filter(ImageFilter.SHARPEN)

        # 노이즈 제거
        image = image.filter(ImageFilter.MedianFilter(size=3))

        # 이미지 배열로 변환
        image_np = np.array(image)

        # EasyOCR로 텍스트 인식 (GPU 사용)
        result = reader.readtext(
            image_np,
            detail=0,
            paragraph=True,
            contrast_ths=0.05,  # 대비 임계값 낮춤
            adjust_contrast=0.7,  # 대비 조정 비율 상향
            text_threshold=0.6,  # 텍스트 임계값 미세 조정
            low_text=0.4,  # 작은 글씨 인식 임계값 추가 설정
            link_threshold=0.4  # 텍스트 간 연결 임계값 조정
        )

        return " ".join(result)  # 텍스트 합치기

    def numerical_sort(self, value):
        """
        파일 이름에서 모든 숫자를 추출하여 정렬 키 생성
        """
        numbers = re.findall(r'\d+', value)
        # 숫자가 없는 경우 매우 큰 숫자를 반환하여 정렬 시 뒤로 오도록 함
        return tuple(int(num) for num in numbers) if numbers else (float('inf'),)

class NWebtoon:
    DOWNLOAD_PATH = "/var/www/html/Python/image/Webtoon_Download"  # 다운로드 경로
    OUTPUT_PATH = "/var/www/html/Python/image/Webtoon_Output"  # 자른 이미지 저장 경로

    def __init__(self, title_id: str, session_id: str) -> None:
        """
        title_id를 주고 객체를 생성하면 이 생성자에서 처리를 합니다.
        :param title_id: 웹툰의 titleId
        :param session_id: 세션 ID
        """
        self.__title_id: str = title_id
        self.session_id = session_id
        self.__title: str = ""
        self.__wtype: Literal["webtoon", "challenge", "bestChallenge"] = "webtoon"
        self.__number: int = 0
        self.__content: str = ""

        try:
            res = requests.get(
                f"https://comic.naver.com/api/article/list/info?titleId={self.__title_id}",
                headers=headers  # 헤더 추가
            )
            res.raise_for_status()
            res_json: dict = json.loads(res.content)
            self.__title = res_json.get('titleName', 'Unknown Title')
            self.__content = res_json.get('synopsis', 'No content available')
            json_level_code = res_json.get('webtoonLevelCode', 'WEBTOON')
            self.__wtype = "webtoon" if json_level_code == "WEBTOON" else "challenge"

            res = requests.get(
                f"https://comic.naver.com/api/article/list?titleId={self.__title_id}&page=1",
                headers=headers  # 헤더 추가
            )
            res.raise_for_status()
            res_json: dict = json.loads(res.content)
            self.__number = int(res_json['totalCount'])
        except requests.exceptions.RequestException as e:
            print(f"웹 요청 중 오류가 발생했습니다: {e}")

    def multi_download(self, start_index: int, end_index: int) -> None:
        """
        지정된 화 번호 범위 내의 모든 이미지를 병렬로 다운로드하고, 각 화별로 이미지를 병합합니다.
        :param start_index: 시작 화 번호
        :param end_index: 종료 화 번호
        """
        total_steps = 4  # 전체 단계 수 (다운로드, 병합, OCR 등)
        current_step = 0

        # 진행 상황 업데이트 함수
        progress_file = f'/tmp/progress_{self.session_id}.txt'

        def update_progress(progress, complete=False):
            try:
                progress_data = {'progress': progress, 'complete': complete}
                with open(progress_file, 'w') as f:
                    json.dump(progress_data, f)
            except Exception as e:
                print(f"Failed to write progress file: {e}")

        # 다운로드 단계
        current_step += 1
        progress = int((current_step / total_steps) * 100)
        update_progress(progress)

        # 다운로드 경로가 없으면 생성합니다.
        if not os.path.exists(NWebtoon.DOWNLOAD_PATH):
            os.makedirs(NWebtoon.DOWNLOAD_PATH)
        if not os.path.exists(NWebtoon.OUTPUT_PATH):
            os.makedirs(NWebtoon.OUTPUT_PATH)

        # 다운로드할 이미지의 URL과 저장 경로를 저장할 리스트
        download_tasks = []

        for i in range(start_index, end_index + 1):
            url = f"https://comic.naver.com/{self.__wtype}/detail?titleId={self.__title_id}&no={i}"
            try:
                req = requests.get(url, headers=headers)  # 헤더 추가
                req.raise_for_status()
                soup = BeautifulSoup(req.content, 'html.parser')
                image_tags = soup.select('div.wt_viewer > img')
                if not image_tags:
                    print(f'no={i}가 없습니다. 순번이 존재하지 않거나 미리보기, 유료화된 페이지입니다. 다운로드 하지 않고 SKIP 합니다.')
                    continue
                for j, img in enumerate(image_tags, 1):
                    img_url = img.get('src')
                    if not img_url.startswith('http'):
                        img_url = 'https:' + img_url
                    img_path = os.path.join(NWebtoon.DOWNLOAD_PATH, f"{i}_{j}.jpg")
                    download_tasks.append((img_url, img_path))
            except requests.exceptions.RequestException as e:
                print(f"이미지 다운로드 중 오류가 발생했습니다 (화: {i}): {e}")

        # ThreadPoolExecutor를 사용하여 병렬로 이미지 다운로드
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.image_download, url, path) for url, path in download_tasks]
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"다운로드 중 오류가 발생했습니다: {e}")

        # 다운로드 완료 후 진행 상황 업데이트
        current_step += 1
        progress = int((current_step / total_steps) * 100)
        update_progress(progress)

        # 이미지 병합
        self.merge_all_episodes(start_index, end_index)

        # 병합 완료 후 진행 상황 업데이트
        current_step += 1
        progress = int((current_step / total_steps) * 100)
        update_progress(progress)

        # 다운로드된 이미지 삭제
        self.delete_downloaded_images()

        # 모든 작업 완료 후 진행 상황 업데이트
        current_step = total_steps
        progress = int((current_step / total_steps) * 100)
        update_progress(progress, complete=True)

    def image_download(self, url: str, file_name: str) -> None:
        """
        주어진 URL에서 이미지를 다운로드하여 지정된 경로에 저장합니다.
        :param url: 이미지 URL
        :param file_name: 저장할 파일 경로
        """
        try:
            response = requests.get(url, headers=image_headers)  # image_headers 사용
            response.raise_for_status()
            with open(file_name, "wb") as file:
                file.write(response.content)  # 파일에 내용 쓰기
            print(f"다운로드 완료: {file_name}")
        except requests.exceptions.RequestException as e:
            print(f"이미지 다운로드 중 예외 발생: {e}")

    def merge_all_episodes(self, start_index: int, end_index: int) -> None:
        """
        지정된 화 번호 범위 내의 모든 화에 대해 이미지를 병합합니다.
        :param start_index: 시작 화 번호
        :param end_index: 종료 화 번호
        """
        for i in range(start_index, end_index + 1):
            merger = ImageMerger(NWebtoon.DOWNLOAD_PATH, i)
            merger.merge_images()

    def delete_downloaded_images(self):
        """
        다운로드된 이미지를 모두 삭제합니다.
        """
        try:
            for filename in os.listdir(NWebtoon.DOWNLOAD_PATH):
                file_path = os.path.join(NWebtoon.DOWNLOAD_PATH, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"삭제 완료: {file_path}")
            print("모든 다운로드된 이미지를 삭제했습니다.")
        except Exception as e:
            print(f"다운로드된 이미지 삭제 중 오류 발생: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python3 webtoon_download.py [titleId] [start_index] [end_index] [session_id]")
        sys.exit(1)
    titleId = sys.argv[1]
    start_index = int(sys.argv[2])
    end_index = int(sys.argv[3])
    session_id = sys.argv[4]
    webtoon = NWebtoon(titleId, session_id)
    webtoon.multi_download(start_index, end_index)
    print("다운로드 및 병합이 완료되었습니다.")
