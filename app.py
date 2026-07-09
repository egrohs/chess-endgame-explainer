import chess
import chess.svg
import streamlit as st
import requests

st.set_page_config(layout="wide")
st.title("♟️ Analisador de Finais Espaciais")

# 1. Inicializa a posição (Exemplo: Final de Reis e Peão)
if "fen" not in st.session_state:
    # Posição clássica de teste
    st.session_state.fen = "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"

board = chess.Board(st.session_state.fen)

# Extração da lógica para funcionar de forma global antes do layout
@st.cache_data
def obter_dados_syzygy(fen):
    url = f"http://tablebase.lichess.ovh/standard?fen={fen.replace(' ', '_')}"
    try:
        resposta = requests.get(url, timeout=5)
        resposta.raise_for_status()
        return resposta.json()
    except:
        return None

def classificar_final(board):
    pieces_w = []
    pieces_b = []
    for pt in [chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]:
        pieces_w.extend([chess.piece_symbol(pt).upper()] * len(board.pieces(pt, chess.WHITE)))
        pieces_b.extend([chess.piece_symbol(pt).upper()] * len(board.pieces(pt, chess.BLACK)))
    
    order = {"K": 0, "Q": 1, "R": 2, "B": 3, "N": 4, "P": 5}
    pieces_w.sort(key=lambda x: order[x])
    pieces_b.sort(key=lambda x: order[x])
    str_w = "".join(pieces_w)
    str_b = "".join(pieces_b)
    
    return f"{str_w}v{str_b}", f"{str_b}v{str_w}"

dados_syzygy = obter_dados_syzygy(board.fen())
lances_avaliados = {m["uci"]: m for m in dados_syzygy["moves"]} if dados_syzygy else {}

setas_analiticas = []
dados_tabela = []

for move in board.legal_moves:
    lance_san = board.san(move)
    lance_uci = move.uci()
    
    status, dtz, dtm, cor, acao = "A calcular...", "?", "?", "#3498db", "Seta Azul"

    if lance_uci in lances_avaliados:
        dados = lances_avaliados[lance_uci]
        categoria = dados.get("category", "unknown")
        dtz_val = dados.get("dtz")
        dtz = str(abs(dtz_val)) if dtz_val is not None else "-"
        dtm_val = dados.get("dtm")
        dtm = str(abs(dtm_val)) if dtm_val is not None else "-"

        if categoria in ["loss", "blessed"]:
            status, cor, acao = "Ganho", "#27ae60", "Seta Verde"
        elif categoria in ["win", "cursed"]:
            status, cor, acao = "Derrota", "#c0392b", "Seta Vermelha"
        elif categoria == "draw":
            status, cor, acao = "Empate", "#7f8c8d", "Seta Cinza"

    setas_analiticas.append(chess.svg.Arrow(move.from_square, move.to_square, color=cor))
    dados_tabela.append({"Lance": lance_san, "Status": status, "DTZ": dtz, "DTM": dtm, "Ação": acao})

casas_destacadas = chess.SquareSet([chess.E3, chess.E5])
board_svg = chess.svg.board(
    board=board,
    arrows=setas_analiticas,
    fill=dict.fromkeys(casas_destacadas, "#f39c1255"),
    size=360, # Reduzido para caber sem scroll vertical
)

# 2. Configurando o Novo Layout Otimizado em 3 Colunas
col_board, col_metrics, col_moves = st.columns([1.1, 1.4, 1.5])

with col_board:
    st.markdown("#### Tabuleiro")
    st.write(board_svg, unsafe_allow_html=True)
    # Input da FEN agora fica compacto debaixo do tabuleiro
    nova_fen = st.text_input("Modificar posição (FEN):", st.session_state.fen)
    if nova_fen != st.session_state.fen:
        st.session_state.fen = nova_fen
        st.rerun()

with col_metrics:
    st.markdown("#### Avaliação da Posição")
    if dados_syzygy:
        cat_root = dados_syzygy.get("category", "unknown")
        dtz_root = dados_syzygy.get("dtz")
        dtm_root = dados_syzygy.get("dtm")
        vez = "Brancas" if board.turn == chess.WHITE else "Pretas"
        oponente = "Pretas" if board.turn == chess.WHITE else "Brancas"

        if cat_root in ["win", "cursed"]:
            status_txt = f"Vitória: {vez}"
        elif cat_root in ["loss", "blessed"]:
            status_txt = f"Vitória: {oponente}"
        else:
            status_txt = "Empate Forçado"

        dtz_txt = str(abs(dtz_root)) if dtz_root is not None else "-"
        dtm_txt = str(abs(dtm_root)) if dtm_root is not None else "-"

        c1, c2, c3 = st.columns(3)
        c1.metric("Status", status_txt)
        c2.metric("DTZ", dtz_txt)
        c3.metric("DTM", dtm_txt)

    estatisticas_conhecidas = {
        "KPvK": {"win": "54.1%", "draw": "45.9%", "loss": "0.0%"},
        "KRvK": {"win": "98.5%", "draw": "1.5%", "loss": "0.0%"},
        "KQvK": {"win": "99.8%", "draw": "0.2%", "loss": "0.0%"},
        "KBBvK": {"win": "95.0%", "draw": "5.0%", "loss": "0.0%"},
        "KBNvK": {"win": "90.0%", "draw": "10.0%", "loss": "0.0%"},
        "KNNvK": {"win": "0.5%", "draw": "99.5%", "loss": "0.0%"},
        "KBPvK": {"win": "65.0%", "draw": "35.0%", "loss": "0.0%"},
    }

    classe_w_b, classe_b_w = classificar_final(board)
    stats = estatisticas_conhecidas.get(classe_w_b) or estatisticas_conhecidas.get(classe_b_w)
    
    st.markdown(f"#### Estatísticas ({classe_w_b})")
    if stats:
        s1, s2, s3 = st.columns(3)
        s1.metric("Vitória", stats["win"])
        s2.metric("Empate", stats["draw"])
        s3.metric("Derrota", stats["loss"])
    else:
        st.info("Estatísticas não mapeadas no código.")

    st.info("💡 **Efeito Borboleta:** Mover o Rei para d1 altera o resultado de GANHO para EMPATE.")

with col_moves:
    st.markdown("#### Lances Disponíveis")
    lances_dict = {board.san(m): m for m in board.legal_moves}
    
    # Alinha a caixa de seleção de lances junto ao botão na mesma linha
    c_sel, c_btn = st.columns([3, 1])
    with c_sel:
        lance_selecionado = st.selectbox(
            "Lance Interativo", 
            options=[""] + list(lances_dict.keys()), 
            format_func=lambda x: "Selecione um lance..." if x == "" else x,
            label_visibility="collapsed"
        )
    with c_btn:
        if st.button("Jogar", type="primary", use_container_width=True):
            if lance_selecionado:
                board.push(lances_dict[lance_selecionado])
                st.session_state.fen = board.fen()
                st.rerun()
                
    # Trava a altura do dataframe para evitar que ele estique a coluna até o fim da página
    st.dataframe(dados_tabela, height=250, use_container_width=True)