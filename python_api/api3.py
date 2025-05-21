import openai
import sys
import json
import os

# OpenAI API 키를 환경 변수에서 가져오기 (보안상 더 안전함)
openai.api_key = "your_key"

def summarize_text(text, task_type="summary", temperature=0.3):
    """주어진 텍스트를 요약하거나 문법을 교정하는 함수"""
    try:
        # 요약을 할 경우
        if task_type == "grammar":
            response = openai.ChatCompletion.create(
                model="gpt-4",
                temperature=temperature,
                messages=[
                    {"role": "system", "content": "당신은 문법 교정과 오탈자 수정을 전문으로 하는 교정자입니다. 주어진 텍스트의 의미나 톤을 변경하지 않고 오탈자를 수정하고 문법을 개선해 주세요."},
                    {"role": "user", "content": f"다음 텍스트의 문법을 교정해 주세요:\n\n{text}"}
                ]
            )
        
        # 문법 교정을 할 경우
        elif task_type == "summary":
            response = openai.ChatCompletion.create(
                model="gpt-4",
                temperature=temperature,
                messages=[
                    {"role": "system", "content": "당신은 복잡한 이야기를 간결하게 요약하는 데 전문가입니다. 주요 중요한 사건에 집중하여 간단하고 이해하기 쉬운 요약을 작성해 주세요."},
                    {"role": "user", "content": f"다음 텍스트를 한국어로 짧게 요약해 주세요. 출력할 때는 오직 요약문만 출력해주세요.:\n\n{text}"}
                ]
            )
        
        else:
            return "알 수 없는 작업 유형입니다."

        summary_or_grammar = response['choices'][0]['message']['content']
        return summary_or_grammar.strip()
    
    except openai.error.OpenAIError as e:
        return f"오류 발생: {str(e)}"
    except Exception as e:
        return f"예기치 못한 오류 발생: {str(e)}"

def process_request():
    """PHP에서 전달된 텍스트를 받아서 요약 또는 문법 교정 결과를 반환하는 함수"""
    # PHP에서 전달된 텍스트를 가져오기
    input_text = sys.argv[1]  # 텍스트가 첫 번째 인자로 전달된다고 가정

    if not input_text:
        print(json.dumps({"error": "텍스트가 전달되지 않았습니다."}))
        return

    # 작업 유형을 결정 (예: "summary" 또는 "grammar")
    task_type = sys.argv[2] if len(sys.argv) > 2 else "summary"  # 기본값은 요약

    # 작업 수행 (요약 또는 문법 교정)
    result = summarize_text(input_text, task_type)
    
    # 결과 반환
    if result:
        print(json.dumps({"result": result}))
    else:
        print(json.dumps({"error": "처리에 실패했습니다."}))

if __name__ == "__main__":
    # 환경 변수가 설정되지 않은 경우, 종료
    if not openai.api_key:
        print(json.dumps({"error": "OpenAI API 키가 설정되지 않았습니다."}))
        sys.exit(1)

    process_request()