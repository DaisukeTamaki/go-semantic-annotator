from __future__ import annotations

# ruff: noqa: E501
import json
import random
import uuid
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from go_semantic_annotator.models import (
    KataGoPositionAnalysis,
    ManualAnnotationRecord,
    SemanticAnnotation,
)


def run_annotation_app(
    *,
    queue_dir: Path,
    output_path: Path,
    host: str = "127.0.0.1",
    port: int = 8765,
    open_browser: bool = True,
) -> None:
    """Start the local annotation app."""

    queue_dir = queue_dir.resolve()
    output_path = output_path.resolve()
    handler = _make_handler(queue_dir=queue_dir, output_path=output_path)
    server = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{port}"

    print(f"Annotation app: {url}")
    print(f"Queue: {queue_dir}")
    print(f"Output: {output_path}")

    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down annotation app.")
    finally:
        server.server_close()


def position_files(queue_dir: Path) -> list[Path]:
    """Return normalized position JSON files from a queue directory."""

    if not queue_dir.exists():
        return []

    files: list[Path] = []
    for path in sorted(queue_dir.glob("*.json")):
        try:
            KataGoPositionAnalysis.model_validate(_read_json(path))
        except (OSError, json.JSONDecodeError, ValidationError):
            continue
        files.append(path)
    return files


def load_random_position(queue_dir: Path) -> KataGoPositionAnalysis:
    """Load a random valid normalized position."""

    files = position_files(queue_dir)
    if not files:
        msg = f"no valid normalized position JSON files found in {queue_dir}"
        raise FileNotFoundError(msg)

    payload = _read_json(random.choice(files))
    return KataGoPositionAnalysis.model_validate(payload)


def append_annotation_record(
    *,
    position: KataGoPositionAnalysis,
    annotation: SemanticAnnotation,
    output_path: Path,
    annotator: str | None = None,
    notes: str | None = None,
) -> ManualAnnotationRecord:
    """Validate and append a manual annotation row as JSONL."""

    record = ManualAnnotationRecord(
        record_id=str(uuid.uuid4()),
        position=position,
        annotation=annotation,
        annotator=annotator or None,
        notes=notes or None,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a") as handle:
        handle.write(record.model_dump_json() + "\n")
    return record


def _make_handler(*, queue_dir: Path, output_path: Path) -> type[BaseHTTPRequestHandler]:
    class AnnotationHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/" or self.path == "/index.html":
                self._send_text(INDEX_HTML, content_type="text/html; charset=utf-8")
                return

            if self.path == "/api/tasks/random":
                try:
                    position = load_random_position(queue_dir)
                except FileNotFoundError as error:
                    self._send_json({"error": str(error)}, status=HTTPStatus.NOT_FOUND)
                    return
                self._send_json(position.model_dump(mode="json"))
                return

            if self.path == "/api/tasks":
                self._send_json(
                    {
                        "queue_dir": str(queue_dir),
                        "count": len(position_files(queue_dir)),
                    }
                )
                return

            self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            if self.path != "/api/annotations":
                self._send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
                return

            try:
                payload = self._read_body()
                position = KataGoPositionAnalysis.model_validate(payload["position"])
                annotation = SemanticAnnotation.model_validate(payload["annotation"])
                record = append_annotation_record(
                    position=position,
                    annotation=annotation,
                    output_path=output_path,
                    annotator=payload.get("annotator"),
                    notes=payload.get("notes"),
                )
            except (KeyError, json.JSONDecodeError, ValidationError, TypeError) as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
                return

            self._send_json(record.model_dump(mode="json"), status=HTTPStatus.CREATED)

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _read_body(self) -> dict[str, Any]:
            content_length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(content_length).decode("utf-8")
            return json.loads(body)

        def _send_json(
            self,
            payload: dict[str, Any],
            *,
            status: HTTPStatus = HTTPStatus.OK,
        ) -> None:
            encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_text(self, payload: str, *, content_type: str) -> None:
            encoded = payload.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return AnnotationHandler


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Go Semantic Annotator</title>
  <style>
    :root {
      color-scheme: light dark;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * {
      box-sizing: border-box;
    }
    body {
      margin: 0;
      background: #111827;
      color: #e5e7eb;
    }
    header, main {
      max-width: 1180px;
      margin: 0 auto;
      padding: 20px;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
    }
    button, input, textarea, select {
      border: 1px solid #374151;
      border-radius: 8px;
      padding: 8px 10px;
      background: #1f2937;
      color: #f9fafb;
      font: inherit;
    }
    button {
      cursor: pointer;
      background: #2563eb;
      border-color: #2563eb;
    }
    button.secondary {
      background: #374151;
      border-color: #4b5563;
    }
    .grid {
      display: grid;
      grid-template-columns: minmax(320px, 1fr) minmax(360px, 1fr);
      gap: 18px;
    }
    .card {
      background: #172033;
      border: 1px solid #273244;
      border-radius: 14px;
      padding: 16px;
    }
    .board {
      display: grid;
      width: min(68vw, 520px);
      aspect-ratio: 1;
      background: #c9944b;
      border: 10px solid #8b5a2b;
      border-radius: 10px;
      padding: 18px;
      position: relative;
    }
    .cell {
      position: relative;
      display: grid;
      place-items: center;
      min-width: 0;
      min-height: 0;
      overflow: hidden;
      cursor: pointer;
      font-size: 11px;
      color: rgba(0, 0, 0, 0.55);
    }
    .cell:hover {
      background: rgba(255, 255, 255, 0.12);
    }
    .cell::before,
    .cell::after {
      content: "";
      position: absolute;
      background: rgba(0, 0, 0, 0.55);
      z-index: 0;
    }
    .cell::before {
      left: 0;
      right: 0;
      top: 50%;
      height: 1px;
    }
    .cell::after {
      top: 0;
      bottom: 0;
      left: 50%;
      width: 1px;
    }
    .cell.edge-left::before {
      left: 50%;
    }
    .cell.edge-right::before {
      right: 50%;
    }
    .cell.edge-top::after {
      top: 50%;
    }
    .cell.edge-bottom::after {
      bottom: 50%;
    }
    .stone {
      position: relative;
      z-index: 1;
      width: 72%;
      height: 72%;
      border-radius: 999px;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.45);
    }
    .stone.b {
      background: radial-gradient(circle at 35% 30%, #4b5563, #030712 70%);
    }
    .stone.w {
      background: radial-gradient(circle at 35% 30%, #ffffff, #cbd5e1 75%);
    }
    .candidate {
      position: relative;
      z-index: 1;
      width: 60%;
      height: 60%;
      border: 2px solid #2563eb;
      border-radius: 999px;
      background: rgba(37, 99, 235, 0.15);
      display: grid;
      place-items: center;
      color: #1d4ed8;
      font-weight: 700;
    }
    .hover-label {
      position: absolute;
      z-index: 2;
      bottom: 100%;
      left: 50%;
      transform: translate(-50%, -4px);
      padding: 2px 6px;
      border-radius: 6px;
      background: #0b1020;
      color: #f9fafb;
      font-size: 11px;
      pointer-events: none;
      white-space: nowrap;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
    }
    .board.pick-mode {
      box-shadow: 0 0 0 4px #f59e0b inset;
    }
    .board.pick-mode .cell {
      cursor: crosshair;
    }
    .pick-banner {
      display: none;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      margin: 12px 0;
      background: #78350f;
      color: #fef3c7;
      border-radius: 8px;
      font-weight: 600;
    }
    .pick-banner.visible {
      display: flex;
    }
    .context-menu {
      position: fixed;
      z-index: 9999;
      background: #0b1020;
      border: 1px solid #374151;
      border-radius: 8px;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
      padding: 4px;
      display: none;
      min-width: 180px;
    }
    .context-menu.visible {
      display: block;
    }
    .context-menu button {
      display: block;
      width: 100%;
      text-align: left;
      background: transparent;
      border: none;
      color: #f9fafb;
      padding: 8px 10px;
      border-radius: 6px;
      cursor: pointer;
    }
    .context-menu button:hover {
      background: #1f2937;
    }
    .candidate-row.active {
      outline: 2px solid #2563eb;
      outline-offset: 2px;
    }
    label {
      display: grid;
      gap: 6px;
      margin: 10px 0;
      color: #cbd5e1;
    }
    textarea {
      min-height: 76px;
      resize: vertical;
    }
    pre {
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      background: #0b1020;
      padding: 12px;
      border-radius: 10px;
      max-height: 260px;
      overflow: auto;
    }
    .muted {
      color: #9ca3af;
    }
    .candidate-list {
      display: grid;
      gap: 8px;
    }
    .candidate-row {
      display: grid;
      grid-template-columns: auto 1fr auto;
      gap: 8px;
      align-items: center;
      padding: 8px;
      border: 1px solid #273244;
      border-radius: 8px;
      background: #111827;
    }
    .toolbar {
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 8px;
      margin: 12px 0;
      align-items: end;
    }
    .section-heading {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Go Semantic Annotator</h1>
      <div class="muted">Manual expert labels for KataGo-derived semantic JSON.</div>
    </div>
    <div>
      <button id="load-random">Load Random Position</button>
      <button id="save" class="secondary">Save Annotation</button>
    </div>
  </header>

  <main class="grid">
    <section class="card">
      <h2>Position</h2>
      <div id="status" class="muted">Loading...</div>
      <div class="toolbar">
        <label>KataGo WS URL <input id="katago-url" value="ws://127.0.0.1:8000/ws/analyze" /></label>
        <label>Visits <input id="max-visits" type="number" min="1" value="200" /></label>
        <button id="refresh-analysis" class="secondary">Refresh Analysis</button>
      </div>
      <div class="toolbar">
        <label>Side to play <input id="side-to-play" readonly /></label>
        <button id="reset-line" class="secondary">Reset Line</button>
        <span class="muted">Click an empty intersection or a candidate to try a move.</span>
      </div>
      <div id="pick-banner" class="pick-banner">
        <span>Pick Mode: click any intersection to insert a move link into <strong id="pick-target-name">Main reason</strong>. ESC to cancel.</span>
      </div>
      <div id="board" class="board"></div>
      <h3>Candidates</h3>
      <div id="candidates" class="candidate-list"></div>
    </section>

    <section class="card">
      <div class="section-heading">
        <h2>Annotation</h2>
        <button id="insert-move-link" class="secondary">Insert Move Link</button>
      </div>
      <div class="muted">
        Target field: <strong id="active-field-name">Main reason</strong>.
        Move references use Markdown links like [R3](move:R3).
        Right-click the board for Insert/Copy.
      </div>
      <label>Annotator <input id="annotator" placeholder="optional" /></label>
      <label>Move <input id="move" /></label>
      <label>Move role CSV <input id="move-role" value="katago_top_choice" /></label>
      <label>Local tactics CSV <input id="local-tactics" /></label>
      <label>Global context CSV <input id="global-context" /></label>
      <label>Main reason <textarea id="main-reason"></textarea></label>
      <label>Bad if ignored <textarea id="bad-if-ignored"></textarea></label>
      <label>Notes <textarea id="notes"></textarea></label>
      <label>Confidence <input id="confidence" type="number" min="0" max="1" step="0.01" value="0.8" /></label>
      <h3>Current Input</h3>
      <pre id="raw"></pre>
    </section>
  </main>

  <div id="context-menu" class="context-menu">
    <button data-action="insert">Insert link into focused field</button>
    <button data-action="copy">Copy link to clipboard</button>
  </div>

  <script>
    const COLUMNS = "ABCDEFGHJKLMNOPQRSTUVWXYZ";
    let currentPosition = null;
    let basePosition = null;
    let trialMoves = [];
    let selectedCandidate = null;
    let katagoSocket = null;
    let pendingQueryId = null;
    let activeAnnotationField = null;
    let pickMode = false;
    let contextMenuTarget = null;

    const $ = (id) => document.getElementById(id);
    const csv = (value) => value.split(",").map((x) => x.trim()).filter(Boolean);
    const annotationFieldLabels = {
      "main-reason": "Main reason",
      "bad-if-ignored": "Bad if ignored",
      "notes": "Notes"
    };
    const annotationFieldIds = Object.keys(annotationFieldLabels);
    const MOVE_LINK_PATTERN = /\[[^\]]*\]\(move:([^)]+)\)/g;

    async function loadRandom() {
      const response = await fetch("/api/tasks/random");
      if (!response.ok) {
        $("status").textContent = await response.text();
        return;
      }
      basePosition = await response.json();
      currentPosition = structuredClone(basePosition);
      trialMoves = structuredClone(currentPosition.move_history || []);
      selectedCandidate = currentPosition.candidates[0] || null;
      renderPosition();
      prefillFromCandidate();
    }

    function renderPosition() {
      $("status").textContent = `${currentPosition.id} | ${currentPosition.context.game_phase} | move ${currentPosition.context.move_number ?? "?"}`;
      $("raw").textContent = JSON.stringify(currentPosition, null, 2);
      $("side-to-play").value = nextColor();
      renderBoard();
      renderCandidates();
    }

    function renderBoard() {
      const size = currentPosition.context.board_size || 19;
      const board = $("board");
      board.style.gridTemplateColumns = `repeat(${size}, 1fr)`;
      board.style.gridTemplateRows = `repeat(${size}, 1fr)`;
      board.innerHTML = "";
      const stones = new Map(trialMoves.map((move) => [`${move.row},${move.col}`, move]));
      const candidates = new Map(currentPosition.candidates.map((move) => [vertexToKey(move.vertex, size), move]));
      for (let row = size - 1; row >= 0; row--) {
        for (let col = 0; col < size; col++) {
          const cell = document.createElement("div");
          cell.className = "cell";
          if (col === 0) cell.classList.add("edge-left");
          if (col === size - 1) cell.classList.add("edge-right");
          if (row === size - 1) cell.classList.add("edge-top");
          if (row === 0) cell.classList.add("edge-bottom");
          cell.dataset.row = row;
          cell.dataset.col = col;
          cell.dataset.vertex = pointToVertex(row, col);
          cell.title = cell.dataset.vertex;
          cell.onclick = (event) => handleBoardClick(event, row, col);
          cell.oncontextmenu = (event) => openContextMenu(event, row, col);
          cell.onmouseenter = () => showHoverLabel(cell);
          cell.onmouseleave = () => hideHoverLabel(cell);
          const stone = stones.get(`${row},${col}`);
          const candidate = candidates.get(`${row},${col}`);
          if (stone) {
            const node = document.createElement("div");
            node.className = `stone ${stone.color}`;
            cell.appendChild(node);
          } else if (candidate) {
            const node = document.createElement("div");
            node.className = "candidate";
            node.textContent = candidate.rank;
            cell.appendChild(node);
          }
          board.appendChild(cell);
        }
      }
    }

    function showHoverLabel(cell) {
      if (!pickMode) return;
      if (cell.querySelector(".hover-label")) return;
      const label = document.createElement("div");
      label.className = "hover-label";
      label.textContent = cell.dataset.vertex;
      cell.appendChild(label);
    }

    function hideHoverLabel(cell) {
      const label = cell.querySelector(".hover-label");
      if (label) label.remove();
    }

    function handleBoardClick(event, row, col) {
      const vertex = pointToVertex(row, col);
      if (pickMode) {
        event.preventDefault();
        insertLinkAtCaret(vertex);
        exitPickMode();
        return;
      }
      playMove(row, col);
    }

    function renderCandidates() {
      const container = $("candidates");
      container.innerHTML = "";
      currentPosition.candidates.forEach((candidate) => {
        const row = document.createElement("button");
        row.className = "candidate-row secondary";
        if (selectedCandidate && selectedCandidate.vertex === candidate.vertex) {
          row.classList.add("active");
        }
        row.innerHTML = `<strong>#${candidate.rank} ${candidate.vertex}</strong><span>score ${candidate.score_lead ?? "?"}, winrate ${candidate.winrate ?? "?"}</span><span>${candidate.visits ?? 0} visits</span>`;
        row.onclick = () => playCandidateMove(candidate);
        container.appendChild(row);
      });
    }

    function playCandidateMove(candidate) {
      selectedCandidate = candidate;
      prefillFromCandidate();
      const key = vertexToKey(candidate.vertex, currentPosition.context.board_size);
      if (!key) return;
      const [row, col] = key.split(",").map((value) => Number.parseInt(value, 10));
      playMove(row, col);
    }

    function prefillFromCandidate() {
      if (!selectedCandidate) return;
      $("move").value = selectedCandidate.vertex;
      $("global-context").value = [currentPosition.context.game_phase].filter(Boolean).join(", ");
      $("main-reason").value = "";
      $("bad-if-ignored").value = "";
    }

    function trackAnnotationFocus() {
      annotationFieldIds.forEach((id) => {
        $(id).addEventListener("focus", (event) => {
          setActiveAnnotationField(event.target);
        });
      });
      setActiveAnnotationField($("main-reason"));
    }

    function setActiveAnnotationField(field) {
      activeAnnotationField = field;
      const label = annotationFieldLabels[field?.id] || "Main reason";
      $("active-field-name").textContent = label;
      $("pick-target-name").textContent = label;
    }

    function enterPickMode() {
      if (!currentPosition) return;
      pickMode = true;
      $("board").classList.add("pick-mode");
      $("pick-banner").classList.add("visible");
      $("status").textContent = "Pick a board point to insert a move link. ESC to cancel.";
    }

    function exitPickMode() {
      pickMode = false;
      $("board").classList.remove("pick-mode");
      $("pick-banner").classList.remove("visible");
    }

    function insertLinkAtCaret(vertex) {
      const target = activeAnnotationField || $("main-reason");
      const selectedText = target.value.slice(target.selectionStart, target.selectionEnd);
      const label = selectedText || vertex;
      const link = `[${label}](move:${vertex})`;
      const before = target.value.slice(0, target.selectionStart);
      const after = target.value.slice(target.selectionEnd);
      target.value = `${before}${link}${after}`;
      const cursor = before.length + link.length;
      target.focus();
      target.setSelectionRange(cursor, cursor);
      $("status").textContent = `Inserted ${link} into ${annotationFieldLabels[target.id] || "field"}`;
    }

    async function copyLinkToClipboard(vertex) {
      const link = `[${vertex}](move:${vertex})`;
      try {
        await navigator.clipboard.writeText(link);
        $("status").textContent = `Copied ${link}`;
      } catch (error) {
        $("status").textContent = `Could not copy: ${error.message}`;
      }
    }

    function openContextMenu(event, row, col) {
      event.preventDefault();
      const vertex = pointToVertex(row, col);
      contextMenuTarget = vertex;
      const menu = $("context-menu");
      menu.style.left = `${event.clientX}px`;
      menu.style.top = `${event.clientY}px`;
      menu.classList.add("visible");
    }

    function closeContextMenu() {
      $("context-menu").classList.remove("visible");
      contextMenuTarget = null;
    }

    function setupContextMenu() {
      const menu = $("context-menu");
      menu.querySelectorAll("button").forEach((button) => {
        button.onclick = () => {
          if (!contextMenuTarget) {
            closeContextMenu();
            return;
          }
          if (button.dataset.action === "insert") {
            insertLinkAtCaret(contextMenuTarget);
          } else if (button.dataset.action === "copy") {
            copyLinkToClipboard(contextMenuTarget);
          }
          closeContextMenu();
        };
      });
      document.addEventListener("click", (event) => {
        if (!menu.contains(event.target)) closeContextMenu();
      });
      document.addEventListener("scroll", closeContextMenu, true);
    }

    function setupKeyboard() {
      window.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && pickMode) {
          exitPickMode();
        }
      });
    }

    function extractMoveLinks(text) {
      if (!text) return [];
      const out = [];
      const pattern = new RegExp(MOVE_LINK_PATTERN.source, "g");
      let match;
      while ((match = pattern.exec(text)) !== null) {
        out.push(match[1]);
      }
      return out;
    }

    function isLegalVertex(vertex) {
      if (!vertex) return false;
      const size = currentPosition?.context?.board_size || 19;
      return vertexToKey(vertex, size) !== "";
    }

    function collectInvalidMoveLinks() {
      const fields = annotationFieldIds.map((id) => $(id).value);
      const all = fields.flatMap(extractMoveLinks);
      return all.filter((vertex) => !isLegalVertex(vertex));
    }

    function playMove(row, col) {
      if (!currentPosition) return;
      if (trialMoves.some((move) => move.row === row && move.col === col)) return;
      const move = {
        color: nextColor(),
        vertex: pointToVertex(row, col),
        row,
        col
      };
      trialMoves.push(move);
      currentPosition.move_history = structuredClone(trialMoves);
      currentPosition.context.side_to_move = nextColor();
      currentPosition.context.move_number = trialMoves.length;
      renderPosition();
      refreshAnalysis();
    }

    function resetLine() {
      if (!basePosition) return;
      currentPosition = structuredClone(basePosition);
      trialMoves = structuredClone(currentPosition.move_history || []);
      selectedCandidate = currentPosition.candidates[0] || null;
      renderPosition();
      prefillFromCandidate();
    }

    function nextColor() {
      const baseColor = basePosition?.context?.side_to_move || currentPosition?.context?.side_to_move || "b";
      const baseCount = basePosition?.move_history?.length || 0;
      const played = Math.max(0, trialMoves.length - baseCount);
      if (played % 2 === 0) return baseColor;
      return baseColor === "b" ? "w" : "b";
    }

    function pointToVertex(row, col) {
      return `${COLUMNS[col]}${row + 1}`;
    }

    function vertexToKey(vertex, size) {
      if (!vertex || vertex.toLowerCase() === "pass") return "";
      const col = COLUMNS.indexOf(vertex[0].toUpperCase());
      const row = Number.parseInt(vertex.slice(1), 10) - 1;
      if (col < 0 || Number.isNaN(row) || row < 0 || row >= size) return "";
      return `${row},${col}`;
    }

    function movesForKatago() {
      return trialMoves.map((move) => ({
        color: move.color,
        position: [move.row, move.col]
      }));
    }

    function refreshAnalysis() {
      if (!currentPosition) return;
      const url = $("katago-url").value.trim();
      const queryId = `annotation-${Date.now()}`;
      pendingQueryId = queryId;
      $("status").textContent = `Requesting KataGo analysis for ${trialMoves.length} moves...`;

      const sendQuery = () => {
        katagoSocket.send(JSON.stringify({
          id: queryId,
          moves: movesForKatago(),
          komi: currentPosition.context.komi,
          board_size_x: currentPosition.context.board_size,
          board_size_y: currentPosition.context.board_size,
          analyze_turns: [trialMoves.length],
          max_visits: Number.parseInt($("max-visits").value, 10),
          include_policy: true,
          include_ownership: true
        }));
      };

      if (!katagoSocket || katagoSocket.readyState === WebSocket.CLOSED) {
        katagoSocket = new WebSocket(url);
        katagoSocket.onopen = sendQuery;
        katagoSocket.onerror = () => {
          $("status").textContent = `Could not connect to ${url}`;
        };
        katagoSocket.onmessage = (event) => handleKatagoResponse(JSON.parse(event.data));
        return;
      }

      if (katagoSocket.readyState === WebSocket.CONNECTING) {
        katagoSocket.addEventListener("open", sendQuery, {once: true});
        return;
      }

      sendQuery();
    }

    function handleKatagoResponse(response) {
      if (!currentPosition || response.id !== pendingQueryId || response.isDuringSearch) return;
      currentPosition.id = response.id;
      currentPosition.root_winrate = response.rootInfo?.winrate ?? null;
      currentPosition.root_score_lead = response.rootInfo?.scoreLead ?? null;
      currentPosition.root_score_stdev = response.rootInfo?.scoreStdev ?? null;
      currentPosition.candidates = (response.moveInfos || []).map((moveInfo, index) => ({
        vertex: moveInfo.move,
        rank: index + 1,
        visits: moveInfo.visits ?? null,
        policy: moveInfo.prior ?? null,
        winrate: moveInfo.winrate ?? null,
        score_lead: moveInfo.scoreLead ?? null,
        score_stdev: moveInfo.scoreStdev ?? null,
        pv: moveInfo.pv || [],
        source: "katago_live"
      }));
      currentPosition.raw = response;
      selectedCandidate = currentPosition.candidates[0] || null;
      renderPosition();
      prefillFromCandidate();
      $("status").textContent = `Live KataGo analysis updated for ${trialMoves.length} moves`;
    }

    async function saveAnnotation() {
      if (!currentPosition || !selectedCandidate) return;
      const invalid = collectInvalidMoveLinks();
      if (invalid.length > 0) {
        const proceed = confirm(
          `These move references look invalid for this board: ${invalid.join(", ")}\n\nSave anyway?`
        );
        if (!proceed) {
          $("status").textContent = `Fix invalid move links: ${invalid.join(", ")}`;
          return;
        }
      }
      const annotation = {
        position_id: currentPosition.id,
        move: $("move").value,
        move_role: csv($("move-role").value),
        local_tactics: csv($("local-tactics").value),
        global_context: csv($("global-context").value),
        main_reason: $("main-reason").value,
        bad_if_ignored: $("bad-if-ignored").value || null,
        evidence: {
          candidate_vertex: selectedCandidate.vertex,
          candidate_rank: selectedCandidate.rank,
          winrate_delta: null,
          score_delta: null,
          visits: selectedCandidate.visits ?? null,
          pv_reference: selectedCandidate.pv || [],
          ownership_regions: currentPosition.ownership_deltas.map((x) => x.region)
        },
        confidence: Number.parseFloat($("confidence").value)
      };

      const response = await fetch("/api/annotations", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          position: currentPosition,
          annotation,
          annotator: $("annotator").value,
          notes: $("notes").value
        })
      });

      if (!response.ok) {
        $("status").textContent = await response.text();
        return;
      }
      const record = await response.json();
      $("status").textContent = `Saved ${record.record_id}`;
    }

    $("load-random").onclick = loadRandom;
    $("save").onclick = saveAnnotation;
    $("insert-move-link").onclick = enterPickMode;
    $("refresh-analysis").onclick = refreshAnalysis;
    $("reset-line").onclick = resetLine;
    trackAnnotationFocus();
    setupContextMenu();
    setupKeyboard();
    loadRandom();
  </script>
</body>
</html>
"""
