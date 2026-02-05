import streamlit as st
import pandas as pd
from openai import OpenAI

# =====================
# 기본 설정
# =====================
st.set_page_config(page_title="키워드 추천 및 분석받기", layout="wide")
st.title("키워드 추천 및 분석받기")
st.caption("네이버 SEO 실전 · 키워드 분석 → 글 자동 생성")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# =====================
# 세션 상태 초기화
# =====================
for key in [
    "df_all", "df_top10", "selected_keywords",
    "run_generate", "post_text"
]:
    if key not in st.session_state:
        st.session_state[key] = None

# =====================
# 키워드 분석 로직 (Google Trends 실패e러 대비 실사용용)
# =====================
def analyze_keywords(base):
    suffixes = [
        "주차", "위치", "가는법", "운영시간", "산책",
        "사진 명소", "데이트", "가볼만한곳", "코스",
        "야경", "혼잡도", "계절", "날씨", "아이와",
        "혼자", "주말", "평일", "입장료", "지도",
        "주변 맛집", "근처 카페", "전망", "힐링",
        "자전거", "피크닉", "가족", "연인"
    ]

    rows = []
    for s in suffixes:
        kw = f"{base} {s}"
        seo = 0
        click = 0
        ai = 0

        if s in ["주차", "위치", "가는법", "운영시간"]:
            seo += 40
        if s in ["사진 명소", "데이트", "산책", "가볼만한곳"]:
            click += 35
        if len(kw) >= 10:
            ai += 25

        total = seo + click + ai
        rows.append({
            "키워드": kw,
            "SEO 점수": seo,
            "클릭 점수": click,
            "AI 검색 점수": ai,
            "총점": total
        })

    df = pd.DataFrame(rows).sort_values("총점", ascending=False)
    top10 = df.head(10)

    return df, top10

# =====================
# 입력 영역
# =====================
base_kw = st.text_input(
    "분석할 키워드를 입력하세요",
    placeholder="예: 전주 덕진공원"
)

if st.button("키워드 분석"):
    if base_kw.strip():
        df_all, df_top10 = analyze_keywords(base_kw.strip())
        st.session_state.df_all = df_all
        st.session_state.df_top10 = df_top10
        st.session_state.selected_keywords = []
        st.session_state.post_text = None

# =====================
# 1️⃣ 연관 키워드 50개 (작은 박스)
# =====================
if st.session_state.df_all is not None:
    st.subheader("1️⃣ 키워드 분석 결과 (연관 키워드 50개)")
    st.dataframe(
        st.session_state.df_all[["키워드", "총점"]].head(50),
        height=260,
        use_container_width=True
    )

# =====================
# 2️⃣ SEO·클릭·AI 최적 키워드 10개 (선택)
# =====================
if st.session_state.df_top10 is not None:
    st.subheader("2️⃣ SEO·클릭·AI 검색 최적 키워드 10개")
    st.caption("※ 글에 사용할 키워드를 직접 선택하세요")

    selected = []
    for _, row in st.session_state.df_top10.iterrows():
        if st.checkbox(
            f"{row['키워드']} (총점 {row['총점']})",
            key=row["키워드"]
        ):
            selected.append(row["키워드"])

    st.session_state.selected_keywords = selected

# =====================
# 3️⃣ 글 생성 버튼
# =====================
if st.session_state.selected_keywords:
    st.markdown("---")
    if st.button("선택한 키워드로 글 생성"):
        st.session_state.run_generate = True

# =====================
# GPT 글 생성 (버튼 클릭 시 1회)
# =====================
if st.session_state.run_generate:
    with st.spinner("네이버 블로그 글 생성 중..."):
        kws = st.session_state.selected_keywords[:3]

        prompt = f"""
너는 네이버 블로그 전문 SEO 작가다.

[대원칙]
- 정보가 감정보다 먼저다
- 처음 방문하는 사람 기준이다
- 구조는 절대 바꾸지 않는다

[주제]
{base_kw}

[핵심 키워드]
{", ".join(kws)}

[글 구조]
제목
도입부(4~5줄)

① 이 공간은 무엇인가요
② 언제·어떻게 이용하나요
③ 내부 구성·동선·이용 흐름
④ 접근 방법·주차·교통
⑤ 이런 사람에게 잘 맞아요

마무리(3문장)
해시태그(7~10개, 쉼표 구분)

[금지]
- 후기체
- 감성 과장
- 추상적 표현
"""

        res = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
            max_output_tokens=1200
        )

        st.session_state.post_text = res.output_text
        st.session_state.run_generate = False

# =====================
# 결과 출력
# =====================
if st.session_state.post_text:
    st.markdown("## ✏️ 생성된 네이버 블로그 글")
    st.markdown(st.session_state.post_text)
