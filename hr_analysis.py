import streamlit as st
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns


# Streamlit 앱 코드 예시
import korean_font_config

# 한글 폰트 설정 적용
selected = korean_font_config.setup_korean_fonts()

# 설정된 폰트 확인 출력
font_info = korean_font_config.get_font_info()
st.write(f"Matplotlib 기본 폰트 패밀리: {font_info['rcParams.font.family']}")
st.write(f"실제 사용 폰트: {font_info['effective_font_name']} ({font_info['effective_font_path']})")

# 예시 차트 그리기
import matplotlib.pyplot as plt
plt.figure()
plt.title("예시 차트 - 한글 출력 확인")
plt.plot([1, 2, 3], [1, 4, 9])
st.pyplot(plt)  # Streamlit에 Matplotlib 차트 렌더링



# 0) 페이지 설정
st.set_page_config(page_title="퇴직율 대시보드", layout="wide")

# 1) 폰트 설정(A안: packages.txt로 설치된 시스템 폰트만 사용)
@st.cache_resource
def setup_korean_font():
    # 이전 실행 흔적 초기화(스트림릿은 프로세스 재사용)
    mpl.rcParams.update(mpl.rcParamsDefault)
    mpl.rcParams["axes.unicode_minus"] = False

    # 컨테이너에 설치될 가능성이 높은 후보들
    preferred = [
        "NanumGothic",        # fonts-nanum
        "Noto Sans CJK KR",   # fonts-noto-cjk
        "Noto Sans KR",       # 일부 배포판 명칭
        "NanumBarunGothic",   # fonts-nanum 포함
    ]

    available = {f.name for f in fm.fontManager.ttflist}

    # 1차: 정확 일치
    chosen = next((name for name in preferred if name in available), None)

    # 2차: 부분 일치(배포판/버전에 따라 이름이 조금 다른 경우)
    if chosen is None:
        for name in sorted(available):
            if ("Nanum" in name) or ("Noto" in name and "KR" in name):
                chosen = name
                break

    # 3차: 최후 폴백(그래도 한글은 Noto CJK가 있으면 그걸 택함)
    if chosen is None:
        chosen = "DejaVu Sans"

    # ⛔ 리스트가 아닌 "문자열 하나"로 확정해서 세팅
    mpl.rcParams["font.family"] = chosen

    # Seaborn은 스타일만 적용(폰트는 rc를 따른다)
    sns.set_theme(style="whitegrid")

    # 디버깅용: 여기서 리스트를 넣으면 TypeError가 나니 'chosen'만 넘긴다
    resolved_path = fm.findfont(fm.FontProperties(family=chosen))
    return {"chosen": chosen, "resolved": resolved_path}

font_info = setup_korean_font()
# 필요 시 확인:
# st.caption(f"🖋 사용 폰트: {font_info['chosen']} | 경로: {font_info['resolved']}")

# 2) 데이터 로드(인코딩 튼튼하게)
@st.cache_data(show_spinner=False)
def load_df(path: str = "HR Data.csv") -> pd.DataFrame:
    df = None
    for enc in ("utf-8-sig", "utf-8", "cp949", "euc-kr"):
        try:
            df = pd.read_csv(path, encoding=enc)
            break
        except Exception:
            continue
    if df is None:
        return pd.DataFrame()

    # BOM 제거
    df.columns = [c.lstrip("\ufeff") for c in df.columns]

    if "퇴직여부" in df.columns:
        df["퇴직"] = df["퇴직여부"].map({"Yes": 1, "No": 0}).astype("int8")
    df.drop(['직원수', '18세이상'], axis=1, errors="ignore", inplace=True)
    return df

df = load_df()
if df.empty:
    st.error("데이터가 없습니다. 'HR Data.csv' 파일을 확인하세요.")
    st.stop()

# 3) KPI
st.title("퇴직율 분석 및 인사이트")
n = len(df); quit_n = int(df["퇴직"].sum())
quit_rate = df["퇴직"].mean() * 100
stay_rate = 100 - quit_rate
k1, k2, k3, k4 = st.columns(4)
k1.metric("전체 직원 수", f"{n:,}명")
k2.metric("퇴직자 수", f"{quit_n:,}명")
k3.metric("유지율", f"{stay_rate:.1f}%")
k4.metric("퇴직율", f"{quit_rate:.1f}%")

# 4) 부서별 퇴직율
if "부서" in df.columns:
    dept = (df.groupby("부서")["퇴직"].mean().sort_values(ascending=False) * 100)
    st.subheader("부서별 퇴직율")
    fig1, ax1 = plt.subplots(figsize=(7.5, 3.8))
    sns.barplot(x=dept.index, y=dept.values, ax=ax1)
    ax1.set_ylabel("퇴직율(%)")
    ax1.bar_label(ax1.containers[0], fmt="%.1f")
    plt.xticks(rotation=15, ha="right")
    st.pyplot(fig1)

# 5) 두 칼럼: 급여인상율/야근정도
c1, c2 = st.columns(2)

if "급여증가분백분율" in df.columns:
    tmp = df[["급여증가분백분율", "퇴직"]].dropna().copy()
    tmp["인상률(%)"] = tmp["급여증가분백분율"].round().astype(int)
    sal = tmp.groupby("인상률(%)")["퇴직"].mean() * 100
    with c1:
        st.subheader("💰 급여인상율과 퇴직율")
        fig2, ax2 = plt.subplots(figsize=(6.5, 3.5))
        sns.lineplot(x=sal.index, y=sal.values, marker="o", ax=ax2)
        ax2.set_xlabel("급여인상율(%)")
        ax2.set_ylabel("퇴직율(%)")
        st.pyplot(fig2)

col_name = "야근정도"
if col_name in df.columns:
    ot = (df.groupby(col_name)["퇴직"].mean() * 100)
    with c2:
        st.subheader("⏰ 야근정도별 퇴직율")
        fig3, ax3 = plt.subplots(figsize=(6.5, 3.5))
        sns.barplot(x=ot.index, y=ot.values, ax=ax3)
        ax3.set_ylabel("퇴직율(%)")
        ax3.bar_label(ax3.containers[0], fmt="%.1f")
        st.pyplot(fig3)

