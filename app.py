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
    placeholder="예: 전주여행 가볼만한곳"
)

# -----------------------------
# 유틸: 키워드 5열 그리드
# -----------------------------
def make_grid(items, cols=5):
    rows = math.ceil(len(items) / cols)
    grid = [items[i*cols:(i+1)*cols] for i in range(rows)]
    return pd.DataFrame(grid).fillna("")

# -----------------------------
# fallback 키워드 생성기 (최후의 수단)
# -----------------------------
def generate_fallback(keyword):
    base = keyword.replace("  ", " ").strip()
    suffixes = [
        "가볼만한곳", "여행", "관광지", "맛집", "데이트",
        "코스", "추천", "후기", "사진", "명소"
    ]
    results = [f"{base} {s}" for s in suffixes]
    return results[:10]

# -----------------------------
# Google Trends 분석 함수 (관대 버전)
# -----------------------------
@st.cache_data(show_spinner=False)
def analyze(keyword):
    pytrends = TrendReq(hl='ko', tz=540)

    def fetch(k):
        try:
            pytrends.build_payload([k], timeframe='today 12-m', geo='KR')
            related = pytrends.related_queries()
            rq = related.get(k)

            if rq is None:
                return []

            frames = []
            if rq.get('top') is not None:
                frames.append(rq.get('top'))
            if rq.get('rising') is not None:
                frames.append(rq.get('rising'))

            if not frames:
                return []

            df = pd.concat(frames, ignore_index=True)
            return df['query'].drop_duplicates().tolist()
        except Exception:
            return []

    # 1️⃣ 원본 키워드
    keywords = fetch(keyword)

    # 2️⃣ 띄어쓰기 분해
    if not keywords and " " in keyword:
        for part in keyword.split():
            keywords.extend(fetch(part))

    # 3️⃣ 지역/여행 자동 보정
    if not keywords:
        for extra in ["여행", "가볼만한곳", "관광"]:
            keywords.extend(fetch(f"{keyword} {extra}"))

    # 4️⃣ 그래도 없으면 fallback 생성
    if not keywords:
        keywords = generate_fallback(keyword)

    keywords = list(dict.fromkeys(keywords))[:50]
    top10 = keywords[:10]

    return keywords, top10

# -----------------------------
# 버튼 클릭 시 실행
# -----------------------------
if st.button("키워드 추천 및 분석하기"):
    if not keyword:
        st.warning("키워드를 입력해주세요.")
    else:
        with st.spinner("키워드 분석 중입니다..."):
            all_kw, top10 = analyze(keyword)

        st.subheader("1️⃣ 연관 키워드 추천")
        st.dataframe(make_grid(all_kw))

        st.subheader("2️⃣ 상위 활용 추천 키워드")
        st.dataframe(pd.DataFrame(top10, columns=["키워드"]))
