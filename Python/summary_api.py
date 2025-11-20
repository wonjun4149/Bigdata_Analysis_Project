#!/usr/bin/env python3
import google.generativeai as genai
import sys
import json
import os

GOOGLE_API_KEY = "AIzaSyCYs36VA-vB75FoP8zkjC_PAEjvEubn02U"

if not GOOGLE_API_KEY:
    print(json.dumps({"error": "Google API 키가 설정되지 않았습니다."}))
    sys.exit(1)

genai.configure(api_key=GOOGLE_API_KEY)

# ▼▼▼▼▼ 핵심 수정 부분 (process_text 함수) ▼▼▼▼▼
def process_text(text, task_type="summary", prev_summary=None, temperature=0.3):
    """
    주어진 텍스트를 요약하거나 문법 교정하는 함수.
    prev_summary: 이전 파트의 요약 내용 (문맥 유지를 위해 사용)
    """
    try:
        prompt = "" # 프롬프트 변수 초기화
        if task_type == "grammar":
            prompt = f"""
            당신은 문법 교정과 오탈자 수정을 전문으로 하는 교정자입니다.
            주어진 텍스트의 의미나 톤을 변경하지 않고 오탈자를 수정하고 문법을 개선해 주세요.
            입력 텍스트: {text}
            """
        elif task_type == "summary":
            # 이전 요약 내용(prev_summary)이 있는 경우와 없는 경우의 프롬프트를 분리
            if prev_summary:
                prompt = f"""
                당신은 웹툰의 연속된 줄거리를 요약하는 전문가입니다.
                아래는 이전 파트의 요약 내용입니다. 이 내용과 자연스럽게 이어지도록 다음 파트를 요약해야 합니다.

                [이전 파트 요약]:
                {prev_summary}

                ---

                이제 아래에 제공되는 새로운 텍스트를 읽고, 이전 요약과 자연스럽게 이어지도록 다음 파트를 요약해 주세요.
                [이전 파트 요약]에서 이미 다룬 내용은 반복하지 말고, 새로운 사건과 핵심 내용에 집중하세요.
                '이 웹툰은...' 과 같이 새로 시작하는 느낌이 아니라, 마치 하나의 긴 글처럼 흐름이 끊기지 않게 작성해야 합니다.
                또한 [이전 파트 요약]에서 사용한 어투와 동일한 어투를 사용해야 합니다.

                [새로운 파트 텍스트]:
                {text}
                """
            else: # 이전 요약 내용이 없을 경우 (첫 번째 요약)
                prompt = f"""
                당신은 복잡한 이야기를 간결하게 요약하는 전문가입니다.
                주요 사건을 중심으로 간결한 요약을 작성해 주세요.
                입력 텍스트: {text}
                """
        else:
            return "알 수 없는 작업 유형입니다."
        
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"temperature": temperature}
        )
        return response.text.strip()
    
    except Exception as e:
        return f"오류 발생: {str(e)}"
# ▲▲▲▲▲ 핵심 수정 부분 (process_text 함수) ▲▲▲▲▲

# ▼▼▼▼▼ 핵심 수정 부분 (process_request 함수) ▼▼▼▼▼
def process_request():
    """
    명령행 인자로 전달된 텍스트를 받아 요약 또는 문법 교정 결과를 JSON 형태로 반환하는 함수.
    """
    if len(sys.argv) < 2:
        print(json.dumps({"error": "텍스트가 전달되지 않았습니다."}))
        return

    input_text = sys.argv[1]
    task_type = sys.argv[2] if len(sys.argv) > 2 else "summary"
    # 세 번째 인자로 이전 요약 내용을 받음. 없으면 None.
    prev_summary = sys.argv[3] if len(sys.argv) > 3 else None

    result = process_text(input_text, task_type, prev_summary)
    print(json.dumps({"result": result}))
# ▲▲▲▲▲ 핵심 수정 부분 (process_request 함수) ▲▲▲▲▲

if __name__ == "__main__":
    process_request()