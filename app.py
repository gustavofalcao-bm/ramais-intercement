import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import pool
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from dotenv import load_dotenv
import base64

load_dotenv()

# ============================================================================
# CONFIGURAÇÕES - IDENTIDADE BASE TELCO
# ============================================================================

st.set_page_config(
    page_title="OSV Dashboard | Base Telco",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

COLORS = {
    'primary': '#1e3a5f',
    'secondary': '#5dade2',
    'accent': '#3498db',
    'success': '#4CAF50',
    'danger': '#E57373',
    'warning': '#FFB74D',
    'info': '#64B5F6',
    'dark_gray': '#616161'
}

# ============================================================================
# FUNÇÕES UTILITÁRIAS
# ============================================================================

def load_logo(variants):
    for v in variants:
        try:
            with open(v, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except:
            continue
    return None

def format_number(value):
    if pd.isna(value):
        return "0"
    return f"{int(value):,}".replace(',', '.')

def format_percentage(value):
    if pd.isna(value):
        return "0%"
    return f"{value:.2f}%"

# ============================================================================
# CSS ESTILIZADO
# ============================================================================

def aplicar_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    * {{ font-family: 'Inter', sans-serif; }}

    .stApp {{ 
        background: linear-gradient(135deg, #e8f4f8 0%, #d4e9f2 100%); 
    }}

    [data-testid="stSidebar"] {{ 
        background: rgba(30, 58, 95, 0.95) !important; 
        backdrop-filter: blur(20px);
    }}

    [data-testid="stSidebar"] * {{ color: white !important; }}

    .metric-card {{
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(20px);
        padding: 2rem 1.5rem;
        border-radius: 20px;
        border: 1px solid rgba(93, 173, 226, 0.2);
        box-shadow: 0 8px 32px rgba(30, 58, 95, 0.1);
        transition: all 0.4s ease;
        text-align: center;
    }}

    .metric-card:hover {{
        transform: translateY(-8px);
        box-shadow: 0 20px 60px rgba(93, 173, 226, 0.25);
    }}

    .metric-icon {{
        font-size: 2.5rem;
        margin-bottom: 0.8rem;
    }}

    .metric-value {{
        font-size: 2.3rem;
        font-weight: 900;
        margin: 0.5rem 0;
    }}

    .metric-label {{
        font-size: 0.75rem;
        color: {COLORS['dark_gray']};
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 700;
    }}

    .header-parallax {{
        background: linear-gradient(135deg, #1e3a5f 0%, #154360 25%, #5dade2 75%, #3498db 100%);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
    }}

    @keyframes gradientShift {{
        0%, 100% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
    }}
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# CONFIGURAÇÃO BANCO DE DADOS
# ============================================================================

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '10.211.216.242'),
    'database': os.getenv('DB_NAME', 'basedb'),
    'user': os.getenv('DB_USER', 'base'),
    'password': os.getenv('DB_PASSWORD', 'base2015'),
    'port': os.getenv('DB_PORT', '5432'),
}

QUERY_BY_COMPANY = """
WITH latest_records AS (
    SELECT DISTINCT ON (st.serviceid)
        st.serviceid,
        st.contactregstate,
        sl.bgname
    FROM osvsubscriberstatus st
    INNER JOIN osvsubscriberlist sl ON st.subscriberid = sl.id
    WHERE st.lastsync::timestamp >= NOW() - INTERVAL '1 hour'
    ORDER BY st.serviceid, st.lastsync::timestamp DESC
)
SELECT 
    bgname as empresa,
    COUNT(serviceid) as total_ramais,
    SUM(CASE WHEN contactregstate = 1 THEN 1 ELSE 0 END) as ramais_ativos,
    SUM(CASE WHEN contactregstate = 0 THEN 1 ELSE 0 END) as ramais_inativos,
    ROUND((SUM(CASE WHEN contactregstate = 1 THEN 1 ELSE 0 END)::numeric / NULLIF(COUNT(serviceid), 0) * 100), 2) as taxa_ativacao
FROM latest_records
GROUP BY bgname
ORDER BY total_ramais DESC
"""

# ============================================================================
# FUNÇÕES DE DADOS
# ============================================================================

@st.cache_resource
def get_connection_pool():
    try:
        return psycopg2.pool.SimpleConnectionPool(1, 10, **DB_CONFIG)
    except Exception as e:
        st.error(f"Erro ao criar pool: {e}")
        return None

@st.cache_data(ttl=300)
def get_company_summary():
    pool = get_connection_pool()
    if not pool:
        return pd.DataFrame()
    conn = pool.getconn()
    try:
        df = pd.read_sql_query(QUERY_BY_COMPANY, conn)
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
        return pd.DataFrame()
    finally:
        pool.putconn(conn)

# ============================================================================
# APLICAR CSS
# ============================================================================

aplicar_css()

# ============================================================================
# HEADER
# ============================================================================

logo_icon = load_logo(['image.jpg', 'BT-Icone.png', 'logo.png'])

st.markdown(f"""
<div class="header-parallax">
    <div style="display: flex; align-items: center; gap: 1.5rem;">
        {"<img src='data:image/png;base64," + logo_icon + "' style='height: 60px; filter: brightness(0) invert(1);'>" if logo_icon else "<div style='font-size: 2.5rem;'>📞</div>"}
        <div>
            <h1 style="color: white; font-size: 1.9rem; font-weight: 900; margin: 0;">OSV Dashboard</h1>
            <p style="color: #aed6f1; font-size: 0.9rem; margin: 0.3rem 0 0 0; font-weight: 600;">
                Monitoramento de Ramais • Base Telco
            </p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# BOTÃO ATUALIZAR
# ============================================================================

col_btn, col_space = st.columns([1, 5])
with col_btn:
    if st.button("🔄 Atualizar", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("##")

# ============================================================================
# CARREGAR DADOS
# ============================================================================

with st.spinner("Carregando dados..."):
    df_companies = get_company_summary()

if df_companies.empty:
    st.error("❌ Nenhum dado disponível")
    st.stop()

# ============================================================================
# MÉTRICAS
# ============================================================================

total_ramais = int(df_companies['total_ramais'].sum())
total_ativos = int(df_companies['ramais_ativos'].sum())
total_inativos = int(df_companies['ramais_inativos'].sum())
taxa_geral = round((total_ativos / total_ramais * 100), 2) if total_ramais > 0 else 0

st.subheader("📊 Indicadores Gerais (Última Hora)")

cols = st.columns(4)

cards = [
    ("📊", "Total Ramais", total_ramais, COLORS['primary']),
    ("✅", "Registrados", total_ativos, COLORS['success']),
    ("❌", "Não Registrados", total_inativos, COLORS['danger']),
    ("📈", "Taxa de Registro", f"{taxa_geral}%", COLORS['accent'])
]

for i, (icon, label, value, cor) in enumerate(cards):
    with cols[i]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon" style="color: {cor}">{icon}</div>
            <div class="metric-value" style="color: {cor}">{value if isinstance(value, str) else format_number(value)}</div>
            <div class="metric-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.info(f"**Total**: {format_number(total_ramais)} ramais | **Registrados**: {format_number(total_ativos)} ({taxa_geral}%) | **Não Registrados**: {format_number(total_inativos)}")

st.markdown("---")

# ============================================================================
# GRÁFICOS
# ============================================================================

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("### 📈 Top 10 Empresas")
    top10 = df_companies.head(10).copy()

    fig_bar = px.bar(
        top10, 
        x='empresa', 
        y=['ramais_ativos', 'ramais_inativos'],
        title='Registrados vs Não Registrados',
        color_discrete_map={
            'ramais_ativos': COLORS['accent'],
            'ramais_inativos': '#aed6f1'
        },
        barmode='stack'
    )
    fig_bar.update_layout(
        xaxis_tickangle=-45,
        height=400,
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_chart2:
    st.markdown("### 🥧 Distribuição por Empresa")

    fig_pie = px.pie(
        top10, 
        values='total_ramais', 
        names='empresa',
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.Blues_r
    )
    fig_pie.update_traces(
        textposition='inside',
        textinfo='percent+label'
    )
    fig_pie.update_layout(
        height=400,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("---")

# ============================================================================
# TABELA
# ============================================================================

st.subheader("📋 Detalhamento por Empresa")

col_search, col_filter = st.columns([3, 1])

with col_search:
    search_term = st.text_input("🔍 Buscar empresa", placeholder="Digite o nome...")

with col_filter:
    min_ramais = st.number_input("Min. Ramais", min_value=0, value=0, step=100)

df_display = df_companies.copy()
if search_term:
    df_display = df_display[df_display['empresa'].str.contains(search_term, case=False, na=False)]
if min_ramais > 0:
    df_display = df_display[df_display['total_ramais'] >= min_ramais]

df_formatted = df_display.copy()
df_formatted['total_ramais'] = df_formatted['total_ramais'].apply(format_number)
df_formatted['ramais_ativos'] = df_formatted['ramais_ativos'].apply(format_number)
df_formatted['ramais_inativos'] = df_formatted['ramais_inativos'].apply(format_number)
df_formatted['taxa_ativacao'] = df_formatted['taxa_ativacao'].apply(format_percentage)
df_formatted.columns = ['Empresa', 'Total', 'Registrados', 'Não Registrados', 'Taxa (%)']

st.dataframe(df_formatted, use_container_width=True, hide_index=True, height=400)

col_stats, col_download = st.columns([3, 1])
with col_stats:
    st.caption(f"📊 Exibindo {len(df_display)} de {len(df_companies)} empresas")
with col_download:
    csv = df_companies.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        "📥 Baixar CSV",
        csv,
        f"osv_ramais_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv",
        use_container_width=True
    )

# ============================================================================
# RODAPÉ
# ============================================================================

st.markdown("---")
st.markdown(f"<p style='text-align:center; color:#7f8c8d; font-size:0.85rem;'>Base Telco © {datetime.now().year} • Todos os direitos reservados</p>", unsafe_allow_html=True)
