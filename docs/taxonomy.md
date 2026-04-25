# Initial Label Taxonomy

This is intentionally small. Treat it as the first controlled vocabulary for expert
annotation, not as a complete Go ontology.

## Move Roles

- `katago_top_choice`: the move is the top KataGo candidate.
- `inferior_candidate`: the move is a comparison candidate with clearly worse score or winrate.
- `direction_of_play`: opening move whose value depends on whole-board direction.
- `whole_board_balance`: middle-game move balancing multiple board areas.
- `endgame_value`: endgame move primarily selected for point value and sente/gote context.
- `score_gain`: candidate has a positive score delta against the comparison baseline.
- `territory_shift`: ownership deltas indicate a meaningful territorial swing.
- `thin_delta`: ownership signal exists but is too small to rely on strongly.

## Local Tactics

- `follow_up_sequence`: principal variation has enough continuation to cite.
- `short_tactical_sequence`: principal variation is present but short.
- `probe`
- `shape_point`
- `sente`
- `gote`
- `tesuji`
- `sacrifice`
- `sabaki`

## Global Context

- `opening`
- `middle_game`
- `endgame`
- `unknown`
- `black_leads`
- `white_leads`
- `close_game`
- `score_unknown`

## Near-Term Annotation Goal

The first useful eval set should stress positions where the same local shape changes
meaning by whole-board context:

- invasion vs reduction
- attack vs defense
- kikashi vs overplay
- sente endgame vs gote endgame
- sabaki vs running away
- big point vs urgent point
