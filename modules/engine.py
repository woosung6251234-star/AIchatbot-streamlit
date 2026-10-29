import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

def get_gemini_response(api_key, messages, system_prompt, temp, top_p, max_tokens):
    genai.configure(api_key=api_key.strip())
    
    safety = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    }
    
    # 🚨 유령 모델(3.8)을 삭제하고 구글 공식 권장 모델로 정상화
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
    
    # 다시 타자기 효과(스트리밍)를 켜서 1초 만에 글자가 찍히도록 복구
    response = chat.send_message(
        current_message,
        generation_config=config,
        safety_settings=safety,
        stream=True 
    )
    
    return response
