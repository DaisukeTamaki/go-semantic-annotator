from __future__ import annotations

import json
from pathlib import Path

from go_semantic_annotator import KataGoPositionAnalysis, annotate_position

ROOT = Path(__file__).resolve().parents[1]


def test_baseline_annotates_top_candidate() -> None:
    payload = json.loads((ROOT / "examples" / "katago_position.json").read_text())
    position = KataGoPositionAnalysis.model_validate(payload)

    annotation = annotate_position(position)

    assert annotation.move == "Q4"
    assert annotation.move_role == [
        "direction_of_play",
        "katago_top_choice",
        "territory_shift",
    ]
    assert annotation.evidence.score_delta == 0.0
    assert annotation.confidence == 0.85


def test_baseline_can_annotate_inferior_candidate() -> None:
    payload = json.loads((ROOT / "examples" / "katago_position.json").read_text())
    position = KataGoPositionAnalysis.model_validate(payload)

    annotation = annotate_position(position, candidate_rank=2)

    assert annotation.move == "D16"
    assert annotation.evidence.score_delta == -0.7
    assert "inferior_candidate" not in annotation.move_role
