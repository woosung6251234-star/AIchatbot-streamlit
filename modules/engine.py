import google.generativeai as genai

def get_gemini_response(api_key, messages, system_prompt, temp, top_p, max_tokens):
    genai.configure(api_key=api_key.strip())
    
    # 무조건 작동이 확인된 3.8-flash 모델로 고정
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
    
    # stream=True로 설정하여 서버 통신 강제 종료(504 에러)를 방지하고 실시간으로 데이터를 받아옴
    response = chat.send_message(
        messages[-1]["content"],
        generation_config=config,
        stream=True
    )
    
    return response
