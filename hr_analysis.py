import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib  # 한글/마이너스 자동 설정

# 페이지 기본 설정
st.set_page_config(page_title="퇴직율 대시보드", layout="wide")
sns.set(style="whitegrid")

# 1) 데이터 로드 함수 정의
@st.cache_data
def load_df(path: str = "HR Data.csv") -> pd.DataFrame:
    try:
        df = pd.read_csv(path, encoding="utf-8")
    except:
        return df  # 파일 로드 실패 시 (df가 없을 경우)
    # 필요한 전처리 수행
    df["퇴직"] = df["퇴직여부"].map({"Yes": 1, "No": 0}).astype("int8")
    df.drop(['직원수', '18세이상'], axis=1, inplace=True)
    return df

# 데이터 불러오기
df = load_df()
if df.empty:
    st.error("데이터가 없습니다. 'HR Data.csv' 파일을 확인하세요.")
    st.stop()

# ===== KPI 섹션 =====
st.title("퇴직율 분석 및 인사이트")
n = len(df)
quit_n = int(df["퇴직"].sum())
quit_rate = df["퇴직"].mean() * 100
stay_rate = 100 - quit_rate

# KPI 표시
k1, k2, k3, k4 = st.columns(4)
k1.metric("전체 직원 수", f"{n:,}명")
k2.metric("퇴직자 수", f"{quit_n:,}명")
k3.metric("유지율", f"{stay_rate:.1f}%")
k4.metric("퇴직율", f"{quit_rate:.1f}%")

# 3) 그래프 1: 부서별 퇴직율
if "부서" in df.columns:
    dept = df.groupby("부서")["퇴직"].mean().sort_values(ascending=False) * 100
    st.subheader("부서별 퇴직율")
    fig1, ax1 = plt.subplots(figsize=(7.5, 3.8))
    sns.barplot(x=dept.index, y=dept.values, ax=ax1)
    ax1.set_ylabel("퇴직율(%)")
    ax1.bar_label(ax1.containers[0], fmt="%.1f")
    plt.xticks(rotation=15)
    st.pyplot(fig1)

# 4) 그래프 2와 그래프 3: 두 개의 칼럼에 배치
c1, c2 = st.columns(2)

# (좌측) 급여인상율과 퇴직율 (라인 차트)
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

# (우측) 야근정도별 퇴직율 (막대 차트)
if "야근정도" in df.columns:
    ot = df.groupby("야근정도")["퇴직"].mean() * 100
    with c2:
        st.subheader("⏰ 야근정도별 퇴직율")
        fig3, ax3 = plt.subplots(figsize=(6.5, 3.5))
        sns.barplot(x=ot.index, y=ot.values, ax=ax3)
        ax3.set_ylabel("퇴직율(%)")
        ax3.bar_label(ax3.containers[0], fmt="%.1f")
        st.pyplot(fig3)
