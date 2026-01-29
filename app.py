import streamlit as st
import pandas as pd
import psycopg2
from psycopg2 import pool
from datetime import datetime

# ============================================================================
# CONFIGURAÇÕES
# ============================================================================

st.set_page_config(
    page_title="Ramais Intercement",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Esconder menu hamburger e footer do Streamlit
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

COLORS = {
    'primary': '#1e3a5f',
    'secondary': '#5dade2',
    'accent': '#3498db',
    'success': '#4CAF50',
    'danger': '#E57373'
}

# ============================================================================
# CSS COMPLETO
# ============================================================================

def aplicar_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    * {{ font-family: 'Inter', sans-serif; }}

    .stApp {{ 
        background: linear-gradient(135deg, #e8f4f8 0%, #d4e9f2 100%); 
    }}

    /* Esconder botões de ação do Streamlit */
    .stActionButton {{ display: none; }}
    button[kind="header"] {{ display: none; }}

    .header-intercement {{
        background: linear-gradient(135deg, #1e3a5f 0%, #3498db 100%);
        padding: 2.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(30, 58, 95, 0.2);
    }}

    .metric-card {{
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(20px);
        padding: 1.8rem;
        border-radius: 18px;
        border: 1px solid rgba(93, 173, 226, 0.2);
        box-shadow: 0 8px 32px rgba(30, 58, 95, 0.12);
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        text-align: center;
    }}

    .metric-card:hover {{
        transform: translateY(-8px);
        box-shadow: 0 20px 60px rgba(93, 173, 226, 0.25);
    }}

    .metric-icon {{
        font-size: 2.5rem;
        margin-bottom: 0.6rem;
        filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
    }}

    .metric-value {{
        font-size: 2.2rem;
        font-weight: 900;
        margin: 0.4rem 0;
        letter-spacing: -0.5px;
    }}

    .metric-label {{
        font-size: 0.7rem;
        color: {COLORS['primary']};
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 700;
        opacity: 0.8;
    }}

    /* Estilo da tabela */
    [data-testid="stDataFrame"] {{
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(30, 58, 95, 0.1);
    }}
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# SPINNER PREMIUM
# ============================================================================

def show_loading():
    return """
    <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100vh; 
                background: rgba(30, 58, 95, 0.98); display: flex; 
                flex-direction: column; align-items: center; 
                justify-content: center; z-index: 9999;
                backdrop-filter: blur(10px);">
        <div style="position: relative; width: 140px; height: 140px;">
            <div style="position: absolute; width: 140px; height: 140px; 
                       border: 10px solid rgba(93, 173, 226, 0.15); 
                       border-top-color: #5dade2; border-radius: 50%; 
                       animation: spin 1.2s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;"></div>
            <div style="position: absolute; top: 20px; left: 20px; 
                       width: 100px; height: 100px; 
                       border: 8px solid rgba(52, 152, 219, 0.15); 
                       border-bottom-color: #3498db; border-radius: 50%; 
                       animation: spin-reverse 1.8s linear infinite;"></div>
            <div style="position: absolute; top: 50%; left: 50%; 
                       transform: translate(-50%, -50%); font-size: 3rem;
                       filter: drop-shadow(0 0 15px rgba(93, 173, 226, 0.6));">📞</div>
        </div>
        <div style="margin-top: 2.5rem; font-size: 1.6rem; font-weight: 900; 
                   color: white; text-transform: uppercase; letter-spacing: 3px;
                   animation: pulse 1.5s ease-in-out infinite;">
            Carregando Dados
        </div>
        <div style="margin-top: 1.5rem; width: 260px; height: 6px; 
                   background: rgba(255, 255, 255, 0.1); border-radius: 4px; overflow: hidden;
                   box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);">
            <div style="width: 100%; height: 100%; 
                       background: linear-gradient(90deg, #5dade2, #3498db, #5dade2); 
                       background-size: 200% 100%; 
                       animation: progress 2s ease-in-out infinite;"></div>
        </div>
    </div>
    <style>
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes spin-reverse {
            0% { transform: rotate(360deg); }
            100% { transform: rotate(0deg); }
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        @keyframes progress {
            0% { background-position: 0% 50%; }
            100% { background-position: 200% 50%; }
        }
    </style>
    """

# ============================================================================
# FUNÇÃO PARA NORMALIZAR BONAME
# ============================================================================

def normalizar_boname(nome):
    if pd.isna(nome):
        return ""
    return str(nome).replace('_', ' ')

# ============================================================================
# BANCO DE DADOS - CONFIGURAÇÃO SEGURA (LGPD)
# ============================================================================

def get_db_config():
    """
    Busca credenciais APENAS do st.secrets
    SEM fallback que exponha senhas no código
    Conforme LGPD - Art. 46 (Segurança da Informação)
    """
    try:
        return {
            'host': st.secrets['DB_HOST'],
            'database': st.secrets['DB_NAME'],
            'user': st.secrets['DB_USER'],
            'password': st.secrets['DB_PASSWORD'],
            'port': st.secrets['DB_PORT'],
            'connect_timeout': 10,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5
        }
    except KeyError as e:
        st.error(f"""
        🔐 **Configuração de Secrets Ausente**

        A variável {str(e)} não foi configurada no Streamlit.

        **Como configurar:**
        1. Vá em Settings → Secrets
        2. Adicione as variáveis necessárias
        """)
        st.stop()

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
# FUNÇÕES DE DADOS - COM MELHOR TRATAMENTO DE ERROS
# ============================================================================

@st.cache_resource(ttl=600)
def get_connection_pool():
    """Cria pool de conexões PostgreSQL com tratamento robusto de erros"""
    db_config = get_db_config()

    try:
        connection_pool = psycopg2.pool.SimpleConnectionPool(1, 3, **db_config)

        # Testar se a conexão funciona
        test_conn = connection_pool.getconn()
        test_conn.close()
        connection_pool.putconn(test_conn)

        return connection_pool

    except psycopg2.OperationalError as e:
        error_msg = str(e).lower()

        if "timeout" in error_msg or "timed out" in error_msg:
            st.error("""
            ⚠️ **Tempo de Conexão Esgotado**

            O servidor de banco de dados não respondeu a tempo.

            **Possíveis causas:**
            - Servidor em manutenção
            - Firewall bloqueando conexão
            - Rede instável

            **Solução:**
            Aguarde alguns minutos e recarregue a página.
            """)
        elif "could not connect" in error_msg or "connection refused" in error_msg:
            st.error("""
            ❌ **Servidor Inacessível**

            Não foi possível estabelecer conexão com o banco de dados.

            **Ação necessária:**
            Entre em contato com o suporte técnico da Base Telco.
            """)
        elif "authentication failed" in error_msg or "password" in error_msg:
            st.error("""
            🔐 **Erro de Autenticação**

            As credenciais do banco de dados estão incorretas.

            **Ação necessária:**
            Verifique as configurações em Settings → Secrets.
            """)
        else:
            st.error(f"""
            ❌ **Erro de Conexão**

            Detalhes técnicos: {str(e)[:200]}

            Entre em contato com o suporte.
            """)
        return None

    except Exception as e:
        st.error(f"""
        ❌ **Erro Inesperado**

        Ocorreu um erro ao conectar ao banco de dados.

        Detalhes: {str(e)[:200]}
        """)
        return None

@st.cache_data(ttl=300)
def get_ramais_intercement():
    """Busca ramais da Intercement com tratamento de erros"""
    pool = get_connection_pool()
    if not pool:
        return pd.DataFrame()

    conn = None
    try:
        conn = pool.getconn()
        df = pd.read_sql_query(QUERY_INTERCEMENT, conn)

        if not df.empty and 'boname' in df.columns:
            df['boname'] = df['boname'].apply(normalizar_boname)

        return df

    except psycopg2.Error as e:
        st.error(f"""
        ❌ **Erro ao Buscar Dados**

        Não foi possível recuperar os dados dos ramais.

        Detalhes: {str(e)[:200]}
        """)
        return pd.DataFrame()

    except Exception as e:
        st.error(f"❌ Erro inesperado ao processar dados: {str(e)[:200]}")
        return pd.DataFrame()

    finally:
        if conn:
            try:
                pool.putconn(conn)
            except:
                pass

# ============================================================================
# APLICAR CSS
# ============================================================================

aplicar_css()

# ============================================================================
# HEADER
# ============================================================================

st.markdown("""
<div class="header-intercement">
    <h1 style="color: white; font-size: 2.2rem; font-weight: 900; margin: 0; letter-spacing: 0.5px;">
        📞 Ramais Intercement
    </h1>
    <p style="color: #aed6f1; font-size: 1rem; margin: 0.6rem 0 0 0; font-weight: 600; opacity: 0.95;">
        Monitoramento em Tempo Real
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# LOADING COM SPINNER PREMIUM
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
# CARDS DE MÉTRICAS
# ============================================================================

if not df_ramais.empty:
    total = len(df_ramais)
    registrados = len(df_ramais[df_ramais['status'] == 'Registrado'])
    nao_registrados = len(df_ramais[df_ramais['status'] == 'Não Registrado'])
    taxa = round((registrados / total * 100), 2) if total > 0 else 0

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

    st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# TABELA DE RAMAIS
# ============================================================================

if not df_ramais.empty:
    st.markdown("### 📋 Lista de Ramais")

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
            "🔍 Buscar",
            placeholder="Usuário ou ramal...",
            key='search_ramais'
        )

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

    df_display = df_filtered.copy()
    df_display = df_display[['boname', 'bglinename', 'serviceid', 'status']]
    df_display.columns = ['Unidade', 'Usuário', 'Ramal', 'Status']

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

    st.caption(f"📊 Exibindo {len(df_filtered):,} de {len(df_ramais):,} ramais".replace(',', '.'))

    st.markdown("<br>", unsafe_allow_html=True)

    csv = df_filtered.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        "📥 Baixar Dados (CSV)",
        csv,
        f"intercement_ramais_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv",
        use_container_width=False
    )

else:
    st.warning("⚠️ Nenhum dado disponível no momento. Por favor, tente novamente mais tarde.")

# ============================================================================
# RODAPÉ - LGPD
# ============================================================================

st.markdown("---")
st.markdown(f"""
<p style='text-align:center; color:#95a5a6; font-size:0.8rem; margin-top: 2rem;'>
    Base Telco © {datetime.now().year} • Atualizado automaticamente<br>
    <small style='font-size:0.7rem; opacity:0.7;'>
        Dados processados conforme LGPD (Lei 13.709/2018)
    </small>
</p>
""", unsafe_allow_html=True)
