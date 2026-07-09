import chess
import chess.svg
import chess.engine
import streamlit as st
import requests

st.set_page_config(layout="wide")

# Reduzir o espaço vazio no topo injetando CSS globalmente
st.markdown("""
    <style>
        .block-container { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

st.title("♟️ Analisador de Finais Espaciais")

# 1. Inicializa a posição (Exemplo: Final de Reis e Peão)
if "fen" not in st.session_state:
    # Posição clássica de teste
    st.session_state.fen = "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1"
    st.session_state.history = [st.session_state.fen]
    st.session_state.history_idx = 0

def registrar_nova_fen(nova_fen):
    st.session_state.fen = nova_fen
    st.session_state.history = st.session_state.history[:st.session_state.history_idx + 1]
    st.session_state.history.append(nova_fen)
    st.session_state.history_idx += 1

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

def calcular_regra_quadrado(board):
    casas_quadrado = set()
    mensagens = []
    
    for sq in board.pieces(chess.PAWN, chess.WHITE):
        f, r = chess.square_file(sq), chess.square_rank(sq)
        
        # Identifica se é um peão passado
        is_passed = True
        for enemy_sq in board.pieces(chess.PAWN, chess.BLACK):
            ef, er = chess.square_file(enemy_sq), chess.square_rank(enemy_sq)
            if abs(f - ef) <= 1 and er > r:
                is_passed = False
                break
                
        if not is_passed:
            continue
            
        # Ajuste de turnos e regra de 2 casas iniciais
        eff_r = r
        if board.turn == chess.WHITE:
            if r == 1:
                eff_r = 3 
            else:
                eff_r = r + 1
        else:
            if r == 1:
                eff_r = 2 
            else:
                eff_r = r
                
        if eff_r > 7:
            continue
            
        tamanho = 7 - eff_r + 1
        rank_inicial = r if r == 1 else eff_r
        ranks = range(rank_inicial, 8)
        
        enemy_king_sq = board.king(chess.BLACK)
        enemy_k_f = chess.square_file(enemy_king_sq) if enemy_king_sq else f
        
        if enemy_k_f < f:
            files = range(max(0, f - tamanho + 1), f + 1)
        else:
            files = range(f, min(8, f + tamanho))
            
        quadrado_atual = set()
        for rr in ranks:
            for ff in files:
                quadrado_atual.add(chess.square(ff, rr))
                
        casas_quadrado.update(quadrado_atual)
        
        if enemy_king_sq is not None:
            kr = chess.square_rank(enemy_king_sq)
            kf = chess.square_file(enemy_king_sq)
            dentro = (eff_r <= kr <= 7) and (kf in files)
            
            nome_casa = chess.square_name(sq)
            if dentro:
                mensagens.append(f"O Rei Preto **alcança** o peão branco em {nome_casa}.")
            else:
                mensagens.append(f"O Rei Preto **não alcança** o peão branco em {nome_casa}.")
                
    for sq in board.pieces(chess.PAWN, chess.BLACK):
        f, r = chess.square_file(sq), chess.square_rank(sq)
        
        is_passed = True
        for enemy_sq in board.pieces(chess.PAWN, chess.WHITE):
            ef, er = chess.square_file(enemy_sq), chess.square_rank(enemy_sq)
            if abs(f - ef) <= 1 and er < r:
                is_passed = False
                break
                
        if not is_passed:
            continue
            
        eff_r = r
        if board.turn == chess.BLACK:
            if r == 6:
                eff_r = 4
            else:
                eff_r = r - 1
        else:
            if r == 6:
                eff_r = 5
            else:
                eff_r = r
                
        if eff_r < 0:
            continue
            
        tamanho = eff_r + 1
        rank_inicial = r if r == 6 else eff_r
        ranks = range(0, rank_inicial + 1)
        
        enemy_king_sq = board.king(chess.WHITE)
        enemy_k_f = chess.square_file(enemy_king_sq) if enemy_king_sq else f
        
        if enemy_k_f < f:
            files = range(max(0, f - tamanho + 1), f + 1)
        else:
            files = range(f, min(8, f + tamanho))
            
        quadrado_atual = set()
        for rr in ranks:
            for ff in files:
                quadrado_atual.add(chess.square(ff, rr))
                
        casas_quadrado.update(quadrado_atual)
        
        if enemy_king_sq is not None:
            kr = chess.square_rank(enemy_king_sq)
            kf = chess.square_file(enemy_king_sq)
            dentro = (0 <= kr <= eff_r) and (kf in files)
            
            nome_casa = chess.square_name(sq)
            if dentro:
                mensagens.append(f"O Rei Branco **alcança** o peão preto em {nome_casa}.")
            else:
                mensagens.append(f"O Rei Branco **não alcança** o peão preto em {nome_casa}.")
                
    return casas_quadrado, mensagens

def calcular_oposicao(board):
    pares_w = {}
    pares_b = {}
    
    wk_sq = board.king(chess.WHITE)
    bk_sq = board.king(chess.BLACK)
    
    if wk_sq is None or bk_sq is None:
        return pares_w, pares_b
        
    # Filtra as casas adjacentes válidas considerando a restrição de distância entre Reis
    w_adj = [sq for sq in chess.SQUARES if chess.square_distance(wk_sq, sq) == 1 and board.color_at(sq) != chess.WHITE and chess.square_distance(sq, bk_sq) > 1]
    b_adj = [sq for sq in chess.SQUARES if chess.square_distance(bk_sq, sq) == 1 and board.color_at(sq) != chess.BLACK and chess.square_distance(sq, wk_sq) > 1]
            
    pair_id = 1
    for w_sq in w_adj:
        for b_sq in b_adj:
            rf_w, rr_w = chess.square_file(w_sq), chess.square_rank(w_sq)
            rf_b, rr_b = chess.square_file(b_sq), chess.square_rank(b_sq)
            
            dist_f = abs(rf_w - rf_b)
            dist_r = abs(rr_w - rr_b)
            
            is_aligned = (dist_f == 0) or (dist_r == 0) or (dist_f == dist_r)
            dist = max(dist_f, dist_r)
            
            if is_aligned and dist % 2 == 0 and dist > 1:
                if w_sq not in pares_w and b_sq not in pares_b:
                    pares_w[w_sq] = str(pair_id)
                    pares_b[b_sq] = str(pair_id)
                    pair_id += 1
                    
    return pares_w, pares_b

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

mostrar_pv = st.sidebar.toggle("Mostrar linha PV (Stockfish)", value=True)
mostrar_regra_quadrado = st.sidebar.toggle("Mostrar Regra do Quadrado", value=False)
mostrar_oposicao = st.sidebar.toggle("Mostrar Oposição dos Reis", value=False)
svg_texts = []
pv_string_display = ""

if mostrar_pv:
    try:
        with chess.engine.SimpleEngine.popen_uci("stockfish") as engine:
            # Aumentamos o limite para garantir uma linha (PV) longa. Antes o tempo curto cortava em poucos lances.
            info = engine.analyse(board, chess.engine.Limit(depth=15, time=0.5))
            if "pv" in info:
                temp_board = board.copy()
                pv_lances = []
                for i, pv_move in enumerate(info["pv"][:10], start=1):
                    san_move = temp_board.san(pv_move)
                    temp_board.push(pv_move)
                    texto_lance = f"{i}. {san_move}"
                    pv_lances.append(texto_lance)
                    
                    setas_analiticas.append(chess.svg.Arrow(pv_move.from_square, pv_move.to_square, color="#9b59b6aa")) # Roxo translúcido
                    
                    # Calcula as coordenadas cartesianas do centro da casa de destino (viewBox 390x390 do python-chess)
                    file = chess.square_file(pv_move.to_square)
                    rank = chess.square_rank(pv_move.to_square)
                    x = 15 + file * 45 + 22.5
                    y = 15 + (7 - rank) * 45 + 22.5
                    
                    # Cria as tags SVG para o número e notação (retângulo arredondado branco + texto roxo)
                    largura_rect = len(texto_lance) * 6 + 10
                    svg_texts.append(f'<rect x="{x - largura_rect/2}" y="{y - 9}" width="{largura_rect}" height="18" rx="4" fill="white" stroke="#9b59b6" stroke-width="1.5"/>')
                    svg_texts.append(f'<text x="{x}" y="{y+1}" font-size="10" font-weight="bold" fill="#9b59b6" text-anchor="middle" dominant-baseline="central" font-family="sans-serif">{texto_lance}</text>')
                pv_string_display = " ".join(pv_lances)
    except FileNotFoundError:
        st.sidebar.warning("⚠️ Executável 'stockfish' não encontrado. Certifique-se de que ele está instalado e no seu PATH.")

fill_dict = {}
mensagens_quadrado = []
if mostrar_regra_quadrado:
    casas_quadrado, mensagens_quadrado = calcular_regra_quadrado(board)
    fill_dict = {sq: "#2ecc7155" for sq in casas_quadrado}  # Verde semitransparente

if mostrar_oposicao:
    pares_w, pares_b = calcular_oposicao(board)
    todas_casas = {**pares_w, **pares_b}
    for sq, texto in todas_casas.items():
        file = chess.square_file(sq)
        rank = chess.square_rank(sq)
        x = 15 + file * 45 + 22.5
        y = 15 + (7 - rank) * 45 + 22.5
        
        svg_texts.append(f'<circle cx="{x}" cy="{y}" r="11" fill="#e67e22" stroke="white" stroke-width="1.5"/>')
        svg_texts.append(f'<text x="{x}" y="{y+1}" font-size="12" font-weight="bold" fill="white" text-anchor="middle" dominant-baseline="central" font-family="sans-serif">{texto}</text>')

board_svg = chess.svg.board(
    board=board,
    arrows=setas_analiticas,
    fill=fill_dict,
    size=550, # Aumentado para preencher a nova coluna expandida de 50%
)

# Injeta estilo CSS (para afinar as setas roxas) e as bolinhas antes de fechar o SVG gerado
if svg_texts:
    css_setas = '<style>path[stroke="#9b59b6aa"], line[stroke="#9b59b6aa"] { stroke-width: 6 !important; }</style>'
    board_svg = board_svg.replace('</svg>', css_setas + '\n' + '\n'.join(svg_texts) + '\n</svg>')

# 2. Configurando o Novo Layout Otimizado em 3 Colunas
col_board, col_metrics, col_moves = st.columns([2, 1, 1]) # Tabuleiro passa a ocupar 50% da tela e o restante divide o restante

with col_board:
    cor_vez = "⚪ Brancas" if board.turn == chess.WHITE else "⚫ Pretas"
    st.markdown(f"#### Tabuleiro (Vez das {cor_vez})")
    
    # Botões de navegação do histórico de lances
    c_prev, c_next = st.columns(2)
    with c_prev:
        if st.button("⬅️ Voltar Lance", use_container_width=True, disabled=st.session_state.history_idx == 0):
            st.session_state.history_idx -= 1
            st.session_state.fen = st.session_state.history[st.session_state.history_idx]
            st.rerun()
    with c_next:
        if st.button("Avançar Lance ➡️", use_container_width=True, disabled=st.session_state.history_idx >= len(st.session_state.history) - 1):
            st.session_state.history_idx += 1
            st.session_state.fen = st.session_state.history[st.session_state.history_idx]
            st.rerun()
            
    # Exibe a linha de melhores lances do Stockfish em formato texto
    if pv_string_display:
        st.info(f"**Linha de Melhores Lances (PV):** {pv_string_display}")

    if mostrar_regra_quadrado and mensagens_quadrado:
        for msg in mensagens_quadrado:
            if "não alcança" in msg:
                st.success(f"🏃 {msg}")
            else:
                st.warning(f"🚨 {msg}")

    st.write(board_svg, unsafe_allow_html=True)
    nova_fen = st.text_input("Modificar posição (FEN):", st.session_state.fen)
    if nova_fen != st.session_state.fen:
        registrar_nova_fen(nova_fen)
        st.rerun()

    if st.button("Trocar a Vez (Brancas / Pretas)"):
        partes_fen = st.session_state.fen.split(" ")
        partes_fen[1] = "b" if partes_fen[1] == "w" else "w"
        partes_fen[3] = "-"  # Remove alvo de en-passant para evitar FEN inválida
        registrar_nova_fen(" ".join(partes_fen))
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
    st.markdown("#### Lances Disponíveis (Clique na linha)")
    lances_dict = {board.san(m): m for m in board.legal_moves}
    
    # Tabela interativa com seleção de linha
    event = st.dataframe(
        dados_tabela, 
        height=620, # Expandido para ocupar o máximo de espaço vertical na coluna de lances
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    # Processa o clique na tabela e engatilha a jogada
    if hasattr(event, "selection") and event.selection.rows:
        selected_idx = event.selection.rows[0]
        lance_san = dados_tabela[selected_idx]["Lance"]
        board.push(lances_dict[lance_san])
        registrar_nova_fen(board.fen())
        st.rerun()