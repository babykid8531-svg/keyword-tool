import streamlit as st
import pandas as pd
from pytrends.request import TrendReq

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="Google Trends 기반 키워드 분석",
    layout="wide"
)

st.title("키워드 추천 및 분석받기")
st.caption("Google Trends 실제 검색 데이터 기반 · 개인용 SEO 키워드 도구")

# -----------------------------
# Google Trends 분석 함수
# -----------------------------
@st.cache_data(show_spinner=False)
def analyze_with_trends(keyword: str):
    pytrends = TrendReq(hl="ko-KR", tz=540)

    # 최근 12개월, 한국 기준
    pytrends.build_payload(
        kw_list=[keyword],
        timeframe="today 12-m",
        geo="KR"
    )

    related = pytrends.related_queries()

    if keyword not in related or related[keyword] is None:
        return pd.DataFrame(), pd.DataFrame()

    top_df = related[keyword].get("top")
    rising_df = related[keyword].get("rising")

    frames = []
    if top_df is not None:
        frames.append(top_df.assign(구분="상위"))
    if rising_df is not None:
        frames.append(rising_df.assign(구분="급상승"))

    if not frames:
        return pd.DataFrame(), pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)

    # 정리
    df = (
        df.rename(columns={"query": "키워드", "value": "지표"})
        .drop_duplicates(subset="키워드")
        .reset_index(drop=True)
    )

    # 1️⃣ 연관 키워드 50개
    kw50 = df.head(50)[["키워드", "구분", "지표"]]

    # 2️⃣ SEO·클릭 최적 키워드 10개 (지표 높은 순)
    top10 = df.sort_values("지표", ascending=False).head(10)[["키워드", "구분", "지표"]]

    return kw50, top10


# -----------------------------
# UI
# -----------------------------
keyword = st.text_input(
    "분석할 키워드를 입력하세요",
    placeholder="예: 전주 덕진공원 / 김치 / 파리 여행"
)

if st.button("🚀 키워드 추천 및 분석하기"):
    if not keyword.strip():
        st.warning("키워드를 입력해주세요.")
    else:
        with st.spinner("Google Trends 실제 검색 데이터 분석 중..."):
            kw50, top10 = analyze_with_trends(keyword.strip())

        if kw50.empty:
            st.error("해당 키워드는 Google Trends에서 충분한 검색 데이터가 없습니다.")
        else:
            # -----------------------------
            # 1️⃣ 연관 키워드 50개
            # -----------------------------
            st.subheader("1️⃣ 연관 키워드 50개 (Google Trends 실제 검색)")
            st.dataframe(
                kw50,
                use_container_width=True,
                height=260
            )

            # -----------------------------
            # 2️⃣ SEO·클릭 최적 키워드 10개
            # -----------------------------
            st.subheader("2️⃣ SEO·클릭·AI 검색 최적 키워드 10개")
            st.caption("검색 지표 기준 상위 키워드")
            st.dataframe(
                top10,
                use_container_width=True,
                height=260
            )
