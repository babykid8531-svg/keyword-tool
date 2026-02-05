import streamlit as st
import pandas as pd
from openai import OpenAI
from openai import OpenAI, RateLimitError, APIError, APITimeoutError, BadRequestError

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
@@ -131,41 +131,56 @@ if st.session_state.run_generate:

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
        try:
            res = client.responses.create(
                model="gpt-4.1-mini",
                input=prompt,
                max_output_tokens=1200
            )
        except RateLimitError:
            st.error(
                "요청이 몰려 잠시 사용할 수 없어요. 1~2분 뒤 다시 시도해주세요."
            )
            res = None
        except (APITimeoutError, APIError):
            st.error(
                "OpenAI 서버 연결에 문제가 있어요. 잠시 후 다시 시도해주세요."
            )
            res = None
        except BadRequestError as exc:
            st.error(f"요청 형식 오류가 발생했어요: {exc}")
            res = None

        if res is not None:
            st.session_state.post_text = res.output_text

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
