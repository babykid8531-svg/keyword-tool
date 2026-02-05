import streamlit as st
import pandas as pd
from openai import OpenAI
import re

# ===============================
# 기본 설정
# ===============================
st.set_page_config(page_title="키워드 추천 및 분석받기", layout="wide")
st.title("키워드 추천 및 분석받기")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ===============================
# 입력
# ===============================
keyword = st.text_input(
    "분석할 키워드를 입력해주세요 😊",
    placeholder="예: 전주덕진공원 / 이천피에뜰 / 부산 송도 케이블카"
)

# ===============================
# 키워드 강제 분해
# ===============================
def split_keyword(keyword):
    keyword = keyword.strip()
    parts = re.findall(r"[가-힣]+", keyword)

    expanded = set()
    expanded.add(keyword)

    for p in parts:
        if len(p) >= 2:
            expanded.add(p)

    if len(parts) >= 2:
        expanded.add(" ".join(parts))

    return list(expanded)

# ===============================
# ChatGPT 기반 키워드 생성
# ===============================
def generate_keywords_with_gpt(base_keywords):
    prompt = f"""
아래 키워드를 기반으로
네이버 검색 의도 + SEO 관점에서
연관 키워드 30개를 생성하라.

조건:
- 검색어 형태 그대로
- 지역 + 장소 + 정보형 조합
- 후기, 힐링, 강추 같은 감성 단어 금지
- 실제 블로그 제목에 쓸 수 있는 키워드

기본 키워드:
{", ".join(base_keywords)}

출력은 키워드만 한 줄에 하나씩.
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )

    keywords = response.choices[0].message.content.split("\n")
    keywords = [k.strip("- ").strip() for k in keywords if k.strip()]
    return keywords[:30]

# ===============================
# 글 자동 생성
# ===============================
def generate_article(main_keyword, sub_keywords):
    prompt = f"""
너는 네이버 SEO 정보형 블로그 글 작성 전문가다.

아래 지침서를 반드시 지켜 글 전체를 완성하라.

[메인 키워드]
{main_keyword}

[서브 키워드]
{", ".join(sub_keywords)}

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

조건:
- 감성 표현 금지
- 후기, 강추, 힐링 금지
- 처음 방문자 기준
- 정보 우선
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content

# ===============================
# 실행
# ===============================
if st.button("키워드 추천 및 분석하기"):
    if not keyword:
        st.warning("키워드를 입력해주세요.")
    else:
        with st.spinner("키워드 분석 중입니다..."):
            base_keywords = split_keyword(keyword)
            all_keywords = generate_keywords_with_gpt(base_keywords)

        st.subheader("1️⃣ 자동 생성된 연관 키워드")
        selected = st.multiselect(
            "최대 3개 선택하세요",
            all_keywords,
            max_selections=3
        )

        if st.button("선택한 키워드로 글 완성하기"):
            if not selected:
                st.warning("키워드를 선택해주세요.")
            else:
                with st.spinner("글을 생성 중입니다..."):
                    article = generate_article(selected[0], selected[1:])

                st.subheader("✍️ 자동 생성된 글")
                st.write(article)
