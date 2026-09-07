"""
A single simple, rule-based tutor (per scope: one tutor for this vertical
slice, not a suite of tutoring strategies).
"""

from __future__ import annotations

from typing import List, Optional

from src.simulation.problems import MISCONCEPTION_RELEVANT_SKILL, Problem
from src.student.behavior import StudentResponse
from src.student.state import StudentState
from src.tutor.base import Tutor, TutorAction


class SimpleTutor(Tutor):
    """
    Rule: if the student's most recent response was incorrect, requested a
    hint, gave up, or didn't attempt, respond with an explanation targeting
    that problem's skill, addressing the relevant misconception if the tutor
    is aware the student holds one.

    Toy simplification: this tutor is given oracle access to the student's
    latent misconception via `state`, rather than inferring it purely from
    observed incorrect answers (e.g. error-type classification of the wrong
    answer). CLAUDE.md's observation/latent-state distinction says a real
    tutor should only see behavior, not ground truth -- error-pattern
    inference is deferred to future work; this toy keeps the tutor minimal.
    """

    def respond(self, state: StudentState, problem: Problem, history: List[StudentResponse]) -> TutorAction:
        if not history:
            return TutorAction(type="none", target_skill=None, addresses_misconception=False, note="no interaction yet")

        last = history[-1]
        struggling = (not last.attempted) or (last.correct is False) or last.requested_hint or last.gave_up
        if not struggling:
            return TutorAction(
                type="none", target_skill=None, addresses_misconception=False, note="student succeeded unaided; no intervention needed"
            )

        relevant_misconception: Optional[str] = next(
            (
                name
                for name, skill in MISCONCEPTION_RELEVANT_SKILL.items()
                if skill == problem.skill and state.misconception_strength(name) > 0
            ),
            None,
        )
        addresses_misconception = relevant_misconception is not None
        note = f"explains {problem.skill.value}" + (f", addressing '{relevant_misconception}'" if addresses_misconception else "")

        return TutorAction(
            type="explanation",
            target_skill=problem.skill,
            addresses_misconception=addresses_misconception,
            note=note,
        )
