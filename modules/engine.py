import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

def get_gemini_response(api_key, messages, system_prompt, temp, top_p, max_tokens):
    # 새 API 키 적용 및 공백 제거
    genai.configure(api_key=api_key.strip())
    
    safety = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    }
    
    # 새 API 키에서 가장 완벽하게 스트리밍이 지원되는 공식 무료 모델 고정
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
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
    
    # 타자기 효과(스트리밍) 활성화
    response = chat.send_message(
        current_message,
        generation_config=config,
        safety_settings=safety,
        stream=True 
    )
    
    return response
