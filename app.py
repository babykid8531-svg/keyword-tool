import streamlit as st
from pytrends.request import TrendReq
import pandas as pd

st.set_page_config(page_title="키워드 추천 및 분석받기")

st.title("키워드 추천 및 분석받기")

keyword = st.text_input(
    "분석할 키워드를 입력해주세요 😊",
    placeholder="예: 전주 덕진공원 연꽃"
)

@st.cache_data(show_spinner=False)
def analyze(keyword):
    pytrends = TrendReq(hl='ko', tz=540)
    pytrends.build_payload([keyword], timeframe='today 12-m', geo='KR')
    related = pytrends.related_queries()

    if keyword not in related or related[keyword] is None:
        return [], []

    rq = related[keyword]
    df = pd.concat(
        [rq.get('top', pd.DataFrame()),
         rq.get('rising', pd.DataFrame())],
        ignore_index=True
    )

    df = df.drop_duplicates(subset='query').head(50)
    keywords = df['query'].tolist()

    top10 = keywords[:10]
    return keywords, top10

if st.button("키워드 추천 및 분석받기"):
    if not keyword:
        st.warning("키워드를 입력해주세요.")
    else:
        with st.spinner("Google Trends 기반 분석 중입니다..."):
            all_kw, top10 = analyze(keyword)

        st.subheader("1️⃣ 연관 키워드 50개")
        st.dataframe(pd.DataFrame(all_kw, columns=["키워드"]))

        st.subheader("2️⃣ 상위 노출 가능 키워드 10개")
        st.dataframe(pd.DataFrame(top10, columns=["키워드"]))
