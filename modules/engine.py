import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

def get_gemini_response(api_key, messages, system_prompt, temp, top_p, max_tokens):
    # API 키 공백 제거
    clean_key = api_key.strip()
    genai.configure(api_key=clean_key)
    
    safety = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    }
    
    # 구글 서버에서 에러 메시지로 요구한 최신 모델명으로 변경
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
    current_message = messages[-1]["content"]
    
    response = chat.send_message(
        current_message,
        generation_config=config,
        safety_settings=safety,
        stream=True
    )
    
    return response
