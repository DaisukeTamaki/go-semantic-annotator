from __future__ import annotations

from go_semantic_annotator.models import Evidence, KataGoPositionAnalysis, SemanticAnnotation


def annotate_position(
    position: KataGoPositionAnalysis, *, candidate_rank: int = 1
) -> SemanticAnnotation:
    """Create a deterministic baseline annotation for one candidate move.

    This is not meant to replace the trained model. It gives the repo a working
    contract, useful fixtures, and a simple baseline to beat during evaluation.
    """

    candidate = _candidate_by_rank(position, candidate_rank)
    best = _candidate_by_rank(position, 1)

    winrate_delta = _delta(candidate.winrate, best.winrate)
    score_delta = _delta(candidate.score_lead, best.score_lead)
    ownership_regions = [
        delta.region for delta in position.ownership_deltas if abs(delta.delta) >= 0.5
    ][:3]

    move_role = _infer_move_role(position, score_delta)
    global_context = _infer_global_context(position)
    local_tactics = _infer_local_tactics(candidate.pv)

    reason = _reason_for(move_role, global_context, ownership_regions)
    confidence = _confidence(candidate.rank, candidate.visits, position.candidates)

    return SemanticAnnotation(
        position_id=position.id,
        move=candidate.vertex,
        move_role=move_role,
        local_tactics=local_tactics,
        global_context=global_context,
        main_reason=reason,
        bad_if_ignored=_bad_if_ignored(move_role),
        evidence=Evidence(
            candidate_vertex=candidate.vertex,
            candidate_rank=candidate.rank,
            winrate_delta=winrate_delta,
            score_delta=score_delta,
            visits=candidate.visits,
            pv_reference=candidate.pv[:8],
            ownership_regions=ownership_regions,
        ),
        confidence=confidence,
    )


def _candidate_by_rank(position: KataGoPositionAnalysis, rank: int):
    for candidate in position.candidates:
        if candidate.rank == rank:
            return candidate
    msg = f"position {position.id!r} has no candidate with rank {rank}"
    raise ValueError(msg)


def _delta(value: float | None, baseline: float | None) -> float | None:
    if value is None or baseline is None:
        return None
    return round(value - baseline, 4)


def _infer_move_role(position: KataGoPositionAnalysis, score_delta: float | None) -> list[str]:
    roles: list[str] = []

    if position.context.game_phase == "endgame":
        roles.append("endgame_value")
    elif position.context.game_phase == "opening":
        roles.append("direction_of_play")
    else:
        roles.append("whole_board_balance")

    if score_delta is not None and score_delta < -1.5:
        roles.append("inferior_candidate")
    elif score_delta is not None and score_delta > 0.5:
        roles.append("score_gain")
    else:
        roles.append("katago_top_choice")

    if position.ownership_deltas:
        largest = max(position.ownership_deltas, key=lambda item: abs(item.delta))
        roles.append("territory_shift" if abs(largest.delta) >= 0.5 else "thin_delta")

    return roles


def _infer_global_context(position: KataGoPositionAnalysis) -> list[str]:
    context: list[str] = [position.context.game_phase]

    score = position.root_score_lead
    if score is None:
        context.append("score_unknown")
    elif score >= 5:
        context.append("black_leads")
    elif score <= -5:
        context.append("white_leads")
    else:
        context.append("close_game")

    return context


def _infer_local_tactics(pv: list[str]) -> list[str]:
    if len(pv) >= 4:
        return ["follow_up_sequence"]
    if len(pv) >= 2:
        return ["short_tactical_sequence"]
    return []


def _reason_for(
    move_role: list[str], global_context: list[str], ownership_regions: list[str]
) -> str:
    region_text = ""
    if ownership_regions:
        region_text = (
            f" The strongest visible ownership changes are in {', '.join(ownership_regions)}."
        )

    if "inferior_candidate" in move_role:
        return (
            "This candidate appears meaningfully worse than the top line and should be treated "
            f"as a comparison point rather than the main recommendation.{region_text}"
        )

    if "endgame_value" in move_role:
        return (
            "The move is selected for endgame value while preserving the current "
            f"score context.{region_text}"
        )

    if "direction_of_play" in move_role:
        return (
            "The move fits the opening direction of play according to the candidate "
            f"ordering.{region_text}"
        )

    return (
        "The move balances whole-board value with the strongest available KataGo "
        f"line.{region_text}"
    )


def _bad_if_ignored(move_role: list[str]) -> str | None:
    if "inferior_candidate" in move_role:
        return "The top candidate likely keeps better score or winrate prospects."
    if "territory_shift" in move_role:
        return "The opponent may take the key area indicated by the ownership swing."
    return None


def _confidence(candidate_rank: int, visits: int | None, candidates: list[object]) -> float:
    base = 0.75 if candidate_rank == 1 else 0.55
    if visits is not None and visits >= 500:
        base += 0.1
    if len(candidates) < 2:
        base -= 0.1
    return max(0.0, min(round(base, 2), 1.0))
