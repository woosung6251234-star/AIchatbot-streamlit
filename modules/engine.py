import google.generativeai as genai

def get_gemini_response(api_key, messages, system_prompt, temp, top_p, max_tokens):
    genai.configure(api_key=api_key.strip())
    
    # 404 에러가 나지 않는 3.8-flash 모델로 완전히 고정
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
    
    # 3.8 모델의 스트리밍 증발 버그를 막기 위해 통째로 받아옵니다 (stream=False)
    response = chat.send_message(
        messages[-1]["content"],
        generation_config=config,
        stream=False 
    )
    
    return response.text
