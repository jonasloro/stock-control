import streamlit as st
import pandas as pd
import numpy as np
import re

# 1. CONFIGURAÇÃO DE PÁGINA
st.set_page_config(
    page_title="Stock Control - Sistema de Gestão por Peças",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# BLOCO 1: CAMADA DE DADOS E ESTADO DO SISTEMA (BACK-END / CAPACIDADE EM PEÇAS)
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
    "Rua 12": {"tipo": "G_Seq", "cols_impar": list(range(1, 38)), "cols_par": []},
    "Rua 14": {"tipo": "Especial_Rua_14", "cols_impar": [], "cols_par": [], "cols_seq": list(range(1, 49))},
    "Rua 15": {"tipo": "Misto_Lado_15", "cols_impar": list(range(1, 88, 2)), "cols_par": list(range(2, 139, 2))},
    "Rua 16": {"tipo": "G", "metal": [43], "cols_impar": list(range(1, 101, 2)), "cols_par": list(range(2, 102, 2))},
    "Rua 17": {"tipo": "G", "metal": [101, 102, 103, 104, 105, 106], "cols_impar": list(range(1, 115, 2)), "cols_par": list(range(2, 116, 2))},
    "Rua 18": {"tipo": "M", "metal": [35, 36, 37, 38, 39, 40], "cols_impar": list(range(1, 81, 2)), "cols_par": list(range(2, 82, 2))},
    "Rua 19": {"tipo": "P", "metal": [101, 102, 103, 104, 105, 106], "cols_impar": list(range(1, 115, 2)), "cols_par": list(range(2, 116, 2))},
    "Rua 20": {"tipo": "P", "metal_impar": [35, 37, 39], "cols_impar": list(range(1, 81, 2)), "cols_par": list(range(2, 82, 2))},
    "Rua 21": {"tipo": "Metal_Seq_21", "cols_impar": list(range(1, 78)), "cols_par": []}
}

NIVEIS_G = ["B", "E", "H", "K", "N", "Q", "T"]
NIVEIS_M = ["B", "D", "E", "G", "H", "J", "K", "M", "N", "P", "Q", "S", "T", "V"]
NIVEIS_P = ["B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V"]
NIVEIS_METAL_5 = ["B", "C", "D", "E", "F"]

FATOR_ESTACAO = {
    "Verão": 1.2,        
    "Meia-Estação": 1.0, 
    "Inverno": 0.75      
}

def obter_niveis_e_capacidade_pecas(rua_nome, coluna, lado="impar", temporada="Meia-Estação"):
    try:
        col = int(coluna)
    except (ValueError, TypeError):
        col = 1

    config = ESTRUTURA_CD.get(rua_nome, {})
    tipo = config.get("tipo", "")
    fator = FATOR_ESTACAO.get(temporada, 1.0)

    is_metal = False
    if "metal" in config and col in config["metal"]:
        is_metal = True
    if "metal_impar" in config and lado == "impar" and col in config["metal_impar"]:
        is_metal = True
    if "metal_par" in config and lado == "par" and col in config["metal_par"]:
        is_metal = True

    if is_metal:
        base_Comum = int(120 * fator)
        base_F = int(90 * fator)
        vol_dict = {n: (base_F if n == "F" else base_Comum) for n in NIVEIS_METAL_5}
        return NIVEIS_METAL_5, vol_dict, "Metal Infiltrado"

    if tipo == "P":
        vol_dict = {n: int(45 * fator) for n in NIVEIS_P}
        return NIVEIS_P, vol_dict, "Pequeno (P)"
    elif tipo == "G":
        vol_dict = {n: int(150 * fator) for n in NIVEIS_G}
        return NIVEIS_G, vol_dict, "Grande (G)"
    elif tipo == "M":
        vol_dict = {n: int(80 * fator) for n in NIVEIS_M}
        return NIVEIS_M, vol_dict, "Médio (M)"
    elif tipo == "G_Unilateral":
        if lado == "par":
            vol_dict = {n: int(150 * fator) for n in NIVEIS_G}
            return NIVEIS_G, vol_dict, "Grande (G) - Unilateral"
        else:
            return [], {}, "Vazio"
    elif tipo == "Metal_Seq_21":
        base_Comum = int(120 * fator)
        base_F = int(90 * fator)
        vol_dict = {n: (base_F if n == "F" else base_Comum) for n in NIVEIS_METAL_5}
        return NIVEIS_METAL_5, vol_dict, "Metal Sequencial Rua 21"
    elif tipo == "G_Seq":
        vol_dict = {n: int(150 * fator) for n in NIVEIS_G}
        return NIVEIS_G, vol_dict, "Grande Sequencial"
    elif tipo == "Especial_Rua_14":
        if 1 <= col <= 23:
            niveis_14 = ["D", "G", "J", "M", "P"]
            v_comum = int(350 * fator)
            v_p = int(450 * fator)
            vol_dict = {n: (v_p if n == "P" else v_comum) for n in niveis_14}
            return niveis_14, vol_dict, "Rua 14 - Madeira Gigante"
        elif 24 <= col <= 31:
            niveis_14 = ["B", "C", "D", "E", "F"]
            v_comum = int(250 * fator)
            vol_dict = {n: int(180 * fator) if n == "F" else v_comum for n in niveis_14}
            return niveis_14, vol_dict, "Rua 14 - Metal Profundo"
        elif 32 <= col <= 41:
            niveis_14 = ["A", "B", "C", "D"]
            vol_dict = {n: int(90 * fator) for n in niveis_14}
            return niveis_14, vol_dict, "Rua 14 - Carrinhos"
        elif 42 <= col <= 48:
            niveis_14 = ["B", "C", "D", "E", "F"]
            vol_dict = {n: int(120 * fator) for n in niveis_14}
            return niveis_14, vol_dict, "Rua 14 - Metal Raso"
    elif tipo == "Rua 02":
        if col < 103:
            vol_dict = {n: int(45 * fator) for n in NIVEIS_P}
            return NIVEIS_P, vol_dict, "Pequeno (P)"
        else:
            vol_dict = {n: int(150 * fator) for n in NIVEIS_G}
            return NIVEIS_G, vol_dict, "Grande (G)"
    elif tipo == "Misto_Lado":
        if lado == "par":
            vol_dict = {n: int(150 * fator) for n in NIVEIS_G}
            return NIVEIS_G, vol_dict, "Grande (G)"
        else:
            vol_dict = {n: int(45 * fator) for n in NIVEIS_P}
            return NIVEIS_P, vol_dict, "Pequeno (P)"
    elif tipo == "Misto_Lado_15":
        if lado == "par":
            vol_dict = {n: int(80 * fator) for n in NIVEIS_M}
            return NIVEIS_M, vol_dict, "Médio (M)"
        else:
            vol_dict = {n: int(150 * fator) for n in NIVEIS_G}
            return NIVEIS_G, vol_dict, "Grande (G)"

    return NIVEIS_P, {n: int(45 * fator) for n in NIVEIS_P}, "Padrão"

# Inicialização do Estado
if 'temporada_atual' not in st.session_state:
    st.session_state.temporada_atual = "Meia-Estação"

if 'base_dados_cd' not in st.session_state:
    st.session_state.base_dados_cd = {}
    for r_nome, r_cfg in ESTRUTURA_CD.items():
        lista_lados = [("impar", r_cfg.get("cols_impar", [])), ("par", r_cfg.get("cols_par", []))]
        if "cols_seq" in r_cfg:
            lista_lados = [("seq", r_cfg["cols_seq"])]
            
        for lado, cols in lista_lados:
            for c in cols:
                l_param = "par" if r_nome == "Rua 11" else ("impar" if lado == "seq" else lado)
                niveis, _, _ = obter_niveis_e_capacidade_pecas(r_nome, c, l_param, st.session_state.temporada_atual)
                for n in niveis:
                    chave_casulo = f"{r_nome}|{lado}|{c:03d}|{n}"
                    st.session_state.base_dados_cd[chave_casulo] = 0 

if 'busca_destaque' not in st.session_state:
    st.session_state.busca_destaque = None
if 'aba_ativa_selecionada' not in st.session_state:
    st.session_state.aba_ativa_selecionada = "🏠 Tela Inicial (Geral)"


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
        font-size: 10px;
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

# SIDEBAR: NAVEGAÇÃO E TEMPORADA
st.sidebar.markdown("<h2 style='color: #ffcc00; text-align: center;'>⚙️ NAVEGAÇÃO</h2>", unsafe_allow_html=True)

opcoes_telas = ["🏠 Tela Inicial (Geral)", "📦 Visualizador de Casulos", "📥 Entrada de Dados / Abastecimento"]
st.session_state.aba_ativa_selecionada = st.sidebar.radio("Selecione a Tela:", opcoes_telas, index=opcoes_telas.index(st.session_state.aba_ativa_selecionada))

st.sidebar.markdown("---")
st.sidebar.markdown("<h4 style='color: #ffcc00; text-align: center;'>☀️❄️ Inteligência Sazonal</h4>", unsafe_allow_html=True)
c_bt1, c_bt2, c_bt3 = st.sidebar.columns(3)
with c_bt1:
    if st.button("Verão"): st.session_state.temporada_atual = "Verão"
with c_bt2:
    if st.button("Meia"): st.session_state.temporada_atual = "Meia-Estação"
with c_bt3:
    if st.button("Inverno"): st.session_state.temporada_atual = "Inverno"

st.sidebar.info(f"Mix Atual: **{st.session_state.temporada_atual}**")

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
# TELA 1: TELA INICIAL (PAINEL DE PEÇAS)
# ==========================================
if st.session_state.aba_ativa_selecionada == "🏠 Tela Inicial (Geral)":
    st.markdown("<h3 style='text-align: center; color: #ffcc00;'>📊 Painel Geral de Ocupação em Peças</h3>", unsafe_allow_html=True)
    
    total_pecas_capacidade = 0
    total_pecas_atuais = 0
    casulos_livres = 0
    total_casulos = len(st.session_state.base_dados_cd)

    for chave, pecas_atuais in st.session_state.base_dados_cd.items():
        r_nome, lado, c_str, n = chave.split("|")
        l_param = "par" if r_nome == "Rua 11" else ("impar" if lado == "seq" else lado)
        _, cap_dict, _ = obter_niveis_e_capacidade_pecas(r_nome, int(c_str), l_param, st.session_state.temporada_atual)
        p_max = cap_dict.get(n, 10)
        total_pecas_capacidade += p_max
        total_pecas_atuais += pecas_atuais
        if pecas_atuais == 0:
            casulos_livres += 1

    pct_geral = (total_pecas_atuais / total_pecas_capacidade * 100) if total_pecas_capacidade > 0 else 0.0

    kcol1, kcol2, kcol3, kcol4 = st.columns(4)
    with kcol1: st.markdown(f"<div class='card-dashboard'><h5>Total Casulos</h5><h2>{total_casulos:,}</h2></div>", unsafe_allow_html=True)
    with kcol2: st.markdown(f"<div class='card-dashboard'><h5>Ocupação Média</h5><h2>{pct_geral:.1f}%</h2></div>", unsafe_allow_html=True)
    with kcol3: st.markdown(f"<div class='card-dashboard'><h5>Casulos Zerados</h5><h2>{casulos_livres:,}</h2></div>", unsafe_allow_html=True)
    with kcol4: st.markdown(f"<div class='card-dashboard'><h5>Peças Armazenadas</h5><h2>{total_pecas_atuais:,} un</h2></div>", unsafe_allow_html=True)
    
    st.write("---")
    st.markdown("<h4 style='text-align: center; color: #ffcc00;'>🗺️ Mapa de Calor por Rua (Contagem de Peças)</h4>", unsafe_allow_html=True)

    def obter_classe_cor(pct):
        if pct == 0: return "cor-verde"
        elif pct < 50: return "cor-verde"
        elif pct <= 80: return "cor-amarelo"
        elif pct < 100: return "cor-laranja"
        else: return "cor-vermelho"

    ruas_nomes = list(ESTRUTURA_CD.keys())
    bloco_cols = st.columns(3)
    
    for idx, rua in enumerate(ruas_nomes):
        col_alvo = bloco_cols[idx % 3]
        
        p_rua_max = 0
        p_rua_atual = 0
        for chave, p_at in st.session_state.base_dados_cd.items():
            r_n, lado_r, c_r, n_r = chave.split("|")
            if r_n == rua:
                l_param = "par" if rua == "Rua 11" else ("impar" if lado_r == "seq" else lado_r)
                _, c_d, _ = obter_niveis_e_capacidade_pecas(rua, int(c_r), l_param, st.session_state.temporada_atual)
                p_rua_max += c_d.get(n_r, 10)
                p_rua_atual += p_at
        
        pct_rua = (p_rua_atual / p_rua_max * 100) if p_rua_max > 0 else 0.0
        classe_cor = obter_classe_cor(pct_rua)
        
        with col_alvo:
            st.markdown(f"""
            <div class="planta-rua-bloco">
                <div style="font-weight: bold; font-size: 15px; color: #ffcc00;">{rua}</div>
                <div style="font-size: 12px; margin-top: 2px; color: #8892b0;">{p_rua_atual:,} / {p_rua_max:,} un ({pct_rua:.1f}%)</div>
                <div class="bar-container">
                    <div class="bar-fill {classe_cor}" style="width: {pct_rua}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ==========================================
# TELA 2: VISUALIZADOR DE CASULOS
# ==========================================
elif st.session_state.aba_ativa_selecionada == "📦 Visualizador de Casulos":
    lista_ruas = list(ESTRUTURA_CD.keys())
    rua_inicial_idx = 0
    if st.session_state.busca_destaque and st.session_state.busca_destaque['rua'] in lista_ruas:
        rua_inicial_idx = lista_ruas.index(st.session_state.busca_destaque['rua'])

    rua_selecionada = st.selectbox("Selecione a Rua para Inspeção Detalhada:", lista_ruas, index=rua_inicial_idx)
    
    st.markdown(f"<h3 style='text-align: center; color: #ffcc00;'>📍 Malha Física do Corredor: <b>{rua_selecionada}</b></h3>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="topicos-legenda">
        <b style="color: #ffcc00; display: block; margin-bottom: 6px; text-align: center;">📋 Legenda de Ocupação por Quantidade de Peças:</b>
        <ul>
            <li><span style="color: #45a29e; font-weight: bold;">Verde:</span> Disponível / Baixa (&lt; 50%)</li>
            <li><span style="color: #ffcc00; font-weight: bold;">Amarelo:</span> Moderado (50% a 80%)</li>
            <li><span style="color: #f39c12; font-weight: bold;">Laranja:</span> Alerta (81% a 99%)</li>
            <li><span style="color: #e74c3c; font-weight: bold;">Vermelho:</span> Saturado (100%)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    config_rua = ESTRUTURA_CD.get(rua_selecionada, {})
    
    # RENDERIZAÇÃO ESPECIAL PARA A RUA 14 (DIVIDIDA POR BLOCOS DE TIPOLOGIA)
    if rua_selecionada == "Rua 14":
        st.markdown("<p style='text-align:center; color:#8892b0; font-size:13px;'>Corredor segmentado por Tipologia Estrutural (Madeira, Metal e Carrinhos)</p>", unsafe_allow_html=True)
        
        # Definição dos Blocos da Rua 14
        blocos_r14 = [
            ("🌲 Bloco 1: Prateleiras de Madeira Gigante (Colunas 01 a 23)", list(range(1, 24))),
            ("🔩 Bloco 2: Prateleiras de Metal Profundo (Colunas 24 a 31)", list(range(24, 32))),
            ("🛒 Bloco 3: Setor de Carrinhos (Colunas 32 a 41)", list(range(32, 42))),
            ("⚙️ Bloco 4: Prateleiras de Metal Raso (Colunas 42 a 48)", list(range(42, 49)))
        ]
        
        for titulo_bloco, cols_bloco in blocos_r14:
            st.markdown(f"<div class='lado-container'>", unsafe_allow_html=True)
            st.markdown(f"<div class='lado-titulo'>{titulo_bloco}</div>", unsafe_allow_html=True)
            
            # Pega os níveis específicos deste bloco através da primeira coluna
            niveis_bloco, _, desc_bloco = obter_niveis_e_capacidade_pecas(rua_selecionada, cols_bloco[0], "impar", st.session_state.temporada_atual)
            niveis_ordenados = sorted(niveis_bloco)
            
            for nivel in niveis_ordenados:
                grid_bloco = st.columns(len(cols_bloco) + 1)
                with grid_bloco[0]:
                    st.markdown(f"<div style='line-height:28px; text-align:center; font-weight:bold; color:#8892b0; font-size: 10px;'>{nivel}</div>", unsafe_allow_html=True)
                for idx, col_num in enumerate(cols_bloco):
                    with grid_bloco[idx + 1]:
                        niveis_col, caps_col, _ = obter_niveis_e_capacidade_pecas(rua_selecionada, col_num, "impar", st.session_state.temporada_atual)
                        if nivel not in niveis_col:
                            st.markdown(f"<div class='nicho' style='background: transparent;'>-</div>", unsafe_allow_html=True)
                            continue

                        chave = f"{rua_selecionada}|seq|{col_num:03d}|{nivel}"
                        pecas_max = caps_col.get(nivel, 10)
                        pecas_atuais = st.session_state.base_dados_cd.get(chave, 0)
                        pct_ocupacao = (pecas_atuais / pecas_max) * 100 if pecas_max > 0 else 0

                        status = "livre"
                        if pct_ocupacao >= 100: status = "saturado"
                        elif pct_ocupacao >= 81: status = "saturado"
                        elif pct_ocupacao >= 50: status = "atencao"

                        is_destaque = (st.session_state.busca_destaque and st.session_state.busca_destaque['rua'] == rua_selecionada and st.session_state.busca_destaque['nivel'] == nivel and st.session_state.busca_destaque['col'] == col_num)
                        classe_destaque = "destaque-ativo" if is_destaque else ""

                        st.markdown(f"<div class='nicho {status} {classe_destaque}' title='{col_num:03d}-{nivel} | {pecas_atuais}/{pecas_max} peças ({pct_ocupacao:.1f}%)'>{col_num:03d}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # RENDERIZAÇÃO ESPECIAL PARA A RUA 11 (UNILATERAL AMPLIADA) OU OUTRAS SEQUENCIAIS
    elif "cols_seq" in config_rua or rua_selecionada == "Rua 11":
        if rua_selecionada == "Rua 11":
            todas_colunas = config_rua.get("cols_par", [])
            modo_unilateral = True
        else:
            todas_colunas = config_rua.get("cols_seq", [])
            modo_unilateral = False
        
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
            niveis_exibicao, _, tipo_desc = obter_niveis_e_capacidade_pecas(rua_selecionada, colunas_exemplo[0] if colunas_exemplo else 22, l_ref, st.session_state.temporada_atual)
            niveis_ordenados = sorted(niveis_exibicao)

            st.markdown(f"<p style='text-align:center; color:#8892b0; font-size:12px;'>Especificação: <b>{tipo_desc}</b> | Estação: <b>{st.session_state.temporada_atual}</b></p>", unsafe_allow_html=True)

            st.markdown("<div class='lado-container'>", unsafe_allow_html=True)
            st.markdown(f"<div class='lado-titulo'>Corredor Sequencial / Unilateral ({rua_selecionada})</div>", unsafe_allow_html=True)
            
            for nivel in niveis_ordenados:
                grid_seq = st.columns(len(colunas_exemplo) + 1)
                with grid_seq[0]:
                    st.markdown(f"<div style='line-height:28px; text-align:center; font-weight:bold; color:#8892b0; font-size: 10px;'>{nivel}</div>", unsafe_allow_html=True)
                for idx, col_num in enumerate(colunas_exemplo):
                    with grid_seq[idx + 1]:
                        l_param_col = "par" if rua_selecionada == "Rua 11" else "impar"
                        niveis_col, caps_col, _ = obter_niveis_e_capacidade_pecas(rua_selecionada, col_num, l_param_col, st.session_state.temporada_atual)
                        if nivel not in niveis_col:
                            st.markdown(f"<div class='nicho' style='background: transparent;'>-</div>", unsafe_allow_html=True)
                            continue

                        lado_chave = "par" if rua_selecionada == "Rua 11" else "seq"
                        chave = f"{rua_selecionada}|{lado_chave}|{col_num:03d}|{nivel}"
                        pecas_max = caps_col.get(nivel, 10)
                        pecas_atuais = st.session_state.base_dados_cd.get(chave, 0)
                        pct_ocupacao = (pecas_atuais / pecas_max) * 100 if pecas_max > 0 else 0

                        status = "livre"
                        if pct_ocupacao >= 100: status = "saturado"
                        elif pct_ocupacao >= 81: status = "saturado"
                        elif pct_ocupacao >= 50: status = "atencao"

                        is_destaque = (st.session_state.busca_destaque and st.session_state.busca_destaque['rua'] == rua_selecionada and st.session_state.busca_destaque['nivel'] == nivel and st.session_state.busca_destaque['col'] == col_num)
                        classe_destaque = "destaque-ativo" if is_destaque else ""

                        st.markdown(f"<div class='nicho {status} {classe_destaque}' title='{col_num:03d}-{nivel} | {pecas_atuais}/{pecas_max} peças ({pct_ocupacao:.1f}%)'>{col_num:03d}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    else:
        # RENDERIZAÇÃO PADRÃO DE DUPLO LADO (ÍMPAR E PAR) PARA AS OUTRAS RUAS
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

            exemplo_col_ref = colunas_impares[0] if colunas_impares else (colunas_pares[0] if colunas_pares else 1)
            l_param_ref = "impar" if colunas_impares else "par"

            niveis_exibicao, _, tipo_desc = obter_niveis_e_capacidade_pecas(rua_selecionada, exemplo_col_ref, l_param_ref, st.session_state.temporada_atual)
            niveis_ordenados = sorted(niveis_exibicao)

            st.markdown(f"<p style='text-align:center; color:#8892b0; font-size:12px;'>Especificação: <b>{tipo_desc}</b> | Estação: <b>{st.session_state.temporada_atual}</b></p>", unsafe_allow_html=True)

            col_esq_layout, col_dir_layout = st.columns(2)
            
            with col_esq_layout:
                st.markdown("<div class='lado-container'>", unsafe_allow_html=True)
                st.markdown("<div class='lado-titulo'>◀ Lado Ímpar</div>", unsafe_allow_html=True)
                if colunas_impares:
                    for nivel in niveis_ordenados:
                        grid_impar = st.columns(len(colunas_impares) + 1)
                        with grid_impar[0]:
                            st.markdown(f"<div style='line-height:28px; text-align:center; font-weight:bold; color:#8892b0; font-size: 10px;'>{nivel}</div>", unsafe_allow_html=True)
                        for idx, col_num in enumerate(colunas_impares):
                            with grid_impar[idx + 1]:
                                niveis_col, caps_col, _ = obter_niveis_e_capacidade_pecas(rua_selecionada, col_num, "impar", st.session_state.temporada_atual)
                                if nivel not in niveis_col:
                                    st.markdown(f"<div class='nicho' style='background: transparent;'>-</div>", unsafe_allow_html=True)
                                    continue

                                chave = f"{rua_selecionada}|impar|{col_num:03d}|{nivel}"
                                pecas_max = caps_col.get(nivel, 10)
                                pecas_atuais = st.session_state.base_dados_cd.get(chave, 0)
                                pct_ocupacao = (pecas_atuais / pecas_max) * 100 if pecas_max > 0 else 0

                                status = "livre"
                                if pct_ocupacao >= 100: status = "saturado"
                                elif pct_ocupacao >= 81: status = "saturado"
                                elif pct_ocupacao >= 50: status = "atencao"

                                is_destaque = (st.session_state.busca_destaque and st.session_state.busca_destaque['rua'] == rua_selecionada and st.session_state.busca_destaque['nivel'] == nivel and st.session_state.busca_destaque['col'] == col_num)
                                classe_destaque = "destaque-ativo" if is_destaque else ""

                                st.markdown(f"<div class='nicho {status} {classe_destaque}' title='{col_num:03d}-{nivel} | {pecas_atuais}/{pecas_max} peças ({pct_ocupacao:.1f}%)'>{col_num:03d}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color: #8892b0; font-size: 12px; padding: 20px;'>Sem casulos neste lado.</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col_dir_layout:
                st.markdown("<div class='lado-container'>", unsafe_allow_html=True)
                st.markdown("<div class='lado-titulo'>Lado Par ▶</div>", unsafe_allow_html=True)
                if colunas_pares:
                    for nivel in niveis_ordenados:
                        grid_par = st.columns(len(colunas_pares) + 1)
                        with grid_par[0]:
                            st.markdown(f"<div style='line-height:28px; text-align:center; font-weight:bold; color:#8892b0; font-size: 10px;'>{nivel}</div>", unsafe_allow_html=True)
                        for idx, col_num in enumerate(colunas_pares):
                            with grid_par[idx + 1]:
                                l_param_par = "par" 
                                niveis_col, caps_col, _ = obter_niveis_e_capacidade_pecas(rua_selecionada, col_num, l_param_par, st.session_state.temporada_atual)
                                if nivel not in niveis_col:
                                    st.markdown(f"<div class='nicho' style='background: transparent;'>-</div>", unsafe_allow_html=True)
                                    continue

                                chave = f"{rua_selecionada}|par|{col_num:03d}|{nivel}"
                                pecas_max = caps_col.get(nivel, 10)
                                pecas_atuais = st.session_state.base_dados_cd.get(chave, 0)
                                pct_ocupacao = (pecas_atuais / pecas_max) * 100 if pecas_max > 0 else 0

                                status = "livre"
                                if pct_ocupacao >= 100: status = "saturado"
                                elif pct_ocupacao >= 81: status = "saturado"
                                elif pct_ocupacao >= 50: status = "atencao"

                                is_destaque = (st.session_state.busca_destaque and st.session_state.busca_destaque['rua'] == rua_selecionada and st.session_state.busca_destaque['nivel'] == nivel and st.session_state.busca_destaque['col'] == col_num)
                                classe_destaque = "destaque-ativo" if is_destaque else ""

                                st.markdown(f"<div class='nicho {status} {classe_destaque}' title='{col_num:03d}-{nivel} | {pecas_atuais}/{pecas_max} peças ({pct_ocupacao:.1f}%)'>{col_num:03d}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<p style='color: #8892b0; font-size: 12px; padding: 20px;'>Sem casulos neste lado.</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)


# ==========================================
# TELA 3: ENTRADA DE DADOS / ABASTECIMENTO
# ==========================================
elif st.session_state.aba_ativa_selecionada == "📥 Entrada de Dados / Abastecimento":
    st.markdown("<h3 style='text-align: center; color: #ffcc00;'>📥 Entrada de Dados por Quantidade de Peças</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #8892b0; text-align: center;'>Gerencie as peças alocadas nos casulos. Temporada ativa: <b>{st.session_state.temporada_atual}</b></p>", unsafe_allow_html=True)

    tab_cad1, tab_cad2 = st.tabs(["✏️ Atualização de Casulo Individual", "🧹 Ações Globais na Base"])

    with tab_cad1:
        st.markdown("#### Configurar Quantidade de Peças do Casulo")
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        with col_f1:
            rua_cad = st.selectbox("Rua", list(ESTRUTURA_CD.keys()), key="rcad")
        
        cfg_r_cad = ESTRUTURA_CD.get(rua_cad, {})
        
        with col_f2:
            if "cols_seq" in cfg_r_cad:
                lado_cad = "seq"
                st.selectbox("Lado", ["Sequencial (Rua 14)"], key="lcad_seq_disabled", disabled=True)
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
        niveis_cad_lista, caps_cad_dict, _ = obter_niveis_e_capacidade_pecas(rua_cad, col_cad, l_param_func, st.session_state.temporada_atual)
        
        with col_f4:
            if niveis_cad_lista:
                nivel_cad = st.selectbox("Nível", niveis_cad_lista, key="ncad")
            else:
                nivel_cad = st.selectbox("Nível", ["B"], key="ncad_vazio")

        pecas_max_casulo = caps_cad_dict.get(nivel_cad, 50)
        chave_alvo = f"{rua_cad}|{lado_cad}|{int(col_cad):03d}|{nivel_cad}"
        pecas_atuais_existente = st.session_state.base_dados_cd.get(chave_alvo, 0)

        st.info(f"Capacidade Máxima deste Casulo ({rua_cad} - Col {col_cad:03d} - Nível {nivel_cad}): **{pecas_max_casulo} peças** (Mix: {st.session_state.temporada_atual})")

        nova_qtd_input = st.number_input("Quantidade Atual de Peças:", min_value=0, max_value=int(pecas_max_casulo), value=int(pecas_atuais_existente), step=1)

        if st.button("Salvar Quantidade de Peças", type="primary"):
            st.session_state.base_dados_cd[chave_alvo] = int(nova_qtd_input)
            st.success(f"Casulo {rua_cad} - {col_cad:03d}-{nivel_cad} atualizado para {nova_qtd_input} peças!")
            st.rerun()

    with tab_cad2:
        st.markdown("#### Manutenção Geral da Base de Dados")
        st.warning("⚠️ Atenção: Os botões abaixo modificam permanentemente a quantidade de peças em todo o CD na memória.")

        c_A, c_B = st.columns(2)
        with c_A:
            if st.button("Zerar Todos os Casulos (0 Peças)"):
                for k in st.session_state.base_dados_cd.keys():
                    st.session_state.base_dados_cd[k] = 0
                st.success("Todos os casulos foram zerados com sucesso!")
                st.rerun()
        with c_B:
            if st.button("Popular com Dados Simulados Aleatórios"):
                np.random.seed(321)
                for k in st.session_state.base_dados_cd.keys():
                    r_n, l_n, c_n, n_n = k.split("|")
                    l_param_pop = "par" if r_n == "Rua 11" else ("impar" if l_n == "seq" else l_n)
                    _, c_d, _ = obter_niveis_e_capacidade_pecas(r_n, int(c_n), l_param_pop, st.session_state.temporada_atual)
                    p_max_val = c_d.get(n_n, 50)
                    st.session_state.base_dados_cd[k] = int(np.random.choice([0, int(p_max_val * 0.3), int(p_max_val * 0.7), p_max_val]))
                st.success("Base populada com dados de teste em peças!")
                st.rerun()