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
.board-root .drawing-layer { pointer-events: none; }
.board-root .drawing-layer line {
    stroke: #eab308;
    stroke-width: 6;
    stroke-linecap: round;
}
.board-root .drawing-layer polygon { fill: #eab308; }
.board-root .drawing-layer .preview { opacity: 0.7; }
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
export default function ({ data, parentElement, setStateValue, setTriggerValue }) {
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
    let drawing = null;
    let promotion = null;
    let arrows = data.arrows;
    const svgNS = "http://www.w3.org/2000/svg";
    const drawingLayer = document.createElementNS(svgNS, "g");
    drawingLayer.setAttribute("class", "drawing-layer");
    svg.appendChild(drawingLayer);

    function squareCenter(square) {
        return {
            x: 37.5 + 45 * "abcdefgh".indexOf(square[0]),
            y: 37.5 + 45 * (8 - Number(square[1]))
        };
    }

    function drawArrow(from, to, preview = false) {
        const start = squareCenter(from);
        const end = squareCenter(to);
        const dx = end.x - start.x;
        const dy = end.y - start.y;
        const length = Math.hypot(dx, dy);
        if (!length) return;
        const ux = dx / length;
        const uy = dy / length;
        const tipX = end.x - ux * 8;
        const tipY = end.y - uy * 8;
        const baseX = tipX - ux * 14;
        const baseY = tipY - uy * 14;
        const group = document.createElementNS(svgNS, "g");
        if (preview) group.setAttribute("class", "preview");
        const shaft = document.createElementNS(svgNS, "line");
        shaft.setAttribute("x1", start.x);
        shaft.setAttribute("y1", start.y);
        shaft.setAttribute("x2", baseX);
        shaft.setAttribute("y2", baseY);
        const head = document.createElementNS(svgNS, "polygon");
        head.setAttribute("points",
            `${tipX},${tipY} ${baseX - uy * 8},${baseY + ux * 8} ` +
            `${baseX + uy * 8},${baseY - ux * 8}`);
        group.append(shaft, head);
        drawingLayer.appendChild(group);
    }

    function renderArrows(to = null) {
        drawingLayer.replaceChildren();
        for (const [from, end] of arrows) drawArrow(from, end);
        if (drawing && to && to !== drawing.from) {
            drawArrow(drawing.from, to, true);
        }
    }
    renderArrows();

    function saveArrows() {
        setStateValue("arrows", { fen: data.fen, items: arrows });
    }

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

    svg.oncontextmenu = event => event.preventDefault();
    svg.onpointerdown = event => {
        if (event.button === 2 && !drag && !promotion) {
            const from = squareAt(event);
            if (!from) return;
            event.preventDefault();
            svg.setPointerCapture(event.pointerId);
            drawing = { from, pointerId: event.pointerId };
            return;
        }
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
        if (drawing && drawing.pointerId === event.pointerId) {
            renderArrows(squareAt(event));
            return;
        }
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
    function endDrawing(event, cancelled = false) {
        if (!drawing || drawing.pointerId !== event.pointerId) return;
        const from = drawing.from;
        const to = cancelled ? null : squareAt(event);
        drawing = null;
        if (to === from) {
            arrows = [];
            saveArrows();
        } else if (to) {
            const index = arrows.findIndex(([start, end]) =>
                start === from && end === to);
            arrows = index < 0
                ? [...arrows, [from, to]]
                : arrows.filter((_, i) => i !== index);
            saveArrows();
        }
        renderArrows();
    }
    svg.onpointerup = event => {
        endDrawing(event);
        endDrag(event);
    };
    svg.onpointercancel = event => {
        endDrawing(event, true);
        endDrag(event, true);
    };

    return () => {
        clearPromotion();
        root.replaceChildren();
    };
}
""",
)


def draggable_board(svg, labels, board, *, key="chess_board"):
    annotations_key = f"{key}_annotations"
    fen = board.fen()
    saved = st.session_state.get(annotations_key)
    if saved is None or saved["fen"] != fen:
        saved = {"fen": fen, "items": []}
        st.session_state[annotations_key] = saved

    def save_arrows():
        st.session_state[annotations_key] = st.session_state[key].arrows

    return _BOARD(
        key=key,
        data={
            "svg": svg,
            "labels": labels,
            "fen": fen,
            "turn": "w" if board.turn else "b",
            "legalMoves": [move.uci() for move in board.legal_moves],
            "arrows": saved["items"],
        },
        on_move_change=lambda: None,
        on_arrows_change=save_arrows,
    )
