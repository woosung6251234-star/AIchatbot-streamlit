import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import re
import random
import urllib.parse
from PIL import Image
import pandas as pd

st.set_page_config(page_title="AI 심화탐구 챗봇", page_icon="🤖", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0
if "ab_test_active" not in st.session_state:
    st.session_state.ab_test_active = False
if "ab_data" not in st.session_state:
    st.session_state.ab_data = {}

def check_security_guardrail(text):
    compact_text = re.sub(r'\s+', '', text)
    banned_patterns = ["규칙을무시", "이전지시를무시", "탈옥", "시스템프롬프트", "성인물", "음란", "폭력", "자살", "마약", "해킹", "불법"]
    for pattern in banned_patterns:
        if pattern in compact_text:
            return False, "🚨 [보안 가드레일 작동] AI 윤리 및 보안 규정에 위배되는 질문이 감지되어 전송이 차단되었습니다."
    masked_text = re.sub(r'01[016789][-\s.]?\d{3,4}[-\s.]?\d{4}', '[🔒전화번호 숨김]', text)
    masked_text = re.sub(r'\d{6}[-\s]?[1-4]\d{6}', '[🔒주민번호 숨김]', masked_text)
    return True, masked_text

def apply_language_filter(user_prompt, ai_response, filter_enabled):
    if not filter_enabled:
        return ai_response
    bypass_keywords = ["한자", "중국어", "일본어", "번역", "외국어", "원어", "어원", "영어로"]
    if any(k in user_prompt for k in bypass_keywords):
        return ai_response
    cleaned_response = re.sub(r'[\u4e00-\u9fff\u3040-\u30ff]+', '', ai_response)
    return cleaned_response

def parse_ai_response(text):
    thought = ""
    keywords = []
    main_answer = text
    thought_match = re.search(r'\[추론과정\](.*?)\[/추론과정\]', main_answer, re.DOTALL)
    if thought_match:
        thought = thought_match.group(1).strip()
        main_answer = re.sub(r'\[추론과정\].*?\[/추론과정\]', '', main_answer, flags=re.DOTALL).strip()
    kw_match = re.search(r'\[검증키워드:\s*(.*?)\]', main_answer)
    if kw_match:
        raw_kw = kw_match.group(1)
        keywords = [k.strip() for k in raw_kw.split(',') if k.strip()]
        main_answer = re.sub(r'\[검증키워드:\s*.*?\]', '', main_answer).strip()
    return thought, main_answer, keywords

def render_verification_links(keywords):
    if not keywords:
        return
    st.caption("🔍 **출처 환각(Hallucination) 교차 검증 바로가기:**")
    cols = st.columns(len(keywords[:3]))
    for idx, kw in enumerate(keywords[:3]):
        encoded_kw = urllib.parse.quote(kw)
        with cols[idx]:
            st.markdown(
                f"📄 **{kw}** : "
                f"[DBpia](https://www.dbpia.co.kr/search/topSearch?searchOption=all&query={encoded_kw}) | "
                f"[Google 학술검색](https://scholar.google.com/scholar?q={encoded_kw}) | "
                f"[네이버 백과](https://terms.naver.com/search.naver?query={encoded_kw})"
            )

with st.sidebar:
    st.title("🎛️ AI 컨트롤 대시보드")
    api_key = st.text_input("🔑 Gemini API Key 입력", type="password", help="Google AI Studio에서 발급받은 무료 키를 입력하세요.")
    
    st.subheader("📊 리소스 모니터링")
    daily_limit = 1500000
    usage_percent = min((st.session_state.total_tokens / daily_limit) * 100, 100.0)
    st.metric(label="누적 사용 토큰 (추정)", value=f"{st.session_state.total_tokens:,} 개", delta=f"일일 한도의 {usage_percent:.4f}%")
    st.progress(usage_percent / 100)
    
    st.subheader("🧠 AI 추론 제어")
    persona_mode = st.radio("작동 모드 선택", ["🤖 일반 AI 비서", "🏛️ 소크라테스 튜터 (정답 대신 힌트)", "⚖️ 비판적 토론자 (반론 제기)"])
    temperature = st.slider("창의성 조절 (Temperature)", min_value=0.0, max_value=1.0, value=0.4, step=0.1)
    
    st.subheader("🗂️ 문서 기반 답변 (Mini-RAG)")
    uploaded_doc = st.file_uploader("참조할 텍스트 파일(.txt) 업로드", type=["txt"])
    rag_content = ""
    if uploaded_doc is not None:
        rag_content = uploaded_doc.read().decode("utf-8")
        st.success("✅ 문서 장착 완료! 외부 지식을 차단하고 이 문서만 참고합니다.")

    st.subheader("📷 멀티모달 입력 (사진/음성)")
    uploaded_image = st.file_uploader("분석할 사진 첨부", type=["png", "jpg", "jpeg"])
    audio_input = st.audio_input("🎤 음성으로 질문 녹음하기")

    with st.expander("⚙️ 고급 설정 및 시연 도구"):
        lang_filter = st.checkbox("🇰🇷 외국어 섞임 방지", value=True)
        force_rlhf = st.checkbox("🎲 이번 질문에 A/B 답변 비교 강제 실행", value=False)
        show_sample_chart = st.checkbox("📈 한글 깨짐 방지 웹 차트 예시 보기", value=False)

    if st.button("🗑️ 대화 기록 초기화", use_container_width=True):
        st.session_state.messages = []
        st.session_state.ab_test_active = False
        st.rerun()

st.title("🤖 나만의 투명하고 안전한 AI 챗봇")
st.caption(f"현재 설정: **{persona_mode}** | 창의성: **{temperature}** | 3중 보안 가드레일 **작동 중🛡️**")

if show_sample_chart:
    with st.container(border=True):
        st.markdown("##### 📊 [시각화 모듈] 스트림릿 네이티브 한글 차트")
        chart_data = pd.DataFrame({
            "구분": ["응답 정확도", "보안성", "비용 효율성", "속도"],
            "일반 상용 챗봇": [75, 60, 50, 85],
            "내가 설계한 챗봇": [92, 98, 95, 88]
        }).set_index("구분")
        st.bar_chart(chart_data)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("thought"):
            with st.expander("🧠 AI의 논리적 사고 과정 (Chain of Thought) 펼쳐보기"):
                st.write(msg["thought"])
        st.markdown(msg["content"])
        if msg.get("keywords"):
            render_verification_links(msg["keywords"])

if st.session_state.ab_test_active:
    st.info("💡 **[인간 피드백 기반 강화학습(RLHF) 시뮬레이션]** 두 가지 스타일의 답변 중 하나를 선택해 주세요!")
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("#### 🅰️ 답변 A (논리·분석 중심)")
            st.markdown(st.session_state.ab_data["ans_a"])
            if st.button("👍 A 답변 채택하기", use_container_width=True):
                st.session_state.messages.append({"role": "assistant", "content": st.session_state.ab_data["ans_a"], "thought": st.session_state.ab_data["thought"], "keywords": st.session_state.ab_data["keywords"]})
                st.session_state.ab_test_active = False
                st.rerun()
    with col_b:
        with st.container(border=True):
            st.markdown("#### 🅱️ 답변 B (친절한 비유·예시 중심)")
            st.markdown(st.session_state.ab_data["ans_b"])
            if st.button("👍 B 답변 채택하기", use_container_width=True):
                st.session_state.messages.append({"role": "assistant", "content": st.session_state.ab_data["ans_b"], "thought": st.session_state.ab_data["thought"], "keywords": st.session_state.ab_data["keywords"]})
                st.session_state.ab_test_active = False
                st.rerun()

user_input = st.chat_input("질문을 입력하세요 (음성 녹음 시에도 간단한 엔터 입력 필요)...")

if user_input:
    if not api_key:
        st.warning("⚠️ 왼쪽 사이드바에 Gemini API Key를 먼저 입력해 주세요!")
        st.stop()

    is_safe, filtered_input = check_security_guardrail(user_input)
    
    with st.chat_message("user"):
        st.markdown(filtered_input)
        if uploaded_image:
            st.image(uploaded_image, width=250, caption="첨부된 이미지")
            
    st.session_state.messages.append({"role": "user", "content": filtered_input})

    if not is_safe:
        with st.chat_message("assistant"):
            st.error(filtered_input)
        st.stop()

    role_instruction = {
        "🤖 일반 AI 비서": "너는 명확하고 친절하게 설명하는 AI 비서야.",
        "🏛️ 소크라테스 튜터 (정답 대신 힌트)": "너는 소크라테스식 교육 튜터야. 절대 정답을 한 번에 알려주지 말고, 학생이 스스로 생각해서 답을 찾도록 단계별 힌트와 역질문을 던져줘.",
        "⚖️ 비판적 토론자 (반론 제기)": "너는 날카로운 비판적 토론자야. 사용자의 의견에 무조건 동조하지 말고, 논리적인 허점이나 반대 관점의 근거를 제시하며 건전한 토론을 유도해."
    }[persona_mode]

    system_prompt = f"""
    {role_instruction}
    [필수 출력 규칙]
    1. 중국어(한자), 일본어 등 외국어 문자를 한국어 문장 중간에 절대 섞어 쓰지 마라.
    2. 답변을 작성할 때 반드시 맨 처음에 `[추론과정]여기에 질문을 분석하고 답변을 구성한 논리적 단계를 작성[/추론과정]` 형식을 포함해라.
    3. 답변의 맨 마지막 줄에는 이 주제를 학술 데이터베이스에서 검증할 수 있는 핵심 명사 키워드 2~3개를 `[검증키워드: 단어1, 단어2]` 형식으로 남겨라.
    """

    if rag_content:
        system_prompt += f"""
        \n[문서 기반 답변(RAG) 절대 규칙]
        반드시 답변의 첫 문장을 "✅ **제공된 자료만을 참고하여 말씀드립니다.**"로 시작해라.
        아래 제공된 [참조 문서]의 내용만을 바탕으로 대답하고, 문서에 없는 내용은 추측하지 말고 문서에 없다고 답해라.
        [참조 문서]: {rag_content}
        """

    trigger_rlhf = force_rlhf or (random.random() < 0.20)
    if trigger_rlhf:
        system_prompt += """
        \n[A/B 테스트 특별 지시]
        추론과정 작성 후, 본문 답변을 두 가지 버전으로 작성해라.
        `[답변A]`에는 논리적이고 학술적인 요약 스타일의 답변을 작성하고,
        `[답변B]`에는 초보자도 이해하기 쉬운 비유와 예시 중심의 친절한 답변을 작성해라.
        형식: [추론과정]...[/추론과정] [답변A]... [답변B]... [검증키워드: ...]
        """

    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    }

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=system_prompt)

        contents = [filtered_input]
        if uploaded_image is not None:
            img = Image.open(uploaded_image)
            contents.append(img)
        if audio_input is not None:
            audio_bytes = audio_input.read()
            contents.append({"mime_type": "audio/wav", "data": audio_bytes})

        with st.spinner("🧠 문맥을 분석하고 안전 규정을 검토하며 추론 중입니다..."):
            response = model.generate_content(
                contents,
                generation_config=genai.types.GenerationConfig(temperature=temperature),
                safety_settings=safety_settings
            )
            raw_reply = response.text

        estimated_tokens = int((len(filtered_input) + len(raw_reply)) * 1.5)
        st.session_state.total_tokens += estimated_tokens
        cleaned_reply = apply_language_filter(filtered_input, raw_reply, lang_filter)
        thought, main_body, keywords = parse_ai_response(cleaned_reply)

        if trigger_rlhf and "[답변A]" in main_body and "[답변B]" in main_body:
            parts = main_body.split("[답변B]")
            ans_a = parts[0].replace("[답변A]", "").strip()
            ans_b = parts[1].strip()
            st.session_state.ab_data = {"ans_a": ans_a, "ans_b": ans_b, "thought": thought, "keywords": keywords}
            st.session_state.ab_test_active = True
            st.rerun()
        else:
            with st.chat_message("assistant"):
                if thought:
                    with st.expander("🧠 AI의 논리적 사고 과정 (Chain of Thought) 펼쳐보기"):
                        st.write(thought)
                st.markdown(main_body)
                if keywords:
                    render_verification_links(keywords)
            st.session_state.messages.append({"role": "assistant", "content": main_body, "thought": thought, "keywords": keywords})

    except Exception as e:
        st.error(f"⚠️ 답변 생성 중 오류가 발생했거나 구글 안전 필터에 의해 차단되었습니다. (상세 내용: {e})")
