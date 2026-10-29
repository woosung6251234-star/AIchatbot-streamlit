import google.generativeai as genai

def get_best_model():
    """현재 API 키에서 실제로 작동하는 모델을 직접 조회하여 찾습니다."""
    try:
        models = [
            m.name for m in genai.list_models() 
            if 'generateContent' in m.supported_generation_methods
        ]
        # 3.0이나 최신 flash 모델을 최우선으로 찾음
        for target in ['gemini-3.0-flash', 'gemini-2.0-flash', 'flash', 'pro']:
            for m in models:
                if target in m:
                    return m
        if models:
            return models[0]
    except Exception:
        pass
    return "models/gemini-3.0-flash"

def get_gemini_response(api_key, messages, system_prompt, temp, top_p, max_tokens):
    genai.configure(api_key=api_key.strip())
    
    # 실제로 존재하는 모델 이름 자동 장착
    model_name = get_best_model()
    
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=system_prompt if system_prompt else None
    )
    
    # 전체 대화 문맥 구성
    contents = []
    for msg in messages:
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [msg["content"]]})
        
    config = genai.types.GenerationConfig(
        temperature=temp,
        top_p=top_p,
        max_output_tokens=max_tokens
    )
    
    # 버그가 잦은 start_chat 대신 가장 확실한 generate_content 직접 호출
    response = model.generate_content(
        contents,
        generation_config=config,
        stream=True
    )
    
    return response, model_name
