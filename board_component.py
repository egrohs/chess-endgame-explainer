import streamlit as st


_BOARD = st.components.v2.component(
    "chess_board_drag",
    html='<div class="board-root"></div>',
    css="""
.board-root {
    position: relative;
    width: min(100%, calc(100vh - 150px));
    aspect-ratio: 1;
    margin: auto;
    touch-action: none;
    user-select: none;
}
.board-root > svg { display: block; width: 100%; height: 100%; }
.board-root .pv-label {
    position: absolute;
    z-index: 2;
    transform: translate(-50%, -50%);
    pointer-events: none;
    color: #9b59b6;
    font-size: 15px;
    font-weight: bold;
    text-shadow: -1px -1px 0 white, 1px -1px 0 white,
                 -1px 1px 0 white, 1px 1px 0 white;
    white-space: nowrap;
}
.board-root .promotion {
    position: absolute;
    z-index: 3;
    display: flex;
    gap: 4px;
    padding: 6px;
    border-radius: 6px;
    background: var(--st-secondary-background-color, white);
    box-shadow: 0 2px 12px #0006;
    transform: translate(-50%, -50%);
}
.board-root .promotion button { cursor: pointer; font-size: 24px; }
.board-root .feedback { position: absolute; bottom: 0; left: 0; }
""",
    js="""
export default function ({ data, parentElement, setTriggerValue }) {
    const root = parentElement.querySelector(".board-root");
    root.replaceChildren();
    root.insertAdjacentHTML("afterbegin", data.svg);
    const svg = root.querySelector("svg");
    if (!svg) throw new Error("Tabuleiro SVG não encontrado");

    for (const [x, y, text] of data.labels) {
        const label = document.createElement("span");
        label.className = "pv-label";
        label.style.left = `${x / 390 * 100}%`;
        label.style.top = `${y / 390 * 100}%`;
        label.textContent = text;
        root.appendChild(label);
    }

    const feedback = document.createElement("div");
    feedback.className = "feedback";
    feedback.setAttribute("role", "status");
    root.appendChild(feedback);
    const legal = new Set(data.legalMoves);
    let drag = null;
    let promotion = null;

    function squareAt(event) {
        const point = new DOMPoint(event.clientX, event.clientY)
            .matrixTransform(svg.getScreenCTM().inverse());
        const file = Math.floor((point.x - 15) / 45);
        const row = Math.floor((point.y - 15) / 45);
        if (file < 0 || file > 7 || row < 0 || row > 7) return null;
        return "abcdefgh"[file] + (8 - row);
    }

    function sourcePiece(square) {
        const file = "abcdefgh".indexOf(square[0]);
        const row = 8 - Number(square[1]);
        return [...svg.querySelectorAll("use")].find(piece =>
            piece.getAttribute("transform") ===
            `translate(${15 + file * 45}, ${15 + row * 45})`);
    }

    function clearPromotion() {
        promotion?.remove();
        promotion = null;
    }

    function submit(uci) {
        feedback.textContent = "";
        setTriggerValue("move", { fen: data.fen, uci });
    }

    function selectPromotion(moves, event) {
        clearPromotion();
        promotion = document.createElement("div");
        promotion.className = "promotion";
        const rect = root.getBoundingClientRect();
        promotion.style.left = `${(event.clientX - rect.left) / rect.width * 100}%`;
        promotion.style.top = `${(event.clientY - rect.top) / rect.height * 100}%`;
        const symbols = data.turn === "w"
            ? { q: "♕", r: "♖", b: "♗", n: "♘" }
            : { q: "♛", r: "♜", b: "♝", n: "♞" };
        for (const move of moves) {
            const button = document.createElement("button");
            button.type = "button";
            button.textContent = symbols[move[4]];
            button.title = `Promover para ${move[4]}`;
            button.onclick = () => {
                clearPromotion();
                submit(move);
            };
            promotion.appendChild(button);
        }
        root.appendChild(promotion);
    }

    svg.onpointerdown = event => {
        if (event.button !== 0 || drag || promotion) return;
        const from = squareAt(event);
        if (!from || ![...legal].some(move => move.startsWith(from))) return;
        const piece = sourcePiece(from);
        if (!piece) return;
        event.preventDefault();
        svg.setPointerCapture(event.pointerId);
        const ghost = piece.cloneNode(true);
        ghost.style.pointerEvents = "none";
        svg.appendChild(ghost);
        piece.style.opacity = "0.3";
        drag = { from, piece, ghost, pointerId: event.pointerId };
    };

    svg.onpointermove = event => {
        if (!drag || drag.pointerId !== event.pointerId) return;
        const point = new DOMPoint(event.clientX, event.clientY)
            .matrixTransform(svg.getScreenCTM().inverse());
        drag.ghost.setAttribute("transform",
            `translate(${point.x - 22.5}, ${point.y - 22.5})`);
    };

    function endDrag(event, cancelled = false) {
        if (!drag || drag.pointerId !== event.pointerId) return;
        const { from, piece, ghost } = drag;
        const to = cancelled ? null : squareAt(event);
        piece.style.opacity = "";
        ghost.remove();
        drag = null;
        if (!to || to === from) return;
        const moves = [...legal].filter(move => move.startsWith(from + to));
        if (!moves.length) {
            feedback.textContent = "Lance inválido";
        } else if (moves.length > 1) {
            selectPromotion(moves, event);
        } else {
            submit(moves[0]);
        }
    }
    svg.onpointerup = event => endDrag(event);
    svg.onpointercancel = event => endDrag(event, true);

    return () => {
        clearPromotion();
        root.replaceChildren();
    };
}
""",
)


def draggable_board(svg, labels, board, *, key="chess_board"):
    return _BOARD(
        key=key,
        data={
            "svg": svg,
            "labels": labels,
            "fen": board.fen(),
            "turn": "w" if board.turn else "b",
            "legalMoves": [move.uci() for move in board.legal_moves],
        },
        on_move_change=lambda: None,
    )
