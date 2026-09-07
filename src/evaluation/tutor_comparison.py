"""
Two-tutor paired comparison experiment (toy): does the simulated-student
evaluation recover a known ground-truth tutor ranking?

Ground-truth ranking, by construction (not measured): Tutor A (EffectiveTutor)
> Tutor B (WeakTutor), because EffectiveTutor addresses the student's
misconception when the toy tutor's (oracle-accessed) view of the latent state
shows one is present, and WeakTutor never does. See RESEARCH_NOTES.md for the
full rationale and the oracle-access caveat.

Paired design: for each seed, BOTH tutors are run against the SAME initial
student state and SAME scripted problem sequence, via independent
`random.Random(seed)` instances seeded identically. Because neither tutor
consumes randomness (TutorAction.respond is deterministic) and both tutors
produce a `type="explanation"` action targeting the same skill on the same
turn, the two tutor conditions consume the RNG in exactly the same order up
through the aided attempt -- so any divergence in outcomes traces back to the
tutor's `addresses_misconception` flag propagating through the existing
student/learning.py mechanism, not to a different random student. This
reuses `run_episode` from toy_scenario.py unmodified in its student-model
logic -- only a `tutor` parameter was added there so it could be swapped in.

No special-case logic makes Tutor A "win": both tutors run through the exact
same generate_response / update_state path. See "check that the experiment
can fail" in main(), which reports how many individual seeds show B >= A --
the claim is about the aggregate ranking across seeds, not every trajectory.

Run: python -m src.evaluation.tutor_comparison [--seeds 100]
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Dict, List

from src.simulation.toy_scenario import run_episode
from src.tutor.effective_tutor import EffectiveTutor
from src.tutor.weak_tutor import WeakTutor

GROUND_TRUTH_RANKING = ["EffectiveTutor", "WeakTutor"]  # A > B, by tutor design -- not measured
TUTOR_A = "EffectiveTutor"
TUTOR_B = "WeakTutor"


def run_comparison(seeds: List[int]) -> List[dict]:
    records = []
    for seed in seeds:
        for tutor in (EffectiveTutor(), WeakTutor()):
            trace = run_episode(seed, verbose=False, tutor=tutor)
            records.append(trace["summary"])
    return records


def _mean(xs: List[float]) -> float:
    return statistics.mean(xs) if xs else float("nan")


def _stdev(xs: List[float]) -> float:
    return statistics.stdev(xs) if len(xs) > 1 else 0.0


def summarize_by_tutor(records: List[dict]) -> Dict[str, dict]:
    by_tutor: Dict[str, List[dict]] = {}
    for r in records:
        by_tutor.setdefault(r["tutor"], []).append(r)

    summary = {}
    for tutor, rows in by_tutor.items():
        post_p = [r["p_correct_post"] for r in rows]
        knowledge_gain = [r["knowledge_delta"] for r in rows]
        misconception_reduction = [-r["misconception_delta"] for r in rows]  # positive = reduced
        correct_post = [1.0 if r["correct_post"] else 0.0 for r in rows]
        learned = [1.0 if r["learned"] else 0.0 for r in rows]
        summary[tutor] = {
            "n_seeds": len(rows),
            "mean_p_correct_pre": _mean([r["p_correct_pre"] for r in rows]),
            "mean_p_correct_aided": _mean([r["p_correct_aided"] for r in rows]),
            "mean_p_correct_post": _mean(post_p),
            "stdev_p_correct_post": _stdev(post_p),
            "independent_assessment_accuracy": _mean(correct_post),
            "mean_knowledge_gain": _mean(knowledge_gain),
            "stdev_knowledge_gain": _stdev(knowledge_gain),
            "fraction_learned": _mean(learned),
            "mean_misconception_reduction": _mean(misconception_reduction),
        }
    return summary


def paired_differences(records: List[dict], tutor_a: str, tutor_b: str) -> List[dict]:
    by_seed_tutor: Dict[int, Dict[str, dict]] = {}
    for r in records:
        by_seed_tutor.setdefault(r["seed"], {})[r["tutor"]] = r

    diffs = []
    for seed, by_tutor in sorted(by_seed_tutor.items()):
        if tutor_a not in by_tutor or tutor_b not in by_tutor:
            continue
        a, b = by_tutor[tutor_a], by_tutor[tutor_b]
        diffs.append(
            {
                "seed": seed,
                "delta_p_correct_post": a["p_correct_post"] - b["p_correct_post"],
                "delta_knowledge_gain": a["knowledge_delta"] - b["knowledge_delta"],
                "a_correct_post": a["correct_post"],
                "b_correct_post": b["correct_post"],
            }
        )
    return diffs


def distribution_diagnostics(records: List[dict], diffs: List[dict]) -> dict:
    """
    Reports the SHAPE of the outcome distribution, not just its mean, so a
    ranking that "recovers" A > B can be inspected for whether it emerged from
    varied stochastic trajectories or from a near-deterministic switch. A
    tutor-quality mechanism that is genuinely mediated by probabilistic
    student behavior should produce a reasonably continuous/varied spread of
    per-seed outcomes; a handful of exactly-repeated values, or a metric with
    zero variance for one tutor, is a sign the toy tutor definitions may be
    too strong/too binary rather than the ranking emerging gradually.
    """
    deltas = [d["delta_p_correct_post"] for d in diffs]
    deltas_sorted = sorted(deltas)
    n = len(deltas_sorted)

    def pct(p: float) -> float:
        if n == 0:
            return float("nan")
        idx = min(n - 1, int(p * n))
        return deltas_sorted[idx]

    bucket_counts: Dict[float, int] = {}
    for d in deltas:
        key = round(d, 4)
        bucket_counts[key] = bucket_counts.get(key, 0) + 1
    n_distinct_values = len(bucket_counts)
    largest_bucket_fraction = (max(bucket_counts.values()) / n) if n else float("nan")

    by_tutor_misconception_delta: Dict[str, List[float]] = {}
    by_tutor_knowledge_delta: Dict[str, List[float]] = {}
    for r in records:
        by_tutor_misconception_delta.setdefault(r["tutor"], []).append(r["misconception_delta"])
        by_tutor_knowledge_delta.setdefault(r["tutor"], []).append(r["knowledge_delta"])

    zero_variance_metrics = []
    for tutor, vals in by_tutor_misconception_delta.items():
        if _stdev(vals) == 0.0:
            zero_variance_metrics.append(f"{tutor}.misconception_delta (constant {vals[0]:+.4f} across all seeds)")
    for tutor, vals in by_tutor_knowledge_delta.items():
        if _stdev(vals) == 0.0:
            zero_variance_metrics.append(f"{tutor}.knowledge_delta (constant {vals[0]:+.4f} across all seeds)")

    return {
        "delta_p_correct_post": {
            "min": min(deltas) if deltas else float("nan"),
            "p10": pct(0.10),
            "p25": pct(0.25),
            "median": pct(0.50),
            "p75": pct(0.75),
            "p90": pct(0.90),
            "max": max(deltas) if deltas else float("nan"),
            "n_distinct_values": n_distinct_values,
            "largest_bucket_fraction": largest_bucket_fraction,
            "bucket_counts": {f"{k:+.4f}": v for k, v in sorted(bucket_counts.items())},
        },
        "zero_variance_metrics": zero_variance_metrics,
        "flag_highly_discretized_outcome": n_distinct_values <= 6 or largest_bucket_fraction >= 0.5,
    }


def _mean_ci95(xs: List[float]) -> tuple[float, float, float]:
    """Normal-approximation 95% CI (mean +/- 1.96*SE). Toy-scale approximation,
    not a rigorous t-test -- fine given the sample sizes used here."""
    mean = _mean(xs)
    if len(xs) < 2:
        return mean, mean, mean
    se = _stdev(xs) / math.sqrt(len(xs))
    return mean, mean - 1.96 * se, mean + 1.96 * se


def main() -> None:
    parser = argparse.ArgumentParser(description="Two-tutor paired comparison experiment (toy, not the final simulator).")
    parser.add_argument("--seeds", type=int, default=100, help="Number of seeds to run (seeds 0..N-1).")
    parser.add_argument("--json-out", type=str, default="reports/results/tutor_comparison.json")
    parser.add_argument("--summary-out", type=str, default="reports/results/tutor_comparison_summary.md")
    args = parser.parse_args()

    seeds = list(range(args.seeds))
    records = run_comparison(seeds)
    tutor_summary = summarize_by_tutor(records)
    diffs = paired_differences(records, TUTOR_A, TUTOR_B)

    delta_p_values = [d["delta_p_correct_post"] for d in diffs]
    delta_k_values = [d["delta_knowledge_gain"] for d in diffs]
    mean_delta_p, ci_lo_p, ci_hi_p = _mean_ci95(delta_p_values)
    mean_delta_k, ci_lo_k, ci_hi_k = _mean_ci95(delta_k_values)

    n_a_better = sum(1 for d in delta_p_values if d > 1e-9)
    n_tied = sum(1 for d in delta_p_values if abs(d) <= 1e-9)
    n_b_better = sum(1 for d in delta_p_values if d < -1e-9)

    measured_ranking = sorted(tutor_summary.keys(), key=lambda t: tutor_summary[t]["mean_p_correct_post"], reverse=True)
    ranking_recovered = measured_ranking == GROUND_TRUTH_RANKING
    diagnostics = distribution_diagnostics(records, diffs)

    print(f"\n{'=' * 70}\nTWO-TUTOR COMPARISON  (n_seeds={len(seeds)})\n{'=' * 70}")
    for tutor, s in tutor_summary.items():
        print(f"\n{tutor}:")
        for k, v in s.items():
            print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")

    print(f"\n{'-' * 70}\nPAIRED DIFFERENCES (Tutor A - Tutor B, per seed)\n{'-' * 70}")
    print(f"mean delta p_correct_post: {mean_delta_p:+.4f}  95% CI [{ci_lo_p:+.4f}, {ci_hi_p:+.4f}]")
    print(f"mean delta knowledge_gain: {mean_delta_k:+.4f}  95% CI [{ci_lo_k:+.4f}, {ci_hi_k:+.4f}]")
    print(f"seeds where A > B: {n_a_better}   seeds tied: {n_tied}   seeds where B > A: {n_b_better}")
    print("(individual seeds where B >= A are expected under a stochastic mechanism and do not")
    print(" invalidate the comparison -- the claim is about the aggregate ranking across seeds.)")

    print(f"\n{'-' * 70}\nRANKING VALIDITY\n{'-' * 70}")
    print(f"Ground-truth tutor ranking: {' > '.join(GROUND_TRUTH_RANKING)}")
    print(f"Simulator ranking:          {' > '.join(measured_ranking)}")
    print(f"Ranking recovered: {ranking_recovered}")

    dd = diagnostics["delta_p_correct_post"]
    print(f"\n{'-' * 70}\nDISTRIBUTION OF PAIRED DIFFERENCES (not just the mean)\n{'-' * 70}")
    print(f"min={dd['min']:+.4f}  p10={dd['p10']:+.4f}  p25={dd['p25']:+.4f}  median={dd['median']:+.4f}  "
          f"p75={dd['p75']:+.4f}  p90={dd['p90']:+.4f}  max={dd['max']:+.4f}")
    print(f"distinct delta values across {len(diffs)} seeds: {dd['n_distinct_values']}  "
          f"(largest single bucket = {dd['largest_bucket_fraction']:.0%} of seeds)")
    print("bucket counts:", ", ".join(f"{k}:{v}" for k, v in dd["bucket_counts"].items()))
    if diagnostics["zero_variance_metrics"]:
        print("\nZERO-VARIANCE metrics detected (identical outcome on every seed -- a sign of a")
        print("near-deterministic mechanism rather than emergent stochastic variation):")
        for m in diagnostics["zero_variance_metrics"]:
            print(f"  - {m}")
    if diagnostics["flag_highly_discretized_outcome"]:
        print("\nFLAG: the outcome distribution is highly discretized (few distinct values / one")
        print("dominant bucket). See 'Methodological concern' in the markdown summary before treating")
        print("this ranking result as strong evidence of decision validity.")

    results = {
        "experiment": "two_tutor_comparison",
        "n_seeds": len(seeds),
        "seeds": seeds,
        "ground_truth_ranking": GROUND_TRUTH_RANKING,
        "measured_ranking": measured_ranking,
        "ranking_recovered": ranking_recovered,
        "tutor_summary": tutor_summary,
        "paired_comparison": {
            "mean_delta_p_correct_post": mean_delta_p,
            "ci95_delta_p_correct_post": [ci_lo_p, ci_hi_p],
            "mean_delta_knowledge_gain": mean_delta_k,
            "ci95_delta_knowledge_gain": [ci_lo_k, ci_hi_k],
            "n_seeds_a_better": n_a_better,
            "n_seeds_tied": n_tied,
            "n_seeds_b_better": n_b_better,
        },
        "distribution_diagnostics": diagnostics,
        "records": records,
        "paired_diffs": diffs,
    }

    json_path = Path(args.json_out)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nSaved machine-readable results to {json_path}")

    summary_md = _render_markdown_summary(results)
    summary_path = Path(args.summary_out)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary_md)
    print(f"Saved human-readable summary to {summary_path}")


def _render_markdown_summary(results: dict) -> str:
    lines = []
    lines.append("# Two-Tutor Comparison — Toy Experiment Results")
    lines.append("")
    lines.append(f"n_seeds = {results['n_seeds']} (seeds 0..{results['n_seeds'] - 1})")
    lines.append("")
    lines.append("This is a toy / methodological experiment (see RESEARCH_NOTES.md), not the final simulator.")
    lines.append("")
    lines.append("## Ranking validity")
    lines.append("")
    lines.append(f"- Ground-truth tutor ranking: **{' > '.join(results['ground_truth_ranking'])}**")
    lines.append(f"- Simulator-measured ranking: **{' > '.join(results['measured_ranking'])}**")
    lines.append(f"- Ranking recovered: **{results['ranking_recovered']}**")
    lines.append("")
    lines.append("## Tutor-level summary")
    lines.append("")
    lines.append("| tutor | mean p_correct_pre | mean p_correct_aided | mean p_correct_post (primary) | stdev post | independent accuracy | mean knowledge gain | fraction learned | mean misconception reduction |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for tutor, s in results["tutor_summary"].items():
        lines.append(
            f"| {tutor} | {s['mean_p_correct_pre']:.3f} | {s['mean_p_correct_aided']:.3f} | "
            f"{s['mean_p_correct_post']:.3f} | {s['stdev_p_correct_post']:.3f} | "
            f"{s['independent_assessment_accuracy']:.3f} | {s['mean_knowledge_gain']:+.3f} | "
            f"{s['fraction_learned']:.3f} | {s['mean_misconception_reduction']:+.3f} |"
        )
    lines.append("")
    lines.append("`p_correct_post` (independent, unaided, on a new problem) is the primary tutor-quality")
    lines.append("metric. `p_correct_pre`/`p_correct_aided` are immediate performance, reported for")
    lines.append("context only -- not used to judge tutor quality.")
    lines.append("")
    lines.append("## Paired differences (Tutor A − Tutor B, same seed)")
    lines.append("")
    pc = results["paired_comparison"]
    lines.append(f"- mean delta p_correct_post: {pc['mean_delta_p_correct_post']:+.4f}  "
                  f"(95% CI [{pc['ci95_delta_p_correct_post'][0]:+.4f}, {pc['ci95_delta_p_correct_post'][1]:+.4f}])")
    lines.append(f"- mean delta knowledge gain: {pc['mean_delta_knowledge_gain']:+.4f}  "
                  f"(95% CI [{pc['ci95_delta_knowledge_gain'][0]:+.4f}, {pc['ci95_delta_knowledge_gain'][1]:+.4f}])")
    lines.append(f"- seeds where A > B: {pc['n_seeds_a_better']}, tied: {pc['n_seeds_tied']}, B > A: {pc['n_seeds_b_better']}")
    lines.append("")
    lines.append("### Check that the experiment can fail")
    lines.append("")
    lines.append("Individual seeds where B ties or beats A are expected from a stochastic mechanism and are")
    lines.append("not treated as a problem -- no resampling or special-casing is applied. The ranking claim")
    lines.append("is about the aggregate across seeds, not every trajectory. See `paired_diffs` in the JSON")
    lines.append("output for the full per-seed breakdown.")
    lines.append("")
    lines.append("## Distribution of paired differences")
    lines.append("")
    dd = results["distribution_diagnostics"]["delta_p_correct_post"]
    lines.append(f"min={dd['min']:+.4f}, p10={dd['p10']:+.4f}, p25={dd['p25']:+.4f}, median={dd['median']:+.4f}, "
                  f"p75={dd['p75']:+.4f}, p90={dd['p90']:+.4f}, max={dd['max']:+.4f}")
    lines.append("")
    lines.append(f"{dd['n_distinct_values']} distinct delta values across {results['n_seeds']} seeds "
                  f"(largest single bucket = {dd['largest_bucket_fraction']:.0%} of seeds):")
    lines.append("")
    lines.append("| delta_p_correct_post | count |")
    lines.append("|---|---|")
    for k, v in dd["bucket_counts"].items():
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("## Methodological concern: is the tutor gap artificially strong?")
    lines.append("")
    diag = results["distribution_diagnostics"]
    if diag["zero_variance_metrics"] or diag["flag_highly_discretized_outcome"]:
        lines.append("**Yes, likely, at the current parameter values.** Evidence:")
        lines.append("")
        for m in diag["zero_variance_metrics"]:
            lines.append(f"- Zero-variance metric: `{m}`.")
        if diag["flag_highly_discretized_outcome"]:
            lines.append(
                f"- The outcome distribution is highly discretized: only {dd['n_distinct_values']} distinct "
                f"`delta_p_correct_post` values across {results['n_seeds']} seeds, with "
                f"{dd['largest_bucket_fraction']:.0%} of seeds landing on a single value."
            )
        lines.append("")
        lines.append(
            "Root cause: `WeakTutor.addresses_misconception` is a hard, always-False switch, and "
            "`EffectiveTutor.addresses_misconception` is a hard, almost-always-True switch (true whenever "
            "the student is struggling on the tutoring problem, which is most seeds given the toy initial "
            "state). `student/learning.py`'s misconception-decay term is then applied deterministically "
            "whenever that switch is True, unconditional on whether the aided attempt succeeds. The result "
            "is that misconception reduction is either exactly 0 (WeakTutor, every seed) or a fixed decay "
            "amount (EffectiveTutor, whenever it intervenes) -- a near-binary toggle rather than a gradually "
            "emergent property of varied stochastic trajectories. The ranking direction (A > B) is a genuine "
            "consequence of the existing, unmodified learning mechanism -- it was not hardcoded into the "
            "evaluation code -- but the *size and near-certainty* of the gap mostly comes from how strongly "
            "the two toy tutors were defined to differ, not from rich simulated learning dynamics. This "
            "should be treated as a demonstration that the pipeline and metrics are wired correctly end to "
            "end, not as evidence that a real simulator would show this large or this consistent a gap "
            "between a genuinely strong and genuinely weak real tutor."
        )
    else:
        lines.append("No strong evidence of an artificially discretized outcome was detected at this parameter setting.")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
