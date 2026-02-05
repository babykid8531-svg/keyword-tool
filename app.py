import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import math

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(page_title="키워드 추천 및 분석받기")
st.title("키워드 추천 및 분석받기")

keyword = st.text_input(
    "분석할 키워드를 입력해주세요 😊",
    placeholder="예: 전주 덕진공원 연꽃"
)

# -----------------------------
# 유틸: 5열 키워드 표
# -----------------------------
def make_grid(items, cols=5):
    rows = math.ceil(len(items) / cols)
    grid = [items[i*cols:(i+1)*cols] for i in range(rows)]
    return pd.DataFrame(grid).fillna("")

# -----------------------------
# 검색량 레벨 판단 (상대값)
# -----------------------------
def search_level(score, max_score):
    ratio = score / max_score if max_score else 0
    if ratio >= 0.7:
        return "높음"
    elif ratio >= 0.4:
        return "중상"
    else:
        return "중"

# -----------------------------
# 이유 자동 생성
# -----------------------------
def reason_for_keyword(kw):
    if any(x in kw for x in ["시즌", "개화", "시기"]):
        return "시즌성 정보 검색 수요 집중"
    if any(x in kw for x in ["후기", "리뷰", "기록"]):
        return "후기형 콘텐츠 선호 증가"
    if any(x in kw for x in ["명소", "사진", "뷰"]):
        return "사진·뷰 목적 검색 의도"
    if any(x in kw for x in ["코스", "산책", "데이트"]):
        return "동선·코스 탐색형 검색"
    if any(x in kw for x in ["여행", "가볼만한곳"]):
        return "여행 시즌 대표 키워드"
    return "지역 + 주제 결합 롱테일 키워드"

# -----------------------------
# Google Trends 분석
# -----------------------------
@st.cache_data(show_spinner=False)
def analyze(keyword):
    pytrends = TrendReq(hl='ko', tz=540)
    pytrends.build_payload([keyword], timeframe='today 12-m', geo='KR')
    related = pytrends.related_queries()

    if keyword not in related or related[keyword] is None:
        return [], pd.DataFrame()

    rq = related[keyword]
    frames = []

    if rq.get("top") is not None:
        frames.append(rq["top"])
    if rq.get("rising") is not None:
        frames.append(rq["rising"])

    if not frames:
        return [], pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df = df.drop_duplicates(subset="query")
    df = df.rename(columns={"query": "키워드", "value": "점수"})
    df = df.head(50)

    max_score = df["점수"].max()

    df["검색량"] = df["점수"].apply(lambda x: search_level(x, max_score))
    df["이유"] = df["키워드"].apply(reason_for_keyword)

    # 상위 노출용 10개 (구체 키워드 위주)
    top10 = df[df["키워드"].str.len() >= 6].head(10)
    top10 = top10[["키워드", "검색량", "이유"]]

    return df["키워드"].tolist(), top10

# -----------------------------
# 버튼 실행
# -----------------------------
if st.button("키워드 추천 및 분석하기"):
    if not keyword:
        st.warning("키워드를 입력해주세요.")
    else:
        with st.spinner("키워드 분석 중입니다..."):
            all_keywords, top10_df = analyze(keyword)

        if not all_keywords:
            st.info("연관 키워드 데이터가 충분하지 않습니다.")
        else:
            # 1️⃣ 연관 키워드 50개
            st.markdown("### 1️⃣ 연관 키워드 50개 생성")
            st.caption("정렬 기준: 주제 연관성 + 검색 빈도")
            st.dataframe(make_grid(all_keywords))

            # 2️⃣ 상위 노출 가능 키워드 10개
            st.markdown("### 2️⃣ 상위 노출 가능성 높은 키워드 10개")
            st.dataframe(top10_df)

            st.caption("📌 검색량 기준: Google Trends 상대 지수 (참고용)")
