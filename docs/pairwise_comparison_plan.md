# Pairwise Comparison Plan

One of the most important explanations is:

> Why does KataGo prefer move line A instead of a human-preferred move line B?

This should eventually be a first-class semantic annotation task. Do not leave the
relationship entirely to a frontier LLM, because this is where plausible but unsupported
Go explanations are easy to invent.

## Staged Approach

1. Single-line annotations first

   Train and evaluate reliable annotations for each candidate independently:

   - KataGo top move A -> roles, tactics, global context, evidence, short reason.
   - Human-preferred move B -> roles, tactics, global context, evidence, short reason.

2. Pairwise comparison schema second

   Add a separate output type for A-vs-B comparison once the single-line schema is
   stable. This output should be structured JSON, not polished prose.

3. Pairwise training third

   Train on expert-verified comparisons such as KataGo top line vs pro-natural,
   dan-natural, kyu-natural, and beginner-natural alternatives.

## Target Output Shape

```json
{
  "preferred_move": "Q4",
  "alternative_move": "D16",
  "preference_reason": ["better_global_direction", "larger_score_gain"],
  "tradeoff": "D16 is natural locally, but Q4 makes the lower right larger while keeping the whole-board balance.",
  "why_human_likes_alternative": ["natural_shape", "easy_to_understand"],
  "why_katago_prefers_move": ["global_direction", "ownership_swing"],
  "evidence": {
    "score_delta": 2.1,
    "winrate_delta": 0.034,
    "pv_divergence": "after_move_3",
    "ownership_regions": ["lower_right", "center"]
  },
  "confidence": 0.82
}
```

## Responsibility Boundary

The semantic annotator should decide the relationship:

- what A gains over B
- what B gains or preserves
- why B looks human-natural
- why KataGo still prefers A
- which evidence supports the comparison

The frontier LLM should only turn this structured comparison into natural explanation
for the target audience.

## Evaluation Focus

Create eval positions where the difference is subtle and educational:

- KataGo global direction vs human local shape.
- AI-preferred tenuki vs human urgent-looking local defense.
- Lower winrate human move that is easier to explain or safer for weaker players.
- Move with similar winrate but different score variance.
- Same local sequence with different whole-board meaning.
- KataGo top move that looks thin, ugly, or anti-shape to humans.
