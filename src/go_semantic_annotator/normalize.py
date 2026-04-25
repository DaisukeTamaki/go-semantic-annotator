from __future__ import annotations

from typing import Any

from go_semantic_annotator.models import CandidateMove, KataGoPositionAnalysis, PositionContext


def normalize_katago_response(
    payload: dict[str, Any],
    *,
    position_id: str | None = None,
    side_to_move: str = "b",
    board_size: int = 19,
    komi: float = 6.5,
) -> KataGoPositionAnalysis:
    """Convert a raw KataGo analysis response into the initial training schema.

    This intentionally preserves only stable, compact fields. Add richer derived
    features here as you decide which signals are useful for expert labels.
    """

    root = payload.get("rootInfo", {})
    move_infos = payload.get("moveInfos", [])

    candidates = [
        CandidateMove(
            vertex=str(move_info.get("move", "")),
            rank=rank,
            visits=move_info.get("visits"),
            policy=move_info.get("prior"),
            winrate=move_info.get("winrate"),
            score_lead=move_info.get("scoreLead"),
            score_stdev=move_info.get("scoreStdev"),
            pv=[str(move) for move in move_info.get("pv", [])],
        )
        for rank, move_info in enumerate(move_infos, start=1)
        if move_info.get("move")
    ]

    return KataGoPositionAnalysis(
        id=position_id or str(payload.get("id", "position")),
        context=PositionContext(
            side_to_move=side_to_move,  # type: ignore[arg-type]
            board_size=board_size,
            move_number=payload.get("turnNumber"),
            komi=komi,
        ),
        root_winrate=root.get("winrate"),
        root_score_lead=root.get("scoreLead"),
        root_score_stdev=root.get("scoreStdev"),
        candidates=candidates,
        raw=payload,
    )
