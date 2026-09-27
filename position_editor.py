import chess
import chess.svg
import streamlit as st


_PIECE_DEFS = chess.svg.board(board=chess.Board()).split("<defs>", 1)[1].split("</defs>", 1)[0]
_EMPTY_BOARD_SVG = chess.svg.board(board=chess.Board(None), size=700).replace(
    "</svg>", f"<defs>{_PIECE_DEFS}</defs></svg>"
)


def position_data(fen):
    board = chess.Board(fen)
    return {
        "pieces": {chess.square_name(sq): piece.symbol()
                   for sq, piece in board.piece_map().items()},
        "turn": "w" if board.turn else "b",
        "castling": board.castling_xfen().replace("-", ""),
        "ep": chess.square_name(board.ep_square) if board.ep_square is not None else "-",
        "selected": "K",
    }


def board_from_draft(draft):
    board = chess.Board(None)
    for square, symbol in draft["pieces"].items():
        board.set_piece_at(chess.parse_square(square), chess.Piece.from_symbol(symbol))
    fen = (f"{board.board_fen()} {draft['turn']} "
           f"{draft['castling'] or '-'} {draft['ep']} 0 1")
    return chess.Board(fen)


_EDITOR = st.components.v2.component(
    "chess_position_editor",
    html='<div class="position-editor"></div>',
    css="""
.position-editor { display: grid; gap: 12px; }
.position-editor .palette { display: flex; flex-wrap: wrap; gap: 4px; }
.position-editor button { cursor: pointer; border: 1px solid #9998;
    border-radius: 5px; background: var(--st-secondary-background-color, #eee);
    color: var(--st-text-color, #222); padding: 4px 9px; }
.position-editor .palette button { font-size: 29px; line-height: 1.2; }
.position-editor button.selected { outline: 3px solid #eab308; }
.position-editor .editor-board { width: min(100%, calc(100vh - 230px));
    aspect-ratio: 1; margin: auto; touch-action: none; }
.position-editor svg { display: block; width: 100%; height: 100%; }
.position-editor .settings { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
""",
    js="""
export default function ({ data, parentElement, setStateValue }) {
    const root = parentElement.querySelector(".position-editor");
    root.replaceChildren();
    const palette = document.createElement("div");
    palette.className = "palette";
    const boardArea = document.createElement("div");
    boardArea.className = "editor-board";
    boardArea.innerHTML = data.svg;
    const svg = boardArea.querySelector("svg");
    const layer = document.createElementNS("http://www.w3.org/2000/svg", "g");
    svg.appendChild(layer);
    const settings = document.createElement("div");
    settings.className = "settings";
    root.append(palette, boardArea, settings);

    let pieces = { ...data.draft.pieces };
    let turn = data.draft.turn;
    let castling = data.draft.castling;
    let ep = data.draft.ep;
    let selected = data.draft.selected || "K";
    let drag = null;
    const symbols = {
        K: "♔", Q: "♕", R: "♖", B: "♗", N: "♘", P: "♙",
        k: "♚", q: "♛", r: "♜", b: "♝", n: "♞", p: "♟", erase: "⌫"
    };
    const names = {
        K: "Rei branco", Q: "Dama branca", R: "Torre branca",
        B: "Bispo branco", N: "Cavalo branco", P: "Peão branco",
        k: "Rei preto", q: "Dama preta", r: "Torre preta",
        b: "Bispo preto", n: "Cavalo preto", p: "Peão preto",
        erase: "Apagar peça"
    };
    function persist() {
        setStateValue("draft", { pieces, turn, castling, ep, selected });
    }
    function squareAt(event) {
        const point = new DOMPoint(event.clientX, event.clientY)
            .matrixTransform(svg.getScreenCTM().inverse());
        const file = Math.floor((point.x - 15) / 45);
        const row = Math.floor((point.y - 15) / 45);
        if (file < 0 || file > 7 || row < 0 || row > 7) return null;
        return "abcdefgh"[file] + (8 - row);
    }
    function renderPieces() {
        layer.replaceChildren();
        for (const [square, piece] of Object.entries(pieces)) {
            const file = "abcdefgh".indexOf(square[0]);
            const row = 8 - Number(square[1]);
            const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
            const color = piece === piece.toUpperCase() ? "white" : "black";
            const kind = { k: "king", q: "queen", r: "rook", b: "bishop",
                           n: "knight", p: "pawn" }[piece.toLowerCase()];
            use.setAttribute("href", `#${color}-${kind}`);
            use.setAttribute("transform", `translate(${15 + file * 45}, ${15 + row * 45})`);
            layer.appendChild(use);
        }
    }
    function select(piece) {
        selected = piece;
        for (const button of palette.querySelectorAll("button")) {
            button.classList.toggle("selected", button.dataset.piece === selected);
        }
    }
    for (const piece of Object.keys(symbols)) {
        const button = document.createElement("button");
        button.type = "button";
        button.dataset.piece = piece;
        button.textContent = symbols[piece];
        button.title = names[piece];
        button.setAttribute("aria-label", names[piece]);
        button.draggable = piece !== "erase";
        button.ondragstart = event => event.dataTransfer.setData("text/plain", piece);
        button.onclick = () => { select(piece); persist(); };
        palette.appendChild(button);
    }
    select(selected);

    boardArea.ondragover = event => event.preventDefault();
    boardArea.ondrop = event => {
        event.preventDefault();
        const square = squareAt(event);
        const piece = event.dataTransfer.getData("text/plain");
        if (square && Object.hasOwn(symbols, piece) && piece !== "erase") {
            pieces[square] = piece;
            renderPieces();
            persist();
        }
    };
    svg.oncontextmenu = event => event.preventDefault();
    svg.onpointerdown = event => {
        const square = squareAt(event);
        if (!square) return;
        event.preventDefault();
        if (event.button === 2) {
            delete pieces[square];
            renderPieces();
            persist();
        } else if (event.button === 0) {
            svg.setPointerCapture(event.pointerId);
            drag = { from: square, pointerId: event.pointerId };
        }
    };
    svg.onpointerup = event => {
        if (!drag || drag.pointerId !== event.pointerId) return;
        const from = drag.from;
        drag = null;
        const to = squareAt(event);
        if (!to) return;
        if (to !== from && pieces[from]) {
            pieces[to] = pieces[from];
            delete pieces[from];
        } else if (to === from) {
            if (selected === "erase") delete pieces[to];
            else pieces[to] = selected;
        }
        renderPieces();
        persist();
    };
    svg.onpointercancel = () => { drag = null; };

    const turnLabel = document.createElement("label");
    turnLabel.textContent = "Vez de jogar: ";
    const turnSelect = document.createElement("select");
    for (const [value, label] of [["w", "Brancas"], ["b", "Pretas"]]) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = label;
        turnSelect.appendChild(option);
    }
    turnSelect.value = turn;
    turnSelect.onchange = () => { turn = turnSelect.value; persist(); };
    turnLabel.appendChild(turnSelect);
    settings.appendChild(turnLabel);
    const castlingInputs = {};
    for (const [right, label] of [
        ["K", "Roque branco curto"], ["Q", "Roque branco longo"],
        ["k", "Roque preto curto"], ["q", "Roque preto longo"]
    ]) {
        const wrapper = document.createElement("label");
        const checkbox = document.createElement("input");
        castlingInputs[right] = checkbox;
        checkbox.type = "checkbox";
        checkbox.checked = castling.includes(right);
        checkbox.onchange = () => {
            castling = checkbox.checked
                ? castling + right
                : castling.replace(right, "");
            persist();
        };
        wrapper.append(checkbox, ` ${label}`);
        settings.appendChild(wrapper);
    }
    const epLabel = document.createElement("label");
    epLabel.textContent = "En passant: ";
    const epSelect = document.createElement("select");
    for (const value of ["-", ..."abcdefgh".split("").flatMap(
        file => [file + "3", file + "6"])]) {
        const option = document.createElement("option");
        option.value = value;
        option.textContent = value;
        epSelect.appendChild(option);
    }
    epSelect.value = ep;
    epSelect.onchange = () => { ep = epSelect.value; persist(); };
    epLabel.appendChild(epSelect);
    settings.appendChild(epLabel);

    renderPieces();
}
""",
)


def position_editor(draft, *, key):
    def save_draft():
        st.session_state.editor_draft = st.session_state[key].draft

    return _EDITOR(
        key=key,
        data={
            "svg": _EMPTY_BOARD_SVG,
            "draft": draft,
        },
        on_draft_change=save_draft,
    )
