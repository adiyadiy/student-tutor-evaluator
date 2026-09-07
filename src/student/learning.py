"""
Interpretable state-transition function.

new_K_c = K_c + learning_rate * (target - K_c)

`learning_rate` and `target` depend only on THIS turn's interaction (was there
an attempt, was it correct, was it a guess, did the tutor help and did that
help address the relevant misconception) -- never on any later problem or
evaluation step. This function has no way to know whether an independent
assessment is coming next, so it cannot be (and is not) special-cased to make
that later assessment look better.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Optional

from src.simulation.problems import MISCONCEPTION_RELEVANT_SKILL, Problem
from src.student.behavior import StudentResponse
from src.student.params import ToyLearningParams
from src.student.state import StudentState


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def update_state(
    state: StudentState,
    problem: Problem,
    response: StudentResponse,
    tutor_action: Optional[Any],
    params: ToyLearningParams,
) -> StudentState:
    skill = problem.skill
    k = state.knowledge_of(skill)

    tutor_helped = tutor_action is not None and getattr(tutor_action, "type", None) == "explanation"
    addresses_misconception = tutor_helped and bool(getattr(tutor_action, "addresses_misconception", False))

    new_knowledge = dict(state.knowledge)
    new_confidence = state.confidence
    learning_rate = params.learning_rate_aided if tutor_helped else params.learning_rate_unaided

    if response.attempted:
        if response.correct and response.is_guess:
            # a lucky guess is weak evidence of mastery -- pull toward a low target, not a mastery target
            target = params.target_correct_guess
            confidence_target = params.confidence_target_correct_unaided
        elif response.correct:
            target = params.target_correct_aided if tutor_helped else params.target_correct_unaided
            confidence_target = params.confidence_target_correct_aided if tutor_helped else params.confidence_target_correct_unaided
            if addresses_misconception:
                learning_rate += params.teaching_effectiveness_bonus
        else:
            target = params.target_incorrect
            confidence_target = params.confidence_target_incorrect

        new_knowledge[skill] = _clip01(k + learning_rate * (target - k))
        new_confidence = _clip01(state.confidence + params.confidence_learning_rate * (confidence_target - state.confidence))

    new_misconceptions = dict(state.misconceptions)
    if addresses_misconception:
        decay = params.misconception_decay_addressed
        if response.attempted and response.correct:
            decay += params.misconception_decay_correct_followup
        decay = min(decay, 1.0)
        for name, strength in list(new_misconceptions.items()):
            if strength > 0 and MISCONCEPTION_RELEVANT_SKILL.get(name) == skill:
                new_misconceptions[name] = _clip01(strength * (1.0 - decay))

    engagement = state.engagement
    if response.attempted and not response.correct and not tutor_helped:
        engagement -= params.engagement_decay_on_struggle
    if tutor_helped:
        engagement += params.engagement_recovery_on_support
    if response.attempted and response.correct:
        engagement += params.engagement_recovery_on_success
    new_engagement = _clip01(engagement)

    return replace(
        state,
        knowledge=new_knowledge,
        misconceptions=new_misconceptions,
        confidence=new_confidence,
        engagement=new_engagement,
    )
