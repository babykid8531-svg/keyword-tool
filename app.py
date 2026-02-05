import streamlit as st
import pandas as pd
from openai import OpenAI

# =============================
# 기본 설정
# =============================
st.set_page_config(page_title="키워드 추천 및 분석받기", layout="wide")
st.title("키워드 추천 및 분석받기")
st.caption("네이버 SEO 실전용 · 키워드 분석 → 글 자동 생성")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# =============================
# 세션 상태
# =============================
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "analysis_df" not in st.session_state:
    st.session_state.analysis_df = None
if "seo_top3" not in st.session_state:
    st.session_state.seo_top3 = None
if "post_text" not in st.session_state:
    st.session_state.post_text = None

# =============================
# 1️⃣ 키워드 분석 (GPT ❌)
# =============================
def analyze_keywords(base):
    suffixes = [
        "연꽃", "연꽃 시즌", "개화 시기", "주차",
        "산책", "사진 명소", "데이트",
        "가볼만한곳", "위치", "운영시간",
        "야경", "코스", "혼자 산책",
        "아이와", "주말", "평일",
        "입장료", "지도", "가는법",
        "추천", "후기", "풍경",
        "힐링", "근처 카페", "주변 맛집",
        "봄", "여름", "가을",
        "연인", "가족", "노을",
        "자전거", "피크닉", "호수",
        "전망", "촬영", "사진 스팟",
        "시간대", "혼잡도", "비 오는 날",
        "날씨", "벚꽃", "단풍",
        "계절별", "주차장 위치"
    ]

    keywords = [f"{base} {s}" for s in suffixes[:50]]

    rows = []
    for kw in keywords:
        score = 0

        # 정보/방문 의도
        if any(x in kw for x in ["주차", "위치", "운영시간", "가는법"]):
            score += 40
        if any(x in kw for x in ["사진", "데이트", "산책", "코스"]):
            score += 30
        if len(kw) >= 10:
            score += 20  # 롱테일
        if any(x in kw for x in ["후기", "추천"]):
            score -= 10  # 경쟁 심함

        rows.append({
            "키워드": kw,
            "SEO 점수": score
        })

    df = pd.DataFrame(rows).sort_values("SEO 점수", ascending=False)

    # ✅ SEO 기준으로 상위 3개 (1~3위 아님)
    top3 = df.head(3)["키워드"].tolist()
    return df, top3

# =============================
# 2️⃣ 글 생성 (GPT ⭕ 1회)
# =============================
@st.cache_data(show_spinner=False)
def generate_post(base, top3):
    k1, k2, k3 = top3

    prompt = f"""
너는 네이버 블로그 전문 작가다.

주제: {base}
핵심 키워드:
- {k1}
- {k2}
- {k3}

조건:
- 정보형 글
- 처음 가는 사람 기준
- 제목 → 도입부 → ①~⑤ → 마무리 → 해시태그
- 감성 표현 최소화
- SEO 최적화
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    return res.choices[0].message.content

# =============================
# UI
# =============================
base_kw = st.text_input("분석할 키워드를 입력해주세요", placeholder="예: 전주 덕진공원")

if st.button("키워드 분석"):
    df, top3 = analyze_keywords(base_kw)
    st.session_state.analysis_df = df
    st.session_state.seo_top3 = top3
    st.session_state.analysis_done = True
    st.session_state.post_text = None

if st.session_state.analysis_done:
    st.subheader("1️⃣ 키워드 분석 결과 (연관 키워드 50개)")
    st.dataframe(st.session_state.analysis_df, use_container_width=True)

    st.subheader("2️⃣ SEO·클릭·AI 검색 최적 키워드 3개")
    for i, kw in enumerate(st.session_state.seo_top3, 1):
        st.write(f"{i}. {kw}")

    if st.button("이 키워드로 글 생성"):
        with st.spinner("네이버 블로그 글 생성 중..."):
            st.session_state.post_text = generate_post(
                base_kw,
                st.session_state.seo_top3
            )

if st.session_state.post_text:
    st.markdown("## ✏️ 생성된 네이버 블로그 글")
    st.markdown(st.session_state.post_text)
