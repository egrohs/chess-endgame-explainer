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

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Visualização Teórica do Tabuleiro")

    # Consulta a API pública do Lichess que provê dados da Syzygy gratuitamente
    @st.cache_data
    def obter_dados_syzygy(fen):
        # A API do Lichess lida melhor com a FEN se trocarmos espaços por underscores
        url = f"http://tablebase.lichess.ovh/standard?fen={fen.replace(' ', '_')}"
        try:
            resposta = requests.get(url, timeout=5)
            resposta.raise_for_status()
            return resposta.json()
        except:
            return None

    dados_syzygy = obter_dados_syzygy(board.fen())
    # Cria um dicionário rápido indexado pelo UCI do lance (ex: 'e1d1')
    lances_avaliados = {m["uci"]: m for m in dados_syzygy["moves"]} if dados_syzygy else {}

    # 2. Configura as setas dinâmicas e marcações de quadrados
    setas_analiticas = []
    dados_tabela = []

    # Calcula os lances legais da posição dinamicamente
    for move in board.legal_moves:
        lance_san = board.san(move)
        lance_uci = move.uci()
        
        # Valores padrão
        status = "A calcular..."
        dtz = "?"
        dtm = "?"
        cor = "#3498db" # Azul
        acao = "Seta Azul"

        if lance_uci in lances_avaliados:
            dados = lances_avaliados[lance_uci]
            
            # A API do Lichess retorna um campo 'category' explícito (win, draw, loss)
            # que já está na perspectiva correta do lance realizado, evitando confusões.
            categoria = dados.get("category", "unknown")
            
            dtz_val = dados.get("dtz")
            dtz = str(abs(dtz_val)) if dtz_val is not None else "-"
            
            dtm_val = dados.get("dtm")
            dtm = str(abs(dtm_val)) if dtm_val is not None else "-"

            # A avaliação ('category') na lista de lances é dada na perspectiva do OPONENTE (que fará o próximo lance).
            # Logo, se o oponente recebe um "loss" (derrota), significa que o nosso lance nos garante a vitória ("Ganho").
            if categoria in ["loss", "blessed"]:
                status, cor, acao = "Ganho", "#27ae60", "Seta Verde"
            elif categoria in ["win", "cursed"]:
                status, cor, acao = "Derrota", "#c0392b", "Seta Vermelha"
            elif categoria == "draw":
                status, cor, acao = "Empate", "#7f8c8d", "Seta Cinza"

        # Adiciona a seta colorida de acordo com a avaliação real do lance
        setas_analiticas.append(chess.svg.Arrow(move.from_square, move.to_square, color=cor))
        
        # Prepara os dados do lance para exibir na tabela
        dados_tabela.append({
            "Lance": lance_san,
            "Status": status,
            "DTZ": dtz,
            "DTM": dtm,
            "Ação": acao,
        })

    # Destacar casas críticas (ex: casas de empate ou oposição)
    casas_destacadas = chess.SquareSet([chess.E3, chess.E5])

    # 3. Gera o SVG do tabuleiro usando o python-chess
    board_svg = chess.svg.board(
        board=board,
        arrows=setas_analiticas,
        fill=dict.fromkeys(
            casas_destacadas, "#f39c1255"
        ),  # Laranja semitransparente
        size=500,
    )

    # 4. Renderiza o SVG diretamente no navegador via Streamlit
    st.write(board_svg, unsafe_allow_html=True)

with col2:
    st.subheader("Painel de Métricas (Syzygy)")

    # 1. Painel de Status da Posição Atual (Raiz)
    if dados_syzygy:
        st.write("### Avaliação da Posição Atual")
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

        # Exibição bonita usando st.metric em colunas
        c1, c2, c3 = st.columns(3)
        c1.metric("Status", status_txt)
        c2.metric("DTZ (Zerar)", dtz_txt)
        c3.metric("DTM (Mate)", dtm_txt)

    # 2. Estatísticas Globais das Posições Únicas (Ex: KPvK)
    def classificar_final(board):
        pieces_w = []
        pieces_b = []
        for pt in [chess.KING, chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT, chess.PAWN]:
            pieces_w.extend([chess.piece_symbol(pt).upper()] * len(board.pieces(pt, chess.WHITE)))
            pieces_b.extend([chess.piece_symbol(pt).upper()] * len(board.pieces(pt, chess.BLACK)))
        
        # Ordena pela importância: K, Q, R, B, N, P
        order = {"K": 0, "Q": 1, "R": 2, "B": 3, "N": 4, "P": 5}
        pieces_w.sort(key=lambda x: order[x])
        pieces_b.sort(key=lambda x: order[x])
        str_w = "".join(pieces_w)
        str_b = "".join(pieces_b)
        
        return f"{str_w}v{str_b}", f"{str_b}v{str_w}"

    # Estatísticas hardcoded das bases de dados clássicas de xadrez
    estatisticas_conhecidas = {
        "KPvK": {"win": "54.1%", "draw": "45.9%", "loss": "0.0%"},
        "KRvK": {"win": "98.5%", "draw": "1.5%", "loss": "0.0%"},
        "KQvK": {"win": "99.8%", "draw": "0.2%", "loss": "0.0%"},
        "KBBvK": {"win": "95.0%", "draw": "5.0%", "loss": "0.0%"},
        "KBNvK": {"win": "90.0%", "draw": "10.0%", "loss": "0.0%"},
        "KNNvK": {"win": "0.5%", "draw": "99.5%", "loss": "0.0%"}, # Exceção curiosa (KNN vs K quase sempre empata)
        "KBPvK": {"win": "65.0%", "draw": "35.0%", "loss": "0.0%"},
    }

    classe_w_b, classe_b_w = classificar_final(board)
    classe_exibida = classe_w_b
    stats = estatisticas_conhecidas.get(classe_w_b) or estatisticas_conhecidas.get(classe_b_w)
    
    st.write(f"### Estatísticas Globais ({classe_w_b})")
    if stats:
        s1, s2, s3 = st.columns(3)
        s1.metric("Vitória (Lado Forte)", stats["win"])
        s2.metric("Empate", stats["draw"])
        s3.metric("Derrota", stats["loss"])
    else:
        st.info(f"As estatísticas matemáticas exatas não estão mapeadas no código para esse material.")

    st.divider()

    # Exibe informações textuais lado a lado
    st.info("💡 **Efeito Borboleta:** Mover o Rei para d1 altera o resultado de GANHO para EMPATE.")

    # Tabela simulando os dados calculados pelo backend
    st.write("### Lances Disponíveis:")
    st.dataframe(dados_tabela)

    st.divider()

    st.write("### 🎮 Fazer um Lance Interativo")
    # Mapeia os lances legais para a notação algébrica clássica (SAN)
    lances_dict = {board.san(m): m for m in board.legal_moves}
    
    # Selectbox nativo do Streamlit para escolher o lance
    lance_selecionado = st.selectbox(
        "Escolha o lance que deseja jogar no tabuleiro:", 
        options=[""] + list(lances_dict.keys()), 
        format_func=lambda x: "Selecione um lance..." if x == "" else x
    )
    
    if st.button("Jogar Lance", type="primary"):
        if lance_selecionado:
            board.push(lances_dict[lance_selecionado])
            # Atualiza a FEN global da sessão e força o recarregamento (rerun)
            st.session_state.fen = board.fen()
            st.rerun()

    # Input para o usuário testar novas FENs
    nova_fen = st.text_input("Modificar posição (Insira uma FEN):", st.session_state.fen)
    if nova_fen != st.session_state.fen:
        st.session_state.fen = nova_fen
        st.rerun()