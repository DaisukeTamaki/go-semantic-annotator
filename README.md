# go-semantic-annotator

Structured Go move semantics from KataGo analysis.

This repo is the third component beside `katago-server` and `stonehearts`:

- `katago-server` owns KataGo process management and raw analysis.
- `go-semantic-annotator` owns normalized inputs, labels, datasets, evals, and model experiments.
- `stonehearts` consumes the resulting JSON to render explanations.

The project goal is not to train an LLM to play Go. KataGo remains the source of
truth. This repo trains and evaluates a small model that translates KataGo-derived
facts into constrained semantic JSON.

## Current Scope

The initial version includes:

- Pydantic schemas for normalized KataGo position analysis and semantic output.
- A deterministic baseline annotator to establish the contract.
- A CLI for validation, normalization, and baseline annotation.
- A lightweight local manual annotation app for expert JSONL dataset creation.
- Example input/output fixtures.
- A starter label taxonomy.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Validate the example payloads:

```bash
go-semantic-annotator validate-input examples/katago_position.json
go-semantic-annotator validate-output examples/semantic_annotation.json
```

Run the baseline annotator:

```bash
go-semantic-annotator annotate \
  examples/katago_position.json \
  outputs/example_annotation.json
```

Launch the manual annotation app:

```bash
go-semantic-annotator annotation-app
```

## Data Contract

Input:

```text
KataGoPositionAnalysis
  context
  move_history
  root winrate / score / score stdev
  candidate moves with policy, visits, winrate, score, and PV
  optional compact ownership deltas
```

Output:

```text
SemanticAnnotation
  move_role
  local_tactics
  global_context
  main_reason
  bad_if_ignored
  evidence
  confidence
```

See `examples/` and `docs/taxonomy.md`.

## Manual Annotation

Use the local annotation app to load normalized positions, try moves on the board,
refresh live `katago-server` analysis, write expert semantic labels, and export
validated JSONL rows. This is intended as the fast internal dataset tool before any
deeper `stonehearts` UI integration.

See `docs/manual_annotation_app.md`.

## Pairwise Comparisons

A later core task is explaining why KataGo prefers move line A over a
human-preferred move line B. The plan is to first make single-line annotations reliable,
then add an explicit pairwise comparison schema and train it on expert-verified
A-vs-B examples. The frontier LLM should use that structured comparison for prose, not
invent the relationship itself.

See `docs/pairwise_comparison_plan.md`.

## Suggested Roadmap

1. Expand `normalize.py` to consume the exact payloads emitted by `katago-server`.
2. Add derived features: ownership summaries, group safety, liberties, eyespace, and phase.
3. Build a small expert eval set before generating large synthetic data.
4. Add annotation tooling for expert corrections.
5. Add a pairwise comparison schema for KataGo top moves vs human-preferred alternatives.
6. Train LoRA/QLoRA adapters for Qwen small models.
7. Add an inference service once the JSON schema stabilizes.

## Artifact Policy

Do not commit large generated datasets, model weights, or training runs. Keep this repo
for code, schemas, configs, docs, and small fixtures. Store larger artifacts in external
storage, Hugging Face, DVC, or Git LFS.
