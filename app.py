import streamlit as st
import pandas as pd
from openai import OpenAI

# =====================
# 기본 설정
# =====================
st.set_page_config(page_title="키워드 추천 및 분석받기", layout="wide")
st.title("키워드 추천 및 분석받기")
st.caption("네이버 SEO 실전 · 키워드 분석 → 제목 → 글 생성")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# =====================
# session state
# =====================
for k in [
    "df_all", "df_top10",
    "selected_keywords",
    "titles", "post",
    "run_title", "run_post"
]:
    if k not in st.session_state:
        st.session_state[k] = None

# =====================
# 키워드 분석 (GPT ❌, 로컬)
# =====================
def analyze_keywords(base):
    suffixes = [
        "주차", "위치", "가는법", "운영시간",
        "산책", "사진 명소", "데이트", "가볼만한곳",
        "코스", "야경", "아이와", "혼자",
        "주말", "평일", "입장료", "지도",
        "주변 맛집", "근처 카페", "전망", "힐링"
    ]

    rows = []
    for s in suffixes:
        kw = f"{base} {s}"
        seo = 40 if s in ["주차", "위치", "가는법", "운영시간"] else 0
        click = 35 if s in ["사진 명소", "데이트", "산책", "가볼만한곳"] else 0
        ai = 25 if len(kw) >= 10 else 0

        rows.append({
            "키워드": kw,
            "총점": seo + click + ai
        })

    df = pd.DataFrame(rows).sort_values("총점", ascending=False)
    return df, df.head(10)

# =====================
# 입력
# =====================
base_kw = st.text_input("분석할 키워드를 입력하세요", "전주 덕진공원")

if st.button("키워드 분석"):
    df_all, df_top10 = analyze_keywords(base_kw)
    st.session_state.df_all = df_all
    st.session_state.df_top10 = df_top10
    st.session_state.selected_keywords = []
    st.session_state.titles = None
    st.session_state.post = None

# =====================
# 1️⃣ 키워드 50개
# =====================
if st.session_state.df_all is not None:
    st.subheader("1️⃣ 연관 키워드 50개")
    st.dataframe(
        st.session_state.df_all.head(50),
        height=260,
        use_container_width=True
    )

# =====================
# 2️⃣ 최적 키워드 10개 선택
# =====================
if st.session_state.df_top10 is not None:
    st.subheader("2️⃣ SEO·클릭·AI 최적 키워드 10개")

    selected = []
    for _, r in st.session_state.df_top10.iterrows():
        if st.checkbox(r["키워드"], key=r["키워드"]):
            selected.append(r["키워드"])

    st.session_state.selected_keywords = selected

# =====================
# 3️⃣ 네이버 제목 5개 생성
# =====================
if st.session_state.selected_keywords:
    if st.button("네이버 제목 5개 생성"):
        st.session_state.run_title = True

if st.session_state.run_title:
    prompt = f"""
너는 네이버 SEO 제목 전문가다.

주제: {base_kw}
핵심 키워드: {", ".join(st.session_state.selected_keywords[:3])}

조건:
- 정보형 제목
- 감성, 후기, 과장 금지
- 형식: 지역 + 장소명 + 정보 2~3개 + 총정리
- 클릭 유도는 정보 기반으로만

제목 5개만 줄바꿈으로 출력
"""

    res = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        max_output_tokens=300
    )

    st.session_state.titles = res.output_text
    st.session_state.run_title = False

if st.session_state.titles:
    st.markdown("### 📌 추천 제목 5개")
    st.text(st.session_state.titles)

# =====================
# 4️⃣ 네이버 글 생성
# =====================
if st.session_state.titles:
    if st.button("이 키워드로 네이버 글 생성"):
        st.session_state.run_post = True

if st.session_state.run_post:
    prompt = f"""
너는 네이버 블로그 전문 작가다.

[대원칙]
- 정보가 감정보다 먼저
- 처음 방문자 기준
- 구조 절대 고정

[주제]
{base_kw}

[핵심 키워드]
{", ".join(st.session_state.selected_keywords[:3])}

[글 구조]
제목
도입부(4~5줄)

① 이 공간은 무엇인가요
② 언제·어떻게 이용하나요
③ 내부 구성·동선·이용 흐름
④ 접근 방법·주차·교통
⑤ 이런 사람에게 잘 맞아요

마무리(3문장)
해시태그(7~10개, 쉼표)

후기체·감성체·과장 금지
"""

    res = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        max_output_tokens=1500
    )

    st.session_state.post = res.output_text
    st.session_state.run_post = False

if st.session_state.post:
    st.markdown("## ✏️ 생성된 네이버 블로그 글")
    st.markdown(st.session_state.post)
