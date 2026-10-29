import google.generativeai as genai

def get_gemini_response(api_key, messages, system_prompt, temp, top_p, max_tokens):
    genai.configure(api_key=api_key.strip())
    
    # 1.5나 최신 버전 충돌을 피하기 위해 모든 계정에서 100% 작동하는 기본 모델 사용
    model = genai.GenerativeModel(model_name="gemini-pro")
    
    history = []
    
    # 시스템 프롬프트(최면)를 구형 모델도 이해할 수 있도록 첫 번째 대화로 강제 주입
    if system_prompt:
        history.append({"role": "user", "parts": [f"[시스템 지시사항]: {system_prompt}\n\n위 지시사항을 숙지하고 대답해 주세요."]})
        history.append({"role": "model", "parts": ["네, 시스템 지시사항을 완벽히 숙지했습니다. 지시하신 역할에 맞춰 답변하겠습니다."]})
    
    # 이전 대화 기록 이어붙이기
    for msg in messages[:-1]:
        role = "model" if msg["role"] == "assistant" else "user"
        history.append({"role": role, "parts": [msg["content"]]})
        
    chat = model.start_chat(history=history)
    current_message = messages[-1]["content"]
    
    # 실시간 스트리밍 활성화
    response = chat.send_message(
        current_message,
        stream=True
    )
    
    return response
