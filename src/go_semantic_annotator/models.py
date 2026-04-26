from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Color = Literal["b", "w"]
GamePhase = Literal["opening", "middle_game", "endgame", "unknown"]


class Move(BaseModel):
    """A board move in normalized coordinates."""

    model_config = ConfigDict(extra="forbid")

    color: Color
    vertex: str = Field(description="KataGo-style vertex, for example D4 or pass.")
    row: int | None = Field(default=None, ge=0)
    col: int | None = Field(default=None, ge=0)


class CandidateMove(BaseModel):
    """One candidate move from KataGo or a human-level policy source."""

    model_config = ConfigDict(extra="forbid")

    vertex: str
    rank: int = Field(ge=1)
    visits: int | None = Field(default=None, ge=0)
    policy: float | None = None
    winrate: float | None = Field(default=None, ge=0.0, le=1.0)
    score_lead: float | None = None
    score_stdev: float | None = Field(default=None, ge=0.0)
    pv: list[str] = Field(default_factory=list)
    source: str = Field(default="katago")


class OwnershipDelta(BaseModel):
    """Compact ownership signal for a region or group."""

    model_config = ConfigDict(extra="forbid")

    region: str
    before: float
    after: float
    delta: float


class PositionContext(BaseModel):
    """Human-facing context that is not directly emitted by KataGo."""

    model_config = ConfigDict(extra="forbid")

    game_phase: GamePhase = "unknown"
    side_to_move: Color
    board_size: int = Field(default=19, ge=2)
    move_number: int | None = Field(default=None, ge=0)
    komi: float = 6.5
    score_context: str | None = Field(
        default=None,
        description="Short precomputed context, for example 'black_leads_by_8'.",
    )


class KataGoPositionAnalysis(BaseModel):
    """Normalized model input for one position and one candidate move set."""

    model_config = ConfigDict(extra="forbid")

    id: str
    context: PositionContext
    move_history: list[Move] = Field(default_factory=list)
    root_winrate: float | None = Field(default=None, ge=0.0, le=1.0)
    root_score_lead: float | None = None
    root_score_stdev: float | None = Field(default=None, ge=0.0)
    candidates: list[CandidateMove]
    ownership_deltas: list[OwnershipDelta] = Field(default_factory=list)
    raw: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional original payload for traceability. Do not train on this blindly.",
    )


class Evidence(BaseModel):
    """Numeric and source-backed fields the language model can cite."""

    model_config = ConfigDict(extra="forbid")

    candidate_vertex: str
    candidate_rank: int
    winrate_delta: float | None = None
    score_delta: float | None = None
    visits: int | None = None
    pv_reference: list[str] = Field(default_factory=list)
    ownership_regions: list[str] = Field(default_factory=list)


class SemanticAnnotation(BaseModel):
    """Constrained output to feed a frontier LLM or UI."""

    model_config = ConfigDict(extra="forbid")

    position_id: str
    move: str
    move_role: list[str]
    local_tactics: list[str] = Field(default_factory=list)
    global_context: list[str] = Field(default_factory=list)
    main_reason: str
    bad_if_ignored: str | None = None
    evidence: Evidence
    confidence: float = Field(ge=0.0, le=1.0)


class ManualAnnotationRecord(BaseModel):
    """One expert-authored dataset row exported by the annotation app."""

    model_config = ConfigDict(extra="forbid")

    record_id: str
    position: KataGoPositionAnalysis
    annotation: SemanticAnnotation
    annotator: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
