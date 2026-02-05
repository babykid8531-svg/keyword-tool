import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import math
import time

# =========================
# 기본 설정
# =========================
st.set_page_config(
    page_title="키워드 추천 및 분석받기",
    layout="wide"
)

st.title("키워드 추천 및 분석받기")
st.caption("분석할 키워드를 입력해주세요 😊")

# =========================
# session_state 초기화
# =========================
for key in [
    "analyzed",
    "all_keywords",
    "top10_df",
    "final_candidates",
    "selected_keywords"
]:
    if key not in st.session_state:
        st.session_state[key] = [] if "keywords" in key or "candidates" in key else False

# =========================
# 키워드 입력
# =========================
keyword = st.text_input(
    "분석 키워드",
    placeholder="예: 전주, 전주 여행, 전주 덕진공원"
)

# =========================
# Google Trends 분석
# =========================
@st.cache_data(show_spinner=False)
def analyze(keyword):
    pytrends = TrendReq(hl="ko", tz=540)
    pytrends.build_payload([keyword], timeframe="today 12-m", geo="KR")

    related = pytrends.related_queries()
    if keyword not in related or related[keyword] is None:
        return [], pd.DataFrame()

    rq = related[keyword]
    frames = []

    if rq.get("top") is not None:
        frames.append(rq["top"])
    if rq.get("rising") is not None:
        frames.append(rq["rising"])

    if not frames:
        return [], pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df = df.drop_duplicates(subset="query")

    df["검색량"] = "중"
    df.loc[:2, "검색량"] = "높음"
    df.loc[3:5, "검색량"] = "중상"

    df["이유"] = "지역 + 정보형 검색 의도"

    return df["query"].tolist(), df

# =========================
# SEO + 상위노출 자동 필터
# =========================
def auto_select_keywords(df):
    banned = ["후기", "힐링", "감성", "추천", "강추", "좋은"]
    result = []

    for kw in df["query"]:
        if any(b in kw for b in banned):
            continue
        if len(kw) < 3:
            continue
        if " " not in kw:
            continue
        result.append(kw)

    return result[:10]

# =========================
# 분석 실행
# =========================
if st.button("키워드 추천 및 분석하기"):
    if not keyword:
        st.warning("키워드를 입력해주세요.")
        st.stop()

    with st.spinner("Google Trends 기반 분석 중입니다..."):
        time.sleep(1)
        all_kw, df = analyze(keyword)

    if not all_kw:
        st.info("연관 키워드 데이터가 충분하지 않습니다.")
        st.stop()

    st.session_state.analyzed = True
    st.session_state.all_keywords = all_kw
    st.session_state.top10_df = df.head(10)
    st.session_state.final_candidates = auto_select_keywords(df)
    st.session_state.selected_keywords = []

# =========================
# 결과 출력
# =========================
if st.session_state.analyzed:

    # 1️⃣ 연관 키워드 50개 (표시만)
    st.markdown("## 1️⃣ 연관 키워드 50개")
    cols = 5
    rows = math.ceil(len(st.session_state.all_keywords) / cols)
    grid = [
        st.session_state.all_keywords[i * cols:(i + 1) * cols]
        for i in range(rows)
    ]
    st.dataframe(pd.DataFrame(grid).fillna(""))

    # 2️⃣ 상위 노출 가능 키워드 10개 (표시만)
    st.markdown("## 2️⃣ 상위 노출 가능성 높은 키워드 10개")
    st.dataframe(
        st.session_state.top10_df[["query", "검색량", "이유"]]
        .rename(columns={"query": "키워드"}),
        use_container_width=True
    )

    # 3️⃣ 자동 선별 키워드 선택
    st.markdown("## 3️⃣ 글 생성용 키워드 선택 (최대 3개)")
    st.caption("SEO · 상위노출 · AI 검색 친화 기준으로 자동 선별됨")

    for kw in st.session_state.final_candidates:
        checked = st.checkbox(
            kw,
            key=f"select_{kw}",
            value=kw in st.session_state.selected_keywords
        )
        if checked and kw not in st.session_state.selected_keywords:
            if len(st.session_state.selected_keywords) < 3:
                st.session_state.selected_keywords.append(kw)
        elif not checked and kw in st.session_state.selected_keywords:
            st.session_state.selected_keywords.remove(kw)

    # =========================
    # 글 뼈대 생성
    # =========================
    if st.button("✅ 선택한 키워드로 글 뼈대 만들기"):
        if len(st.session_state.selected_keywords) != 3:
            st.error("키워드를 정확히 3개 선택해주세요.")
        else:
            k1, k2, k3 = st.session_state.selected_keywords

            st.markdown("## ✍️ 지침서 기반 글 뼈대")
            st.markdown(f"""
### 제목  
{k1} {k2} {k3} 총정리

### 도입부  
안녕하세요.  
오늘은 {k1}에서 한 번쯤 궁금해질 만한 {k2}를 정리해봤습니다.  
이 글에서는 운영 정보와 이용 흐름을 중심으로 설명합니다.  
처음 방문하는 분도 이해할 수 있도록 구성했습니다.

### ① 이곳은 무엇인가요  
### ② 언제·어떻게 이용하나요  
### ③ 내부 구성·동선은 어떻게 되나요  
### ④ 주차·교통·접근성  
### ⑤ 이런 사람에게 맞아요  

### 마무리  
### 해시태그
""")
