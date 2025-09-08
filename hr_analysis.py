import streamlit as st
import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns

# ─────────────────────────────────────────────────────────────
# 0) 페이지 설정(최상단 1회)
st.set_page_config(page_title="퇴직율 대시보드", layout="wide")

# 1) 폰트 안전 설정(A안: packages.txt로 설치된 시스템 폰트만 활용)
@st.cache_resource
def setup_korean_font():
    # 이전 실행 흔적 초기화(스트림릿은 프로세스 재사용하므로 중요)
    mpl.rcParams.update(mpl.rcParamsDefault)
    mpl.rcParams["axes.unicode_minus"] = False

    # 컨테이너에 설치될 가능성이 높은 후보들(우선순위)
    preferred = [
        "NanumGothic",        # fonts-nanum
        "Noto Sans CJK KR",   # fonts-noto-cjk
        "Noto Sans KR",       # 일부 배포판에서 이렇게 등록됨
        "DejaVu Sans"         # 최후 폴백(한글 글리프 없을 수 있음)
    ]

    # 현재 프로세스에서 Matplotlib이 인식한 폰트 패밀리 이름 목록
    available = {f.name for f in fm.fontManager.ttflist}

    # 1차: 정확 일치 탐색
    chosen = next((name for name in preferred if name in available), None)

    # 2차: Noto/Nanum 계열 와일드카드 탐색(배포판마다 이름이 살짝 다름)
    if chosen is None:
        for name in sorted(available):
            if ("Nanum" in name) or ("Noto" in name and "CJK" in name and "KR" in name):
                chosen = name
                break

    # 3차: 완전 폴백
    if chosen is None:
        chosen = "DejaVu Sans"

    # rcParams 반영
    mpl.rcParams["font.family"] = chosen

    # Seaborn은 스타일만 적용(폰트는 rc를 따르게)
    sns.set_theme(style="whitegrid")

    # 디버깅/확인용 정보 반환
    resolved_path = fm.findfont(mpl.rcParams["font.family"])
    return {"chosen": chosen, "resolved": resolved_path}

font_info = setup_korean_font()
# 필요하면 주석 해제하고 확인해보세요(배포 환경에서 어떤 폰트가 잡혔는지).
# st.caption(f"🖋 사용 폰트: {font_info['chosen']} | 경로: {font_info['resolved']}")

# ─────────────────────────────────────────────────────────────
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

    # BOM 제거(가끔 컬럼명에 붙어 들어옴)
    df.columns = [c.lstrip("\ufeff") for c in df.columns]

    # 파생 및 정리
    if "퇴직여부" in df.columns:
        df["퇴직"] = df["퇴직여부"].map({"Yes": 1, "No": 0}).astype("int8")
    df.drop(['직원수', '18세이상'], axis=1, errors="ignore", inplace=True)
    return df

df = load_df()
if df.empty:
    st.error("데이터가 없습니다. 'HR Data.csv' 파일을 확인하세요.")
    st.stop()

# ─────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────
# 4) 그래프 1: 부서별 퇴직율
if "부서" in df.columns:
    dept = (df.groupby("부서")["퇴직"].mean().sort_values(ascending=False) * 100)
    st.subheader("부서별 퇴직율")
    fig1, ax1 = plt.subplots(figsize=(7.5, 3.8))
    sns.barplot(x=dept.index, y=dept.values, ax=ax1)
    ax1.set_ylabel("퇴직율(%)")
    ax1.bar_label(ax1.containers[0], fmt="%.1f")
    plt.xticks(rotation=15, ha="right")
    st.pyplot(fig1)

# ─────────────────────────────────────────────────────────────
# 5) 그래프 2/3: 두 칼럼
c1, c2 = st.columns(2)

# (좌) 급여인상율과 퇴직율
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

# (우) 야근정도별 퇴직율
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
