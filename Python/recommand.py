#!/usr/bin/env python3
import sys
import json
import pymysql

# --- 데이터베이스 설정 (환경에 맞게 수정) ---
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "123",
    "database": "webtoon",
    "charset": "utf8mb4"
}

def search_webtoon(keywords):
    """
    주어진 키워드(태그) 리스트를 기반으로 DB에서 웹툰을 검색하고 매칭 점수 순으로 정렬
    """
    # 키워드가 없는 경우, 메시지를 포함한 리스트를 반환
    if not keywords:
        return ["키워드가 선택되지 않았습니다."]

    connection = None
    try:
        # 데이터베이스에 연결합니다.
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            # 각 키워드에 대해 매칭 여부를 계산하여 점수로 활용하는 부분
            select_keyword_matches = []
            for keyword in keywords:
                # 간단한 SQL 인젝션 방지를 위해 작은 따옴표를 이스케이프 처리합니다.
                clean_keyword = keyword.replace("'", "''")
                select_keyword_matches.append(f"""
                    (CASE
                        WHEN (wi.tag LIKE '%{clean_keyword}%' OR wi.summary LIKE '%{clean_keyword}%')
                        THEN 1
                        ELSE 0
                    END)
                """)

            # WHERE 절: 선택된 키워드 중 하나라도 포함하는 웹툰을 검색 대상으로 합니다.
            where_conditions = []
            for keyword in keywords:
                clean_keyword = keyword.replace("'", "''")
                where_conditions.append(f"(wi.tag LIKE '%{clean_keyword}%' OR wi.summary LIKE '%{clean_keyword}%')")

            # 최종 SQL 쿼리를 구성합니다.
            query = f"""
                SELECT
                    wi.title,
                    wi.S_N,
                    ({ ' + '.join(select_keyword_matches) }) AS keyword_match_count
                FROM webtoon_info wi
                WHERE ( {' OR '.join(where_conditions)} )
                GROUP BY wi.S_N, wi.title
                ORDER BY keyword_match_count DESC, wi.title ASC
                LIMIT 5;
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            if results:
                # 결과에서 S_N (고유번호)만 추출하여 문자열 리스트로 반환
                return [str(row[1]) for row in results]
            else:
                # 일치하는 웹툰이 없는 경우
                return ["선택한 태그와 일치하는 웹툰을 찾을 수 없습니다."]

    except pymysql.MySQLError as e:
        # 데이터베이스 오류 발생 시, 오류 메시지를 포함한 리스트를 반환
        return [f"데이터베이스 검색 중 오류가 발생했습니다: {e}"]
    finally:
        # 연결을 항상 닫습니다.
        if connection:
            connection.close()

# 이 스크립트가 직접 실행될 때만 아래 코드가 동작합니다.
if __name__ == "__main__":
    # PHP에서 전달한 인자가 없거나 비어있는 경우
    if len(sys.argv) < 2 or not sys.argv[1]:
        print(json.dumps({"recommended": ["추천을 원하는 태그를 선택해주세요."]}, ensure_ascii=False))
        sys.exit(0)

    # PHP로부터 쉼표로 구분된 태그 문자열을 받습니다. (예: "로맨스,회귀,능력남")
    user_input_tags = sys.argv[1]
    
    # 받은 문자열을 쉼표 기준으로 잘라 리스트로 만듭니다.
    keywords = [tag.strip() for tag in user_input_tags.split(',') if tag.strip()]
    
    # 웹툰 검색 함수를 호출하여 S_N 리스트를 받습니다.
    recommendation_sn_list = search_webtoon(keywords)
    
    # 최종 결과를 JSON 형태로 표준 출력하여 PHP에 전달합니다.
    print(json.dumps({"recommended": recommendation_sn_list}, ensure_ascii=False))