import streamlit as st
import pandas as pd
from pytrends.request import TrendReq
from openai import OpenAI
import time

# =====================
# 기본 설정
# =====================
st.set_page_config(page_title="키워드 추천 및 분석받기", layout="wide")
st.title("키워드 추천 및 분석받기")
st.caption("Google Trends 기반 · 네이버 SEO 실전용")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# =====================
# Session State
# =====================
for k in ["df", "top10", "post"]:
    if k not in st.session_state:
        st.session_state[k] = None

# =====================
# Google Trends 연결
# =====================
@st.cache_data(ttl=60 * 60)
def get_trends_score(keyword):
    try:
        pytrends = TrendReq(hl="ko", tz=540)
        pytrends.build_payload(
            [keyword],
            timeframe="today 12-m",
            geo="KR"
        )
        data = pytrends.interest_over_time()
        if data.empty:
            return 0
        return int(data[keyword].mean())
    except:
        return 0

# =====================
# 키워드 분석
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

        # 1️⃣ Google Trends 점수
        trend = get_trends_score(kw)
        time.sleep(0.2)  # 차단 방지

        # 2️⃣ SEO 점수
        seo = 40 if s in ["주차", "위치", "가는법", "운영시간"] else 20

        # 3️⃣ 클릭 점수
        click = 30 if s in ["사진 명소", "데이트", "가볼만한곳", "후기"] else 10

        # 4️⃣ AI 검색 친화
        ai = 20 if len(kw) >= 10 else 10

        final_score = (
            trend * 0.4 +
            seo * 0.3 +
            click * 0.2 +
            ai * 0.1
        )

        rows.append({
            "키워드": kw,
            "Trends": trend,
            "SEO 점수": int(final_score)
        })

    df = pd.DataFrame(rows).sort_values("SEO 점수", ascending=False)
    top10 = df.head(10)["키워드"].tolist()
    return df, top10

# =====================
# UI
# =====================
base_kw = st.text_input("분석할 키워드를 입력하세요", placeholder="전주 덕진공원")

if st.button("키워드 분석"):
    with st.spinner("Google Trends 기반 키워드 분석 중..."):
        df, top10 = analyze_keywords(base_kw)
        st.session_state.df = df
        st.session_state.top10 = top10
        st.session_state.post = None

# 1️⃣ 키워드 50개
if st.session_state.df is not None:
    st.subheader("1️⃣ 키워드 분석 결과 (연관 키워드 50개)")
    st.dataframe(
        st.session_state.df[["키워드", "SEO 점수"]].head(50),
        height=180,
        use_container_width=True,
        hide_index=True
    )

# 2️⃣ 최적 키워드 10개
if st.session_state.top10:
    st.subheader("2️⃣ SEO · 클릭 · AI 최적 키워드 (추천 10개)")
    for i, kw in enumerate(st.session_state.top10, 1):
        st.write(f"{i}. {kw}")

    if st.button("이 키워드로 글 생성"):
        with st.spinner("네이버 블로그 글 생성 중..."):
            prompt = f"""
너는 네이버 블로그 SEO 전문 작가다.

주제: {base_kw}

핵심 키워드:
{chr(10).join("- " + k for k in st.session_state.top10[:3])}

조건:
- 정보 중심
- 처음 방문자 기준
- 과장 금지
- 제목 → 도입 → 소제목 5개 → 마무리
"""

            res = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )

            st.session_state.post = res.choices[0].message.content

# 3️⃣ 생성된 글
if st.session_state.post:
    st.markdown("## ✏️ 생성된 네이버 블로그 글")
    st.markdown(st.session_state.post)
