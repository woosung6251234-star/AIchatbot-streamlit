import streamlit as st
import pandas as pd
from modules.security import run_security_scan
from modules.engine import get_gemini_response

# CSS 적용
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 메모리 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "audit_logs" not in st.session_state:
    st.session_state.audit_logs = []

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    st.error("서버에 API 키가 설정되지 않았습니다.")
    st.stop()

# 사이드바: 엔진 컨트롤 패널
with st.sidebar:
    st.markdown("### ⚙️ Engine Control")
    sys_prompt = st.text_area("시스템 프롬프트 (최면 제어)", value="당신은 논리적이고 객관적인 AI 어시스턴트입니다.", height=100)
    
    st.markdown("**Hyperparameters**")
    temp = st.slider("Temperature (창의성)", 0.0, 2.0, 0.7, 0.1)
    top_p = st.slider("Top-P (단어 다양성)", 0.0, 1.0, 0.9, 0.05)
    max_tokens = st.number_input("Max Tokens (길이 제한)", min_value=100, max_value=8192, value=2048)
    
    if st.session_state.audit_logs:
        st.markdown("### 🚨 보안 로그")
        st.dataframe(pd.DataFrame(st.session_state.audit_logs), use_container_width=True)
        
    if st.button("새 대화 시작"):
        st.session_state.messages = []
        st.rerun()

# 메인 채팅 인터페이스
st.title("Advanced AI Studio")

# 이전 대화 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("메시지를 입력하세요...")

if user_input:
    is_safe, filtered_input = run_security_scan(user_input)
    
    # 사용자 입력 화면 출력 및 저장
    with st.chat_message("user"):
        st.markdown(filtered_input)
    st.session_state.messages.append({"role": "user", "content": filtered_input})
    
    if not is_safe:
        with st.chat_message("assistant"):
            st.error(filtered_input)
        st.stop()
        
    # AI 답변 실시간 스트리밍
    with st.chat_message("assistant"):
        stream_response = get_gemini_response(
            API_KEY, st.session_state.messages, sys_prompt, temp, top_p, max_tokens
        )
        # st.write_stream이 제너레이터를 받아 타자기 효과를 자동으로 구현합니다.
        full_response = st.write_stream(chunk.text for chunk in stream_response)
        
    st.session_state.messages.append({"role": "assistant", "content": full_response})
