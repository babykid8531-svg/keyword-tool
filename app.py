import streamlit as st
import pandas as pd
from pytrends.request import TrendReq
import itertools
import random

st.set_page_config(page_title="키워드 추천 및 글 자동 생성기", layout="wide")

st.title("키워드 추천 및 분석받기")
st.caption("Google Trends + 자동 확장 키워드 기반")

base_keyword = st.text_input(
    "분석할 키워드를 입력해주세요 😊",
    placeholder="예: 전주 덕진공원"
)

# -------------------------------
# 키워드 확장 로직 (핵심)
# -------------------------------
def expand_keywords(keyword):
    suffixes = [
        "연꽃", "연꽃 시즌", "개화 시기", "주차", "산책", "사진 명소",
        "가볼만한곳", "데이트", "여행", "후기", "야경",
        "운영시간", "입장료", "위치"
    ]
    expanded = [f"{keyword} {s}" for s in suffixes]
    return expanded

@st.cache_data(show_spinner=False)
def analyze(keyword):
    pytrends = TrendReq(hl="ko", tz=540)

    keywords_to_try = [keyword] + expand_keywords(keyword)
    collected = []

    for kw in keywords_to_try:
        try:
            pytrends.build_payload([kw], timeframe="today 12-m", geo="KR")
            related = pytrends.related_queries()
            if kw in related and related[kw]:
                rq = related[kw]
                for k in ["top", "rising"]:
                    if rq.get(k) is not None:
                        collected += rq[k]["query"].tolist()
        except:
            continue

    # 그래도 부족하면 강제 생성
    if len(collected) < 20:
        collected += expand_keywords(keyword)

    collected = list(dict.fromkeys(collected))[:50]

    top10 = collected[:10]

    return collected, top10

# -------------------------------
# 글 생성 함수 (지침서 반영)
# -------------------------------
def generate_article(main_kw, sub_kws):
    title = f"{main_kw} 운영시간·주차·이용방법 총정리"

    intro = f"""안녕하세요.
오늘은 {main_kw}에 대해 처음 방문하는 분들을 위해 정리해봤어요.
이 공간의 기본 정보와 이용 방법을 중심으로 설명할게요.
운영시간, 주차, 동선까지 한 번에 확인할 수 있도록 구성했어요.
처음 방문하신다면 끝까지 참고해보세요.
"""

    body = f"""
① 이곳은 무엇인가요  
{main_kw}은 지역 내에서 대표적인 공간으로 알려져 있어요.  
과거에는 단순한 휴식 공간으로 활용되었으며, 현재는 관광과 산책 목적의 장소로 이용되요.

② 언제·어떻게 이용하나요  
운영 요일과 시간은 계절에 따라 달라질 수 있어요.  
방문 전 공식 안내를 확인하는 것이 좋아요.  
※ 성수기에는 방문 시간이 집중될 수 있습니다.

③ 내부 구성·동선은 어떻게 되나요  
입구를 기준으로 주요 동선이 이어지며 전체 관람에는 약 1~2시간이 소요됩니다.  
사진 촬영은 오전 시간대가 적합할거같아요.

④ 주차·교통·접근성  
주차장은 인근에 마련되어 있으며 도보 이동이 필요할 수 있어요.  
대중교통 이용도 가능한 편입니다.

⑤ 이런 사람에게 맞아요  
조용히 산책하고 싶은 분  
사진 촬영을 목적으로 방문하는 분  
짧은 일정의 여행을 계획하는 분
"""

    outro = f"""정리하자면 {main_kw}은 기본 정보만 알고 방문해도 충분히 즐길 수 있는 공간이에요.
동선과 이용 조건을 미리 파악하면 일정 관리에 도움이 됩니다.
방문을 계획 중이라면 한 번 참고해보셔도 좋을거 같아요.
"""

    hashtags = " ".join(
        [f"#{main_kw.replace(' ', '')}"] +
        [f"#{k.replace(' ', '')}" for k in sub_kws]
    )

    return f"""
📌 제목  
{title}

📌 도입부  
{intro}

📌 본문  
{body}

📌 마무리  
{outro}

📌 해시태그  
{hashtags}
"""

# -------------------------------
# 실행부
# -------------------------------
if st.button("키워드 추천 및 분석하기"):
    if not base_keyword:
        st.warning("키워드를 입력해주세요.")
    else:
        with st.spinner("키워드 분석 중입니다..."):
            all_kw, top10 = analyze(base_keyword)

        st.subheader("1️⃣ 연관 키워드 50개")
        st.dataframe(pd.DataFrame(
            list(itertools.zip_longest(*[all_kw[i::5] for i in range(5)], fillvalue=""))
        ))

        st.subheader("2️⃣ 상위 노출 가능 키워드 10개")
        top_df = pd.DataFrame({
            "키워드": top10,
            "검색 의도": ["정보형"] * len(top10)
        })
        st.dataframe(top_df)

        st.subheader("3️⃣ 글 생성용 키워드 선택 (최대 3개)")
        selected = st.multiselect(
            "메인 키워드 1개 + 서브 키워드 선택",
            options=top10,
            max_selections=3
        )

        if st.button("선택한 키워드로 글 자동 생성"):
            if not selected:
                st.warning("최소 1개 이상 선택해주세요.")
            else:
                main = selected[0]
                subs = selected[1:]
                article = generate_article(main, subs)

                st.subheader("✏️ 지침서 기반 자동 생성 글")
                st.text_area("복사해서 바로 사용하세요", article, height=600)
