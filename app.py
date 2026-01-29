import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import pool
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

st.set_page_config(
    page_title="Ramais Intercement | Base Telco",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="collapsed"
)

COLORS = {
    'primary': '#1e3a5f',
    'secondary': '#5dade2',
    'accent': '#3498db',
    'success': '#4CAF50',
    'danger': '#E57373'
}

# ============================================================================
# CSS
# ============================================================================

def aplicar_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    * {{ font-family: 'Inter', sans-serif; }}

    .stApp {{ 
        background: linear-gradient(135deg, #e8f4f8 0%, #d4e9f2 100%); 
    }}

    .header-intercement {{
        background: linear-gradient(135deg, #1e3a5f 0%, #3498db 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
    }}

    .metric-card {{
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(20px);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid rgba(93, 173, 226, 0.2);
        box-shadow: 0 8px 32px rgba(30, 58, 95, 0.1);
        transition: all 0.4s ease;
        text-align: center;
    }}

    .metric-card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 15px 50px rgba(93, 173, 226, 0.2);
    }}

    .metric-icon {{
        font-size: 2.2rem;
        margin-bottom: 0.5rem;
    }}

    .metric-value {{
        font-size: 2rem;
        font-weight: 900;
        margin: 0.3rem 0;
    }}

    .metric-label {{
        font-size: 0.7rem;
        color: {COLORS['primary']};
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 700;
    }}
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# SPINNER PREMIUM
# ============================================================================

def show_loading():
    return """
    <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100vh; 
                background: rgba(30, 58, 95, 0.97); display: flex; 
                flex-direction: column; align-items: center; 
                justify-content: center; z-index: 9999;">
        <div style="position: relative; width: 120px; height: 120px;">
            <div style="position: absolute; width: 120px; height: 120px; 
                       border: 8px solid rgba(93, 173, 226, 0.1); 
                       border-top-color: #5dade2; border-radius: 50%; 
                       animation: spin 1s linear infinite;"></div>
            <div style="position: absolute; top: 50%; left: 50%; 
                       transform: translate(-50%, -50%); font-size: 2.5rem;">📞</div>
        </div>
        <div style="margin-top: 2rem; font-size: 1.5rem; font-weight: 900; 
                   color: white; text-transform: uppercase; letter-spacing: 2px;">
            Carregando Ramais
        </div>
    </div>
    <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
    """

# ============================================================================
# FUNÇÃO PARA NORMALIZAR BONAME
# ============================================================================

def normalizar_boname(nome):
    """Substitui _ por espaço"""
    if pd.isna(nome):
        return ""
    return str(nome).replace('_', ' ')

# ============================================================================
# BANCO DE DADOS
# ============================================================================

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '10.211.216.242'),
    'database': os.getenv('DB_NAME', 'basedb'),
    'user': os.getenv('DB_USER', 'base'),
    'password': os.getenv('DB_PASSWORD', 'base2015'),
    'port': os.getenv('DB_PORT', '5432'),
}

# Query: Garantir ramais únicos (1 por serviceid)
QUERY_INTERCEMENT = """
WITH latest_records AS (
    SELECT DISTINCT ON (st.serviceid)
        st.serviceid,
        sl.boname,
        sl.bglinename,
        st.contactregstate,
        st.lastsync
    FROM osvsubscriberstatus st
    INNER JOIN osvsubscriberlist sl ON st.subscriberid = sl.id
    WHERE sl.bgname ILIKE '%intercement%'
        AND st.lastsync::timestamp >= NOW() - INTERVAL '24 hours'
    ORDER BY st.serviceid, st.lastsync::timestamp DESC
)
SELECT 
    serviceid,
    boname,
    bglinename,
    CASE 
        WHEN contactregstate = 1 THEN 'Registrado'
        ELSE 'Não Registrado'
    END as status,
    lastsync::timestamp as ultima_sincronizacao
FROM latest_records
ORDER BY boname, serviceid
"""

# ============================================================================
# FUNÇÕES DE DADOS
# ============================================================================

@st.cache_resource
def get_connection_pool():
    try:
        return psycopg2.pool.SimpleConnectionPool(1, 5, **DB_CONFIG)
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")
        return None

@st.cache_data(ttl=300)
def get_ramais_intercement():
    pool = get_connection_pool()
    if not pool:
        return pd.DataFrame()
    conn = pool.getconn()
    try:
        df = pd.read_sql_query(QUERY_INTERCEMENT, conn)

        # Normalizar boname (substituir _ por espaço)
        if not df.empty and 'boname' in df.columns:
            df['boname'] = df['boname'].apply(normalizar_boname)

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

st.markdown("""
<div class="header-intercement">
    <h1 style="color: white; font-size: 2rem; font-weight: 900; margin: 0;">
        📞 Ramais Intercement
    </h1>
    <p style="color: #aed6f1; font-size: 0.95rem; margin: 0.5rem 0 0 0; font-weight: 600;">
        Monitoramento em Tempo Real • Base Telco
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# BOTÃO ATUALIZAR
# ============================================================================

col_btn, col_space = st.columns([1, 4])
with col_btn:
    if st.button("🔄 Atualizar Dados", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ============================================================================
# LOADING
# ============================================================================

loading_placeholder = st.empty()
loading_placeholder.markdown(show_loading(), unsafe_allow_html=True)

try:
    df_ramais = get_ramais_intercement()
    loading_placeholder.empty()
except Exception as e:
    loading_placeholder.empty()
    st.error(f"❌ Erro ao carregar dados: {e}")
    st.stop()

# ============================================================================
# CARDS DE MÉTRICAS (NO TOPO)
# ============================================================================

if not df_ramais.empty:
    # Calcular totais
    total = len(df_ramais)
    registrados = len(df_ramais[df_ramais['status'] == 'Registrado'])
    nao_registrados = len(df_ramais[df_ramais['status'] == 'Não Registrado'])
    taxa = round((registrados / total * 100), 2) if total > 0 else 0

    # Exibir cards
    cols = st.columns(4)

    cards = [
        ("📊", "Total de Ramais", total, COLORS['primary']),
        ("✅", "Registrados", registrados, COLORS['success']),
        ("❌", "Não Registrados", nao_registrados, COLORS['danger']),
        ("📈", "Taxa de Registro", f"{taxa}%", COLORS['accent'])
    ]

    for i, (icon, label, value, cor) in enumerate(cards):
        with cols[i]:
            valor_formatado = f"{value:,}".replace(',', '.') if isinstance(value, int) else value
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-icon" style="color: {cor}">{icon}</div>
                <div class="metric-value" style="color: {cor}">{valor_formatado}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

# ============================================================================
# TABELA DE RAMAIS
# ============================================================================

if not df_ramais.empty:
    st.markdown("### 📋 Lista de Ramais")

    # Filtros - ADICIONADO FILTRO POR UNIDADE
    col_unidade, col_status, col_search = st.columns([2, 1, 2])

    with col_unidade:
        unidades_disponiveis = ['Todas'] + sorted(df_ramais['boname'].dropna().unique().tolist())
        unidade_filter = st.selectbox(
            "🏢 Filtrar por Unidade",
            options=unidades_disponiveis,
            key='unidade_filter'
        )

    with col_status:
        status_options = ['Todos', 'Registrado', 'Não Registrado']
        status_filter = st.selectbox(
            "📊 Status",
            options=status_options,
            key='status_filter'
        )

    with col_search:
        search_term = st.text_input(
            "🔍 Buscar usuário ou ramal",
            placeholder="Digite para buscar...",
            key='search_ramais'
        )

    # Aplicar filtros
    df_filtered = df_ramais.copy()

    if unidade_filter != 'Todas':
        df_filtered = df_filtered[df_filtered['boname'] == unidade_filter]

    if status_filter != 'Todos':
        df_filtered = df_filtered[df_filtered['status'] == status_filter]

    if search_term:
        df_filtered = df_filtered[
            df_filtered['bglinename'].astype(str).str.contains(search_term, case=False, na=False) |
            df_filtered['serviceid'].astype(str).str.contains(search_term, case=False, na=False)
        ]

    # Preparar para exibição
    df_display = df_filtered.copy()
    df_display = df_display[['boname', 'bglinename', 'serviceid', 'status']]
    df_display.columns = ['Unidade', 'Usuário', 'Ramal', 'Status']

    # Exibir tabela
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        height=550,
        column_config={
            "Status": st.column_config.TextColumn(
                "Status",
                help="Status de registro do ramal"
            )
        }
    )

    # Informações da filtragem
    st.caption(f"📊 Exibindo {len(df_filtered):,} de {len(df_ramais):,} ramais".replace(',', '.'))

    # Download
    st.markdown("##")
    col_download, col_space = st.columns([1, 3])
    with col_download:
        csv = df_filtered.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "📥 Baixar CSV Completo",
            csv,
            f"intercement_ramais_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            use_container_width=True
        )

else:
    st.warning("⚠️ Nenhum ramal encontrado para Intercement nas últimas 24 horas")

# ============================================================================
# RODAPÉ
# ============================================================================

st.markdown("---")
st.markdown(f"""
<p style='text-align:center; color:#7f8c8d; font-size:0.85rem;'>
    Base Telco © {datetime.now().year} • Dashboard Intercement
</p>
""", unsafe_allow_html=True)
