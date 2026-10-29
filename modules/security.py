import re
import datetime
import streamlit as st

def get_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def run_security_scan(text):
    compact = re.sub(r'\s+', '', text)
    banned = ["탈옥", "규칙무시", "해킹", "음란", "폭력"]
    
    for b in banned:
        if b in compact:
            st.session_state.audit_logs.append({"time": get_time(), "type": "차단", "trigger": b})
            return False, "🚨 보안 규정 위배로 요청이 차단되었습니다."
            
    masked = re.sub(r'01[016789][-\s.]?\d{3,4}[-\s.]?\d{4}', '[개인정보_전화번호]', text)
    if text != masked:
        st.session_state.audit_logs.append({"time": get_time(), "type": "마스킹", "trigger": "전화번호"})
        
    return True, masked
