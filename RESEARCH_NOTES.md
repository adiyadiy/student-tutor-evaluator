# Research Notes & Known Simplifications

## Toy-model simplifications

### Oracle misconception access
In this initial toy, the tutor has oracle access to the latent
misconception state.

This is an intentional simplification. The purpose of the toy is
to demonstrate the student-state → tutor-intervention → learning
dynamics pipeline.

In the data-calibrated simulator, misconception inference should
be based only on observable student behavior (e.g. answers,
errors, hints, response patterns), rather than direct access to
the latent state.

Status: TODO for data-calibrated simulator

### Other current toy assumptions

- **Skill ontology**: 3 flat, hand-picked skills for linear equations
  (`S1_one_step_add_sub`, `S2_one_step_mul_div`, `S3_two_step_linear`), no
  dependency graph. Placeholder until FoundationalASSIST's own skill/concept
  labels are available.
- **Hand-specified parameters**: all behavior/learning coefficients
  (`src/student/params.py`) were chosen once, before any run, based on
  generic plausibility ("a hint helps somewhat," "an unaided correct answer
  is stronger evidence than a guess"). None were fit to data, and none were
  adjusted after seeing outcomes to make a result look better.
- **Stochastic behavior**: every student decision (attempt, guess, correctness,
  hint-seeking, give-up, response time) is sampled from an explicit
  probability, seeded via `random.Random(seed)` for reproducibility.
- **Simplified tutors**: two rule-based tutors (`EffectiveTutor`,
  `WeakTutor`), no NLG, no LLM deciding student or tutor behavior.
- **Simplified learning dynamics**: a single interpretable moving-target
  update (`K_c += learning_rate * (target - K_c)`), not a fitted model.

---

## Two-tutor comparison experiment

`src/evaluation/tutor_comparison.py` extends the single-seed toy vertical
slice (`src/simulation/toy_scenario.py`) to ask: if Tutor A is designed to be
more effective than Tutor B, does the simulated-student evaluation recover
that ranking using independent post-tutoring performance?

**Why the same student for both tutors.** Tutor A and Tutor B are each run
against an identical initial student state and identical scripted problem
sequence (warm-up -> pre-tutoring attempt -> tutor turn -> aided attempt ->
independent assessment). If we instead drew a fresh random student per
tutor, any measured difference would be confounded with student-to-student
variation and would say nothing about the tutors themselves.

**Why paired seeds.** For each seed, both tutors are run through
`run_episode(seed, tutor=...)` with independent `random.Random(seed)`
instances. Because neither tutor consumes randomness and both produce
`type="explanation"` targeting the same skill on the same turn, the two
conditions consume the RNG in identical order through the aided attempt --
so `p_correct_pre` and the sequence of random draws up to the state update
are identical for A and B on a given seed, and any divergence after that
point is attributable to the tutor's effect on the state update, not to a
different random draw. This makes `post_p(A) - post_p(B)` a valid paired
difference per seed, analyzed both as a mean-with-CI and as a full
distribution (see `reports/results/tutor_comparison_summary.md`).

**Why independent assessment is the primary outcome.** The aided attempt
(immediately after the tutor's explanation, on the *same* problem) is
recorded but explicitly NOT used to judge tutor quality -- it conflates
tutoring help with performance, and a hint can raise immediate correctness
without producing any lasting learning. The independent assessment uses a
*different* problem on the same skill, presented with no tutor help, after
the state update -- so it measures transfer/learning rather than
in-the-moment assistance.

**What "ranking validity" means here.** A ground-truth ranking (`EffectiveTutor
> WeakTutor`) is defined by construction, not measured: EffectiveTutor is
designed to address the student's misconception when the tutor's (oracle)
view of the latent state shows one is present, WeakTutor never does.
"Ranking validity" is then the question of whether the simulator's *measured*
ranking (via mean independent post-tutoring `p_correct`, aggregated across
100 seeds) matches that ground truth. It was recovered in the 100-seed run
(see results file), but see the concern below before treating that as a
strong result.

### Known limitation: tutor gap may be artificially strong

The 100-seed run recovers `EffectiveTutor > WeakTutor` with 89/100 seeds
favoring A, 11 exact ties, and **0/100 seeds favoring B** -- and
`WeakTutor.misconception_delta` is **exactly 0.0 with zero variance across
all 100 seeds** (it structurally cannot reduce the misconception, since
`addresses_misconception` is hardcoded `False`). The paired `delta_p_correct_post`
distribution has only 5 distinct values across 100 seeds, with 65% of seeds
landing on one exact value. This is a near-deterministic switch, not a
gradually emergent property of varied stochastic trajectories: the *direction*
of the ranking is a genuine, unmodified consequence of `student/learning.py`
(no special-casing was added for this experiment), but the *size and
near-certainty* of the gap mostly reflects how strongly the two toy tutors
were defined to differ, particularly that `WeakTutor` never touches the
misconception term at all. Treat this run as a demonstration that the
pipeline and metrics are wired correctly end-to-end -- not as evidence that a
real strong-vs-weak tutor pair would show a gap this large or this
consistent. Full diagnostics are written to every run of
`tutor_comparison.py` (see "Methodological concern" section of the generated
summary) rather than only reported ad hoc.

If a less binary gap is wanted, candidates to reconsider (not applied without
review, since these are the parameters/behaviors that determine the
ground-truth effect size, not implementation bugs): making WeakTutor address
the misconception with some nonzero probability, or making the misconception
decay itself scale with the aided attempt's actual outcome rather than firing
unconditionally whenever `addresses_misconception` is True.

