import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

def get_available_model():
    """현재 API 키로 접근 가능한 최적의 Gemini 모델을 자동으로 탐색합니다."""
    try:
        available_models = [
            m.name for m in genai.list_models() 
            if 'generateContent' in m.supported_generation_methods
        ]
        # 우선순위별로 모델 매칭
        for target in ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
            for m in available_models:
                if target in m:
                    return m
        # 매칭되는 게 없으면 사용 가능한 첫 번째 모델 반환
        if available_models:
            return available_models[0]
    except Exception:
        pass
    return "models/gemini-1.5-flash"

def get_gemini_response(api_key, messages, system_prompt, temp, top_p, max_tokens):
    # API 키 앞뒤에 실수로 들어간 공백이나 줄바꿈 제거
    clean_key = api_key.strip()
    genai.configure(api_key=clean_key)
    
    safety = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    }
    
    # 사용 가능한 모델 이름 자동 획득
    active_model_name = get_available_model()
    
    try:
        model = genai.GenerativeModel(
            model_name=active_model_name,
            system_instruction=system_prompt
        )
    except Exception:
        # 구버전 모델이 system_instruction을 지원하지 않을 경우 대비
        model = genai.GenerativeModel(model_name=active_model_name)
    
    history = []
    for msg in messages[:-1]:
        role = "model" if msg["role"] == "assistant" else "user"
        history.append({"role": role, "parts": [msg["content"]]})
        
    config = genai.types.GenerationConfig(
        temperature=temp,
        top_p=top_p,
        max_output_tokens=max_tokens
    )
    
    chat = model.start_chat(history=history)
    current_message = messages[-1]["content"]
    
    response = chat.send_message(
        current_message,
        generation_config=config,
        safety_settings=safety,
        stream=True
    )
    
    return response
