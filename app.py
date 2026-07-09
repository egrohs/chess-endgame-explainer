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
    # No seu app real, as cores e lances virão das respostas da Tablebase (DTZ/WDL)
    setas_analiticas = [
        # Seta Verde (Melhor Lance - Ganha): ex: e2 para e4
        chess.svg.Arrow(
            chess.E2, chess.E4, color="#27ae60"
        ),  # Verde Brilhante
        # Seta Vermelha (Erro/Blunder - Perde): ex: e1 para d1
        chess.svg.Arrow(
            chess.E1, chess.D1, color="#c0392b"
        ),  # Vermelho Alerta[cite: 1]
    ]

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
    st.dataframe(
        [
            {
                "Lance": "e4",
                "Status": "Ganho",
                "DTZ": "+18",
                "Ação": "Seta Verde",
            },  #[cite: 1]
            {
                "Lance": "Kd1",
                "Status": "Empate",
                "DTZ": "0",
                "Ação": "Seta Cinza",
            },  #[cite: 1]
            {
                "Lance": "Kf1",
                "Status": "Derrota",
                "DTZ": "-12",
                "Ação": "Seta Vermelha",
            },  #[cite: 1]
        ]
    )

    # Input para o usuário testar novas FENs
    nova_fen = st.text_input("Modificar posição (Insira uma FEN):", st.session_state.fen)
    if nova_fen != st.session_state.fen:
        st.session_state.fen = nova_fen
        st.rerun()