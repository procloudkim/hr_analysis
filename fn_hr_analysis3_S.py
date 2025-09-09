import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# 페이지 설정
st.set_page_config(
    page_title="HR Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'df' not in st.session_state:
    st.session_state.df = None
if 'column_mapping' not in st.session_state:
    st.session_state.column_mapping = {}
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True
if 'custom_fields' not in st.session_state:
    st.session_state.custom_fields = {}

# 다크모드/라이트모드 스타일
def get_theme_styles():
    if st.session_state.dark_mode:
        return """
        <style>
            .metric-card { background-color: #1e1e1e; padding: 20px; border-radius: 10px; margin: 10px 0; border: 1px solid #333; }
            .insight-box { background-color: #1a3a52; color: #e0e0e0; padding: 15px; border-radius: 8px; border-left: 4px solid #4da6ff; margin: 20px 0; }
            .warning-box { background-color: #4a3a1a; color: #ffd700; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107; margin: 20px 0; }
            .danger-box { background-color: #4a1a1a; color: #ff6b6b; padding: 15px; border-radius: 8px; border-left: 4px solid #dc3545; margin: 20px 0; }
            .formula-box { background-color: #2e2e2e; color: #e0e0e0; padding: 15px; border-radius: 8px; border: 1px solid #444; margin: 15px 0; font-family: 'Courier New', monospace; }
        </style>
        """
    else:
        return """
        <style>
            .metric-card { background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin: 10px 0; border: 1px solid #dee2e6; }
            .insight-box { background-color: #e8f4f8; color: #0c5460; padding: 15px; border-radius: 8px; border-left: 4px solid #1f77b4; margin: 20px 0; }
            .warning-box { background-color: #fff3cd; color: #856404; padding: 15px; border-radius: 8px; border-left: 4px solid #ffc107; margin: 20px 0; }
            .danger-box { background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 8px; border-left: 4px solid #dc3545; margin: 20px 0; }
            .formula-box { background-color: #f8f9fa; color: #212529; padding: 15px; border-radius: 8px; border: 1px solid #dee2e6; margin: 15px 0; font-family: 'Courier New', monospace; }
        </style>
        """
    
# CSS 적용 및 Plotly 템플릿 설정
st.markdown(get_theme_styles(), unsafe_allow_html=True)
px.defaults.template = "plotly_dark" if st.session_state.dark_mode else "plotly_white"

# --- 사이드바 ---
st.sidebar.title("🎯 HR Analytics Dashboard")

# 다크모드 토글 스위치
dark_mode_on = st.sidebar.toggle("🌙 다크 모드", value=st.session_state.dark_mode)
if dark_mode_on != st.session_state.dark_mode:
    st.session_state.dark_mode = dark_mode_on
    st.rerun()

st.sidebar.markdown("---")

# 파일 업로드
uploaded_file = st.sidebar.file_uploader("CSV 파일 업로드", type=['csv'])

# 기본 컬럼 매핑
default_mapping = {
    '직원ID': 'EmployeeNumber', '퇴직여부': 'Attrition', '나이': 'Age', '성별': 'Gender', '출장빈도': 'BusinessTravel',
    '일대비급여수준': 'DailyRate', '부서': 'Department', '집과의거리': 'DistanceFromHome', '전공': 'EducationField',
    '업무환경만족도': 'EnvironmentSatisfaction', '업무참여도': 'JobInvolvement', '업무만족도': 'JobSatisfaction',
    '결혼여부': 'MaritalStatus', '월급여': 'MonthlyIncome', '일한회사수': 'NumCompaniesWorked', '총경력': 'TotalWorkingYears',
    '야근정도': 'OverTime', '급여인상률': 'PercentSalaryHike', '스톡옵션': 'StockOptionLevel', '근속연수': 'YearsAtCompany',
    '현재역할년수': 'YearsInCurrentRole', '마지막승진년수': 'YearsSinceLastPromotion'
}

# --- 데이터 처리 및 계산 함수 ---
def load_and_process_data(file):
    """데이터 로드"""
    return pd.read_csv(file)

def calculate_early_warning_score(df, mapping):
    """조기 경보 점수 계산"""
    scores = pd.Series(0, index=df.index)
    if '업무만족도' in mapping and mapping['업무만족도'] in df.columns:
        scores += df[mapping['업무만족도']].apply(lambda x: 40 if x <= 2 else (20 if x == 3 else 0))
    if '야근정도' in mapping and mapping['야근정도'] in df.columns:
        scores += df[mapping['야근정도']].isin(['Yes', 'yes', '예', '네']) * 30
    if '마지막승진년수' in mapping and mapping['마지막승진년수'] in df.columns:
        scores += df[mapping['마지막승진년수']].apply(lambda x: 20 if x >= 3 else (10 if x >= 2 else 0))
    if '집과의거리' in mapping and mapping['집과의거리'] in df.columns:
        scores += (df[mapping['집과의거리']] > 20) * 10
    return scores

def calculate_retention_risk_score(df, mapping):
    """잔류 위험 점수 계산"""
    scores = pd.Series(0, index=df.index)
    if '야근정도' in mapping and mapping['야근정도'] in df.columns:
        scores += df[mapping['야근정도']].isin(['Yes', 'yes', '예', '네']) * 25
    if '업무만족도' in mapping and mapping['업무만족도'] in df.columns:
        scores += (5 - df[mapping['업무만족도']]) * 10
    if '업무환경만족도' in mapping and mapping['업무환경만족도'] in df.columns:
        scores += (5 - df[mapping['업무환경만족도']]) * 8
    if '마지막승진년수' in mapping and mapping['마지막승진년수'] in df.columns:
        scores += (df[mapping['마지막승진년수']] * 4).clip(upper=20)
    if '일한회사수' in mapping and mapping['일한회사수'] in df.columns:
        scores += (df[mapping['일한회사수']] * 2).clip(upper=15)
    return scores

def generate_insight_comment(attrition_rate, scope_name):
    """인사이트 코멘트 생성"""
    if attrition_rate > 20:
        return f"🚨 **{scope_name}** 퇴직률이 {attrition_rate:.1f}%로 매우 높습니다. 즉각적인 대응이 필요합니다!"
    elif attrition_rate > 15:
        return f"⚠️ **{scope_name}** 퇴직률이 {attrition_rate:.1f}%로 업계 평균(15%)보다 높습니다."
    else:
        return f"✅ **{scope_name}** 퇴직률이 {attrition_rate:.1f}%로 안정적인 수준입니다."

# --- 데이터 로드 및 자동 매핑 ---
if uploaded_file is not None and st.session_state.df is None:
    st.session_state.df = load_and_process_data(uploaded_file)
    if not st.session_state.column_mapping:
        df_cols_lower = {col.lower(): col for col in st.session_state.df.columns}
        for korean, english in default_mapping.items():
            if korean in st.session_state.df.columns: st.session_state.column_mapping[korean] = korean
            elif english in st.session_state.df.columns: st.session_state.column_mapping[korean] = english
            elif english.lower() in df_cols_lower: st.session_state.column_mapping[korean] = df_cols_lower[english.lower()]

# --- 사이드바 메뉴 ---
st.sidebar.markdown("---")
menu_options = ["🏠 홈", "⚠️ 조기 경보", "📈 잔류 위험", "🏢 부서 건강도", "⚙️ 컬럼 매핑", "📊 커스텀 차트"]
menu = st.sidebar.radio("메뉴 선택", menu_options)

# --- 메인 콘텐츠 ---

if menu == "🏠 홈":
    st.title("🏠 HR Analytics Dashboard")
    if st.session_state.df is not None:
        df = st.session_state.df
        mapping = st.session_state.column_mapping
        
        # 부서 필터
        selected_dept = '전체'
        if '부서' in mapping and mapping['부서'] in df.columns:
            dept_options = ['전체'] + sorted(list(df[mapping['부서']].unique()))
            selected_dept = st.selectbox("부서 선택", dept_options, key='home_dept_filter')
        else:
            st.sidebar.warning("'부서' 컬럼을 매핑해야 부서별 필터링이 가능합니다.")

        filtered_df = df if selected_dept == '전체' else df[df[mapping['부서']] == selected_dept]
        
        # 직원 수 및 퇴사자 수 계산
        leavers_count = 0
        if '퇴직여부' in mapping and mapping['퇴직여부'] in filtered_df.columns:
            is_leaver = filtered_df[mapping['퇴직여부']].isin(['Yes', 'yes', '예', '네'])
            leavers_count = is_leaver.sum()
        else:
            st.warning("'퇴직여부' 컬럼이 매핑되지 않아 퇴사 관련 지표를 계산할 수 없습니다.")
        
        total_employees = len(filtered_df)
        current_employees = total_employees - leavers_count
        attrition_rate = (leavers_count / total_employees * 100) if total_employees > 0 else 0
        
        insight = generate_insight_comment(attrition_rate, '전체' if selected_dept == '전체' else selected_dept)
        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)
        
        # 메트릭 카드
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("재직 직원 수", f"{current_employees:,}명")
        with col2: st.metric("퇴사자 수", f"{leavers_count:,}명")
        with col3: st.metric("퇴직률", f"{attrition_rate:.1f}%", delta=f"{attrition_rate - 15:+.1f}%p (업계평균 대비)", delta_color="inverse")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            chart_options = {}
            temp_df = filtered_df.copy() # 원본 수정을 피하기 위해 복사본 사용
            if '나이' in mapping and mapping['나이'] in temp_df.columns:
                temp_df['연령대'] = pd.cut(temp_df[mapping['나이']], bins=[17, 29, 39, 49, 100], labels=['20대', '30대', '40대', '50대+'])
                chart_options['연령대'] = '연령대별 분포'
            if '업무만족도' in mapping and mapping['업무만족도'] in temp_df.columns: chart_options[mapping['업무만족도']] = '업무만족도'
            if '결혼여부' in mapping and mapping['결혼여부'] in temp_df.columns: chart_options[mapping['결혼여부']] = '결혼여부'
            
            if chart_options:
                selected_chart_col = st.selectbox("파이 차트 선택", options=list(chart_options.keys()), format_func=lambda x: chart_options[x])
                chart_data = temp_df[selected_chart_col].value_counts()
                fig_pie = px.pie(values=chart_data.values, names=chart_data.index, title=chart_options[selected_chart_col], hole=0.3)
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            if ('나이' in mapping and mapping['나이'] in filtered_df.columns and 
                '월급여' in mapping and mapping['월급여'] in filtered_df.columns):
                
                temp_df = filtered_df.copy()
                temp_df['연령대'] = pd.cut(temp_df[mapping['나이']], bins=[17, 29, 39, 49, 100], labels=['20대', '30대', '40대', '50대+'])
                age_salary = temp_df.groupby('연령대', observed=False).agg(
                    평균급여=(mapping['월급여'], 'mean'),
                    인원수=(mapping['월급여'], 'count')
                ).reset_index()
                
                fig_combo = make_subplots(specs=[[{"secondary_y": True}]])
                fig_combo.add_trace(go.Bar(x=age_salary['연령대'], y=age_salary['인원수'], name='인원수'), secondary_y=False)
                fig_combo.add_trace(go.Scatter(x=age_salary['연령대'], y=age_salary['평균급여'], name='평균 월급여', mode='lines+markers'), secondary_y=True)
                fig_combo.update_layout(title="연령대별 인원 및 평균 월급여", yaxis_title="인원수", yaxis2_title="평균 월급여")
                st.plotly_chart(fig_combo, use_container_width=True)

    else:
        st.info("📁 왼쪽 사이드바에서 CSV 파일을 업로드하여 대시보드를 시작하세요.")

elif menu == "⚠️ 조기 경보":
    st.title("⚠️ Early Warning System (조기 경보)")
    if st.session_state.df is not None:
        df = st.session_state.df.copy()
        mapping = st.session_state.column_mapping
        
        with st.expander("ℹ️ 조기 경보 점수 계산 공식 보기"):
            st.markdown("""
            **- 업무만족도:** 2점 이하 (+40점), 3점 (+20점)
            **- 야근:** Yes (+30점)
            **- 마지막 승진:** 3년 이상 (+20점), 2년 (+10점)
            **- 장거리 출퇴근:** 20km 초과 (+10점)
            """)
        
        df['early_warning_score'] = calculate_early_warning_score(df, mapping)
        high_risk = df[df['early_warning_score'] >= 70]
        medium_risk = df[(df['early_warning_score'] >= 40) & (df['early_warning_score'] < 70)]
        low_risk = df[df['early_warning_score'] < 40]
        
        # Insight comment
        high_risk_pct = (len(high_risk) / len(df)) * 100
        insight = generate_insight_comment(high_risk_pct, '조기 경보 시스템')
        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)
        
        # Metric cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🔴 고위험군", f"{len(high_risk)}명", f"{high_risk_pct:.1f}%")
        with col2:
            st.metric("🟡 중위험군", f"{len(medium_risk)}명", f"{(len(medium_risk)/len(df)*100):.1f}%")
        with col3:
            st.metric("🟢 저위험군", f"{len(low_risk)}명", f"{(len(low_risk)/len(df)*100):.1f}%")
        with col4:
            avg_score = df['early_warning_score'].mean()
            st.metric("평균 위험 점수", f"{avg_score:.1f}점")
        
        st.markdown("---")
        
        # Donut chart for risk distribution
        col1, col2 = st.columns(2)
        with col1:
            risk_dist = pd.DataFrame({
                '위험군': ['고위험', '중위험', '저위험'],
                '인원': [len(high_risk), len(medium_risk), len(low_risk)]
            })
            fig_risk = px.pie(risk_dist, values='인원', names='위험군', title="위험군 분포", hole=0.4,
                              color_discrete_map={'고위험': '#ff4444', '중위험': '#ffaa00', '저위험': '#00c851'})
            st.plotly_chart(fig_risk, use_container_width=True)
        
        # Bar chart for department-wise high-risk percentage
        with col2:
            if '부서' in mapping and mapping['부서'] in df.columns:
                dept_risk = df.groupby(mapping['부서'])['early_warning_score'].apply(
                    lambda x: (x >= 70).sum() / len(x) * 100
                ).reset_index()
                dept_risk.columns = ['부서', '고위험군 비율(%)']
                fig_dept_risk = px.bar(dept_risk, x='부서', y='고위험군 비율(%)',
                                       title="부서별 고위험군 비율",
                                       color='고위험군 비율(%)', color_continuous_scale='Reds')
                st.plotly_chart(fig_dept_risk, use_container_width=True)
        
        # High-risk employee table
        st.markdown("### 🔴 고위험군 직원 리스트")
        if len(high_risk) > 0:
            display_cols = [col for col in [mapping.get('직원ID'), mapping.get('부서'), 
                                           mapping.get('업무만족도'), mapping.get('야근정도'),
                                           'early_warning_score'] if col in df.columns]
            st.dataframe(high_risk[display_cols].head(20))
        else:
            st.info("고위험군 직원이 없습니다.")
    else:
        st.info("📁 왼쪽 사이드바에서 CSV 파일을 업로드하여 대시보드를 시작하세요.")

elif menu == "📈 잔류 위험":
    st.title("📈 Retention Risk Score (잔류 위험 점수)")
    if st.session_state.df is not None:
        df = st.session_state.df.copy()
        mapping = st.session_state.column_mapping
        
        with st.expander("ℹ️ 잔류 위험 점수 계산 공식 보기"):
            st.markdown("""
            **- 야근:** Yes (+25점)
            **- 업무만족도:** (5 - 점수) × 10점 (최대 40점)
            **- 업무환경만족도:** (5 - 점수) × 8점 (최대 32점)
            **- 마지막 승진년수:** 년수 × 4 (최대 20점)
            **- 과거 근무 회사 수:** 회사 수 × 2 (최대 15점)
            """)
        
        df['retention_risk_score'] = calculate_retention_risk_score(df, mapping)
        high_risk = df[df['retention_risk_score'] >= 70]
        medium_risk = df[(df['retention_risk_score'] >= 50) & (df['retention_risk_score'] < 70)]
        low_risk = df[df['retention_risk_score'] < 50]
        
        # Insight comment
        avg_risk = df['retention_risk_score'].mean()
        insight = f"🚨 퇴직 위험이 매우 높습니다. 근무환경 개선이 시급합니다." if avg_risk > 60 else \
                  f"⚡ 퇴직 위험 평균 {avg_risk:.1f}점, 고위험군 {len(high_risk)}명에 집중 관리 필요." if avg_risk > 40 else \
                  f"💚 퇴직 위험이 평균 {avg_risk:.1f}점으로 낮은 수준입니다."
        st.markdown(f'<div class="warning-box">{insight}</div>', unsafe_allow_html=True)
        
        # Metric cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🚨 고위험군", f"{len(high_risk)}명", f"{(len(high_risk)/len(df)*100):.1f}%")
        with col2:
            st.metric("⚡ 중위험군", f"{len(medium_risk)}명", f"{(len(medium_risk)/len(df)*100):.1f}%")
        with col3:
            st.metric("✅ 저위험군", f"{len(low_risk)}명", f"{(len(low_risk)/len(df)*100):.1f}%")
        with col4:
            st.metric("평균 위험 점수", f"{avg_risk:.1f}점", delta="높음" if avg_risk > 60 else "보통")
        
        st.markdown("---")
        
        # Histogram for risk score distribution
        fig_hist = px.histogram(df, x='retention_risk_score', nbins=30,
                                title="잔류 위험 점수 분포",
                                labels={'retention_risk_score': '위험 점수', 'count': '인원수'})
        fig_hist.add_vline(x=70, line_dash="dash", line_color="red", annotation_text="고위험 기준선")
        fig_hist.add_vline(x=50, line_dash="dash", line_color="orange", annotation_text="중위험 기준선")
        st.plotly_chart(fig_hist, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        # Bar chart for attrition by risk level
        with col1:
            if '퇴직여부' in mapping and mapping['퇴직여부'] in df.columns:
                df['퇴직'] = df[mapping['퇴직여부']].isin(['Yes', 'yes', '예', '네']).astype(int)
                risk_levels = ['저위험\n(<50)', '중위험\n(50-69)', '고위험\n(≥70)']
                attrition_by_risk = [
                    df[df['retention_risk_score'] < 50]['퇴직'].mean() * 100,
                    df[(df['retention_risk_score'] >= 50) & (df['retention_risk_score'] < 70)]['퇴직'].mean() * 100,
                    df[df['retention_risk_score'] >= 70]['퇴직'].mean() * 100
                ]
                fig_validation = go.Figure(data=[
                    go.Bar(x=risk_levels, y=attrition_by_risk, marker_color=['#00c851', '#ffaa00', '#ff4444'])
                ])
                fig_validation.update_layout(title="위험군별 실제 퇴직률 검증", yaxis_title="퇴직률 (%)")
                st.plotly_chart(fig_validation, use_container_width=True)
        
        # Bar chart for key risk factors
        with col2:
            factors = []
            if '야근정도' in mapping and mapping['야근정도'] in df.columns:
                overtime_impact = df[df[mapping['야근정도']].isin(['Yes', 'yes', '예', '네'])]['retention_risk_score'].mean()
                factors.append(('야근', overtime_impact))
            if '업무만족도' in mapping and mapping['업무만족도'] in df.columns:
                low_satisfaction_impact = df[df[mapping['업무만족도']] <= 2]['retention_risk_score'].mean()
                factors.append(('낮은 만족도', low_satisfaction_impact))
            if '마지막승진년수' in mapping and mapping['마지막승진년수'] in df.columns:
                promotion_stagnation_impact = df[df[mapping['마지막승진년수']] >= 3]['retention_risk_score'].mean()
                factors.append(('승진 정체', promotion_stagnation_impact))
            if factors:
                factor_df = pd.DataFrame(factors, columns=['요인', '평균 위험 점수'])
                fig_factors = px.bar(factor_df, x='요인', y='평균 위험 점수',
                                    title="주요 위험 요인별 영향도",
                                    color='평균 위험 점수', color_continuous_scale='YlOrRd')
                st.plotly_chart(fig_factors, use_container_width=True)
        
        # High-risk employee table
        st.markdown("### 🚨 고위험군 직원 리스트")
        if len(high_risk) > 0:
            display_cols = [col for col in [mapping.get('직원ID'), mapping.get('부서'), 
                                           mapping.get('업무만족도'), mapping.get('야근정도'),
                                           'retention_risk_score'] if col in df.columns]
            st.dataframe(high_risk[display_cols].head(20))
        else:
            st.info("고위험군 직원이 없습니다.")
    else:
        st.info("📁 왼쪽 사이드바에서 CSV 파일을 업로드하여 대시보드를 시작하세요.")

elif menu == "🏢 부서 건강도":
    st.title("🏢 Department Health (부서 건강도)")
    if st.session_state.df is not None and '부서' in st.session_state.column_mapping and st.session_state.column_mapping['부서'] in st.session_state.df.columns:
        df = st.session_state.df.copy()
        mapping = st.session_state.column_mapping
        dept_col = mapping['부서']
        
        # Department statistics
        dept_stats = []
        for dept in df[dept_col].unique():
            dept_df = df[df[dept_col] == dept]
            stats = {
                '부서': dept,
                '인원': len(dept_df),
                '퇴직률': 0,
                '평균만족도': 0,
                '야근비율': 0,
                '평균근속': 0,
                '건강도점수': 0
            }
            if '퇴직여부' in mapping and mapping['퇴직여부'] in df.columns:
                stats['퇴직률'] = (dept_df[mapping['퇴직여부']].isin(['Yes', 'yes', '예', '네']).sum() / len(dept_df)) * 100
            satisfaction_cols = [col for col in [mapping.get('업무만족도'), mapping.get('업무환경만족도')] if col in df.columns]
            if satisfaction_cols:
                stats['평균만족도'] = dept_df[satisfaction_cols].mean().mean()
            if '야근정도' in mapping and mapping['야근정도'] in df.columns:
                stats['야근비율'] = (dept_df[mapping['야근정도']].isin(['Yes', 'yes', '예', '네']).sum() / len(dept_df)) * 100
            if '근속연수' in mapping and mapping['근속연수'] in df.columns:
                stats['평균근속'] = dept_df[mapping['근속연수']].mean()
            health_score = 0
            health_score += (stats['평균만족도'] / 4) * 25 if stats['평균만족도'] > 0 else 0
            health_score += (100 - stats['퇴직률']) * 0.3
            health_score += (100 - stats['야근비율']) * 0.25
            health_score += min(20, stats['평균근속'] * 2) if stats['평균근속'] > 0 else 0
            stats['건강도점수'] = health_score
            dept_stats.append(stats)
        
        dept_df_stats = pd.DataFrame(dept_stats)
        
        # Insight comment
        best_dept = dept_df_stats.loc[dept_df_stats['건강도점수'].idxmax(), '부서']
        worst_dept = dept_df_stats.loc[dept_df_stats['건강도점수'].idxmin(), '부서']
        insight = f"🏆 {best_dept} 부서가 가장 건강한 조직문화를 보이고 있습니다. 반면 {worst_dept} 부서는 개선이 필요합니다."
        if dept_df_stats['퇴직률'].max() > 20:
            high_attrition_dept = dept_df_stats.loc[dept_df_stats['퇴직률'].idxmax(), '부서']
            insight += f" 특히 {high_attrition_dept} 부서의 퇴직률 {dept_df_stats['퇴직률'].max():.1f}%는 즉각적인 조치가 필요합니다."
        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)
        
        # Metric cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_health = dept_df_stats['건강도점수'].mean()
            st.metric("평균 건강도", f"{avg_health:.1f}점")
        with col2:
            st.metric("최고 부서", best_dept, f"{dept_df_stats.loc[dept_df_stats['부서']==best_dept, '건강도점수'].values[0]:.1f}점")
        with col3:
            st.metric("최저 부서", worst_dept, f"{dept_df_stats.loc[dept_df_stats['부서']==worst_dept, '건강도점수'].values[0]:.1f}점")
        with col4:
            high_risk_depts = len(dept_df_stats[dept_df_stats['건강도점수'] < 60])
            st.metric("위험 부서", f"{high_risk_depts}개")
        
        st.markdown("---")
        
        # Radar chart for department health
        categories = ['만족도', '유지율', '워라벨', '안정성']
        fig_radar = go.Figure()
        for _, dept_row in dept_df_stats.iterrows():
            values = [
                (dept_row['평균만족도'] / 4) * 100 if dept_row['평균만족도'] > 0 else 0,
                100 - dept_row['퇴직률'],
                100 - dept_row['야근비율'],
                min(100, dept_row['평균근속'] * 10) if dept_row['평균근속'] > 0 else 0
            ]
            fig_radar.add_trace(go.Scatterpolar(
                r=values, theta=categories, fill='toself', name=dept_row['부서']
            ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True, title="부서별 건강도 레이더 차트"
        )
        st.plotly_chart(fig_radar, use_container_width=True)
        
        # Heatmap for department metrics
        st.markdown("### 부서별 상세 지표")
        heatmap_data = dept_df_stats[['부서', '퇴직률', '평균만족도', '야근비율', '평균근속', '건강도점수']]
        heatmap_data_normalized = heatmap_data.copy()
        for col in ['퇴직률', '평균만족도', '야근비율', '평균근속', '건강도점수']:
            if col == '퇴직률' or col == '야근비율':
                heatmap_data_normalized[col] = 1 - (heatmap_data[col] / heatmap_data[col].max()) if heatmap_data[col].max() > 0 else 0
            else:
                heatmap_data_normalized[col] = heatmap_data[col] / heatmap_data[col].max() if heatmap_data[col].max() > 0 else 0
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=heatmap_data_normalized[['퇴직률', '평균만족도', '야근비율', '평균근속', '건강도점수']].values.T,
            x=heatmap_data['부서'].values,
            y=['퇴직률↓', '만족도↑', '야근↓', '근속↑', '건강도↑'],
            colorscale='RdYlGn',
            text=heatmap_data[['퇴직률', '평균만족도', '야근비율', '평균근속', '건강도점수']].values.T,
            texttemplate='%{text:.1f}',
            textfont={"size": 10},
            colorbar=dict(title="상대 점수")
        ))
        fig_heatmap.update_layout(title="부서별 지표 히트맵 (↑높을수록 좋음, ↓낮을수록 좋음)", height=400)
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Department summary table
        st.markdown("### 부서별 핵심 지표 비교")
        styled_dept_df = dept_df_stats.copy()
        styled_dept_df['퇴직률'] = styled_dept_df['퇴직률'].apply(lambda x: f"{x:.1f}%")
        styled_dept_df['평균만족도'] = styled_dept_df['평균만족도'].apply(lambda x: f"{x:.2f}/4.0" if x > 0 else "N/A")
        styled_dept_df['야근비율'] = styled_dept_df['야근비율'].apply(lambda x: f"{x:.1f}%")
        styled_dept_df['평균근속'] = styled_dept_df['평균근속'].apply(lambda x: f"{x:.1f}년" if x > 0 else "N/A")
        styled_dept_df['건강도점수'] = styled_dept_df['건강도점수'].apply(lambda x: f"{x:.1f}점")
        st.dataframe(styled_dept_df.sort_values(by='건강도점수', ascending=False), hide_index=True, use_container_width=True)
    else:
        st.warning("부서 데이터를 분석하려면 파일을 업로드하고 '⚙️ 컬럼 매핑' 메뉴에서 **'부서' 필드를 정확히 지정**해주세요.")

elif menu == "⚙️ 컬럼 매핑":
    st.title("⚙️ Column Mapping (컬럼 매핑)")
    if st.session_state.df is not None:
        df = st.session_state.df
        st.info("정형화된 대시보드(홈, 조기경보 등)가 올바르게 작동하도록 표준 필드와 실제 컬럼을 매핑해주세요.")
        
        cols = st.columns(2)
        mapping_items = list(default_mapping.items())
        mid_point = len(mapping_items) // 2
        
        new_mapping = {}
        with cols[0]:
            for korean, english in mapping_items[:mid_point]:
                current_selection = st.session_state.column_mapping.get(korean)
                try: index = list(df.columns).index(current_selection) if current_selection in df.columns else 0
                except ValueError: index = 0
                selected_col = st.selectbox(f"`{korean}` 필드", options=df.columns, index=index, key=f"map_{english}")
                new_mapping[korean] = selected_col
        with cols[1]:
            for korean, english in mapping_items[mid_point:]:
                current_selection = st.session_state.column_mapping.get(korean)
                try: index = list(df.columns).index(current_selection) if current_selection in df.columns else 0
                except ValueError: index = 0
                selected_col = st.selectbox(f"`{korean}` 필드", options=df.columns, index=index, key=f"map_{english}")
                new_mapping[korean] = selected_col
        
        if st.button("매핑 저장", use_container_width=True, type="primary"):
            st.session_state.column_mapping = new_mapping
            st.success("컬럼 매핑이 성공적으로 저장되었습니다!")
            st.rerun()
    else:
        st.info("📁 먼저 CSV 파일을 업로드해주세요.")

elif menu == "📊 커스텀 차트":
    st.title("📊 Custom Chart Builder (커스텀 차트)")
    if st.session_state.df is not None:
        df = st.session_state.df.copy()
        st.info("데이터에 포함된 모든 컬럼과 직접 만든 '계산 필드'를 사용하여 자유롭게 차트를 만들어보세요.")

        for field_name, formula in st.session_state.custom_fields.items():
            try: df[field_name] = df.eval(formula)
            except Exception: pass
        
        st.markdown("### 1. (선택) 계산된 필드 생성")
        with st.expander("새로운 필드를 계산하여 추가하기"):
            new_field_name = st.text_input("새 필드 이름 (예: ROI)")
            formula = st.text_input("계산 공식 (예: 월급여 / 총경력)", help=f"사용 가능 컬럼: {', '.join(df.columns)}")

            if st.button("계산 필드 추가/수정"):
                if new_field_name and formula:
                    try:
                        df.eval(formula)
                        st.session_state.custom_fields[new_field_name] = formula
                        st.success(f"'{new_field_name}' 필드가 추가/수정되었습니다.")
                        st.rerun()
                    except Exception as e: st.error(f"공식 오류: {e}")
                else: st.warning("필드 이름과 공식을 모두 입력해주세요.")
        
        if st.session_state.custom_fields:
            st.write("현재 커스텀 필드:")
            st.json(st.session_state.custom_fields)

        st.markdown("---")
        st.markdown("### 2. 차트 구성")
        chart_type = st.selectbox("차트 종류 선택", ["Bar Chart", "Scatter Plot", "Pie Chart", "Line Chart"])
        
        available_columns = list(df.columns)
        
        if chart_type == "Pie Chart":
            col_names = st.selectbox("레이블 (Names) 선택", available_columns)
            col_values = st.selectbox("값 (Values) 선택", available_columns)
            if st.button("파이 차트 생성", type="primary"):
                fig = px.pie(df, names=col_names, values=col_values, title=f"{col_values} by {col_names}")
                st.plotly_chart(fig, use_container_width=True)
        else:
            x_axis = st.selectbox("X축 선택", available_columns)
            y_axis = st.selectbox("Y축 선택", available_columns)
            color_axis = st.selectbox("색상 (Color) 기준 선택", [None] + available_columns)
            
            if st.button(f"{chart_type} 생성", type="primary"):
                try:
                    if chart_type == "Bar Chart": fig = px.bar(df, x=x_axis, y=y_axis, color=color_axis, title=f"{y_axis} by {x_axis}")
                    elif chart_type == "Scatter Plot": fig = px.scatter(df, x=x_axis, y=y_axis, color=color_axis, title=f"{y_axis} vs {x_axis}")
                    elif chart_type == "Line Chart": fig = px.line(df.sort_values(by=x_axis), x=x_axis, y=y_axis, color=color_axis, title=f"{y_axis} over {x_axis}")
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e: st.error(f"차트 생성 중 오류: {e}")
    else:
        st.info("📁 먼저 CSV 파일을 업로드해주세요.")

# 페이지 하단 정보
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; color: #666; font-size: 12px;'>
    HR Analytics Dashboard v1.0<br>
    © 2024 Your Company
</div>
""", unsafe_allow_html=True)