from __future__ import annotations

import json
from pathlib import Path

from go_semantic_annotator.annotation_app import (
    append_annotation_record,
    load_random_position,
    position_files,
)
from go_semantic_annotator.models import KataGoPositionAnalysis, SemanticAnnotation

ROOT = Path(__file__).resolve().parents[1]


def test_position_files_finds_valid_queue_items() -> None:
    files = position_files(ROOT / "examples")

    assert ROOT / "examples" / "katago_position.json" in files


def test_load_random_position_validates_payload() -> None:
    position = load_random_position(ROOT / "examples")

    assert position.id == "opening-direction-example"


def test_append_annotation_record_writes_jsonl(tmp_path: Path) -> None:
    position_payload = json.loads((ROOT / "examples" / "katago_position.json").read_text())
    annotation_payload = json.loads((ROOT / "examples" / "semantic_annotation.json").read_text())
    position = KataGoPositionAnalysis.model_validate(position_payload)
    annotation = SemanticAnnotation.model_validate(annotation_payload)
    output_path = tmp_path / "manual_annotations.jsonl"

    record = append_annotation_record(
        position=position,
        annotation=annotation,
        output_path=output_path,
        annotator="daisuke",
        notes="fixture",
    )

    saved = json.loads(output_path.read_text().strip())
    assert saved["record_id"] == record.record_id
    assert saved["annotator"] == "daisuke"
    assert saved["annotation"]["move"] == "Q4"
