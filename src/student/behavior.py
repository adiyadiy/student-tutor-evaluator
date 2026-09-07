"""
Probabilistic student response-generation pipeline.

Behavior is decomposed into small, composable probabilistic decisions rather
than one categorical rule or a large if/else cascade (attempt? guess? correct?
hint? give up? how long?), per CLAUDE.md's guidance to decompose behavior into
separate probabilistic decisions such as P(request_hint | ...), P(correct | ...).

`compute_p_correct` is the ONLY function that determines correctness, and it
depends on knowledge, problem difficulty, and misconceptions -- never on
confidence. Confidence instead influences whether the student attempts at all
and whether they seek help, which is a behavioral effect, not a mathematical
one. This split is a deliberate modeling constraint, not an oversight.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.simulation.problems import MISCONCEPTION_RELEVANT_SKILL, Problem
from src.student.params import ToyBehaviorParams
from src.student.state import StudentState


@dataclass(frozen=True)
class StudentResponse:
    problem_id: str
    attempted: bool
    is_guess: bool
    correct: Optional[bool]  # None if the student did not attempt
    requested_hint: bool
    gave_up: bool
    response_time: Optional[float]  # None if the student did not attempt
    p_correct: float  # underlying probability used to sample correctness -- printed for transparency, not just the sampled outcome
    p_correct_components: Dict[str, float]
    p_hint_request: float
    p_give_up: float
    misconception_active: Optional[str]


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def compute_p_correct(
    state: StudentState,
    problem: Problem,
    tutor_action: Optional[Any],
    params: ToyBehaviorParams,
) -> tuple[float, Dict[str, float], Optional[str]]:
    knowledge_term = params.knowledge_gap_scale * (state.knowledge_of(problem.skill) - problem.difficulty)

    misconception_term = 0.0
    active_misconception = None
    for name, strength in state.misconceptions.items():
        if strength > 0 and MISCONCEPTION_RELEVANT_SKILL.get(name) == problem.skill:
            misconception_term -= params.misconception_penalty * strength
            active_misconception = name

    hint_term = 0.0
    if tutor_action is not None and getattr(tutor_action, "type", None) == "explanation" and getattr(tutor_action, "target_skill", None) == problem.skill:
        hint_term = params.hint_bonus

    logit = knowledge_term + misconception_term + hint_term
    p_correct = _sigmoid(logit)
    components = {
        "knowledge_term": knowledge_term,
        "misconception_term": misconception_term,
        "hint_term": hint_term,
        "logit": logit,
    }
    return p_correct, components, active_misconception


def decide_attempt(state: StudentState, params: ToyBehaviorParams, rng) -> tuple[bool, float]:
    logit = (
        params.attempt_base_logit
        + params.attempt_confidence_weight * (state.confidence - 0.5)
        + params.attempt_engagement_weight * (state.engagement - 0.5)
    )
    p_attempt = _sigmoid(logit)
    return rng.random() < p_attempt, p_attempt


def decide_guess(state: StudentState, problem: Problem, params: ToyBehaviorParams, rng) -> bool:
    if state.knowledge_of(problem.skill) >= params.guess_knowledge_threshold:
        return False
    return rng.random() < params.guess_probability


def decide_help_seeking(state: StudentState, params: ToyBehaviorParams, rng) -> tuple[bool, bool, float, float]:
    hint_logit = (
        params.hint_request_base_logit
        + params.hint_request_confidence_weight * (state.confidence - 0.5)
        + params.hint_request_tendency_weight * (state.stable_tendencies.help_seeking_propensity - 0.5)
    )
    p_hint = _sigmoid(hint_logit)

    give_up_logit = params.give_up_base_logit + params.give_up_engagement_weight * (state.engagement - 0.5)
    p_give_up = _sigmoid(give_up_logit)

    requested_hint = rng.random() < p_hint
    gave_up = (not requested_hint) and (rng.random() < p_give_up)
    return requested_hint, gave_up, p_hint, p_give_up


def sample_response_time(state: StudentState, problem: Problem, params: ToyBehaviorParams, rng) -> float:
    mu_seconds = params.response_time_base_seconds + params.response_time_difficulty_weight * problem.difficulty
    mu_seconds /= max(state.stable_tendencies.response_speed_factor, 0.1)
    mu_seconds *= 1.0 + 0.3 * (1.0 - state.engagement)  # toy direction: lower engagement -> somewhat slower/more distracted
    mu_log = math.log(max(mu_seconds, 1.0))
    return math.exp(rng.gauss(mu_log, params.response_time_speed_log_std))


def generate_response(
    state: StudentState,
    problem: Problem,
    params: ToyBehaviorParams,
    rng,
    tutor_action: Optional[Any] = None,
) -> StudentResponse:
    p_correct, components, active_misconception = compute_p_correct(state, problem, tutor_action, params)
    attempted, _p_attempt = decide_attempt(state, params, rng)

    if not attempted:
        return StudentResponse(
            problem_id=problem.id,
            attempted=False,
            is_guess=False,
            correct=None,
            requested_hint=False,
            gave_up=False,
            response_time=None,
            p_correct=p_correct,
            p_correct_components=components,
            p_hint_request=0.0,
            p_give_up=0.0,
            misconception_active=active_misconception,
        )

    is_guess = decide_guess(state, problem, params, rng)
    correct = (rng.random() < params.guess_correct_rate) if is_guess else (rng.random() < p_correct)

    requested_hint, gave_up, p_hint, p_give_up = False, False, 0.0, 0.0
    if not correct:
        requested_hint, gave_up, p_hint, p_give_up = decide_help_seeking(state, params, rng)

    response_time = sample_response_time(state, problem, params, rng)

    return StudentResponse(
        problem_id=problem.id,
        attempted=True,
        is_guess=is_guess,
        correct=correct,
        requested_hint=requested_hint,
        gave_up=gave_up,
        response_time=response_time,
        p_correct=p_correct,
        p_correct_components=components,
        p_hint_request=p_hint,
        p_give_up=p_give_up,
        misconception_active=active_misconception,
    )
