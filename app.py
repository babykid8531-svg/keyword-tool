import streamlit as st
import pandas as pd
from pytrends.request import TrendReq
from openai import OpenAI

# ---------------------------------
# 기본 설정
# ---------------------------------
st.set_page_config(page_title="SEO 키워드 분석 + 네이버 글 자동 생성", layout="wide")
st.title("키워드 추천 및 분석받기")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ---------------------------------
# Google Trends 연결
# ---------------------------------
pytrends = TrendReq(hl="ko-KR", tz=540)

# ---------------------------------
# 세션 상태
# ---------------------------------
for k in ["done", "kw50", "top10", "top3", "base"]:
    if k not in st.session_state:
        st.session_state[k] = None

# ---------------------------------
# 1️⃣ Google Trends 키워드 수집
# ---------------------------------
def fetch_keywords_from_trends(base_keyword):
    pytrends.build_payload(
        kw_list=[base_keyword],
        timeframe="today 12-m",
        geo="KR"
    )

    related = pytrends.related_queries().get(base_keyword, {})
    top = related.get("top", pd.DataFrame())
    rising = related.get("rising", pd.DataFrame())

    combined = pd.concat([top, rising], ignore_index=True)
    combined = combined.drop_duplicates(subset=["query"])

    keywords = combined["query"].tolist()
    return keywords[:50], combined


# ---------------------------------
# 2️⃣ 상위 10개 + 핵심 3개 자동 선정
# ---------------------------------
def analyze_keywords(df, base_keyword):
    df = df.copy()

    def score(row):
        s = 0
        if base_keyword in row["query"]:
            s += 3
        if any(x in row["query"] for x in ["시즌", "주차", "시간", "요금"]):
            s += 2
        if any(x in row["query"] for x in ["사진", "산책", "코스", "데이트"]):
            s += 1
        return s

    df["score"] = df.apply(score, axis=1)
    top10 = df.sort_values("score", ascending=False).head(10)

    main = top10.iloc[0]["query"]
    info = next((k for k in top10["query"] if "시즌" in k or "주차" in k), main)
    long = next((k for k in top10["query"] if "사진" in k or "산책" in k), main)

    return top10[["query", "score"]], [main, info, long]


# ---------------------------------
# 3️⃣ GPT로 네이버 블로그 글 생성
# ---------------------------------
def generate_blog_post(base, top3):
    kw1, kw2, kw3 = top3

    prompt = f"""
너는 네이버 블로그 전문 작가다.
아래 지침을 절대 어기지 말고 글을 작성해라.

[주제] {base}
[메인 키워드] {kw1}
[정보형 키워드] {kw2}
[롱테일 키워드] {kw3}

조건:
- 정보 중심
- 처음 가는 사람 기준
- 고정 구조 유지
- 제목, 도입부, ①~⑤, 마무리, 해시태그 포함
- HTML 사용 금지
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
    )

    return res.choices[0].message.content.strip()


# ---------------------------------
# UI
# ---------------------------------
base = st.text_input("분석할 키워드를 입력하세요", placeholder="예: 전주 덕진공원")

if st.button("키워드 분석"):
    kw50, raw_df = fetch_keywords_from_trends(base)
    top10, top3 = analyze_keywords(raw_df, base)

    st.session_state.done = True
    st.session_state.kw50 = kw50
    st.session_state.top10 = top10
    st.session_state.top3 = top3
    st.session_state.base = base

if st.session_state.done:
    st.subheader("1️⃣ 연관 키워드 50개 (Google Trends)")
    st.dataframe(pd.DataFrame(st.session_state.kw50, columns=["키워드"]))

    st.subheader("2️⃣ 상위 노출 가능 키워드 10개")
    st.dataframe(st.session_state.top10)

    st.subheader("3️⃣ 자동 선정 핵심 키워드 3개")
    st.write(st.session_state.top3)

    if st.button("네이버 블로그 글 자동 생성"):
        post = generate_blog_post(
            st.session_state.base,
            st.session_state.top3
        )
        st.markdown("---")
        st.markdown(post)
