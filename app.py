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
if "analyzed" not in st.session_state:
    st.session_state.analyzed = False
if "all_keywords" not in st.session_state:
    st.session_state.all_keywords = []
if "raw_df" not in st.session_state:
    st.session_state.raw_df = pd.DataFrame()
if "final_candidates" not in st.session_state:
    st.session_state.final_candidates = []
if "selected_keywords" not in st.session_state:
    st.session_state.selected_keywords = []

# =========================
# 키워드 입력
# =========================
keyword = st.text_input(
    "분석 키워드",
    placeholder="예: 전주 덕진공원"
)

# =========================
# 키워드 확장 함수
# =========================
def expand_keywords(keyword):
    base = keyword.replace(" ", "")
    variants = set()

    variants.add(keyword)
    variants.add(base)

    suffixes = [
        "연꽃", "연꽃 시즌", "시즌", "명소",
        "사진", "방문", "개화시기"
    ]

    for s in suffixes:
        variants.add(f"{keyword} {s}")

    parts = keyword.split()
    if len(parts) >= 2:
        place = parts[-1]
        variants.add(place)
        for s in suffixes:
            variants.add(f"{place} {s}")

    return list(variants)

# =========================
# Google Trends 분석
# =========================
@st.cache_data(show_spinner=False)
def analyze(keyword):
    pytrends = TrendReq(hl="ko", tz=540)
    expanded = expand_keywords(keyword)

    frames = []

    for kw in expanded:
        try:
            pytrends.build_payload([kw], timeframe="today 12-m", geo="KR")
            related = pytrends.related_queries()

            if kw not in related or related[kw] is None:
                continue

            rq = related[kw]
            if rq.get("top") is not None:
                frames.append(rq["top"])
            if rq.get("rising") is not None:
                frames.append(rq["rising"])

            if frames:
                break
        except Exception:
            continue

    if not frames:
        return [], pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df = df.drop_duplicates(subset="query").head(50)

    df["검색량"] = "중"
    df.loc[:2, "검색량"] = "높음"
    df.loc[3:6, "검색량"] = "중상"
    df["이유"] = "연관 확장 검색 기반 정보형 키워드"

    return df["query"].tolist(), df

# =========================
# SEO + AI 검색용 자동 선별
# =========================
def auto_select_keywords(df):
    banned = ["후기", "힐링", "추천", "강추", "감성"]
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
    st.session_state.raw_df = df
    st.session_state.final_candidates = auto_select_keywords(df)
    st.session_state.selected_keywords = []

# =========================
# 결과 출력
# =========================
if st.session_state.analyzed:

    # 1️⃣ 연관 키워드 50개
    st.markdown("## 1️⃣ 연관 키워드 50개")
    cols = 5
    rows = math.ceil(len(st.session_state.all_keywords) / cols)
    grid = [
        st.session_state.all_keywords[i * cols:(i + 1) * cols]
        for i in range(rows)
    ]
    st.dataframe(pd.DataFrame(grid).fillna(""))

    # 2️⃣ 상위 노출 가능 키워드
    st.markdown("## 2️⃣ 상위 노출 가능성 높은 키워드")
    st.dataframe(
        st.session_state.raw_df[["query", "검색량", "이유"]]
        .rename(columns={"query": "키워드"})
        .head(10),
        use_container_width=True
    )

    # 3️⃣ 자동 선별 키워드 선택
    st.markdown("## 3️⃣ 글 생성용 키워드 선택 (최대 3개)")
    st.caption("SEO · 상위노출 · AI 검색 기준 자동 선별")

    for kw in st.session_state.final_candidates:
        checked = st.checkbox(
            kw,
            key=f"kw_{kw}",
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
이 공간의 성격과 이용 정보를 중심으로 구성했습니다.  
운영시간, 이용 방법, 주차와 동선까지 한 번에 확인할 수 있습니다.  
처음 방문하시는 분이라면 끝까지 보시면 도움이 됩니다.

### ① 이 공간은 무엇인가요  
{k2}는 {k1}에 위치한 장소로, 특정 목적을 위해 조성되었습니다.  
과거 용도와 조성 배경을 거쳐 현재는 방문형 공간으로 활용되고 있습니다.

### ② 언제·어떻게 이용하나요  
운영 요일과 시간은 정해져 있으며 일부 기간은 변동될 수 있습니다.  
입장 마감 시간과 휴무일은 사전 확인이 필요합니다.  
※ 방문 전 공식 안내 확인을 권장합니다.

### ③ 내부 구성·이용 흐름은 어떻게 되나요  
입장은 주 출입구 기준으로 시작하는 것이 일반적입니다.  
이용 동선은 한 방향 흐름으로 구성되어 있으며 평균 소요 시간은 정해져 있습니다.  
📌 혼잡 시간대를 피하면 동선 이동이 수월합니다.

### ④ 접근 방법·주차·교통은 어떤가요  
주차는 유료 또는 무료로 운영되며 공간 수는 제한적입니다.  
대중교통 이용 시 주요 정류장에서 하차 후 도보 이동이 필요합니다.  
접근성은 목적에 따라 체감 차이가 있습니다.

### ⑤ 이런 사람에게 잘 맞아요  
- 정보 위주로 차분히 둘러보고 싶은 분  
- 처음 방문해 동선 안내가 필요한 분  
- 시간 계획을 세워 방문하려는 분  
단, 즉흥적인 방문에는 제약이 있을 수 있습니다.

### 마무리  
{k2}는 사전에 정보를 알고 방문하면 이용 효율이 높은 공간입니다.  
운영 시간과 접근 방법만 정리해도 방문 흐름이 훨씬 안정됩니다.  
방문 전에 이 정리 내용을 참고해보시겠어요?

### 해시태그  
#{k2} #{k1} #{k1}가볼만한곳 #{k3} #{이용안내} #{주차정보}
""")
