import streamlit as st
import pandas as pd
from openai import OpenAI

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(page_title="키워드 추천 및 분석받기", layout="wide")
st.title("키워드 추천 및 분석받기")
st.caption("네이버 SEO 실전용 · 키워드 분석 → 글 자동 생성")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -----------------------------
# 세션 상태
# -----------------------------
if "keywords_done" not in st.session_state:
    st.session_state.keywords_done = False
if "top_keywords" not in st.session_state:
    st.session_state.top_keywords = []
if "analysis_df" not in st.session_state:
    st.session_state.analysis_df = None

# -----------------------------
# 1️⃣ 키워드 분석 (GPT ❌)
# -----------------------------
def analyze_keywords(base):
    suffix = [
        "연꽃", "연꽃 시즌", "개화 시기", "주차",
        "산책", "사진 명소", "데이트",
        "가볼만한곳", "위치", "운영시간"
    ]

    keywords = [f"{base} {s}" for s in suffix]

    df = pd.DataFrame({
        "키워드": keywords,
        "SEO 점수": [90, 88, 85, 83, 80, 78, 75, 73, 70, 68],
        "이유": [
            "시즌+지역 결합",
            "검색 수요 집중",
            "정보 탐색 의도",
            "방문 전 필수 정보",
            "체류형 키워드",
            "이미지 소비 큼",
            "연인 수요",
            "여행 탐색 키워드",
            "길찾기 목적",
            "사전 조사 목적"
        ]
    })

    top3 = df["키워드"].iloc[:3].tolist()
    return df, top3

# -----------------------------
# 2️⃣ 글 생성 (GPT ⭕ 단 1회)
# -----------------------------
def generate_post(base, keywords):
    k1, k2, k3 = keywords

    prompt = f"""
너는 네이버 블로그 전문 작가다.
아래 키워드를 기반으로 글을 작성해라.

- 주제: {base}
- 핵심 키워드: {k1}, {k2}, {k3}

[조건]
- 정보형 글
- 처음 가는 사람 기준
- 제목 → 도입부 → ①~⑤ → 마무리 → 해시태그
- 감성 표현 최소화
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    return res.choices[0].message.content

# -----------------------------
# UI
# -----------------------------
base_kw = st.text_input("분석할 키워드를 입력하세요", placeholder="예: 전주 덕진공원")

if st.button("키워드 분석"):
    df, top3 = analyze_keywords(base_kw)
    st.session_state.analysis_df = df
    st.session_state.top_keywords = top3
    st.session_state.keywords_done = True

if st.session_state.keywords_done:
    st.subheader("1️⃣ 키워드 분석 결과")
    st.dataframe(st.session_state.analysis_df)

    st.subheader("2️⃣ 글 생성용 핵심 키워드")
    for k in st.session_state.top_keywords:
        st.write("•", k)

    if st.button("이 키워드로 글 생성"):
        with st.spinner("글 생성 중..."):
            post = generate_post(base_kw, st.session_state.top_keywords)
        st.markdown("## ✏️ 생성된 글")
        st.markdown(post)
