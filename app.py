import streamlit as st
import pandas as pd
import time
from pytrends.request import TrendReq
from pytrends.exceptions import TooManyRequestsError

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="키워드 추천 및 분석하기",
    layout="wide"
)

st.title("키워드 추천 및 분석하기")
st.caption("Google Trends 실제 검색 데이터 기반 · 개인용 SEO 키워드 도구")

# -----------------------------
# ❌ 장소/시설성 키워드 제거
# -----------------------------
BLOCK_WORDS = [
    "주차", "위치", "운영", "운영시간", "입장", "입장료",
    "주소", "가는법", "전화", "시간", "요금",
    "주변", "근처", "지도", "예약", "문의"
]

def is_valid_keyword(keyword: str) -> bool:
    return not any(bw in keyword for bw in BLOCK_WORDS)

# -----------------------------
# 🚨 고위험 키워드 사전 (Trends 차단 빈번)
# -----------------------------
HIGH_RISK_KEYWORDS = [
    "김치", "여행", "보험", "다이어트", "주식",
    "비트코인", "코로나", "환율", "부동산"
]

# -----------------------------
# 🔍 입력 키워드 자동 분해
# -----------------------------
def split_keyword(keyword: str):
    """
    예:
    김치 → ["김치", "김치 레시피", "김치 효능"]
    파리 여행 → ["파리 여행", "파리 여행 코스", "파리 여행 일정"]
    """
    base = keyword.strip()
    parts = [base]

    if len(base.split()) == 1:
        parts.extend([
            f"{base} 레시피",
            f"{base} 효능",
            f"{base} 방법"
        ])
    else:
        parts.extend([
            f"{base} 일정",
            f"{base} 코스",
            f"{base} 비용"
        ])

    return list(dict.fromkeys(parts))  # 중복 제거

# -----------------------------
# Google Trends 분석 함수
# -----------------------------
@st.cache_data(show_spinner=False, ttl=60 * 60)
def analyze_with_trends(keyword: str):
    pytrends = TrendReq(
        hl="ko-KR",
        tz=540,
        timeout=(10, 25),
        retries=2,
        backoff_factor=0.5
    )

    try:
        pytrends.build_payload(
            kw_list=[keyword],
            timeframe="today 12-m",
            geo="KR"
        )

        time.sleep(2)  # ⏱ 요청 간 딜레이
        related = pytrends.related_queries()

    except TooManyRequestsError:
        return "RATE_LIMIT", "RATE_LIMIT"
    except Exception:
        return pd.DataFrame(), pd.DataFrame()

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

    df = (
        pd.concat(frames, ignore_index=True)
        .rename(columns={"query": "키워드", "value": "지표"})
        .drop_duplicates(subset="키워드")
        .reset_index(drop=True)
    )

    # 장소/시설 키워드 제거
    df = df[df["키워드"].apply(is_valid_keyword)]

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
        st.stop()

    # 🚨 고위험 키워드 사전 경고
    if keyword.strip() in HIGH_RISK_KEYWORDS:
        st.warning(
            f"⚠ '{keyword}' 는 Google Trends 요청 제한이 잦은 고위험 키워드입니다.\n\n"
            "자동으로 세분화 키워드로 분석합니다."
        )

    # 🔍 키워드 자동 분해
    keywords_to_try = split_keyword(keyword)

    all_kw50 = []
    all_top10 = []

    with st.spinner("Google Trends 실제 검색 데이터 분석 중..."):
        for kw in keywords_to_try:
            kw50, top10 = analyze_with_trends(kw)

            if kw50 == "RATE_LIMIT":
                st.warning(
                    f"⚠ '{kw}' 분석 중 요청 제한 발생.\n"
                    "잠시 후 다시 시도하거나 더 구체적인 키워드를 사용하세요."
                )
                continue

            if not kw50.empty:
                all_kw50.append(kw50.assign(기준키워드=kw))
                all_top10.append(top10.assign(기준키워드=kw))

    if not all_kw50:
        st.error("의미 있는 키워드를 가져오지 못했습니다.")
        st.stop()

    final_kw50 = pd.concat(all_kw50).drop_duplicates(subset=["키워드"])
    final_top10 = (
        pd.concat(all_top10)
        .sort_values("지표", ascending=False)
        .drop_duplicates(subset=["키워드"])
        .head(10)
    )

    st.subheader("1️⃣ 연관 키워드 50개 (자동 분해 + 필터 적용)")
    st.dataframe(final_kw50, use_container_width=True, height=300)

    st.subheader("2️⃣ SEO·클릭 최적 키워드 10개")
    st.caption("실제 콘텐츠 제작에 바로 사용 가능")
    st.dataframe(final_top10, use_container_width=True, height=300)
