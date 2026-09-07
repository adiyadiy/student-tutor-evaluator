# Two-Tutor Comparison — Toy Experiment Results

n_seeds = 100 (seeds 0..99)

This is a toy / methodological experiment (see RESEARCH_NOTES.md), not the final simulator.

## Ranking validity

- Ground-truth tutor ranking: **EffectiveTutor > WeakTutor**
- Simulator-measured ranking: **EffectiveTutor > WeakTutor**
- Ranking recovered: **True**

## Tutor-level summary

| tutor | mean p_correct_pre | mean p_correct_aided | mean p_correct_post (primary) | stdev post | independent accuracy | mean knowledge gain | fraction learned | mean misconception reduction |
|---|---|---|---|---|---|---|---|---|
| EffectiveTutor | 0.117 | 0.249 | 0.180 | 0.066 | 0.180 | +0.053 | 0.910 | +0.296 |
| WeakTutor | 0.117 | 0.249 | 0.115 | 0.017 | 0.150 | +0.042 | 0.910 | +0.000 |

`p_correct_post` (independent, unaided, on a new problem) is the primary tutor-quality
metric. `p_correct_pre`/`p_correct_aided` are immediate performance, reported for
context only -- not used to judge tutor quality.

## Paired differences (Tutor A − Tutor B, same seed)

- mean delta p_correct_post: +0.0650  (95% CI [+0.0551, +0.0750])
- mean delta knowledge gain: +0.0103  (95% CI [+0.0051, +0.0156])
- seeds where A > B: 89, tied: 11, B > A: 0

### Check that the experiment can fail

Individual seeds where B ties or beats A are expected from a stochastic mechanism and are
not treated as a problem -- no resampling or special-casing is applied. The ranking claim
is about the aggregate across seeds, not every trajectory. See `paired_diffs` in the JSON
output for the full per-seed breakdown.

## Distribution of paired differences

min=+0.0000, p10=+0.0000, p25=+0.0524, median=+0.0524, p75=+0.0524, p90=+0.1868, max=+0.1868

5 distinct delta values across 100 seeds (largest single bucket = 65% of seeds):

| delta_p_correct_post | count |
|---|---|
| +0.0000 | 11 |
| +0.0476 | 8 |
| +0.0524 | 65 |
| +0.0958 | 3 |
| +0.1868 | 13 |

## Methodological concern: is the tutor gap artificially strong?

**Yes, likely, at the current parameter values.** Evidence:

- Zero-variance metric: `WeakTutor.misconception_delta (constant +0.0000 across all seeds)`.
- The outcome distribution is highly discretized: only 5 distinct `delta_p_correct_post` values across 100 seeds, with 65% of seeds landing on a single value.

Root cause: `WeakTutor.addresses_misconception` is a hard, always-False switch, and `EffectiveTutor.addresses_misconception` is a hard, almost-always-True switch (true whenever the student is struggling on the tutoring problem, which is most seeds given the toy initial state). `student/learning.py`'s misconception-decay term is then applied deterministically whenever that switch is True, unconditional on whether the aided attempt succeeds. The result is that misconception reduction is either exactly 0 (WeakTutor, every seed) or a fixed decay amount (EffectiveTutor, whenever it intervenes) -- a near-binary toggle rather than a gradually emergent property of varied stochastic trajectories. The ranking direction (A > B) is a genuine consequence of the existing, unmodified learning mechanism -- it was not hardcoded into the evaluation code -- but the *size and near-certainty* of the gap mostly comes from how strongly the two toy tutors were defined to differ, not from rich simulated learning dynamics. This should be treated as a demonstration that the pipeline and metrics are wired correctly end to end, not as evidence that a real simulator would show this large or this consistent a gap between a genuinely strong and genuinely weak real tutor.
