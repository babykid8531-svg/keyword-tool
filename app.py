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
# ❌ 제거할 장소/시설성 키워드 (의도 필터)
# -----------------------------
BLOCK_WORDS = [
    "주차", "위치", "운영", "운영시간", "입장", "입장료",
    "주소", "가는법", "전화", "시간", "요금",
    "주변", "근처", "지도", "예약", "문의"
]

def is_valid_keyword(keyword: str) -> bool:
    return not any(bw in keyword for bw in BLOCK_WORDS)

# -----------------------------
# Google Trends 분석 함수
# -----------------------------
@st.cache_data(show_spinner=False)
def analyze_with_trends(keyword: str):
    pytrends = TrendReq(hl="ko-KR", tz=540)

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

    # -----------------------------
    # 데이터 정리 + 의도 필터링
    # -----------------------------
    df = (
        df.rename(columns={"query": "키워드", "value": "지표"})
        .drop_duplicates(subset="키워드")
        .reset_index(drop=True)
    )

    # 🚨 핵심: 장소/시설 키워드 제거
    df = df[df["키워드"].apply(is_valid_keyword)]

    # -----------------------------
    # 결과 분리
    # -----------------------------
    kw50 = df.head(50)[["키워드", "구분", "지표"]]
    top10 = df.sort_values("지표", ascending=False).head(10)[["키워드", "구분", "지표"]]

    return kw50, top10

# -----------------------------
# UI
# -----------------------------
keyword = st.text_input(
    "분석할 키워드를 입력하세요",
    placeholder="예: 김치 / 전주 덕진공원 / 파리 여행"
)

if st.button("🚀 키워드 추천 및 분석하기"):
    if not keyword.strip():
        st.warning("키워드를 입력해주세요.")
    else:
        with st.spinner("Google Trends 실제 검색 데이터 분석 중..."):
            kw50, top10 = analyze_with_trends(keyword.strip())

        if kw50.empty:
            st.error("의미 있는 키워드가 부족합니다. 다른 키워드를 시도해보세요.")
        else:
            st.subheader("1️⃣ 연관 키워드 50개 (의도 필터 적용)")
            st.dataframe(
                kw50,
                use_container_width=True,
                height=260
            )

            st.subheader("2️⃣ SEO·클릭 최적 키워드 10개")
            st.caption("콘텐츠 제작에 바로 쓰기 좋은 키워드")
            st.dataframe(
                top10,
                use_container_width=True,
                height=260
            )
