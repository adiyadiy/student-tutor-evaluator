"""
Tutor B ("weaker tutor") for the two-tutor comparison experiment.

Reacts to exactly the same struggle signal as EffectiveTutor (incorrect /
hint-requested / gave-up / no-attempt) and still gives *some* explanation
targeting the right skill -- a plausible tutor, not an absurdly broken one.
The difference from EffectiveTutor is narrow and deliberate: this tutor never
addresses the student's specific misconception, even when one is present. It
represents a generic "here's how to solve this kind of problem" explanation
rather than diagnosing and correcting the student's specific error pattern.

Consequences of that one difference (nothing else changed):
  - `compute_p_correct`'s hint_bonus is IDENTICAL for both tutors on the aided
    attempt (both provide *an* explanation on the same problem), so the
    immediate/aided performance cannot be what distinguishes them.
  - The difference shows up only through student/learning.py's existing
    mechanism -- no teaching_effectiveness_bonus to the learning rate, and no
    misconception decay -- both of which already existed in learning.py
    before this experiment and were NOT modified for it.

This tutor never reads the student's latent misconception state at all: it is
"weaker" by omission, not by having (and ignoring) more oracle information
than EffectiveTutor. No new oracle access is introduced by this class.
"""

from __future__ import annotations

from typing import List

from src.simulation.problems import Problem
from src.student.behavior import StudentResponse
from src.student.state import StudentState
from src.tutor.base import Tutor, TutorAction


class WeakTutor(Tutor):
    def respond(self, state: StudentState, problem: Problem, history: List[StudentResponse]) -> TutorAction:
        if not history:
            return TutorAction(type="none", target_skill=None, addresses_misconception=False, note="no interaction yet")

        last = history[-1]
        struggling = (not last.attempted) or (last.correct is False) or last.requested_hint or last.gave_up
        if not struggling:
            return TutorAction(
                type="none", target_skill=None, addresses_misconception=False, note="student succeeded unaided; no intervention needed"
            )

        return TutorAction(
            type="explanation",
            target_skill=problem.skill,
            addresses_misconception=False,
            note=f"gives a general explanation of {problem.skill.value} (does not target a specific misconception)",
        )
