import os
import re
import requests
from bs4 import BeautifulSoup
import concurrent.futures
import cv2
import numpy as np
import natsort
import glob
import time

headers: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
}
image_headers: dict[str, str] = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36',
    'host': 'image-comic.pstatic.net'}

class ImageProcessor:
    def __init__(self, dir_path, episode_number, ocr_reader):
        self.dir_path = dir_path
        self.episode_number = episode_number
        self.ocr_reader = ocr_reader
        # OpenCV가 처리 가능한 최대 픽셀 크기 (안전 마진 포함)
        self.OPENCV_MAX_PIXELS = 3900

    def process_episode_images(self):
        try:
            merged_image = self._merge_images_memory_efficient()
            if merged_image is None:
                print(f"에피소드 {self.episode_number}: 병합할 이미지가 없습니다.")
                return ""

            text_regions = self._preprocess_and_find_regions(merged_image)
            extracted_text = self._extract_text_from_regions(merged_image, text_regions)
            return extracted_text

        except Exception as e:
            print(f"에피소드 {self.episode_number} 처리 중 오류 발생: {e}")
            return ""
        finally:
            self._cleanup_image_parts()

    def _extract_text_from_regions(self, image, regions):
        if self.ocr_reader is None: return ""
        
        all_texts = []
        for i, (x, y, w, h) in enumerate(regions):
            padding = 10
            y_padded = max(y - padding, 0)
            h_padded = min(h + 2 * padding, image.shape[0] - y_padded)
            
            if h_padded < self.OPENCV_MAX_PIXELS:
                cropped_image_np = image[y_padded : y_padded + h_padded, 0:image.shape[1]]
                region_text = self._perform_ocr_on_image(cropped_image_np)
                if region_text:
                    all_texts.append(region_text)
            else:
                print(f"영역 {i+1}의 높이({h_padded}px)가 한계를 초과하여 분할 처리합니다.")
                oversized_region_image = image[y_padded : y_padded + h_padded, 0:image.shape[1]]
                
                chunk_texts = []
                region_height = oversized_region_image.shape[0]
                overlap = 200  # 겹치는 부분을 조금 줄여서 안정성 확보
                step = self.OPENCV_MAX_PIXELS - overlap # 다음 조각을 시작할 위치

                for y_start in range(0, region_height, step):
                    # 조각의 끝 위치는 항상 MAX_PIXELS를 넘지 않도록 계산
                    y_end = min(y_start + self.OPENCV_MAX_PIXELS, region_height)
                    image_chunk = oversized_region_image[y_start:y_end, :]
                    
                    chunk_text = self._perform_ocr_on_image(image_chunk)
                    if chunk_text:
                        chunk_texts.append(chunk_text)
                
                full_region_text = "\n".join(chunk_texts)
                if full_region_text:
                    all_texts.append(full_region_text)

        return "\n".join(all_texts)

    def _perform_ocr_on_image(self, image_np):
        try:
            result = self.ocr_reader.ocr(image_np)
            if result and result[0]:
                # 새로운 딕셔너리 결과 구조에서 텍스트만 추출합니다.
                res_dict = result[0]
                texts = res_dict.get('rec_texts', [])
                return " ".join(texts)
            return ""
        except Exception as e:
            print(f"OCR 수행 중 오류 발생: {e}")
            return ""

    def _merge_images_memory_efficient(self):
        file_pattern = os.path.join(self.dir_path, f"{self.episode_number}_*.jpg")
        file_lst = natsort.natsorted(glob.glob(file_pattern))
        if not file_lst: return None
        valid_images = []
        for f in file_lst:
            img = cv2.imread(f)
            if img is not None: valid_images.append(img)
        if not valid_images: return None
        target_width = valid_images[0].shape[1]
        total_height = 0
        resized_heights = []
        for img in valid_images:
            height = int(img.shape[0] * target_width / img.shape[1])
            total_height += height
            resized_heights.append(height)
        merged_canvas = np.zeros((total_height, target_width, 3), dtype=np.uint8)
        current_y = 0
        for i, img in enumerate(valid_images):
            resized_img = cv2.resize(img, (target_width, resized_heights[i]), interpolation=cv2.INTER_CUBIC)
            merged_canvas[current_y : current_y + resized_heights[i], :] = resized_img
            current_y += resized_heights[i]
        return merged_canvas

    def _preprocess_and_find_regions(self, image):
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_clahe = clahe.apply(gray)
        gaussian = cv2.GaussianBlur(gray_clahe, (0, 0), sigmaX=15, sigmaY=15)
        divided = cv2.divide(gray_clahe, gaussian, scale=255)
        thresh = cv2.adaptiveThreshold(divided, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 10)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        clean = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=3)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(clean)
        regions = []
        for i in range(1, num_labels):
            x, y, w, h, area = stats[i]
            if area > 1000 and h > 100 and w > 100: regions.append([x, y, w, h])
        def merge_overlapping_regions(regions):
            merged = True
            while merged:
                merged = False
                new_regions = []
                used = [False] * len(regions)
                for i in range(len(regions)):
                    if used[i]: continue
                    x1, y1, w1, h1 = regions[i]
                    for j in range(i + 1, len(regions)):
                        if used[j]: continue
                        x2, y2, w2, h2 = regions[j]
                        if min(x1 + w1, x2 + w2) - max(x1, x2) >= 0 and min(y1 + h1, y2 + h2) - max(y1, y2) >= 0:
                            new_x1, new_y1 = min(x1, x2), min(y1, y2)
                            regions[i] = [new_x1, new_y1, max(x1 + w1, x2 + w2) - new_x1, max(y1 + h1, y2 + h2) - new_y1]
                            used[j] = True
                            merged = True
                    new_regions.append(regions[i])
                regions = new_regions
            return regions
        return sorted(merge_overlapping_regions(regions), key=lambda r: r[1])

    def _cleanup_image_parts(self):
        file_pattern = os.path.join(self.dir_path, f"{self.episode_number}_*.jpg")
        for image_file in glob.glob(file_pattern):
            try:
                os.remove(image_file)
            except OSError as e:
                print(f"파일 삭제 오류 {image_file}: {e}")

class NWebtoon:
    def __init__(self, title_id: str, ocr_reader, tmp_download_path: str) -> None:
        self.__title_id: str = title_id
        self.ocr_reader = ocr_reader
        self.tmp_download_path = tmp_download_path
        self.__title: str = ""
        try:
            res = requests.get(f"https://comic.naver.com/api/article/list/info?titleId={self.__title_id}", headers=headers)
            res.raise_for_status()
            self.__title = res.json().get('titleName', 'Unknown Title')
        except Exception as e:
            print(f"웹툰 정보 초기화 중 오류: {e}")

    def multi_download(self, start_index: int, end_index: int):
        """기존 메서드: 범위 내 모든 에피소드 처리"""
        episodes_to_process = list(range(start_index, end_index + 1))
        return self.multi_download_filtered(episodes_to_process)

    def multi_download_filtered(self, episodes_to_process: list):
        """새 메서드: 지정된 에피소드들만 처리"""
        if not episodes_to_process:
            print("처리할 에피소드가 없습니다.")
            return {}
        
        os.makedirs(self.tmp_download_path, exist_ok=True)
        download_tasks = []
        
        for episode_num in episodes_to_process:
            print(f"에피소드 {episode_num} 다운로드 준비 중...")
            url = f"https://comic.naver.com/webtoon/detail?titleId={self.__title_id}&no={episode_num}"
            try:
                print(f"에피소드 {episode_num} 페이지 요청 전 0.5초 대기...")
                time.sleep(0.5)
                req = requests.get(url, headers=headers)
                req.raise_for_status()
                soup = BeautifulSoup(req.content, 'html.parser')
                image_tags = soup.select('div.wt_viewer > img')
                
                if not image_tags:
                    print(f"에피소드 {episode_num}: 이미지를 찾을 수 없습니다.")
                    continue
                
                for j, img in enumerate(image_tags, 1):
                    img_url = img.get('src')
                    if img_url:
                        img_path = os.path.join(self.tmp_download_path, f"{episode_num}_{j}.jpg")
                        download_tasks.append((img_url, img_path))
                        
            except Exception as e:
                print(f"에피소드 {episode_num} 정보 파싱 중 오류: {e}")
        
        if not download_tasks:
            print("다운로드할 이미지가 없습니다.")
            return {}
        
        print(f"총 {len(download_tasks)}개의 이미지를 다운로드합니다...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(lambda p: self.image_download(*p), download_tasks)
        
        print("OCR 처리를 시작합니다...")
        return self.process_episodes(episodes_to_process)

    def image_download(self, url: str, file_name: str) -> None:
        try:
            response = requests.get(url, headers=image_headers)
            response.raise_for_status()
            with open(file_name, "wb") as file: 
                file.write(response.content)
        except Exception as e:
            print(f"이미지 다운로드 중 예외 발생 ({url}): {e}")

    def process_episodes(self, episodes_to_process: list):
        """지정된 에피소드들에 대해 OCR 처리 수행"""
        episode_results = {}
        total_episodes = len(episodes_to_process)
        
        for i, episode_num in enumerate(episodes_to_process, 1):
            print(f"[{i}/{total_episodes}] 에피소드 {episode_num} OCR 처리 중...")
            processor = ImageProcessor(self.tmp_download_path, episode_num, self.ocr_reader)
            extracted_text = processor.process_episode_images()
            
            if extracted_text:
                episode_results[episode_num] = extracted_text
                print(f"에피소드 {episode_num}: 텍스트 추출 완료 (길이: {len(extracted_text)} 문자)")
            else:
                print(f"에피소드 {episode_num}: 추출된 텍스트가 없습니다.")
                
        return episode_results

    def process_all_episodes(self, start_index: int, end_index: int):
        """기존 메서드와의 호환성을 위한 래퍼"""
        episodes_to_process = list(range(start_index, end_index + 1))
        return self.process_episodes(episodes_to_process)