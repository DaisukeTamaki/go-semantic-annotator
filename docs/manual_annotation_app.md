# Manual Annotation App

The repo includes a lightweight local web app for expert annotation. It is intentionally
dependency-light and uses Python's standard library server rather than a product UI
framework.

## Launch

```bash
go-semantic-annotator annotation-app
```

By default, the app:

- reads normalized position JSON files from `examples/`
- opens `http://127.0.0.1:8765`
- writes validated JSONL records to `datasets/manual_annotations.jsonl`

For live analysis, run `katago-server` separately:

```bash
katago-server serve
```

The browser app connects directly to `ws://127.0.0.1:8000/ws/analyze` by default. You
can edit the WebSocket URL in the app if `katago-server` is running somewhere else.

Custom paths:

```bash
go-semantic-annotator annotation-app \
  --queue-dir data/annotation_queue \
  --output-path datasets/manual_annotations.jsonl
```

## Current Workflow

1. Load a random normalized `KataGoPositionAnalysis` JSON file.
2. Show a simple board, move history, and KataGo candidate moves.
3. Click empty intersections to try moves on the board.
4. Refresh live KataGo analysis for the current trial line.
5. Select a candidate from the updated analysis.
6. Fill semantic labels and short expert explanation fields.
7. Save a validated `ManualAnnotationRecord` row to JSONL.

The app validates both the input position and output annotation with the repo's Pydantic
schemas before export.

Use `Reset Line` to return to the loaded position. The current version sends the full
trial move list as `moves` to `katago-server`, so queued positions should eventually
include complete game history when live analysis quality matters.

## Move References

Use Markdown links with `move:` targets when annotation text refers to a board point:

```md
[R3](move:R3) is larger globally than [R14](move:R14).
```

The app shows the current target field beside the annotation header. Two ways to
insert a move link into that target field:

- **Pick Mode**: click `Insert Move Link`, then click any board intersection.
  ESC cancels. The board border turns amber while pick mode is active.
- **Right-click on a board intersection**: choose `Insert link into focused field` or
  `Copy link to clipboard`.

If text is selected in the target field, that text becomes the link label.

The board shows a small hover label with the vertex name (for example `Q4`) while
pick mode is active.

When you save, the app warns if any `move:XYZ` reference is not a legal coordinate
for the current board.

Clicking a candidate row in the candidate list plays that candidate as a trial move,
the same as clicking the corresponding intersection on the board.

Store the Markdown as-is in manual annotations. Export scripts can later parse `move:`
links into structured reference metadata for board hover/highlight behavior.

## Export Shape

Each JSONL row is:

```text
ManualAnnotationRecord
  record_id
  position: KataGoPositionAnalysis
  annotation: SemanticAnnotation
  annotator
  notes
  created_at
```

This keeps the full normalized input beside the expert label, which makes later schema
migrations and eval construction easier.

## Intended Evolution

Keep this app focused on dataset creation, not polished end-user explanation.

Near-term improvements:

- Load positions from SGF files and sample random turns.
- Display principal variations on the board.
- Add ownership and score-delta visualizations.
- Add keyboard-first labeling for repeated expert work.
- Track reviewed/skipped/difficult positions.
- Export train/dev/test splits.

Later improvements:

- Add A-vs-B pairwise comparison annotation.
- Add human-level alternative candidates: pro-natural, dan-natural, kyu-natural.
- Reuse or migrate UI pieces from the future Sabaki-style `stonehearts` board.
- Support LLM draft labels that are reviewed and corrected by the expert annotator.

## Relationship To Stonehearts

`stonehearts` can eventually provide the nicer Sabaki-style board and LLM explanation
surface. This app should remain the fast internal dataset tool until the annotation
workflow is stable enough to justify deeper UI integration.
