import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

def get_working_model():
    """현재 API 키로 접근 가능한 모델 목록을 구글 서버에서 직접 조회하여 자동 선택합니다."""
    try:
        models = genai.list_models()
        valid_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
        
        # 1.5 flash 최신 버전이나 기본 버전이 있다면 최우선으로 선택
        for target in ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']:
            for vm in valid_models:
                if target in vm:
                    return vm
                    
        # 선호 모델이 없으면, 서버가 허용한 목록 중 무조건 첫 번째 모델을 강제 사용
        if valid_models:
            return valid_models[0]
    except Exception:
        pass
    
    return "models/gemini-1.5-flash" # 최후의 예외 처리

def get_gemini_response(api_key, messages, system_prompt, temp, top_p, max_tokens):
    genai.configure(api_key=api_key.strip())
    
    safety = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    }
    
    # 에러가 나던 고정된 이름 대신, 위에서 찾은 '실제 작동하는 모델명'을 투입
    active_model_name = get_working_model()
    
    model = genai.GenerativeModel(
        model_name=active_model_name,
        system_instruction=system_prompt
    )
    
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
