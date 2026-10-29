import streamlit as st
import pandas as pd
from modules.security import run_security_scan
from modules.engine import get_gemini_response

# CSS 적용 (미니멀하고 세련된 UI)
try:
    with open("assets/style.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass # 파일 생성 전에도 에러가 나지 않도록 예외 처리

# 메모리(세션 상태) 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "audit_logs" not in st.session_state:
    st.session_state.audit_logs = []

# API 키 로드
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("⚠️ 서버(Streamlit Secrets)에 API 키가 설정되지 않았습니다.")
    st.stop()

# 왼쪽 사이드바: 엔진 컨트롤 패널
with st.sidebar:
    st.markdown("### ⚙️ Engine Control")
    sys_prompt = st.text_area("시스템 프롬프트 (AI 성격 부여)", value="당신은 논리적이고 객관적인 AI 어시스턴트입니다.", height=100)
    
    st.markdown("**Hyperparameters**")
    temp = st.slider("Temperature (창의성)", 0.0, 2.0, 0.7, 0.1)
    top_p = st.slider("Top-P (단어 다양성)", 0.0, 1.0, 0.9, 0.05)
    max_tokens = st.number_input("Max Tokens (길이 제한)", min_value=100, max_value=8192, value=2048)
    
    if st.session_state.audit_logs:
        st.markdown("### 🚨 보안 로그")
        st.dataframe(pd.DataFrame(st.session_state.audit_logs), use_container_width=True)
        
    if st.button("새 대화 시작", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# 메인 화면
st.title("Advanced AI Studio")

# 이전 대화 기록 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 채팅 입력창
user_input = st.chat_input("메시지를 입력하세요...")

if user_input:
    # 1. 3중 보안 가드레일 검사
    is_safe, filtered_input = run_security_scan(user_input)
    
    # 2. 사용자 입력 화면에 표시 및 저장
    with st.chat_message("user"):
        st.markdown(filtered_input)
    st.session_state.messages.append({"role": "user", "content": filtered_input})
    
    # 3. 보안 위반 시 차단
    if not is_safe:
        with st.chat_message("assistant"):
            st.error(filtered_input)
        st.stop()
        
    # 4. AI 답변 실시간 스트리밍 (오류 상세 표기 적용)
    with st.chat_message("assistant"):
        try:
            stream_response = get_gemini_response(
                API_KEY, st.session_state.messages, sys_prompt, temp, top_p, max_tokens
            )
            # st.write_stream이 제너레이터를 받아 타자기 효과를 자동으로 구현
            full_response = st.write_stream(chunk.text for chunk in stream_response)
            
            # 정상 응답 시 대화 기록에 저장
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            # 🚨 에러 발생 시 숨기지 않고 화면에 직접 출력 (트러블슈팅용)
            st.error(f"⚠️ 상세 오류 원인: {e}")
            st.info("💡 팁: API 키 문제이거나, 사이드바에서 '새 대화 시작'을 눌러 이전 에러 기록을 지워야 할 수 있습니다.")
