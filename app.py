import streamlit as st
import pandas as pd
import json
import time
import openai
from openai import OpenAI

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(
    page_title="키워드 추천 및 분석받기",
    layout="wide"
)

st.title("키워드 추천 및 분석받기")
st.caption("네이버 SEO 실전용 · 키워드 분석 → 글 자동 생성")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# -----------------------------
# 네이버 글 작성 지침서 (프롬프트용)
# -----------------------------
GUIDELINE = """
너는 네이버 블로그 전문 작가이자 SEO 컨설턴트다.

[대원칙]
- 구조는 항상 같다.
- 정보가 감정보다 먼저다.
- 독자는 처음 방문하는 사람이다.

[글 전체 고정 구조]

제목
도입부(인사 + 요약)

① 이 공간/장소/서비스는 무엇인가요
② 언제·어떻게 이용하나요 (시간·요일·조건)
③ 내부 구성·이용 흐름·동선은 어떻게 되나요
④ 접근 방법·주차·교통은 어떤가요
⑤ 이런 사람에게 잘 맞아요

마무리
해시태그

[제목 지침]
- 형식: 지역/대상 + 이름 + 핵심 정보 2~3개 + 총정리
- 핵심 정보 예시: 운영시간, 주차, 위치, 이용방법, 요금, 예약
- 감성 단어, 후기형 표현, 추상적인 표현은 제목에 쓰지 않는다.

[도입부 지침]
- 분량: 4~5줄
- 구성 예시:
  안녕하세요! 로 시작
  오늘은 [지역]에서 한 번쯤 궁금해질 만한 [대상 이름]을 정리했다고 밝힌다.
  이 대상의 정체성을 한 줄로 설명한다.
  운영시간, 이용 방법, 주차와 동선까지 한 번에 확인할 수 있게 정리했다고 안내한다.
  처음 방문하는 사람에게 도움이 된다고 마무리한다.
- 도입부에는 감정이나 후기 표현을 넣지 않는다.

[① 이곳은 무엇인가요]
- 정체성을 설명하고 신뢰를 확보하는 파트.
- 설명 → 배경 → 현재 모습 순서.
- 연도, 숫자, 사실 정보를 우선.
- 한 문단에 감정 표현은 한 문장만 허용.
- 감상문이 아니라 설명문·관찰 위주로 작성.

[② 이용 시간·조건]
- 요일, 운영시간, 입장 마감 시간, 휴무일, 예외사항을 명확하게 정리.
- 단정적인 문장, 애매한 표현 사용 금지.
- 마지막에 주의사항 또는 팁 한 줄.

[③ 내부 구성·동선·이용 흐름]
- 처음 가는 사람 기준으로 안내.
- 어디서부터 시작하면 좋은지, 어떤 순서로 보면 좋은지, 전체 소요 시간을 설명.
- 사진 포인트·관람 포인트 위치도 함께 언급.
- 마지막에 실전 팁 한 줄.

[④ 주차·교통·접근성]
- 감정 없이 정보만 전달.
- 주차: 무료/유료, 주차 가능 대수, 도보 거리.
- 대중교통: 주요 출발지 기준 노선, 하차 후 도보 시간.
- 마지막에 접근성 종합 판단 한 줄(예: 자차 방문이 편한 편이다 등).

[⑤ 이런 사람에게 맞아요]
- “무조건 추천”이 아니라 어떤 유형에게 적합한지 정리.
- 예: 조용히 둘러보고 싶은 사람, 아이와 함께 오는 가족, 사진 위주 여행러 등.
- “강력 추천, 무조건 가야 한다” 같은 표현은 쓰지 않는다.

[마무리 문단]
- 3문장 구조:
  ① 전체 요약
  ② 핵심 장점 정리
  ③ 부드러운 방문 유도 (질문형 1문장까지 허용)

[해시태그]
- 7~10개.
- 구성: 고유명사 2개 / 지역 관련 2개 / 카테고리 2개 / 정보형 키워드 2개.
- 감성 태그, 의미 없는 태그는 사용하지 않는다.
"""

# -----------------------------
# 공통: GPT 호출 유틸 (RateLimit 방어)
# -----------------------------
def call_gpt_json(system_msg: str, user_msg: str, max_retries: int = 3):
    last_err = None
    for i in range(max_retries):
        try:
            res = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.4,
            )
            content = res.choices[0].message.content.strip()
            return json.loads(content)
        except openai.RateLimitError as e:
            last_err = e
            # 살짝 쉬었다가 재시도 (내부 대기, 화면엔 안 보임)
            time.sleep(1.5 * (i + 1))
        except json.JSONDecodeError as e:
            last_err = e
            break
    raise last_err


def call_gpt_text(system_msg: str, user_msg: str, max_retries: int = 3) -> str:
    last_err = None
    for i in range(max_retries):
        try:
            res = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.5,
            )
            return res.choices[0].message.content.strip()
        except openai.RateLimitError as e:
            last_err = e
            time.sleep(1.5 * (i + 1))
    raise last_err

# -----------------------------
# 1단계: 키워드 분석 (GPT 기반)
# -----------------------------
def analyze_keywords(base_keyword: str):
    """
    base_keyword 하나를 받아서
    - 연관 키워드 50개
    - 상위 노출 가능 키워드 10개 (검색량·이유)
    - 그 중에서 자동 선정한 TOP3
    를 모두 반환.
    """

    user_prompt = f"""
너는 한국 네이버 블로그용 SEO 키워드 기획자다.

[입력 키워드]
{base_keyword}

Google Trends 검색 패턴과 네이버 검색 의도를 함께 고려한다고 가정하고 아래를 생성해라.

1단계: 이 키워드를 중심으로, 실제 사용자가 검색할 법한 연관 키워드 50개를 만든다.
- "지역명 + 구체적 의도" 형태 위주 (예: 전주 덕진공원 연꽃 시즌, 전주 덕진공원 사진 명소)
- 너무 넓은 단어(여행, 맛집 같은 단어 단독)는 피한다.

2단계: 그 중에서 블로그 상위 노출 가능성이 높은 키워드 10개를 고르고,
각각에 대해
- keyword : 키워드
- volume : "높음" / "중상" / "중" 중 하나
- reason : 왜 좋은지 한 줄로 설명
을 만든다.

3단계: 위 10개 중에서 블로그 본문에 메인으로 쓸 핵심 키워드 3개를 자동으로 선정한다.
- 1개는 메인 키워드 (가장 대표적인 검색어)
- 1개는 정보형 키워드 (운영시간·요금·이용방법 등 정보 의도)
- 1개는 롱테일 키워드 (후기·코스·사진명소 등 행동 의도)

출력은 반드시 아래 JSON 형식으로만 작성해라.

{{
  "keywords50": ["키워드1", "키워드2", ... 50개],
  "top10": [
    {{"keyword": "키워드A", "volume": "높음", "reason": "이유"}},
    ...
  ],
  "top3": ["메인키워드", "정보형키워드", "롱테일키워드"]
}}
"""

    data = call_gpt_json(
        system_msg="너는 한국 네이버 SEO를 잘 아는 키워드 분석가다. 반드시 JSON만 반환해라.",
        user_msg=user_prompt,
    )

    # 연관 키워드 50개 → 5열 격자
    kw50 = data.get("keywords50", [])[:50]
    while len(kw50) < 50:
        kw50.append("")
    cols = 5
    grid = [kw50[i : i + cols] for i in range(0, 50, cols)]
    kw_table = pd.DataFrame(grid, columns=[f"{i}" for i in range(1, cols + 1)])

    # 상위 10개
    top10_df = pd.DataFrame(data.get("top10", []))

    # TOP3
    top3 = data.get("top3", [])[:3]

    return kw_table, top10_df, top3

# -----------------------------
# 2단계: TOP3 키워드로 네이버 글 생성
# -----------------------------
def generate_post(base_keyword: str, top3_keywords: list[str]) -> str:
    if len(top3_keywords) < 3:
        raise ValueError("top3 키워드가 부족합니다.")

    kw_main, kw_info, kw_long = top3_keywords[:3]

    user_prompt = f"""
[블로그 글 작성 요청]

- 기본 주제 키워드: {base_keyword}
- 자동 선정된 핵심 키워드 3개:
  1) 메인 키워드: {kw_main}
  2) 정보형 키워드: {kw_info}
  3) 롱테일 키워드: {kw_long}

요청사항:
- 네이버 블로그에 그대로 붙여넣어 쓸 수 있는 글로 작성한다.
- 말투는 '~했어요', '~입니다' 위주의 담백한 1인칭 설명형.
- 제목, 도입부, ①~⑤, 마무리, 해시태그까지 지침서 구조를 정확히 지킨다.
- 세 키워드를 제목·본문·해시태그에 자연스럽게 섞어서 넣는다.
- 해시태그는 # 없이, 쉼표로만 구분해 한 줄에 적는다.
- HTML 태그는 사용하지 말고, 순수 텍스트/마크다운으로만 작성한다.
"""

    text = call_gpt_text(
        system_msg=GUIDELINE,
        user_msg=user_prompt,
    )
    return text

# -----------------------------
# 세션 상태 초기화
# -----------------------------
if "kw_table" not in st.session_state:
    st.session_state.kw_table = None
if "top10_df" not in st.session_state:
    st.session_state.top10_df = None
if "top3" not in st.session_state:
    st.session_state.top3 = None
if "base_keyword" not in st.session_state:
    st.session_state.base_keyword = ""

# -----------------------------
# 화면 구성
# -----------------------------
base_kw = st.text_input(
    "분석할 키워드를 입력해주세요 😊",
    placeholder="예: 전주 덕진공원",
    value=st.session_state.base_keyword,
)

col1, col2 = st.columns([1, 4])
with col1:
    analyze_clicked = st.button("키워드 분석")

# 1단계: 키워드 분석 버튼
if analyze_clicked:
    if not base_kw.strip():
        st.warning("키워드를 먼저 입력해주세요.")
    else:
        try:
            with st.spinner("키워드 분석 중입니다..."):
                kw_table, top10_df, top3 = analyze_keywords(base_kw.strip())

            st.session_state.kw_table = kw_table
            st.session_state.top10_df = top10_df
            st.session_state.top3 = top3
            st.session_state.base_keyword = base_kw.strip()

        except openai.RateLimitError:
            st.error("OpenAI 요청이 너무 많이 몰려서 제한이 걸렸어요. 버튼을 조금 간격을 두고 눌러줘야 해요.")
        except Exception as e:
            st.error(f"키워드 분석 중 오류가 발생했어요: {e}")

# 1, 2, 3번 영역 표시
if st.session_state.kw_table is not None:
    st.markdown("### 1️⃣ 연관 키워드 50개")
    st.caption("정렬 기준: 주제 연관성 + 검색 의도")
    st.dataframe(st.session_state.kw_table, use_container_width=True)

if st.session_state.top10_df is not None:
    st.markdown("### 2️⃣ 상위 노출 가능성이 높은 키워드 10개")
    st.dataframe(st.session_state.top10_df, use_container_width=True)

if st.session_state.top3 is not None and len(st.session_state.top3) == 3:
    k1, k2, k3 = st.session_state.top3
    st.markdown("### 3️⃣ 글 생성용 핵심 키워드 3개 (자동 선정)")
    st.write(f"- ① 메인 키워드: **{k1}**")
    st.write(f"- ② 정보형 키워드: **{k2}**")
    st.write(f"- ③ 롱테일 키워드: **{k3}**")
    st.info("이 세 개를 조합해서 네이버용 본문을 자동으로 생성합니다.")

    if st.button("이 TOP3로 네이버 블로그 글 생성"):
        try:
            with st.spinner("네이버 블로그용 글을 생성하는 중입니다..."):
                post = generate_post(st.session_state.base_keyword, st.session_state.top3)
            st.markdown("## ✏️ 지침서 기반 완성 글")
            st.markdown(post)
        except openai.RateLimitError:
            st.error("OpenAI 요청 제한 때문에 글 생성에 실패했어요. 다시 한 번 시도할 수 있어요.")
        except Exception as e:
            st.error(f"글 생성 중 오류가 발생했어요: {e}")
else:
    st.caption("키워드 분석을 먼저 실행하면 TOP3 키워드와 글 생성 버튼이 나타납니다.")
