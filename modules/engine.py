import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

def get_gemini_response(api_key, messages, system_prompt, temp, top_p, max_tokens):
    genai.configure(api_key=api_key)
    
    safety = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    }
    
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-8b",
        system_instruction=system_prompt
    )
    
    # 마지막 질문을 제외한 '과거 대화 기록'만 먼저 정리
    history = []
    for msg in messages[:-1]:
        role = "model" if msg["role"] == "assistant" else "user"
        history.append({"role": role, "parts": [msg["content"]]})
        
    config = genai.types.GenerationConfig(
        temperature=temp,
        top_p=top_p,
        max_output_tokens=max_tokens
    )
    
    # 1. 과거 기록을 바탕으로 공식 채팅 세션 시작
    chat = model.start_chat(history=history)
    
    # 2. 방금 입력한 새로운 질문만 따로 전송 (실시간 스트리밍 켜기)
    current_message = messages[-1]["content"]
    response = chat.send_message(
        current_message,
        generation_config=config,
        safety_settings=safety,
        stream=True
    )
    
    return response
