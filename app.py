import streamlit as st
from openai import OpenAI
import json

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="SEO 키워드 분석 & 네이버 글 자동 생성",
    layout="wide"
)

st.title("키워드 추천 및 분석받기")
st.caption("네이버 SEO 실전용 · 키워드 → 글 자동 완성")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -----------------------------
# 지침서 (고정)
# -----------------------------
GUIDELINE = """
너는 네이버 블로그 전문 작가이자 SEO 컨설턴트다.

[대원칙]
- 구조는 항상 동일
- 정보가 감정보다 먼저
- 독자는 처음 방문하는 사람

[구조]
제목
도입부

① 이곳은 무엇인가요
② 언제·어떻게 이용하나요
③ 내부 구성·동선
④ 주차·교통·접근성
⑤ 이런 사람에게 맞아요

마무리
해시태그

[제목]
지역 + 대상 + 정보 키워드 2~3개 + 총정리
감성·후기 금지
"""

# -----------------------------
# GPT 단일 호출 (핵심)
# -----------------------------
def generate_all(base_keyword):
    prompt = f"""
'{base_keyword}'를 기준으로
네이버 블로그 실사용 기준으로 아래를 모두 생성해라.

1️⃣ 연관 키워드 50개
- 실제 검색자가 입력할 법한 형태
- 지역 + 구체적 의도

2️⃣ 상위 노출 가능 키워드 10개
- 키워드
- 검색량 (높음/중상/중)
- 이유

3️⃣ 위 10개 중 SEO·AI 검색·클릭률 기준 TOP3 자동 선정
- 메인 1
- 정보형 1
- 롱테일 1

4️⃣ 선정된 TOP3으로 네이버 블로그 글 전체 작성
- 지침서 구조 100% 준수
- 정보형 문체
- HTML 금지
- 해시태그는 쉼표로 구분

출력은 반드시 JSON 형식:

{{
 "keywords50": [...],
 "top10": [
   {{"keyword":"","volume":"","reason":""}}
 ],
 "top3": ["","",""],
 "post": "완성된 글 전체"
}}
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": GUIDELINE},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )

    return json.loads(res.choices[0].message.content)

# -----------------------------
# UI
# -----------------------------
base_kw = st.text_input(
    "분석할 키워드를 입력하세요",
    placeholder="예: 전주 덕진공원"
)

if st.button("키워드 분석 + 글 생성"):
    if not base_kw.strip():
        st.warning("키워드를 입력하세요.")
    else:
        with st.spinner("SEO 분석 및 글 생성 중..."):
            data = generate_all(base_kw.strip())

        st.markdown("### 1️⃣ 연관 키워드 50개")
        cols = 5
        rows = [data["keywords50"][i:i+cols] for i in range(0, 50, cols)]
        st.dataframe(rows)

        st.markdown("### 2️⃣ 상위 노출 가능 키워드 10개")
        st.dataframe(data["top10"])

        st.markdown("### 3️⃣ 자동 선정 TOP3 키워드")
        st.write(data["top3"])

        st.markdown("## ✏️ 네이버 블로그 완성 글")
        st.markdown(data["post"])
