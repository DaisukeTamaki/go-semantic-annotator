from __future__ import annotations

import json
from pathlib import Path

from go_semantic_annotator.models import KataGoPositionAnalysis, SemanticAnnotation

ROOT = Path(__file__).resolve().parents[1]


def test_example_input_matches_schema() -> None:
    payload = json.loads((ROOT / "examples" / "katago_position.json").read_text())

    position = KataGoPositionAnalysis.model_validate(payload)

    assert position.id == "opening-direction-example"
    assert position.candidates[0].vertex == "Q4"


def test_example_output_matches_schema() -> None:
    payload = json.loads((ROOT / "examples" / "semantic_annotation.json").read_text())

    annotation = SemanticAnnotation.model_validate(payload)

    assert annotation.position_id == "opening-direction-example"
    assert annotation.evidence.candidate_vertex == "Q4"
