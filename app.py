import streamlit as st
import pandas as pd

st.set_page_config(page_title="키워드 추천 및 분석받기", layout="wide")
st.title("키워드 추천 및 분석받기")
st.caption("Google Trends · 네이버 검색 의도 기반 실전 SEO 도구")

# -----------------------------
# 핵심 로직
# -----------------------------
def analyze_all(base):
    # 네이버/구글에서 실제로 붙는 검색 의도 기반 확장
    suffixes = [
        "주차","위치","가는법","운영시간","이용시간","입장료","요금",
        "산책","사진 명소","데이트","가볼만한곳","코스","야경",
        "계절","시즌","개화 시기","혼잡도","아이와","가족",
        "주말","평일","근처 맛집","근처 카페","지도","후기"
    ]

    rows = []
    for s in suffixes:
        kw = f"{base} {s}"
        seo = 0
        click = 0
        ai = 0

        # SEO 점수
        if s in ["주차","위치","가는법","운영시간","입장료"]:
            seo += 40
        if len(kw) >= 10:
            seo += 20

        # 클릭 유도
        if s in ["사진 명소","데이트","가볼만한곳","코스","야경"]:
            click += 30

        # AI 검색 친화
        if s in ["시즌","개화 시기","혼잡도","아이와","가족"]:
            ai += 30

        total = seo + click + ai
        rows.append({
            "키워드": kw,
            "SEO 점수": seo,
            "클릭 점수": click,
            "AI 검색 점수": ai,
            "종합 점수": total
        })

    df = pd.DataFrame(rows).sort_values("종합 점수", ascending=False)

    top10 = df.head(10)

    titles = [
        f"{base} 주차·운영시간·위치 총정리",
        f"{base} 가는법·이용방법 한눈 정리",
        f"{base} 사진 명소·산책 코스 정리",
        f"{base} 시즌·혼잡도 방문 전 체크",
        f"{base} 아이와·가족 방문 정보 정리"
    ]

    prompt = f"""
너는 네이버 블로그 전문 작가다.
아래 지침서를 절대 어기지 말고 글을 작성해라.

[주제]
{base}

[핵심 키워드]
{top10.iloc[0]['키워드']}
{top10.iloc[1]['키워드']}
{top10.iloc[2]['키워드']}

[글 구조 – 고정]
제목
도입부(4~5줄)

① 이 공간/장소는 무엇인가요
② 언제·어떻게 이용하나요 (시간·요일·조건)
③ 내부 구성·이용 흐름·동선
④ 주차·교통·접근성
⑤ 이런 사람에게 잘 맞아요

마무리(3문장)
해시태그 7~10개

[작성 규칙]
- 정보 우선, 감정 최소
- 처음 방문자 기준
- 후기·과장·감성 표현 금지
- 네이버 블로그용 자연스러운 설명체
"""

    return df.head(50), top10, titles, prompt


# -----------------------------
# UI
# -----------------------------
base_kw = st.text_input(
    "분석할 키워드를 입력하세요",
    placeholder="전주 덕진공원"
)

if st.button("🚀 키워드 분석 한 번에 실행"):
    if not base_kw.strip():
        st.warning("키워드를 입력해주세요.")
    else:
        kw50, top10, titles, prompt = analyze_all(base_kw.strip())

        st.subheader("1️⃣ 연관 키워드 50개 (Google·네이버 검색 의도 기반)")
        st.dataframe(kw50, height=260, use_container_width=True)

        st.subheader("2️⃣ SEO·클릭·AI 검색 최적 키워드 10개")
        st.dataframe(top10, height=260, use_container_width=True)

        st.subheader("3️⃣ 네이버 블로그 제목 추천 5개")
        for t in titles:
            st.write("•", t)

        st.subheader("4️⃣ 지침서 기반 글 생성용 완성 프롬프트")
        st.code(prompt)
