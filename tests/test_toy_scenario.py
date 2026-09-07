"""
Minimal smoke test for the toy vertical slice. Cheap regression guard, not a
claim of correctness: checks bounds and that outcomes are stochastic rather
than a fixed deterministic rule.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.simulation.toy_scenario import run_episode  # noqa: E402


def test_run_episode_does_not_crash():
    trace = run_episode(seed=0, verbose=False)
    assert "summary" in trace


def test_state_and_probabilities_stay_in_bounds():
    for seed in range(5):
        trace = run_episode(seed=seed, verbose=False)
        for key in ("state_before", "state_after"):
            state = trace[key]
            for v in state["knowledge"].values():
                assert 0.0 <= v <= 1.0
            for v in state["misconceptions"].values():
                assert 0.0 <= v <= 1.0
            assert 0.0 <= state["confidence"] <= 1.0
            assert 0.0 <= state["engagement"] <= 1.0
        for resp_key in ("warmup", "pre_tutoring", "aided_attempt", "post_assessment"):
            resp = trace[resp_key]
            assert 0.0 <= resp["p_correct"] <= 1.0


def test_outcomes_vary_across_seeds():
    deltas = [run_episode(seed=seed, verbose=False)["summary"]["delta_p_correct"] for seed in range(8)]
    # The mechanism is stochastic, not a fixed "always improves by X" rule --
    # different seeds should not all land on the identical delta.
    assert len(set(round(d, 6) for d in deltas)) > 1
