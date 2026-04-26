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

Custom paths:

```bash
go-semantic-annotator annotation-app \
  --queue-dir data/annotation_queue \
  --output-path datasets/manual_annotations.jsonl
```

## Current Workflow

1. Load a random normalized `KataGoPositionAnalysis` JSON file.
2. Show a simple board, move history, and KataGo candidate moves.
3. Select a candidate.
4. Fill semantic labels and short expert explanation fields.
5. Save a validated `ManualAnnotationRecord` row to JSONL.

The app validates both the input position and output annotation with the repo's Pydantic
schemas before export.

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
- Request fresh analysis from `katago-server`.
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
