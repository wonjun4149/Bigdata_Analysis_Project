import openai
import pymysql
import json
import os
import re

# GPT-3 API 설정
def extract_keywords(user_input):
    openai.api_key = "your_key"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            temperature=0.7,
            messages=[ 
                {"role": "system", "content": "당신은 중요한 키워드를 추출하는 도우미입니다."},
                {"role": "user", "content": f"사용자의 요청에서 핵심 키워드를 추출하세요: \"{user_input}\""}
            ]
        )
        keywords = response['choices'][0]['message']['content'].strip()
        # 키워드 중복 제거 및 단어만 추출
        keywords = re.sub(r'[^\w\s]', '', keywords)  # 특수문자 제거
        keyword_list = list(set(keywords.split()))
        return keyword_list
    except openai.error.OpenAIError as e:
        print(f"텍스트 수정 중 오류 발생: {e}")
        return None

# 데이터베이스 설정
db_config = {
    "host": "localhost",
    "user": "webtoon_user",
    "password": "1234",
    "database": "webtoon",
    "charset": "utf8mb4"
}

def search_webtoon(keywords):
    # MySQL 연결
    connection = pymysql.connect(
        host=db_config["host"],
        user=db_config["user"],
        password=db_config["password"],
        database=db_config["database"],
        charset=db_config["charset"]
    )

    try:
        with connection.cursor() as cursor:
            # 키워드를 기반으로 데이터 검색
            keyword_condition = " OR ".join([f"tag LIKE '%{keyword}%' OR summary LIKE '%{keyword}%' OR line LIKE '%{keyword}%'" for keyword in keywords])
            query = f"""
                SELECT webtoon_info.title, webtoon_info.S_N, COUNT(*) AS keyword_matches
                FROM webtoon_info
                LEFT JOIN webtoon_text ON webtoon_info.S_N = webtoon_text.S_N
                WHERE {keyword_condition}
                GROUP BY webtoon_info.S_N
                ORDER BY keyword_matches DESC
                LIMIT 3;
            """
            cursor.execute(query)
            results = cursor.fetchall()  # 여러 개의 결과를 가져옴
            if results:
                # 상위 3개의 S_N만 추출하여 리스트로 반환
                top_3_sn = [str(result[1]) for result in results]
                return top_3_sn
            else:
                return "추천할 웹툰을 찾을 수 없습니다."
    finally:
        connection.close()

def recommend_webtoon(user_input):
    keywords = extract_keywords(user_input)
    recommended_sn = search_webtoon(keywords)
    return recommended_sn

if __name__ == "__main__":
    import sys
    user_input = sys.argv[1]
    recommendations = recommend_webtoon(user_input)
    
    # S_N 값만 출력하기 위해 JSON에서 S_N 리스트로 응답
    if isinstance(recommendations, list):
        response = {"recommended": recommendations}
    else:
        response = {"recommended": [recommendations]}
    
    print(json.dumps(response, ensure_ascii=False))
