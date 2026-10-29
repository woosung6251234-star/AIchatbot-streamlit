import google.generativeai as genai

def get_gemini_response(api_key, messages, system_prompt, temp, top_p, max_tokens):
    genai.configure(api_key=api_key.strip())
    
    # 404 에러를 피해 성공적으로 연결되었던 모델로 고정
    model = genai.GenerativeModel(
        model_name="gemini-3.8-flash",
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
    
    # 무한 재시도를 끄고, 기존 연산 속도(2분 이상)를 고려해 타임아웃을 240초로 넉넉하게 연장
    response = chat.send_message(
        messages[-1]["content"],
        generation_config=config,
        stream=False,
        request_options={"retry": None, "timeout": 240} 
    )
    
    return response.text
