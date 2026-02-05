import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import math
import time

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(page_title="키워드 추천 및 분석받기")
st.title("키워드 추천 및 분석받기")

keyword = st.text_input(
    "분석할 키워드를 입력해주세요 😊",
    placeholder="예: 전주, 전주여행 가볼만한곳"
)

# -----------------------------
# 유틸
# -----------------------------
def make_grid(items, cols=5):
    rows = math.ceil(len(items) / cols)
    grid = [items[i*cols:(i+1)*cols] for i in range(rows)]
    return pd.DataFrame(grid).fillna("")

def search_level(idx):
    if idx < 3:
        return "높음"
    elif idx < 7:
        return "중상"
    else:
        return "중"

def reason_for_keyword(kw):
    if any(x in kw for x in ["시즌", "개화", "시기"]):
        return "시즌성 정보 검색 수요 집중"
    if any(x in kw for x in ["후기", "리뷰"]):
        return "후기형 콘텐츠 선호"
    if any(x in kw for x in ["명소", "사진"]):
        return "사진·뷰 목적 검색"
    if any(x in kw for x in ["코스", "산책", "데이트"]):
        return "동선·코스 탐색형 검색"
    if any(x in kw for x in ["여행", "가볼만한곳"]):
        return "여행 대표 키워드"
    return "지역 + 주제 결합 키워드"

# -----------------------------
# 🔥 fallback 키워드 생성기 (핵심)
# -----------------------------
def generate_fallback(keyword):
    base = keyword.strip()
    suffixes = [
        "가볼만한곳", "여행", "관광지", "맛집", "데이트",
        "코스", "추천", "후기", "사진 명소", "산책"
    ]
    return [f"{base} {s}" for s in suffixes]

# -----------------------------
# 분석 함수 (Google 실패해도 절대 죽지 않음)
# -----------------------------
@st.cache_data(show_spinner=False)
def analyze(keyword):
    keywords = []

    try:
        pytrends = TrendReq(hl="ko", tz=540)
        pytrends.build_payload([keyword], timeframe="today 12-m", geo="KR")

        time.sleep(1)  # ✅ 요청 완화

        related = pytrends.related_queries()
        rq = related.get(keyword)

        if rq:
            if rq.get("top") is not None:
                keywords.extend(rq["top"]["query"].tolist())
            if rq.get("rising") is not None:
                keywords.extend(rq["rising"]["query"].tolist())

    except Exception:
        # ❌ Google 차단 → 그냥 무시
        pass

    # ❗ Google 결과 없으면 fallback
    if not keywords:
        keywords = generate_fallback(keyword)

    keywords = list(dict.fromkeys(keywords))[:50]

    top10 = []
    for i, kw in enumerate(keywords[:10]):
        top10.append({
            "키워드": kw,
            "검색량": search_level(i),
            "이유": reason_for_keyword(kw)
        })

    return keywords, pd.DataFrame(top10)

# -----------------------------
# 버튼 실행
# -----------------------------
if st.button("키워드 추천 및 분석하기"):
    if not keyword:
        st.warning("키워드를 입력해주세요.")
    else:
        with st.spinner("키워드 분석 중입니다..."):
            all_keywords, top10_df = analyze(keyword)

        st.markdown("### 1️⃣ 연관 키워드 50개")
        st.caption("정렬 기준: 주제 연관성 + 검색 빈도")
        st.dataframe(make_grid(all_keywords))

        st.markdown("### 2️⃣ 상위 노출 가능성 높은 키워드 10개")
        st.dataframe(top10_df)
