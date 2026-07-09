import chess
import chess.svg
import streamlit as st

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

    # 2. Configura as setas dinâmicas e marcações de quadrados
    setas_analiticas = []
    dados_tabela = []

    # Calcula os lances legais da posição dinamicamente
    for move in board.legal_moves:
        lance_san = board.san(move)
        
        # Adiciona a seta azul para cada lance legal (cor genérica por enquanto)
        setas_analiticas.append(chess.svg.Arrow(move.from_square, move.to_square, color="#3498db"))
        
        # Prepara os dados do lance para exibir na tabela
        dados_tabela.append({
            "Lance": lance_san,
            "Status": "A calcular...", # Status real virá da Syzygy tablebase futuramente
            "DTZ": "?",
            "Ação": "Seta Azul",
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

    # Exibe informações textuais lado a lado
    st.info("💡 **Efeito Borboleta:** Mover o Rei para d1 altera o resultado de GANHO para EMPATE.")

    # Tabela simulando os dados calculados pelo backend
    st.write("### Lances Disponíveis:")
    st.dataframe(dados_tabela)

    # Input para o usuário testar novas FENs
    nova_fen = st.text_input("Modificar posição (Insira uma FEN):", st.session_state.fen)
    if nova_fen != st.session_state.fen:
        st.session_state.fen = nova_fen
        st.rerun()