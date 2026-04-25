from __future__ import annotations

from go_semantic_annotator.normalize import normalize_katago_response


def test_normalize_raw_katago_response() -> None:
    position = normalize_katago_response(
        {
            "id": "query-1",
            "turnNumber": 12,
            "rootInfo": {
                "winrate": 0.51,
                "scoreLead": 0.4,
                "scoreStdev": 7.9,
            },
            "moveInfos": [
                {
                    "move": "D4",
                    "visits": 120,
                    "prior": 0.2,
                    "winrate": 0.51,
                    "scoreLead": 0.4,
                    "scoreStdev": 7.9,
                    "pv": ["D4", "Q16"],
                }
            ],
        }
    )

    assert position.id == "query-1"
    assert position.context.move_number == 12
    assert position.candidates[0].vertex == "D4"
