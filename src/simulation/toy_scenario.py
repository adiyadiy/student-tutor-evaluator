"""
Toy end-to-end vertical slice of the student-tutor pipeline.

initial state -> pre-tutoring attempt -> tutor turn -> aided attempt ->
state update -> independent assessment -> before/after comparison.

This is a throwaway demonstration that the architecture (state -> probabilistic
behavior -> tutor -> interpretable learning update -> new behavior) runs
end-to-end. It is NOT the simulator and is not meant to look scientifically
validated: every numeric parameter lives in student/params.py, labeled as a
toy placeholder to be replaced once real data is audited.

Outcomes are stochastic and NOT tuned or special-cased to guarantee that the
post-tutoring assessment improves -- see student/learning.py and the run's
per-seed printout, which is expected to show a mix of improved / flat / worse
outcomes across seeds.

Run: python -m src.simulation.toy_scenario [--seeds 0 1 2 3 4] [--save PATH]
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional

from src.simulation.problems import MISCONCEPTION_SIGN_ERROR, Skill, find_problem
from src.student.behavior import StudentResponse, generate_response
from src.student.learning import update_state
from src.student.params import ToyBehaviorParams, ToyLearningParams
from src.student.state import StableTendencies, StudentState
from src.tutor.base import Tutor
from src.tutor.simple_tutor import SimpleTutor


def initial_state() -> StudentState:
    """
    TOY / PLACEHOLDER initial state: a student who has largely mastered
    one-step equations, is shaky on two-step equations (knowledge kept below
    decide_guess's threshold so the guess mechanism is reachable in this
    demo), and carries the toy sign-error misconception.
    """
    return StudentState(
        knowledge={
            Skill.S1_ONE_STEP_ADD_SUB: 0.85,
            Skill.S2_ONE_STEP_MUL_DIV: 0.75,
            Skill.S3_TWO_STEP_LINEAR: 0.22,
        },
        misconceptions={MISCONCEPTION_SIGN_ERROR: 0.6},
        confidence=0.55,
        engagement=0.7,
        stable_tendencies=StableTendencies(
            help_seeking_propensity=0.5,
            guessing_tendency=0.4,
            response_speed_factor=1.0,
        ),
    )


def _state_to_dict(state: StudentState) -> dict:
    return {
        "knowledge": {s.value: v for s, v in state.knowledge.items()},
        "misconceptions": dict(state.misconceptions),
        "confidence": state.confidence,
        "engagement": state.engagement,
    }


def _fmt_state(state: StudentState) -> str:
    k = ", ".join(f"{s.value}={v:.2f}" for s, v in state.knowledge.items())
    m = ", ".join(f"{n}={v:.2f}" for n, v in state.misconceptions.items()) or "none"
    return f"knowledge: {k}\n    misconceptions: {m}\n    confidence={state.confidence:.2f}  engagement={state.engagement:.2f}"


def _fmt_response(label: str, resp: StudentResponse) -> str:
    c = resp.p_correct_components
    lines = [
        f"  [{label}] problem={resp.problem_id}  p_correct={resp.p_correct:.3f}  "
        f"(knowledge_term={c['knowledge_term']:+.2f}, misconception_term={c['misconception_term']:+.2f}, hint_term={c['hint_term']:+.2f})"
    ]
    if not resp.attempted:
        lines.append("    did not attempt (said 'I don't know')")
    else:
        outcome = "correct" if resp.correct else "incorrect"
        guess_note = " [guess]" if resp.is_guess else ""
        lines.append(f"    attempted -> {outcome}{guess_note}  response_time={resp.response_time:.1f}s")
        if not resp.correct:
            lines.append(f"    requested_hint={resp.requested_hint} (p={resp.p_hint_request:.2f})  gave_up={resp.gave_up} (p={resp.p_give_up:.2f})")
    return "\n".join(lines)


def run_episode(seed: int, verbose: bool = True, tutor: Optional[Tutor] = None) -> dict:
    """
    `tutor` defaults to SimpleTutor (this module's original single-tutor demo
    behavior, unchanged). The tutor-comparison experiment
    (src/evaluation/tutor_comparison.py) passes in EffectiveTutor/WeakTutor
    instead, reusing this exact function so both experiments run through
    identical student-model code.
    """
    rng = random.Random(seed)
    behavior_params = ToyBehaviorParams()
    learning_params = ToyLearningParams()
    if tutor is None:
        tutor = SimpleTutor()

    state = initial_state()
    trace: dict = {"seed": seed}

    if verbose:
        print(f"\n{'=' * 70}\nSEED {seed}\n{'=' * 70}")
        print("Initial state:")
        print("  " + _fmt_state(state))

    # Warm-up: mastered skill, no tutor -- sanity-checks the model behaves
    # sensibly (confident, likely-correct) as a contrast to the weak skill below.
    warm_problem = find_problem("P1")
    warm_response = generate_response(state, warm_problem, behavior_params, rng, tutor_action=None)
    if verbose:
        print("\nWarm-up attempt (mastered skill, contrast case):")
        print(_fmt_response("warm-up", warm_response))
    trace["warmup"] = asdict(warm_response)

    # Pre-tutoring attempt on the target (weak) skill.
    pre_problem = find_problem("P4")
    pre_response = generate_response(state, pre_problem, behavior_params, rng, tutor_action=None)
    if verbose:
        print(f"\nPre-tutoring attempt on {pre_problem.id} ({pre_problem.skill.value}, difficulty={pre_problem.difficulty}):")
        print(_fmt_response("pre", pre_response))
    trace["pre_tutoring"] = asdict(pre_response)

    # Tutor turn: reacts only to the pre-tutoring response, has no knowledge of any future step.
    history: List[StudentResponse] = [pre_response]
    tutor_action = tutor.respond(state, pre_problem, history)
    if verbose:
        print(
            f"\nTutor turn: type={tutor_action.type}  "
            f"target_skill={getattr(tutor_action.target_skill, 'value', None)}  "
            f"addresses_misconception={tutor_action.addresses_misconception}\n  note: {tutor_action.note}"
        )
    trace["tutor_action"] = {
        "type": tutor_action.type,
        "target_skill": tutor_action.target_skill.value if tutor_action.target_skill else None,
        "addresses_misconception": tutor_action.addresses_misconception,
        "note": tutor_action.note,
    }

    # Second attempt on the same problem, now with tutor support.
    aided_response = generate_response(state, pre_problem, behavior_params, rng, tutor_action=tutor_action)
    if verbose:
        print("\nStudent attempt after tutoring (same problem):")
        print(_fmt_response("aided", aided_response))
    trace["aided_attempt"] = asdict(aided_response)

    # State update from the tutored interaction.
    state_before_update = state
    state = update_state(state, pre_problem, aided_response, tutor_action, learning_params)
    if verbose:
        print("\nState update (interpretable learning mechanism):")
        print(f"  before: {_fmt_state(state_before_update)}")
        print(f"  after:  {_fmt_state(state)}")
    trace["state_before"] = _state_to_dict(state_before_update)
    trace["state_after"] = _state_to_dict(state)

    # Independent assessment: a NEW problem, same skill, no tutor help, using the updated state.
    post_problem = find_problem("P5")
    post_response = generate_response(state, post_problem, behavior_params, rng, tutor_action=None)
    if verbose:
        print(f"\nIndependent assessment on {post_problem.id} ({post_problem.skill.value}, difficulty={post_problem.difficulty}), unaided:")
        print(_fmt_response("post", post_response))
    trace["post_assessment"] = asdict(post_response)

    target_skill = pre_problem.skill
    knowledge_before = state_before_update.knowledge_of(target_skill)
    knowledge_after = state.knowledge_of(target_skill)
    misconception_before = state_before_update.misconception_strength(MISCONCEPTION_SIGN_ERROR)
    misconception_after = state.misconception_strength(MISCONCEPTION_SIGN_ERROR)

    summary = {
        "seed": seed,
        "tutor": type(tutor).__name__,
        # immediate / aided performance -- NOT the primary tutor-quality signal, kept for comparison
        "p_correct_pre": pre_response.p_correct,
        "correct_pre": pre_response.correct,
        "p_correct_aided": aided_response.p_correct,
        "correct_aided": aided_response.correct,
        # independent post-tutoring performance -- the primary tutor-quality signal
        "p_correct_post": post_response.p_correct,
        "correct_post": post_response.correct,
        "delta_p_correct": post_response.p_correct - pre_response.p_correct,
        # latent state change (from student/learning.py, not touched by this experiment)
        "knowledge_before": knowledge_before,
        "knowledge_after": knowledge_after,
        "knowledge_delta": knowledge_after - knowledge_before,
        "misconception_before": misconception_before,
        "misconception_after": misconception_after,
        "misconception_delta": misconception_after - misconception_before,
        "confidence_before": state_before_update.confidence,
        "confidence_after": state.confidence,
        "engagement_before": state_before_update.engagement,
        "engagement_after": state.engagement,
        "learned": knowledge_after > knowledge_before,
        "tutor_addressed_misconception": bool(tutor_action.addresses_misconception),
    }
    trace["summary"] = summary

    if verbose:
        print("\nSummary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")

    return trace


def main() -> None:
    parser = argparse.ArgumentParser(description="Toy end-to-end vertical slice of the student-tutor pipeline.")
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[0, 1, 2, 3, 4],
        help="Seeds to run. Outcomes are expected to vary across seeds, not improve deterministically.",
    )
    parser.add_argument("--save", type=str, default=None, help="Optional path to dump the full JSON trace of all runs.")
    args = parser.parse_args()

    traces = [run_episode(seed) for seed in args.seeds]

    print(f"\n{'=' * 70}\nOUTCOME DISTRIBUTION ACROSS SEEDS\n{'=' * 70}")
    print(f"{'seed':>5} {'p_pre':>8} {'p_post':>8} {'delta':>8} {'correct_pre':>12} {'correct_post':>13}")
    for t in traces:
        s = t["summary"]
        print(
            f"{s['seed']:>5} {s['p_correct_pre']:>8.3f} {s['p_correct_post']:>8.3f} {s['delta_p_correct']:>+8.3f} "
            f"{str(s['correct_pre']):>12} {str(s['correct_post']):>13}"
        )

    deltas = [t["summary"]["delta_p_correct"] for t in traces]
    n_improved = sum(1 for d in deltas if d > 1e-9)
    n_flat = sum(1 for d in deltas if abs(d) <= 1e-9)
    n_worse = sum(1 for d in deltas if d < -1e-9)
    print(f"\np_correct change across seeds: improved={n_improved} flat={n_flat} worse={n_worse}")
    print("(p_correct_pre is a deterministic function of the fixed initial state, so it is identical")
    print(" across seeds; p_correct_post varies only because the STATE UPDATE depends on the stochastic")
    print(" responses sampled earlier in the episode -- e.g. whether the pre-test attempt was a guess,")
    print(" whether the aided attempt succeeded. This is expected: the mechanism is probabilistic and")
    print(" is not forced to improve.)")

    if args.save:
        out_path = Path(args.save)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(traces, indent=2, default=str))
        print(f"\nSaved full trace to {out_path}")


if __name__ == "__main__":
    main()
