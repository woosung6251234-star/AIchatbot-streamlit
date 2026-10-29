import google.generativeai as genai

def get_gemini_response(api_key, messages, system_prompt, temp, top_p, max_tokens):
    genai.configure(api_key=api_key.strip())
    
    # 스트리밍이 가장 안정적으로 작동하는 공식 모델로 고정
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_prompt
    )
    
    history = []
    for msg in messages[:-1]:
        role = "model" if msg["role"] == "assistant" else "user"
        history.append({"role": role, "parts": [msg["content"]]})
        
    chat = model.start_chat(history=history)
    current_message = messages[-1]["content"]
    
    response = chat.send_message(
        current_message,
        stream=True
    )
    
    return response
