from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from go_semantic_annotator.annotator import annotate_position
from go_semantic_annotator.models import KataGoPositionAnalysis, SemanticAnnotation
from go_semantic_annotator.normalize import normalize_katago_response

app = typer.Typer(help="Tools for Go semantic annotation experiments.")


@app.command()
def validate_input(path: Annotated[Path, typer.Argument(help="Normalized input JSON.")]) -> None:
    """Validate a normalized KataGoPositionAnalysis payload."""

    payload = _read_json(path)
    position = KataGoPositionAnalysis.model_validate(payload)
    typer.echo(f"ok: {position.id} with {len(position.candidates)} candidates")


@app.command()
def validate_output(
    path: Annotated[Path, typer.Argument(help="Semantic annotation JSON.")],
) -> None:
    """Validate a SemanticAnnotation payload."""

    payload = _read_json(path)
    annotation = SemanticAnnotation.model_validate(payload)
    typer.echo(f"ok: {annotation.position_id} {annotation.move}")


@app.command()
def normalize(
    input_path: Annotated[Path, typer.Argument(help="Raw KataGo response JSON.")],
    output_path: Annotated[Path, typer.Argument(help="Destination normalized JSON.")],
    side_to_move: Annotated[str, typer.Option(help="Side to move: b or w.")] = "b",
) -> None:
    """Normalize a raw KataGo response into the training input schema."""

    payload = _read_json(input_path)
    position = normalize_katago_response(payload, side_to_move=side_to_move)
    _write_json(output_path, position.model_dump(mode="json"))
    typer.echo(f"wrote {output_path}")


@app.command()
def annotate(
    input_path: Annotated[Path, typer.Argument(help="Normalized input JSON.")],
    output_path: Annotated[Path, typer.Argument(help="Destination semantic annotation JSON.")],
    candidate_rank: Annotated[int, typer.Option(help="Candidate rank to annotate.")] = 1,
) -> None:
    """Run the deterministic baseline annotator."""

    payload = _read_json(input_path)
    position = KataGoPositionAnalysis.model_validate(payload)
    annotation = annotate_position(position, candidate_rank=candidate_rank)
    _write_json(output_path, annotation.model_dump(mode="json"))
    typer.echo(f"wrote {output_path}")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
