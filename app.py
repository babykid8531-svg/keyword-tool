import streamlit as st
import pandas as pd
from openai import OpenAI

st.set_page_config(page_title="키워드 추천 및 분석받기", layout="wide")
st.title("키워드 추천 및 분석받기")
st.caption("네이버 SEO 실전 · 키워드 분석 → 글 생성")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# =====================
# session state
# =====================
for k in ["df", "top3", "post"]:
    if k not in st.session_state:
        st.session_state[k] = None

# =====================
# 키워드 분석 (GPT ❌)
# =====================
def analyze_keywords(base):
    suffixes = [
        "주차", "위치", "가는법", "운영시간", "산책",
        "사진 명소", "데이트", "가볼만한곳", "후기",
        "코스", "야경", "혼잡도", "계절", "날씨",
        "주변 맛집", "근처 카페", "아이와", "혼자",
        "주말", "평일", "입장료", "지도"
    ]

    rows = []
    for s in suffixes:
        kw = f"{base} {s}"
        score = 0
        if s in ["주차", "위치", "가는법", "운영시간"]:
            score += 40
        if s in ["사진 명소", "데이트", "산책"]:
            score += 30
        if len(kw) >= 10:
            score += 20
        rows.append({"키워드": kw, "SEO 점수": score})

    df = pd.DataFrame(rows).sort_values("SEO 점수", ascending=False)
    top3 = df.head(3)["키워드"].tolist()
    return df, top3

# =====================
# UI
# =====================
base_kw = st.text_input("분석할 키워드를 입력하세요", placeholder="전주 덕진공원")

if st.button("키워드 분석"):
    df, top3 = analyze_keywords(base_kw)
    st.session_state.df = df
    st.session_state.top3 = top3
    st.session_state.post = None

# 1️⃣ 키워드 분석 결과
if st.session_state.df is not None:
    st.subheader("1️⃣ 키워드 분석 결과 (연관 키워드)")
    st.dataframe(
        st.session_state.df,
        use_container_width=True,
        height=260
    )

# 2️⃣ SEO 키워드
if st.session_state.top3:
    st.subheader("2️⃣ SEO·클릭 최적 키워드")
    for i, kw in enumerate(st.session_state.top3, 1):
        st.write(f"{i}. {kw}")

    if st.button("이 키워드로 글 생성"):
        with st.spinner("글 생성 중..."):
            prompt = f"""
네이버 블로그용 정보글 작성.

주제: {base_kw}
핵심 키워드:
- {st.session_state.top3[0]}
- {st.session_state.top3[1]}
- {st.session_state.top3[2]}

조건:
- 정보 중심
- 처음 방문자 기준
- 제목 → 도입 → 소제목 5개 → 마무리
- 과장 금지
"""

            res = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )

            st.session_state.post = res.choices[0].message.content

# 3️⃣ 생성된 글
if st.session_state.post:
    st.markdown("## ✏️ 생성된 글")
    st.markdown(st.session_state.post)
