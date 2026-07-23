
import streamlit as st
import pandas as pd
import numpy as np
import random
import re

# 1. CONFIGURAÇÃO DE PÁGINA
st.set_page_config(
    page_title="Stock Control - Sistema de Gestão por Peças",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# BLOCO 1: CAMADA DE DADOS E ESTADO DO SISTEMA
# ==========================================

ESTRUTURA_CD = {
    "Rua 01": {"tipo": "Morta", "cols_impar": [], "cols_par": []},
    "Rua 02": {"tipo": "Misto_Transicao", "cols_impar": list(range(21, 94, 2)), "cols_par": list(range(22, 103, 2)) + list(range(103, 141))},
    "Rua 03": {"tipo": "P", "cols_impar": list(range(1, 101, 2)), "cols_par": list(range(2, 102, 2))},
    "Rua 04": {"tipo": "Misto_Lado", "cols_impar": list(range(1, 101, 2)), "cols_par": list(range(2, 102, 2))},
    "Rua 05": {"tipo": "M", "cols_impar": list(range(21, 101, 2)), "cols_par": list(range(22, 103, 2))},
    "Rua 06": {"tipo": "M", "cols_impar": list(range(1, 82, 2)), "cols_par": list(range(2, 83, 2))},
    "Rua 07": {"tipo": "M", "cols_impar": list(range(59, 140, 2)), "cols_par": list(range(60, 141, 2))},
    "Rua 08": {"tipo": "M", "cols_impar": list(range(1, 82, 2)), "cols_par": list(range(2, 83, 2))},
    "Rua 09": {"tipo": "M", "cols_impar": list(range(21, 104, 2)), "cols_par": list(range(22, 101, 2))},
    "Rua 10": {"tipo": "G", "cols_impar": list(range(21, 104, 2)), "cols_par": list(range(22, 103, 2))},
    "Rua 11": {"tipo": "G_Unilateral", "cols_impar": [], "cols_par": list(range(22, 95, 2))},
    "Rua 12": {"tipo": "Inexistente", "cols_impar": [], "cols_par": []},
    "Rua 13": {"tipo": "Inexistente", "cols_impar": [], "cols_par": []},
    "Rua 14": {"tipo": "Especial_Rua_14", "cols_impar": [], "cols_par": [], "cols_seq": list(range(1, 32)) + list(range(42, 49))},
    "Rua 15": {"tipo": "Misto_Lado_15", "cols_impar": list(range(1, 88, 2)), "cols_par": list(range(2, 139, 2))},
    "Rua 16": {"tipo": "G", "metal": [43], "cols_impar": list(range(1, 101, 2)), "cols_par": list(range(2, 102, 2))},
    "Rua 17": {"tipo": "G", "metal": [101, 102, 103, 104, 105, 106], "cols_impar": list(range(1, 115, 2)), "cols_par": list(range(2, 116, 2))},
    "Rua 18": {"tipo": "M", "metal": [35, 36, 37, 38, 39, 40], "cols_impar": list(range(1, 81, 2)), "cols_par": list(range(2, 82, 2))},
    "Rua 19": {"tipo": "P", "metal": [101, 102, 103, 104, 105, 106], "cols_impar": list(range(1, 115, 2)), "cols_par": list(range(2, 116, 2))},
    "Rua 20": {"tipo": "Aramado_P_Seq_20", "metal_cols": [35, 37, 39], "cols_impar": [], "cols_par": [], "cols_seq": list(range(35, 138, 2))},
    "Rua 21": {"tipo": "Metal_Seq_21", "cols_impar": [], "cols_par": [], "cols_seq": list(range(1, 78, 2))}
}

NIVEIS_G = ["B", "E", "H", "K", "N", "Q", "T"]
NIVEIS_M = ["B", "D", "E", "G", "H", "J", "K", "M", "N", "P", "Q", "S", "T", "V"]
NIVEIS_P = ["B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V"]
NIVEIS_METAL_5 = ["B", "C", "D", "E", "F"]

# ==========================================
# MOTOR DE CAPACIDADE POR VOLUME (cm³)
# ==========================================
# Volumes unitários REAIS de cada casulo, conforme especificação física do CD.

VOLUME_ARAMADO_P = 16000
VOLUME_ARAMADO_M = 24000
VOLUME_ARAMADO_G = 48000

# Rua 14 - Setor 2 (Metal Profundo, colunas 24-31)
VOLUME_METAL_PROFUNDO = {"F": 162000, "comum": 216000}

# Rua 14 - Setor 4 (Metal Raso, colunas 42-48) e infiltrações de metal nas
# Ruas 16-20 e Rua 21 (mesmo padrão de 5 níveis B-F). OBS: a largura das
# infiltrações das Ruas 16-20/21 não veio especificada no documento — estou
# assumindo a mesma cubagem do Metal Raso da Rua 14 até você confirmar.
VOLUME_METAL_RASO = {"F": 81000, "comum": 108000}

# Tamanhos de peça (classificação que você definiu) com volume médio estimado
# (cm³) por peça dobrada. ⚠️ ESTES VOLUMES SÃO UMA ESTIMATIVA MINHA — ajuste
# aqui se tiver a medida real, é o único lugar que precisa mudar.
TAMANHOS_PECA = {
    "PP": {"nome": "PP - Body/Top/Biquíni", "volume_cm3": 150, "exemplos": "Body, top, biquíni, cropped, underwear"},
    "P":  {"nome": "P - Camiseta/Polo",      "volume_cm3": 250, "exemplos": "Camiseta, polo, regata"},
    "M":  {"nome": "M - Camisa/Suéter/Sarja","volume_cm3": 400, "exemplos": "Camisa, suéter, calça sarja, calça tecido"},
    "G":  {"nome": "G - Jeans/Corta-Vento",  "volume_cm3": 700, "exemplos": "Calça jeans, corta-vento, blusa manga longa, moletom"},
    "GG": {"nome": "GG - Jaqueta/Casaco",    "volume_cm3": 2500, "exemplos": "Bomber, jaqueta pesada, casaco (só madeira/metal)"},
}

# Marca de estação: tag que acompanha a peça (não define mais um "modo global"
# do sistema — várias estações convivem ao mesmo tempo no estoque real).
ESTACOES_PECA = ["Verão", "Inverno", "Meia-Estação"]

# Tamanho de referência usado para estimar "quantas peças cabem" na tela do
# Visualizador (o cálculo de ocupação real, porém, é sempre feito por volume,
# somando o mix real de tamanhos que está em cada casulo).
TAMANHO_REFERENCIA_POR_TIPO = {
    "aramado_P": "PP",
    "aramado_M": "M",
    "aramado_G": "G",
    "madeira": "GG",
    "metal": "GG",
}

def obter_chave_casulo(rua_nome, lado, coluna, nivel):
    try:
        col_int = int(coluna)
    except:
        col_int = 1
    return f"{rua_nome}|{lado}|{col_int:03d}|{str(nivel).upper()}"

def obter_chave_estoque(tamanho, estacao):
    return f"{tamanho}|{estacao}"

def obter_especificacao_casulo(rua_nome, coluna, lado="impar"):
    """
    Retorna a especificação física real de uma coluna/lado de uma rua:
    níveis válidos, tipo estrutural (aramado_P/aramado_M/aramado_G/madeira/metal),
    descrição e volume unitário (cm³) de cada nível.
    """
    try:
        col = int(coluna)
    except (ValueError, TypeError):
        col = 1

    config = ESTRUTURA_CD.get(rua_nome, {})
    tipo = config.get("tipo", "")
    vazio = {"niveis": [], "tipo_estrutural": None, "tipo_desc": "Inexistente", "volumes": {}}

    if tipo == "Inexistente":
        return vazio

    is_metal = False
    if "metal" in config and col in config["metal"]:
        is_metal = True
    if "metal_cols" in config and col in config["metal_cols"]:
        is_metal = True

    if is_metal:
        vols = {n: (VOLUME_METAL_RASO["F"] if n == "F" else VOLUME_METAL_RASO["comum"]) for n in NIVEIS_METAL_5}
        return {"niveis": NIVEIS_METAL_5, "tipo_estrutural": "metal", "tipo_desc": "Metal Infiltrado", "volumes": vols}

    if tipo in ("Aramado_P_Seq_20", "P"):
        vols = {n: VOLUME_ARAMADO_P for n in NIVEIS_P}
        return {"niveis": NIVEIS_P, "tipo_estrutural": "aramado_P", "tipo_desc": "Pequeno (P)", "volumes": vols}
    elif tipo == "G":
        vols = {n: VOLUME_ARAMADO_G for n in NIVEIS_G}
        return {"niveis": NIVEIS_G, "tipo_estrutural": "aramado_G", "tipo_desc": "Grande (G)", "volumes": vols}
    elif tipo == "M":
        vols = {n: VOLUME_ARAMADO_M for n in NIVEIS_M}
        return {"niveis": NIVEIS_M, "tipo_estrutural": "aramado_M", "tipo_desc": "Médio (M)", "volumes": vols}
    elif tipo == "G_Unilateral":
        if lado == "par":
            vols = {n: VOLUME_ARAMADO_G for n in NIVEIS_G}
            return {"niveis": NIVEIS_G, "tipo_estrutural": "aramado_G", "tipo_desc": "Grande (G) - Unilateral", "volumes": vols}
        else:
            return vazio
    elif tipo == "Metal_Seq_21":
        vols = {n: (VOLUME_METAL_RASO["F"] if n == "F" else VOLUME_METAL_RASO["comum"]) for n in NIVEIS_METAL_5}
        return {"niveis": NIVEIS_METAL_5, "tipo_estrutural": "metal", "tipo_desc": "Metal Sequencial Rua 21", "volumes": vols}
    elif tipo == "Especial_Rua_14":
        if 1 <= col <= 23:
            niveis_14 = ["D", "G", "J", "M", "P"]
            if col in (1, 4, 9):
                v_comum, v_p = 303360, 376320
            elif col == 6:
                v_comum, v_p = 223965, 277830
            elif col == 19:
                v_comum, v_p = 507180, 629160
            elif col == 21:
                v_comum, v_p = 274920, 341040
            else:
                v_comum, v_p = 355500, 441000
            vols = {n: (v_p if n == "P" else v_comum) for n in niveis_14}
            return {"niveis": niveis_14, "tipo_estrutural": "madeira", "tipo_desc": "Rua 14 - Madeira Gigante", "volumes": vols}
        elif 24 <= col <= 31:
            niveis_14 = ["B", "C", "D", "E", "F"]
            vols = {n: (VOLUME_METAL_PROFUNDO["F"] if n == "F" else VOLUME_METAL_PROFUNDO["comum"]) for n in niveis_14}
            return {"niveis": niveis_14, "tipo_estrutural": "metal", "tipo_desc": "Rua 14 - Metal Profundo", "volumes": vols}
        elif 42 <= col <= 48:
            niveis_14 = ["B", "C", "D", "E", "F"]
            vols = {n: (VOLUME_METAL_RASO["F"] if n == "F" else VOLUME_METAL_RASO["comum"]) for n in niveis_14}
            return {"niveis": niveis_14, "tipo_estrutural": "metal", "tipo_desc": "Rua 14 - Metal Raso", "volumes": vols}
        else:
            return vazio
    elif tipo == "Misto_Transicao":
        if col < 103:
            vols = {n: VOLUME_ARAMADO_P for n in NIVEIS_P}
            return {"niveis": NIVEIS_P, "tipo_estrutural": "aramado_P", "tipo_desc": "Pequeno (P)", "volumes": vols}
        else:
            vols = {n: VOLUME_ARAMADO_G for n in NIVEIS_G}
            return {"niveis": NIVEIS_G, "tipo_estrutural": "aramado_G", "tipo_desc": "Grande (G)", "volumes": vols}
    elif tipo == "Misto_Lado":
        if lado == "par":
            vols = {n: VOLUME_ARAMADO_G for n in NIVEIS_G}
            return {"niveis": NIVEIS_G, "tipo_estrutural": "aramado_G", "tipo_desc": "Grande (G)", "volumes": vols}
        else:
            vols = {n: VOLUME_ARAMADO_P for n in NIVEIS_P}
            return {"niveis": NIVEIS_P, "tipo_estrutural": "aramado_P", "tipo_desc": "Pequeno (P)", "volumes": vols}
    elif tipo == "Misto_Lado_15":
        if lado == "par":
            vols = {n: VOLUME_ARAMADO_M for n in NIVEIS_M}
            return {"niveis": NIVEIS_M, "tipo_estrutural": "aramado_M", "tipo_desc": "Médio (M)", "volumes": vols}
        else:
            vols = {n: VOLUME_ARAMADO_G for n in NIVEIS_G}
            return {"niveis": NIVEIS_G, "tipo_estrutural": "aramado_G", "tipo_desc": "Grande (G)", "volumes": vols}

    vols = {n: VOLUME_ARAMADO_P for n in NIVEIS_P}
    return {"niveis": NIVEIS_P, "tipo_estrutural": "aramado_P", "tipo_desc": "Padrão", "volumes": vols}

def calcular_pecas_totais(dados_casulo):
    return sum(dados_casulo.values()) if dados_casulo else 0

def calcular_volume_ocupado_cm3(dados_casulo):
    if not dados_casulo:
        return 0
    total = 0
    for chave_combo, qtd in dados_casulo.items():
        tamanho = chave_combo.split("|")[0]
        total += qtd * TAMANHOS_PECA.get(tamanho, {}).get("volume_cm3", 0)
    return total

def obter_capacidade_estimada_pecas(tipo_estrutural, volume_nivel_cm3):
    tamanho_ref = TAMANHO_REFERENCIA_POR_TIPO.get(tipo_estrutural, "M")
    volume_peca_ref = TAMANHOS_PECA.get(tamanho_ref, {}).get("volume_cm3", 1)
    if not volume_peca_ref:
        return 0
    return volume_nivel_cm3 // volume_peca_ref

def montar_html_nicho(rua_selecionada, col_num, nivel, spec, chave_lado):
    if nivel not in spec["niveis"]:
        return "<div class='nicho' style='background: transparent;'>-</div>"

    chave = obter_chave_casulo(rua_selecionada, chave_lado, col_num, nivel)
    dados_casulo = st.session_state.base_dados_cd.get(chave, {})
    pecas_atuais = calcular_pecas_totais(dados_casulo)
    volume_ocupado = calcular_volume_ocupado_cm3(dados_casulo)
    volume_nivel = spec["volumes"].get(nivel, 0)
    capacidade_estimada = obter_capacidade_estimada_pecas(spec["tipo_estrutural"], volume_nivel)
    pct_ocupacao = (volume_ocupado / volume_nivel * 100) if volume_nivel > 0 else 0

    status = "livre"
    if pct_ocupacao >= 100: status = "saturado"
    elif pct_ocupacao >= 81: status = "saturado"
    elif pct_ocupacao >= 50: status = "atencao"

    is_destaque = (st.session_state.busca_destaque and st.session_state.busca_destaque['rua'] == rua_selecionada and st.session_state.busca_destaque['nivel'] == nivel and st.session_state.busca_destaque['col'] == col_num)
    classe_destaque = "destaque-ativo" if is_destaque else ""

    return f"<div class='nicho {status} {classe_destaque}' title='{col_num:03d}-{nivel} | {pecas_atuais}/{capacidade_estimada} peças ({pct_ocupacao:.1f}% do volume)'>{pecas_atuais}/{capacidade_estimada}</div>"

def renderizar_cabecalho_colunas(lista_colunas):
    grid_header = st.columns(len(lista_colunas) + 1)
    with grid_header[0]:
        st.markdown("<div style='font-size:10px;'>&nbsp;</div>", unsafe_allow_html=True)
    for idx, col_num in enumerate(lista_colunas):
        with grid_header[idx + 1]:
            st.markdown(f"<div style='text-align:center; font-weight:bold; color:#ffcc00; font-size:10px;'>{col_num:03d}</div>", unsafe_allow_html=True)

# Inicialização do Estado
if 'base_dados_cd' not in st.session_state:
    st.session_state.base_dados_cd = {}
    for r_nome, r_cfg in ESTRUTURA_CD.items():
        if r_cfg.get("tipo") == "Inexistente":
            continue
        lista_lados = [("impar", r_cfg.get("cols_impar", [])), ("par", r_cfg.get("cols_par", []))]
        if "cols_seq" in r_cfg:
            lista_lados = [("seq", r_cfg["cols_seq"])]

        for lado, cols in lista_lados:
            for c in cols:
                l_param = "par" if r_nome == "Rua 11" else ("impar" if lado == "seq" else lado)
                spec = obter_especificacao_casulo(r_nome, c, l_param)
                for n in spec["niveis"]:
                    chave_casulo = obter_chave_casulo(r_nome, lado, c, n)
                    st.session_state.base_dados_cd[chave_casulo] = {}

if 'busca_destaque' not in st.session_state:
    st.session_state.busca_destaque = None
if 'aba_ativa_selecionada' not in st.session_state:
    st.session_state.aba_ativa_selecionada = "🏠 Tela Inicial (Geral)"

# Base de usuários (login/senha/papel). Guardada em memória (session_state),
# assim como o restante da base de dados do sistema — reinicia se a página
# recarregar. Papel "gerente" tem acesso à aba Gerenciador e a funções críticas;
# papel "operador" tem acesso apenas às telas operacionais.
USUARIOS_PADRAO = {
    "admin": {"senha": "admin123", "papel": "gerente"}
}
if 'usuarios_cadastrados' not in st.session_state:
    st.session_state.usuarios_cadastrados = dict(USUARIOS_PADRAO)
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'usuario_atual' not in st.session_state:
    st.session_state.usuario_atual = None
if 'papel_atual' not in st.session_state:
    st.session_state.papel_atual = None


# ==========================================
# BLOCO 2: INTERFACE VISUAL (FRONT-END & ESTILOS)
# ==========================================

st.markdown("""
<style>
    .stApp {
        background-color: #0b0c10;
        color: #c5c6c7;
        text-align: center;
    }
    .logo-container {
        text-align: center;
        padding: 15px 0;
        margin-bottom: 5px;
    }
    .logo-icone {
        font-size: 55px;
        margin-bottom: -10px;
        filter: drop-shadow(0 0 10px rgba(255, 204, 0, 0.6));
    }
    .logo-texto {
        font-family: 'Trebuchet MS', sans-serif;
        font-size: 40px;
        font-weight: 900;
        letter-spacing: 2px;
        color: #ffcc00;
        text-shadow: 0 0 10px rgba(255, 204, 0, 0.4);
        margin: 0;
    }
    .logo-sub {
        font-size: 12px;
        color: #8892b0;
        letter-spacing: 5px;
        text-transform: uppercase;
        margin-top: -5px;
    }
    .card-dashboard {
        background: linear-gradient(135deg, #1f2833 0%, #0b0c10 100%);
        border: 1px solid #ffcc00;
        border-radius: 12px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(255, 204, 0, 0.1);
    }
    .card-dashboard h5 {
        margin: 0;
        color: #8892b0;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .card-dashboard h2 {
        margin: 10px 0 0 0;
        color: #ffcc00;
        font-size: 26px;
        font-weight: bold;
    }
    .planta-rua-bloco {
        background: #1f2833;
        border: 1px solid #283845;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
        margin-bottom: 10px;
    }
    .bar-container {
        width: 100%;
        background-color: #0b0c10;
        border-radius: 6px;
        height: 10px;
        margin-top: 5px;
        overflow: hidden;
        border: 1px solid #283845;
    }
    .bar-fill {
        height: 100%;
        border-radius: 6px;
    }
    .cor-verde { background-color: #45a29e; }
    .cor-amarelo { background-color: #ffcc00; }
    .cor-laranja { background-color: #f39c12; }
    .cor-vermelho { background-color: #e74c3c; }
    .topicos-legenda {
        background: #1f2833;
        border: 1px solid #283845;
        border-radius: 8px;
        padding: 12px 20px;
        margin: 0 auto 20px auto;
        max-width: 800px;
        text-align: left;
        font-size: 13px;
    }
    .topicos-legenda ul {
        margin: 0;
        padding-left: 20px;
        color: #c5c6c7;
    }
    .topicos-legenda li {
        margin-bottom: 4px;
        text-align: left;
    }
    .lado-container {
        background: #11161d;
        border: 1px solid #283845;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
        margin-bottom: 15px;
    }
    .lado-titulo {
        font-size: 13px;
        font-weight: bold;
        color: #ffcc00;
        text-align: center;
        margin-bottom: 8px;
        border-bottom: 1px solid #283845;
        padding-bottom: 4px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .nicho {
        width: 44px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 9px;
        font-weight: bold;
        border-radius: 4px;
        color: #0b0c10;
        margin: 1.5px auto;
        text-align: center;
    }
    .livre { background-color: #45a29e; color: #fff; }
    .atencao { background-color: #ffcc00; }
    .saturado { background-color: #e74c3c; color: #fff; }
    .destaque-ativo { 
        border: 2px solid #ffffff !important; 
        transform: scale(1.15); 
        box-shadow: 0 0 12px #ffcc00; 
        z-index: 10; 
        background-color: #ffcc00 !important;
        color: #0b0c10 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# BLOCO 1.5: PORTAL DE AUTENTICAÇÃO (LOGIN)
# ==========================================
if not st.session_state.autenticado:
    st.markdown("""
    <div class="logo-container">
        <div class="logo-icone">⚠️📦</div>
        <h1 class="logo-texto">STOCK CONTROL</h1>
        <div class="logo-sub">Gestão por Peças por Casulo</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<h3 style='text-align:center; color:#ffcc00;'>🔐 Acesso ao Sistema</h3>", unsafe_allow_html=True)

    col_login_esq, col_login_meio, col_login_dir = st.columns([1, 1.2, 1])
    with col_login_meio:
        with st.form("form_login"):
            usuario_input = st.text_input("Usuário")
            senha_input = st.text_input("Senha", type="password")
            submit_login = st.form_submit_button("Entrar", type="primary", use_container_width=True)

        if submit_login:
            dados_usuario = st.session_state.usuarios_cadastrados.get(usuario_input)
            if dados_usuario and dados_usuario["senha"] == senha_input:
                st.session_state.autenticado = True
                st.session_state.usuario_atual = usuario_input
                st.session_state.papel_atual = dados_usuario["papel"]
                st.rerun()
            else:
                st.error("⚠️ Usuário ou senha inválidos.")

        st.markdown("<p style='text-align:center; color:#8892b0; font-size:11px; margin-top:10px;'>Acesso padrão inicial: <b>admin</b> / <b>admin123</b><br>(crie os logins da equipe e troque essa senha na aba Gerenciador)</p>", unsafe_allow_html=True)

    st.stop()

# SIDEBAR: NAVEGAÇÃO
st.sidebar.markdown("<h2 style='color: #ffcc00; text-align: center;'>⚙️ NAVEGAÇÃO</h2>", unsafe_allow_html=True)

opcoes_telas = [
    "🏠 Tela Inicial (Geral)", 
    "📦 Visualizador de Casulos", 
    "🔍 Consulta Rápida de Casulos", 
    "📥 Entrada de Dados / Abastecimento"
]
if st.session_state.papel_atual == "gerente":
    opcoes_telas.append("🛠️ Gerenciador (Admin)")

if st.session_state.aba_ativa_selecionada not in opcoes_telas:
    st.session_state.aba_ativa_selecionada = "🏠 Tela Inicial (Geral)"

st.session_state.aba_ativa_selecionada = st.sidebar.radio("Selecione a Tela:", opcoes_telas, index=opcoes_telas.index(st.session_state.aba_ativa_selecionada))

st.sidebar.markdown(f"<p style='text-align:center; color:#8892b0; font-size:12px;'>👤 <b>{st.session_state.usuario_atual}</b> ({st.session_state.papel_atual.capitalize()})</p>", unsafe_allow_html=True)
if st.sidebar.button("🚪 Sair"):
    st.session_state.autenticado = False
    st.session_state.usuario_atual = None
    st.session_state.papel_atual = None
    st.rerun()

# PESQUISA GLOBAL
st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color: #ffcc00;'>🔎 Localizador Global</h4>", unsafe_allow_html=True)
busca_input = st.sidebar.text_input("Digite o endereço:", placeholder="003-B-009...")

if st.sidebar.button("Destacar no Sistema"):
    tokens = re.findall(r'[A-Za-z0-9]+', busca_input)
    if len(tokens) >= 3:
        num_rua = int(tokens[0])
        rua_alvo = f"Rua {num_rua:02d}"
        col_buscada = int(tokens[2])
        nivel_buscado = tokens[1].upper()
        
        if rua_alvo in ESTRUTURA_CD:
            cfg = ESTRUTURA_CD[rua_alvo]
            if cfg.get("tipo") == "Inexistente":
                st.sidebar.error(f"⚠️ A {rua_alvo} é inexistente!")
            else:
                todos_da_rua = cfg.get("cols_impar", []) + cfg.get("cols_par", []) + cfg.get("cols_seq", [])
                if todos_da_rua and col_buscada not in todos_da_rua:
                    st.sidebar.error(f"⚠️ Coluna {col_buscada:03d} não existe na {rua_alvo}!")
                else:
                    st.session_state.busca_destaque = {
                        'rua': rua_alvo,
                        'nivel': nivel_buscado,
                        'col': col_buscada
                    }
                    st.session_state.aba_ativa_selecionada = "📦 Visualizador de Casulos"
                    st.sidebar.success(f"Casulo localizado!")
                    st.rerun()
        else:
            st.sidebar.error("Rua não encontrada!")
    else:
        st.sidebar.error("Formato inválido! Use ex: 003-B-009")

# BRANDING DO APP
st.markdown("""
<div class="logo-container">
    <div class="logo-icone">⚠️📦</div>
    <h1 class="logo-texto">STOCK CONTROL</h1>
    <div class="logo-sub">Gestão por Peças por Casulo</div>
</div>
""", unsafe_allow_html=True)


# ==========================================
# TELA 1: TELA INICIAL (PAINEL GERAL)
# ==========================================
if st.session_state.aba_ativa_selecionada == "🏠 Tela Inicial (Geral)":
    st.markdown("<h3 style='text-align: center; color: #ffcc00;'>📊 Painel Geral de Ocupação por Volume</h3>", unsafe_allow_html=True)

    total_volume_capacidade_cm3 = 0
    total_volume_ocupado_cm3 = 0
    total_pecas_atuais = 0
    casulos_livres = 0
    total_casulos = len(st.session_state.base_dados_cd)

    for chave, dados_casulo in st.session_state.base_dados_cd.items():
        r_nome, lado, c_str, n = chave.split("|")
        l_param = "par" if r_nome == "Rua 11" else ("impar" if lado == "seq" else lado)
        spec = obter_especificacao_casulo(r_nome, int(c_str), l_param)
        volume_nivel = spec["volumes"].get(n, 0)
        total_volume_capacidade_cm3 += volume_nivel
        pecas_casulo = calcular_pecas_totais(dados_casulo)
        total_volume_ocupado_cm3 += calcular_volume_ocupado_cm3(dados_casulo)
        total_pecas_atuais += pecas_casulo
        if pecas_casulo == 0:
            casulos_livres += 1

    pct_geral = (total_volume_ocupado_cm3 / total_volume_capacidade_cm3 * 100) if total_volume_capacidade_cm3 > 0 else 0.0

    kcol1, kcol2, kcol3, kcol4 = st.columns(4)
    with kcol1: st.markdown(f"<div class='card-dashboard'><h5>Total Casulos</h5><h2>{total_casulos:,}</h2></div>", unsafe_allow_html=True)
    with kcol2: st.markdown(f"<div class='card-dashboard'><h5>Ocupação por Volume</h5><h2>{pct_geral:.1f}%</h2></div>", unsafe_allow_html=True)
    with kcol3: st.markdown(f"<div class='card-dashboard'><h5>Casulos Zerados</h5><h2>{casulos_livres:,}</h2></div>", unsafe_allow_html=True)
    with kcol4: st.markdown(f"<div class='card-dashboard'><h5>Peças Armazenadas</h5><h2>{total_pecas_atuais:,} un</h2></div>", unsafe_allow_html=True)

    st.write("---")
    st.markdown("<h4 style='text-align: center; color: #ffcc00;'>🗺️ Mapa de Calor por Rua (Ocupação por Volume)</h4>", unsafe_allow_html=True)

    def obter_classe_cor(pct):
        if pct == 0: return "cor-verde"
        elif pct < 50: return "cor-verde"
        elif pct <= 80: return "cor-amarelo"
        elif pct < 100: return "cor-laranja"
        else: return "cor-vermelho"

    ruas_nomes = list(ESTRUTURA_CD.keys())
    bloco_cols = st.columns(3)
    dados_ranking = []

    for idx, rua in enumerate(ruas_nomes):
        col_alvo = bloco_cols[idx % 3]
        cfg_rua = ESTRUTURA_CD[rua]

        if cfg_rua.get("tipo") == "Inexistente":
            with col_alvo:
                st.markdown(f"""
                <div class="planta-rua-bloco" style="border-color: #333;">
                    <div style="font-weight: bold; font-size: 15px; color: #555;">{rua}</div>
                    <div style="font-size: 11px; margin-top: 4px; color: #e74c3c; text-transform: uppercase; letter-spacing: 1px;">Inexistente</div>
                </div>
                """, unsafe_allow_html=True)
            continue

        v_rua_max = 0
        v_rua_atual = 0
        for chave, dados_casulo in st.session_state.base_dados_cd.items():
            r_n, lado_r, c_r, n_r = chave.split("|")
            if r_n == rua:
                l_param = "par" if rua == "Rua 11" else ("impar" if lado_r == "seq" else lado_r)
                spec_r = obter_especificacao_casulo(rua, int(c_r), l_param)
                v_rua_max += spec_r["volumes"].get(n_r, 0)
                v_rua_atual += calcular_volume_ocupado_cm3(dados_casulo)

        pct_rua = (v_rua_atual / v_rua_max * 100) if v_rua_max > 0 else 0.0
        classe_cor = obter_classe_cor(pct_rua)
        dados_ranking.append({"Rua": rua, "Ocupação (%)": round(pct_rua, 1)})

        with col_alvo:
            st.markdown(f"""
            <div class="planta-rua-bloco">
                <div style="font-weight: bold; font-size: 15px; color: #ffcc00;">{rua}</div>
                <div style="font-size: 12px; margin-top: 2px; color: #8892b0;">{pct_rua:.1f}% ocupado (volume)</div>
                <div class="bar-container">
                    <div class="bar-fill {classe_cor}" style="width: {pct_rua}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.write("---")
    st.markdown("<h4 style='text-align: center; color: #ffcc00;'>📈 Ranking de Ocupação por Corredor (%)</h4>", unsafe_allow_html=True)

    if dados_ranking:
        df_ranking = pd.DataFrame(dados_ranking).set_index("Rua")
        st.bar_chart(df_ranking, color="#ffcc00")

        df_ordenado = pd.DataFrame(dados_ranking).sort_values("Ocupação (%)", ascending=False)
        rua_mais_cheia = df_ordenado.iloc[0]
        rua_mais_vazia = df_ordenado.iloc[-1]

        kcol_rank1, kcol_rank2 = st.columns(2)
        with kcol_rank1:
            st.markdown(f"<div class='card-dashboard'><h5>🔥 Corredor Mais Cheio</h5><h2>{rua_mais_cheia['Rua']}</h2><p style='color:#8892b0; margin-top:4px; font-size:12px;'>{rua_mais_cheia['Ocupação (%)']:.1f}% ocupado</p></div>", unsafe_allow_html=True)
        with kcol_rank2:
            st.markdown(f"<div class='card-dashboard'><h5>🌤️ Corredor Mais Livre</h5><h2>{rua_mais_vazia['Rua']}</h2><p style='color:#8892b0; margin-top:4px; font-size:12px;'>{rua_mais_vazia['Ocupação (%)']:.1f}% ocupado</p></div>", unsafe_allow_html=True)


# ==========================================
# TELA 2: VISUALIZADOR DE CASULOS
# ==========================================
elif st.session_state.aba_ativa_selecionada == "📦 Visualizador de Casulos":
    lista_ruas = list(ESTRUTURA_CD.keys())
    rua_inicial_idx = 0
    if st.session_state.busca_destaque and st.session_state.busca_destaque['rua'] in lista_ruas:
        rua_inicial_idx = lista_ruas.index(st.session_state.busca_destaque['rua'])

    rua_selecionada = st.selectbox("Selecione a Rua para Inspeção Detalhada:", lista_ruas, index=rua_inicial_idx)

    config_rua = ESTRUTURA_CD.get(rua_selecionada, {})

    if config_rua.get("tipo") == "Inexistente":
        st.markdown(f"<h3 style='text-align: center; color: #e74c3c;'>⚠️ Corredor <b>{rua_selecionada}</b> Inexistente</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #8892b0;'>Este corredor não possui estrutura física mapeada no sistema.</p>", unsafe_allow_html=True)
    else:
        st.markdown(f"<h3 style='text-align: center; color: #ffcc00;'>📍 Malha Física do Corredor: <b>{rua_selecionada}</b></h3>", unsafe_allow_html=True)

        st.markdown("""
        <div class="topicos-legenda">
            <b style="color: #ffcc00; display: block; margin-bottom: 6px; text-align: center;">📋 Legenda de Ocupação por Volume de Estoque:</b>
            <ul>
                <li><span style="color: #45a29e; font-weight: bold;">Verde:</span> Disponível / Baixa (&lt; 50%)</li>
                <li><span style="color: #ffcc00; font-weight: bold;">Amarelo:</span> Moderado (50% a 80%)</li>
                <li><span style="color: #f39c12; font-weight: bold;">Laranja:</span> Alerta (81% a 99%)</li>
                <li><span style="color: #e74c3c; font-weight: bold;">Vermelho:</span> Saturado (100%)</li>
                <li>Dentro do casulo: <b>peças atuais / capacidade estimada</b>. A coluna aparece na linha de cabeçalho, acima da grade.</li>
                <li>⚠️ Peças <b>GG</b> (jaquetas pesadas/casacos) só podem ser lançadas em casulos de <b>madeira ou metal</b>.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if rua_selecionada == "Rua 14":
            st.markdown("<p style='text-align:center; color:#8892b0; font-size:13px;'>Corredor segmentado por Tipologia Estrutural (Madeira e Metal)</p>", unsafe_allow_html=True)

            blocos_r14 = [
                ("🌲 Bloco 1: Prateleiras de Madeira Gigante (Colunas 01 a 23)", list(range(1, 24))),
                ("🔩 Bloco 2: Prateleiras de Metal Profundo (Colunas 24 a 31)", list(range(24, 32))),
                ("⚙️ Bloco 3: Prateleiras de Metal Raso (Colunas 42 a 48)", list(range(42, 49)))
            ]

            for titulo_bloco, cols_bloco in blocos_r14:
                st.markdown(f"<div class='lado-container'>", unsafe_allow_html=True)
                st.markdown(f"<div class='lado-titulo'>{titulo_bloco}</div>", unsafe_allow_html=True)

                spec_ref = obter_especificacao_casulo(rua_selecionada, cols_bloco[0], "impar")
                niveis_ordenados = sorted(spec_ref["niveis"])

                renderizar_cabecalho_colunas(cols_bloco)

                for nivel in niveis_ordenados:
                    grid_bloco = st.columns(len(cols_bloco) + 1)
                    with grid_bloco[0]:
                        st.markdown(f"<div style='line-height:28px; text-align:center; font-weight:bold; color:#8892b0; font-size: 10px;'>{nivel}</div>", unsafe_allow_html=True)
                    for idx, col_num in enumerate(cols_bloco):
                        with grid_bloco[idx + 1]:
                            spec_col = obter_especificacao_casulo(rua_selecionada, col_num, "impar")
                            st.markdown(montar_html_nicho(rua_selecionada, col_num, nivel, spec_col, "seq"), unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        elif rua_selecionada == "Rua 20":
            st.markdown("<p style='text-align:center; color:#8892b0; font-size:13px;'>Corredor Sequencial de Aramados Pequenos (Colunas Ímpares de 35 a 137)</p>", unsafe_allow_html=True)

            todas_colunas = config_rua.get("cols_seq", [])
            if not todas_colunas:
                st.warning("⚠️ Não existem colunas cadastradas para a Rua 20.")
            else:
                if len(todas_colunas) > 25:
                    tamanho_bloco = 25
                    blocos = [(f"Colunas {todas_colunas[i]:03d} até {todas_colunas[min(i+tamanho_bloco-1, len(todas_colunas)-1)]:03d}", todas_colunas[i:i+tamanho_bloco]) for i in range(0, len(todas_colunas), tamanho_bloco)]
                    opcoes_bloco = [b[0] for b in blocos]
                    bloco_escolhido_nome = st.selectbox("Selecione o Bloco de Colunas:", opcoes_bloco)
                    colunas_exemplo = next(b[1] for b in blocos if b[0] == bloco_escolhido_nome)
                else:
                    colunas_exemplo = todas_colunas

                niveis_ordenados = sorted(NIVEIS_P)

                st.markdown("<div class='lado-container'>", unsafe_allow_html=True)
                st.markdown(f"<div class='lado-titulo'>Corredor Sequencial Rua 20</div>", unsafe_allow_html=True)

                renderizar_cabecalho_colunas(colunas_exemplo)

                for nivel in niveis_ordenados:
                    grid_seq = st.columns(len(colunas_exemplo) + 1)
                    with grid_seq[0]:
                        st.markdown(f"<div style='line-height:28px; text-align:center; font-weight:bold; color:#8892b0; font-size: 10px;'>{nivel}</div>", unsafe_allow_html=True)
                    for idx, col_num in enumerate(colunas_exemplo):
                        with grid_seq[idx + 1]:
                            spec_col = obter_especificacao_casulo(rua_selecionada, col_num, "impar")
                            st.markdown(montar_html_nicho(rua_selecionada, col_num, nivel, spec_col, "seq"), unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        elif rua_selecionada == "Rua 21":
            st.markdown("<p style='text-align:center; color:#8892b0; font-size:13px;'>Corredor Sequencial de Prateleiras de Metal (Colunas Ímpares de 01 a 77)</p>", unsafe_allow_html=True)

            todas_colunas = config_rua.get("cols_seq", [])
            if not todas_colunas:
                st.warning("⚠️ Não existem colunas cadastradas para a Rua 21.")
            else:
                if len(todas_colunas) > 25:
                    tamanho_bloco = 25
                    blocos = [(f"Colunas {todas_colunas[i]:03d} até {todas_colunas[min(i+tamanho_bloco-1, len(todas_colunas)-1)]:03d}", todas_colunas[i:i+tamanho_bloco]) for i in range(0, len(todas_colunas), tamanho_bloco)]
                    opcoes_bloco = [b[0] for b in blocos]
                    bloco_escolhido_nome = st.selectbox("Selecione o Bloco de Colunas:", opcoes_bloco)
                    colunas_exemplo = next(b[1] for b in blocos if b[0] == bloco_escolhido_nome)
                else:
                    colunas_exemplo = todas_colunas

                spec_ref = obter_especificacao_casulo(rua_selecionada, colunas_exemplo[0], "impar")
                niveis_ordenados = sorted(spec_ref["niveis"])

                st.markdown("<div class='lado-container'>", unsafe_allow_html=True)
                st.markdown(f"<div class='lado-titulo'>Corredor Sequencial Rua 21</div>", unsafe_allow_html=True)

                renderizar_cabecalho_colunas(colunas_exemplo)

                for nivel in niveis_ordenados:
                    grid_seq = st.columns(len(colunas_exemplo) + 1)
                    with grid_seq[0]:
                        st.markdown(f"<div style='line-height:28px; text-align:center; font-weight:bold; color:#8892b0; font-size: 10px;'>{nivel}</div>", unsafe_allow_html=True)
                    for idx, col_num in enumerate(colunas_exemplo):
                        with grid_seq[idx + 1]:
                            spec_col = obter_especificacao_casulo(rua_selecionada, col_num, "impar")
                            st.markdown(montar_html_nicho(rua_selecionada, col_num, nivel, spec_col, "seq"), unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        elif "cols_seq" in config_rua or rua_selecionada == "Rua 11":
            if rua_selecionada == "Rua 11":
                todas_colunas = config_rua.get("cols_par", [])
            else:
                todas_colunas = config_rua.get("cols_seq", [])

            if not todas_colunas:
                st.warning(f"⚠️ Não existem casulos cadastrados nesta rua ({rua_selecionada}).")
            else:
                if len(todas_colunas) > 25:
                    tamanho_bloco = 25
                    blocos = [(f"Colunas {todas_colunas[i]:03d} até {todas_colunas[min(i+tamanho_bloco-1, len(todas_colunas)-1)]:03d}", todas_colunas[i:i+tamanho_bloco]) for i in range(0, len(todas_colunas), tamanho_bloco)]
                    opcoes_bloco = [b[0] for b in blocos]
                    bloco_escolhido_nome = st.selectbox("Selecione o Bloco de Colunas:", opcoes_bloco)
                    colunas_exemplo = next(b[1] for b in blocos if b[0] == bloco_escolhido_nome)
                else:
                    colunas_exemplo = todas_colunas

                l_ref = "par" if rua_selecionada == "Rua 11" else "impar"
                spec_ref = obter_especificacao_casulo(rua_selecionada, colunas_exemplo[0] if colunas_exemplo else 22, l_ref)
                niveis_ordenados = sorted(spec_ref["niveis"])

                st.markdown(f"<p style='text-align:center; color:#8892b0; font-size:12px;'>Especificação: <b>{spec_ref['tipo_desc']}</b></p>", unsafe_allow_html=True)

                st.markdown("<div class='lado-container'>", unsafe_allow_html=True)
                st.markdown(f"<div class='lado-titulo'>Corredor Sequencial / Unilateral ({rua_selecionada})</div>", unsafe_allow_html=True)

                renderizar_cabecalho_colunas(colunas_exemplo)

                for nivel in niveis_ordenados:
                    grid_seq = st.columns(len(colunas_exemplo) + 1)
                    with grid_seq[0]:
                        st.markdown(f"<div style='line-height:28px; text-align:center; font-weight:bold; color:#8892b0; font-size: 10px;'>{nivel}</div>", unsafe_allow_html=True)
                    for idx, col_num in enumerate(colunas_exemplo):
                        with grid_seq[idx + 1]:
                            l_param_col = "par" if rua_selecionada == "Rua 11" else "impar"
                            spec_col = obter_especificacao_casulo(rua_selecionada, col_num, l_param_col)
                            lado_chave = "par" if rua_selecionada == "Rua 11" else "seq"
                            st.markdown(montar_html_nicho(rua_selecionada, col_num, nivel, spec_col, lado_chave), unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        else:
            todas_cols_impares = config_rua.get("cols_impar", [])
            todas_cols_pares = config_rua.get("cols_par", [])
            todas_colunas = sorted(list(set(todas_cols_impares + todas_cols_pares)))

            if not todas_colunas:
                st.warning(f"⚠️ Não existem casulos cadastrados nesta rua ({rua_selecionada}).")
            else:
                if len(todas_colunas) > 20:
                    tamanho_bloco = 20
                    blocos = [(f"Colunas {todas_colunas[i]:03d} até {todas_colunas[min(i+tamanho_bloco-1, len(todas_colunas)-1)]:03d}", todas_colunas[i:i+tamanho_bloco]) for i in range(0, len(todas_colunas), tamanho_bloco)]
                    opcoes_bloco = [b[0] for b in blocos]
                    bloco_escolhido_nome = st.selectbox("Selecione o Bloco de Colunas:", opcoes_bloco)
                    colunas_exemplo = next(b[1] for b in blocos if b[0] == bloco_escolhido_nome)
                else:
                    colunas_exemplo = todas_colunas

                colunas_impares = [c for c in colunas_exemplo if c in todas_cols_impares]
                colunas_pares = [c for c in colunas_exemplo if c in todas_cols_pares]

                niveis_impar_ref, tipo_desc_impar = [], ""
                niveis_par_ref, tipo_desc_par = [], ""
                if colunas_impares:
                    spec_impar = obter_especificacao_casulo(rua_selecionada, colunas_impares[0], "impar")
                    niveis_impar_ref = spec_impar["niveis"]
                    tipo_desc_impar = spec_impar["tipo_desc"]
                if colunas_pares:
                    spec_par = obter_especificacao_casulo(rua_selecionada, colunas_pares[0], "par")
                    niveis_par_ref = spec_par["niveis"]
                    tipo_desc_par = spec_par["tipo_desc"]

                niveis_ordenados = sorted(set(niveis_impar_ref) | set(niveis_par_ref))

                if tipo_desc_impar and tipo_desc_par and tipo_desc_impar != tipo_desc_par:
                    tipo_desc = f"Ímpar: {tipo_desc_impar} | Par: {tipo_desc_par}"
                else:
                    tipo_desc = tipo_desc_impar or tipo_desc_par

                st.markdown(f"<p style='text-align:center; color:#8892b0; font-size:12px;'>Especificação: <b>{tipo_desc}</b></p>", unsafe_allow_html=True)

                col_esq_layout, col_dir_layout = st.columns(2)

                with col_esq_layout:
                    st.markdown("<div class='lado-container'>", unsafe_allow_html=True)
                    st.markdown("<div class='lado-titulo'>◀ Lado Ímpar</div>", unsafe_allow_html=True)
                    if colunas_impares:
                        renderizar_cabecalho_colunas(colunas_impares)
                        for nivel in niveis_ordenados:
                            grid_impar = st.columns(len(colunas_impares) + 1)
                            with grid_impar[0]:
                                st.markdown(f"<div style='line-height:28px; text-align:center; font-weight:bold; color:#8892b0; font-size: 10px;'>{nivel}</div>", unsafe_allow_html=True)
                            for idx, col_num in enumerate(colunas_impares):
                                with grid_impar[idx + 1]:
                                    spec_col = obter_especificacao_casulo(rua_selecionada, col_num, "impar")
                                    st.markdown(montar_html_nicho(rua_selecionada, col_num, nivel, spec_col, "impar"), unsafe_allow_html=True)
                    else:
                        st.markdown("<p style='color: #8892b0; font-size: 12px; padding: 20px;'>Sem casulos neste lado.</p>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                with col_dir_layout:
                    st.markdown("<div class='lado-container'>", unsafe_allow_html=True)
                    st.markdown("<div class='lado-titulo'>Lado Par ▶</div>", unsafe_allow_html=True)
                    if colunas_pares:
                        renderizar_cabecalho_colunas(colunas_pares)
                        for nivel in niveis_ordenados:
                            grid_par = st.columns(len(colunas_pares) + 1)
                            with grid_par[0]:
                                st.markdown(f"<div style='line-height:28px; text-align:center; font-weight:bold; color:#8892b0; font-size: 10px;'>{nivel}</div>", unsafe_allow_html=True)
                            for idx, col_num in enumerate(colunas_pares):
                                with grid_par[idx + 1]:
                                    spec_col = obter_especificacao_casulo(rua_selecionada, col_num, "par")
                                    st.markdown(montar_html_nicho(rua_selecionada, col_num, nivel, spec_col, "par"), unsafe_allow_html=True)
                    else:
                        st.markdown("<p style='color: #8892b0; font-size: 12px; padding: 20px;'>Sem casulos neste lado.</p>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# TELA 3: CONSULTA RÁPIDA DE CASULOS ESPECÍFICOS
# ==========================================
elif st.session_state.aba_ativa_selecionada == "🔍 Consulta Rápida de Casulos":
    st.markdown("<h3 style='text-align: center; color: #ffcc00;'>🔍 Auditoria Rápida de Múltiplos Casulos</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #8892b0;'>Selecione ou insira endereços para auditar simultaneamente a ocupação por volume.</p>", unsafe_allow_html=True)

    chaves_disponiveis = sorted(list(st.session_state.base_dados_cd.keys()))

    casulos_selecionados = st.multiselect(
        "Selecione os Casulos (Formato: Rua|Lado|Coluna|Nível):",
        options=chaves_disponiveis,
        default=chaves_disponiveis[:3] if len(chaves_disponiveis) >= 3 else chaves_disponiveis
    )

    if not casulos_selecionados:
        st.info("💡 Nenhum casulo selecionado acima. Utilize a caixa de seleção para escolher os endereços que deseja auditar.")
    else:
        st.write("---")
        st.caption("Para lançar ou ajustar quantidades, use a aba 📥 Entrada de Dados (o lançamento precisa do tamanho e da estação da peça).")
        cols_cards = st.columns(3)

        for idx, chave in enumerate(casulos_selecionados):
            col_alvo_card = cols_cards[idx % 3]
            r_nome, lado_n, c_str, nivel_n = chave.split("|")
            col_num = int(c_str)

            l_param = "par" if r_nome == "Rua 11" else ("impar" if lado_n == "seq" else lado_n)
            spec = obter_especificacao_casulo(r_nome, col_num, l_param)
            volume_nivel = spec["volumes"].get(nivel_n, 0)
            dados_casulo = st.session_state.base_dados_cd.get(chave, {})
            pecas_atuais = calcular_pecas_totais(dados_casulo)
            volume_ocupado = calcular_volume_ocupado_cm3(dados_casulo)
            pct = (volume_ocupado / volume_nivel * 100) if volume_nivel > 0 else 0.0
            capacidade_estimada = obter_capacidade_estimada_pecas(spec["tipo_estrutural"], volume_nivel)

            c_cor = "cor-verde"
            if pct >= 100: c_cor = "cor-vermelho"
            elif pct >= 81: c_cor = "cor-laranja"
            elif pct >= 50: c_cor = "cor-amarelo"

            breakdown_txt = ", ".join([f"{combo.replace('|', ' ')}: {qtd}" for combo, qtd in dados_casulo.items() if qtd > 0]) or "Vazio"

            with col_alvo_card:
                st.markdown(f"""
                <div class="card-dashboard" style="margin-bottom: 15px; text-align: left; padding: 15px;">
                    <div style="font-size: 13px; font-weight: bold; color: #ffcc00; margin-bottom: 5px;">📍 {r_nome} ({lado_n.upper()})</div>
                    <div style="font-size: 12px; color: #c5c6c7;">Coluna: <b>{col_num:03d}</b> | Nível: <b>{nivel_n}</b> | Tipo: <b>{spec['tipo_desc']}</b></div>
                    <div style="font-size: 16px; font-weight: bold; color: #fff; margin: 8px 0;">{pecas_atuais:,} / {capacidade_estimada:,} un <span style="font-size: 12px; color: #8892b0;">({pct:.1f}% do volume)</span></div>
                    <div class="bar-container">
                        <div class="bar-fill {c_cor}" style="width: {min(pct, 100.0)}%;"></div>
                    </div>
                    <div style="font-size: 10px; color: #8892b0; margin-top: 6px;">Mix atual: {breakdown_txt}</div>
                </div>
                """, unsafe_allow_html=True)


# ==========================================
# TELA 4: ENTRADA DE DADOS / ABASTECIMENTO
# ==========================================
elif st.session_state.aba_ativa_selecionada == "📥 Entrada de Dados / Abastecimento":
    st.markdown("<h3 style='text-align: center; color: #ffcc00;'>📥 Entrada de Dados por Tamanho e Estação</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #8892b0; text-align: center;'>Cada lançamento marca a peça com um tamanho (PP a GG) e uma estação (Verão/Inverno/Meia-Estação). Estoques de estações diferentes convivem no mesmo casulo.</p>", unsafe_allow_html=True)

    with st.expander("📏 Ver volumes de referência por tamanho (estimados)"):
        df_tamanhos = pd.DataFrame([
            {"Tamanho": t, "Nome": d["nome"], "Volume médio (cm³)": d["volume_cm3"], "Exemplos": d["exemplos"]}
            for t, d in TAMANHOS_PECA.items()
        ])
        st.dataframe(df_tamanhos, use_container_width=True, hide_index=True)
        st.caption("⚠️ Volumes estimados por mim — ajuste em TAMANHOS_PECA no código se tiver a medida real.")

    tab_cad1, tab_cad2 = st.tabs(["✏️ Atualização de Casulo Individual", "🧹 Ações Globais na Base"])

    with tab_cad1:
        st.markdown("#### Configurar Estoque do Casulo")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)

        with col_f1:
            rua_cad = st.selectbox("Rua", list(ESTRUTURA_CD.keys()), key="rcad")

        cfg_r_cad = ESTRUTURA_CD.get(rua_cad, {})

        if cfg_r_cad.get("tipo") == "Inexistente":
            st.error(f"⚠️ A {rua_cad} é inexistente e não possui casulos para abastecimento.")
        else:
            with col_f2:
                if "cols_seq" in cfg_r_cad:
                    lado_cad = "seq"
                    st.selectbox("Lado", ["Sequencial Único"], key="lcad_seq_disabled", disabled=True)
                elif rua_cad == "Rua 11":
                    lado_cad = "par"
                    st.selectbox("Lado", ["par (Unilateral)"], key="lcad_r11_disabled", disabled=True)
                else:
                    lado_cad = st.selectbox("Lado", ["impar", "par"], key="lcad")

            if lado_cad == "seq":
                cols_disponiveis = cfg_r_cad.get("cols_seq", [])
            else:
                cols_disponiveis = cfg_r_cad.get("cols_impar" if lado_cad == "impar" else "cols_par", [])

            with col_f3:
                if cols_disponiveis:
                    col_cad = st.selectbox("Coluna", cols_disponiveis, key="ccad")
                else:
                    col_cad = st.selectbox("Coluna", [0], key="ccad_vazio")

            l_param_func = "par" if rua_cad == "Rua 11" else ("impar" if lado_cad == "seq" else lado_cad)
            spec_cad = obter_especificacao_casulo(rua_cad, col_cad, l_param_func)

            with col_f4:
                if spec_cad["niveis"]:
                    nivel_cad = st.selectbox("Nível", sorted(spec_cad["niveis"]), key="ncad")
                else:
                    nivel_cad = st.selectbox("Nível", ["B"], key="ncad_vazio")

            volume_nivel_cad = spec_cad["volumes"].get(nivel_cad, 0)
            aceita_gg = spec_cad["tipo_estrutural"] in ("madeira", "metal")

            lado_chave_cad = "seq" if lado_cad == "seq" else lado_cad
            chave_alvo = obter_chave_casulo(rua_cad, lado_chave_cad, col_cad, nivel_cad)
            dados_casulo_alvo = st.session_state.base_dados_cd.get(chave_alvo, {})
            pecas_atuais_totais = calcular_pecas_totais(dados_casulo_alvo)
            volume_ocupado_atual = calcular_volume_ocupado_cm3(dados_casulo_alvo)
            pct_atual = (volume_ocupado_atual / volume_nivel_cad * 100) if volume_nivel_cad > 0 else 0

            st.info(f"📦 Casulo {rua_cad} - Col {col_cad:03d} - Nível {nivel_cad} | Tipo: **{spec_cad['tipo_desc']}** | Volume: **{volume_nivel_cad:,} cm³** | Ocupação atual: **{pecas_atuais_totais} peças ({pct_atual:.1f}% do volume)**")

            st.markdown("##### Lançar / Ajustar peças por Tamanho e Estação")
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                opcoes_tamanho = list(TAMANHOS_PECA.keys()) if aceita_gg else [t for t in TAMANHOS_PECA.keys() if t != "GG"]
                tamanho_cad = st.selectbox("Tamanho", opcoes_tamanho, format_func=lambda t: TAMANHOS_PECA[t]["nome"], key="tamanho_cad")
            with col_t2:
                estacao_cad = st.selectbox("Estação (marca da peça)", ESTACOES_PECA, key="estacao_cad")
            with col_t3:
                chave_combo_cad = obter_chave_estoque(tamanho_cad, estacao_cad)
                qtd_existente_combo = dados_casulo_alvo.get(chave_combo_cad, 0)
                nova_qtd_input = st.number_input("Quantidade", min_value=0, value=int(qtd_existente_combo), step=1, key="qtd_cad")

            if not aceita_gg:
                st.caption("⚠️ Este casulo é de aramado — peças GG (jaquetas pesadas/casacos) não são permitidas aqui. Só cabem em madeira ou metal.")

            if st.button("💾 Salvar Quantidade", type="primary"):
                dados_atualizados = dict(st.session_state.base_dados_cd.get(chave_alvo, {}))
                if nova_qtd_input <= 0:
                    dados_atualizados.pop(chave_combo_cad, None)
                else:
                    dados_atualizados[chave_combo_cad] = int(nova_qtd_input)
                st.session_state.base_dados_cd[chave_alvo] = dados_atualizados
                st.success(f"Casulo {rua_cad} - {col_cad:03d}-{nivel_cad} atualizado: {TAMANHOS_PECA[tamanho_cad]['nome']} / {estacao_cad} = {nova_qtd_input} peças!")
                st.rerun()

    with tab_cad2:
        st.markdown("#### Manutenção Geral da Base de Dados")

        if st.session_state.papel_atual != "gerente":
            st.info("🔒 Ações globais na base são funções críticas, restritas ao papel de Gerente.")
        else:
            st.warning("⚠️ Atenção: Os botões abaixo modificam permanentemente a quantidade de peças em todo o CD na memória.")

            c_A, c_B = st.columns(2)
            with c_A:
                if st.button("Zerar Todos os Casulos (0 Peças)"):
                    for k in st.session_state.base_dados_cd.keys():
                        st.session_state.base_dados_cd[k] = {}
                    st.success("Todos os casulos foram zerados com sucesso!")
                    st.rerun()
            with c_B:
                if st.button("Popular com Dados Simulados Aleatórios"):
                    np.random.seed(321)
                    for k in st.session_state.base_dados_cd.keys():
                        r_n, l_n, c_n, n_n = k.split("|")
                        l_param_pop = "par" if r_n == "Rua 11" else ("impar" if l_n == "seq" else l_n)
                        spec_pop = obter_especificacao_casulo(r_n, int(c_n), l_param_pop)
                        aceita_gg_pop = spec_pop["tipo_estrutural"] in ("madeira", "metal")
                        opcoes_tam_pop = list(TAMANHOS_PECA.keys()) if aceita_gg_pop else [t for t in TAMANHOS_PECA.keys() if t != "GG"]

                        if np.random.rand() < 0.35:
                            st.session_state.base_dados_cd[k] = {}
                            continue

                        tamanho_sorteado = np.random.choice(opcoes_tam_pop)
                        estacao_sorteada = np.random.choice(ESTACOES_PECA)
                        volume_nivel_pop = spec_pop["volumes"].get(n_n, 0)
                        capacidade_pop = obter_capacidade_estimada_pecas(spec_pop["tipo_estrutural"], volume_nivel_pop)
                        qtd_sorteada = int(np.random.choice([0, int(capacidade_pop * 0.3), int(capacidade_pop * 0.7), capacidade_pop]))

                        if qtd_sorteada > 0:
                            st.session_state.base_dados_cd[k] = {obter_chave_estoque(tamanho_sorteado, estacao_sorteada): qtd_sorteada}
                        else:
                            st.session_state.base_dados_cd[k] = {}
                    st.success("Base populada com dados de teste (tamanhos e estações variados)!")
                    st.rerun()


# ==========================================
# TELA 5: GERENCIADOR (ADMIN)
# ==========================================
elif st.session_state.aba_ativa_selecionada == "🛠️ Gerenciador (Admin)":
    if st.session_state.papel_atual != "gerente":
        st.error("⛔ Acesso restrito a usuários com papel de Gerente.")
    else:
        st.markdown("<h3 style='text-align: center; color: #ffcc00;'>🛠️ Painel do Gerenciador</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #8892b0;'>Funções críticas disponíveis apenas para o papel de Gerente.</p>", unsafe_allow_html=True)

        tab_ger1, tab_ger2 = st.tabs(["👥 Gestão de Logins", "🧾 Usuários Cadastrados"])

        with tab_ger1:
            st.markdown("#### Criar Novo Login")
            col_g1, col_g2, col_g3 = st.columns(3)
            with col_g1:
                novo_usuario = st.text_input("Novo usuário (login)", key="novo_usuario_input")
            with col_g2:
                nova_senha = st.text_input("Senha", type="password", key="nova_senha_input")
            with col_g3:
                novo_papel = st.selectbox("Papel", ["operador", "gerente"], key="novo_papel_input")

            if st.button("➕ Criar Usuário", type="primary"):
                if not novo_usuario or not nova_senha:
                    st.error("⚠️ Preencha usuário e senha.")
                elif novo_usuario in st.session_state.usuarios_cadastrados:
                    st.error(f"⚠️ O usuário '{novo_usuario}' já existe.")
                else:
                    st.session_state.usuarios_cadastrados[novo_usuario] = {"senha": nova_senha, "papel": novo_papel}
                    st.success(f"Usuário '{novo_usuario}' criado como {novo_papel}!")
                    st.rerun()

            st.markdown("---")
            st.markdown("#### Remover Usuário")
            usuarios_removiveis = [u for u in st.session_state.usuarios_cadastrados.keys() if u != st.session_state.usuario_atual]
            if usuarios_removiveis:
                usuario_remover = st.selectbox("Selecione o usuário a remover", usuarios_removiveis, key="usuario_remover_input")
                if st.button("🗑️ Remover Usuário Selecionado"):
                    total_gerentes = sum(1 for u in st.session_state.usuarios_cadastrados.values() if u["papel"] == "gerente")
                    if st.session_state.usuarios_cadastrados[usuario_remover]["papel"] == "gerente" and total_gerentes <= 1:
                        st.error("⚠️ Não é possível remover o último gerente do sistema.")
                    else:
                        del st.session_state.usuarios_cadastrados[usuario_remover]
                        st.success(f"Usuário '{usuario_remover}' removido!")
                        st.rerun()
            else:
                st.info("Não há outros usuários cadastrados para remover.")

        with tab_ger2:
            st.markdown("#### Usuários com Acesso ao Sistema")
            lista_usuarios_df = pd.DataFrame([
                {"Usuário": u, "Papel": dados["papel"].capitalize()}
                for u, dados in st.session_state.usuarios_cadastrados.items()
            ])
            st.dataframe(lista_usuarios_df, use_container_width=True, hide_index=True)
