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
    placeholder="예: 전주 여행, 전주 가볼만한곳"
)

# -----------------------------
# 유틸: 키워드 5열 그리드
# -----------------------------
def make_grid(items, cols=5):
    rows = math.ceil(len(items) / cols)
    grid = [items[i*cols:(i+1)*cols] for i in range(rows)]
    return pd.DataFrame(grid).fillna("")

# -----------------------------
# Google Trends 분석 함수
# -----------------------------
@st.cache_data(show_spinner=False)
def analyze(keyword):
    try:
        pytrends = TrendReq(hl='ko', tz=540)
        pytrends.build_payload([keyword], timeframe='today 12-m', geo='KR')

        related = pytrends.related_queries()

        if keyword not in related or related[keyword] is None:
            return [], []

        rq = related[keyword]
        frames = []

        if rq.get('top') is not None:
            frames.append(rq.get('top'))

        if rq.get('rising') is not None:
            frames.append(rq.get('rising'))

        if not frames:
            return [], []

        df = pd.concat(frames, ignore_index=True)
        df = df.drop_duplicates(subset='query').head(50)

        keywords = df['query'].tolist()
        top10 = keywords[:10]

        return keywords, top10

    except Exception:
        return [], []

# -----------------------------
# 버튼 클릭 시 실행
# -----------------------------
if st.button("키워드 추천 및 분석하기"):
    if not keyword:
        st.warning("키워드를 입력해주세요.")
    else:
        with st.spinner("Google Trends 기반 분석 중입니다..."):
            all_kw, top10 = analyze(keyword)

        if not all_kw:
            st.info("연관 키워드 데이터가 충분하지 않습니다. 조금 더 일반적인 키워드로 시도해보세요.")
        else:
            st.subheader("1️⃣ 연관 키워드 50개")
            st.dataframe(make_grid(all_kw))

            st.subheader("2️⃣ 상위 노출 가능 키워드 10개")
            st.dataframe(pd.DataFrame(top10, columns=["키워드"]))
