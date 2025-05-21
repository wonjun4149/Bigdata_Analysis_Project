from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time

driver_path = '/usr/local/bin/chromedriver'
service = Service(driver_path)

options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=service, options=options)

url = "https://comic.naver.com/webtoon"
driver.get(url)

time.sleep(3)

html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

# 요일별 웹툰 데이터를 저장할 디렉터리 설정
base_path = "/var/www/html/Python/databases/"

# 요일별로 파일 생성
days = soup.select('div.WeekdayMainView__daily_all_item--DnTAH')
for day in days:
    # 요일 이름 추출
    day_name = day.select_one('h3').get_text().strip() if day.select_one('h3') else "요일_불명"
    
    # 파일 경로 지정
    file_path = f"{base_path}{day_name}.txt"
    
    with open(file_path, "w", encoding="utf-8") as file:
        # 해당 요일의 웹툰 제목 목록
        titles = day.select('span.ContentTitle__title--e3qXt')
        
        for title in titles:
            text = title.select_one('span.text')
            if text:
                file.write(f" - {text.get_text()}\n")

driver.quit()
