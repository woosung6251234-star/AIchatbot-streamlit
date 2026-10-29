import google.generativeai as genai

def get_gemini_response(api_key, messages, system_prompt, temp, top_p, max_tokens):
    genai.configure(api_key=api_key.strip())
    
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
    
    # 몰래 2~3분씩 재시도하며 시간을 끄는 라이브러리 내부 기능을 완전히 차단
    response = chat.send_message(
        messages[-1]["content"],
        generation_config=config,
        stream=False,
        request_options={"retry": None, "timeout": 30} 
    )
    
    return response.text
