import streamlit as st
import pandas as pd
import time
import json
from pytrends.request import TrendReq
from openai import OpenAI

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="키워드 추천 및 네이버 글 자동 생성",
    layout="wide"
)

st.title("키워드 추천 및 분석받기")
st.caption("Google Trends 기반 분석 + GPT 백업 + 네이버 블로그 글 자동 생성")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -----------------------------
# 지침서 (고정)
# -----------------------------
GUIDELINE = """
너는 네이버 블로그 전문 작가이자 SEO 컨설턴트다.

[절대 원칙]
- 구조는 항상 동일하게 유지한다.
- 정보가 감정보다 먼저다.
- 독자는 처음 방문하는 사람이다.

[고정 구조]

제목
도입부(인사 + 요약)

① 이 공간/장소/서비스는 무엇인가요
② 언제·어떻게 이용하나요 (시간·요일·조건)
③ 내부 구성·이용 흐름·동선은 어떻게 되나요
④ 접근 방법·주차·교통은 어떤가요
⑤ 이런 사람에게 잘 맞아요

마무리
해시태그

[제목 규칙]
- 지역 + 대상명 + 핵심 정보 2~3개 + 총정리
- 감성, 후기, 추상 표현 금지

[도입부]
- 4~5줄 고정
- 감정·후기 표현 금지

[본문]
- 설명 → 배경 → 현재
- 숫자·연도·사실 우선
- 각 파트 마지막에 실전 팁 1줄

[마무리]
- 3문장
- 질문형 1문장까지 허용

[해시태그]
- 7~10개
- 정보형 키워드만 사용
"""

# -----------------------------
# 1. Google Trends 시도
# -----------------------------
@st.cache_data(ttl=60 * 60)
def fetch_from_trends(base_keyword):
    time.sleep(2)  # 중요: 차단 방지
    pytrends = TrendReq(hl="ko-KR", tz=540)
    pytrends.build_payload(
        kw_list=[base_keyword],
        timeframe="today 12-m",
        geo="KR"
    )

    related = pytrends.related_queries()
    if base_keyword not in related or related[base_keyword] is None:
        return []

    top = related[base_keyword].get("top", pd.DataFrame())
    rising = related[base_keyword].get("rising", pd.DataFrame())

    df = pd.concat([top, rising], ignore_index=True)
    if "query" not in df:
        return []

    return df["query"].drop_duplicates().tolist()

# -----------------------------
# 2. GPT 백업 키워드 생성
# -----------------------------
def fallback_keywords_with_gpt(base_keyword):
    prompt = f"""
'{base_keyword}'를 네이버 검색창에 실제 사람이 입력할 법한
연관 키워드 50개를 만들어라.

조건:
- 지역명 + 구체적 의도
- 정보형 위주
- 여행, 후기 같은 추상 단어 남발 금지

JSON 배열만 반환해라.
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    return json.loads(res.choices[0].message.content)

# -----------------------------
# 3. 키워드 분석 + TOP3 선정
# -----------------------------
def analyze_keywords(base_keyword):
    try:
        keywords = fetch_from_trends(base_keyword)
    except:
        keywords = []

    if not keywords:
        keywords = fallback_keywords_with_gpt(base_keyword)

    keywords = keywords[:50]

    prompt = f"""
다음 키워드 목록을 보고,
네이버 블로그 상위 노출 가능성이 높은 키워드 10개를 뽑아라.

기준:
- 검색 의도 명확
- 경쟁도 과도하지 않음
- 정보형 위주

그중에서
1) 메인 키워드
2) 정보형 키워드
3) 롱테일 키워드
각 1개씩 총 3개를 자동 선정해라.

출력 JSON 형식:
{{
 "top10": [
   {{"keyword":"", "volume":"높음/중상/중", "reason":""}}
 ],
 "top3": ["", "", ""]
}}
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "SEO 키워드 분석가다. JSON만 출력해라."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
    )

    data = json.loads(res.choices[0].message.content)
    return keywords, pd.DataFrame(data["top10"]), data["top3"]

# -----------------------------
# 4. 네이버 블로그 글 생성
# -----------------------------
def generate_post(base_keyword, top3):
    k1, k2, k3 = top3

    prompt = f"""
기본 키워드: {base_keyword}
메인 키워드: {k1}
정보형 키워드: {k2}
롱테일 키워드: {k3}

- 네이버 블로그용
- 지침서 구조 100% 준수
- 담백한 설명형 문체
- HTML 금지
- 해시태그는 쉼표로만 구분
"""

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": GUIDELINE},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6,
    )

    return res.choices[0].message.content.strip()

# -----------------------------
# UI
# -----------------------------
base_kw = st.text_input(
    "분석할 키워드를 입력하세요",
    placeholder="예: 전주 덕진공원"
)

if st.button("키워드 분석"):
    if not base_kw.strip():
        st.warning("키워드를 입력하세요.")
    else:
        with st.spinner("키워드 분석 중..."):
            kw50, top10_df, top3 = analyze_keywords(base_kw.strip())

        st.markdown("### 1️⃣ 연관 키워드 50개")
        cols = 5
        rows = [kw50[i:i+cols] for i in range(0, len(kw50), cols)]
        st.dataframe(pd.DataFrame(rows))

        st.markdown("### 2️⃣ 상위 노출 가능 키워드 10개")
        st.dataframe(top10_df)

        st.markdown("### 3️⃣ 자동 선정 핵심 키워드 3개")
        st.write(f"- 메인: **{top3[0]}**")
        st.write(f"- 정보형: **{top3[1]}**")
        st.write(f"- 롱테일: **{top3[2]}**")

        if st.button("네이버 블로그 글 자동 생성"):
            with st.spinner("글 작성 중..."):
                post = generate_post(base_kw.strip(), top3)

            st.markdown("## ✏️ 네이버 블로그 자동 완성 글")
            st.markdown(post)
