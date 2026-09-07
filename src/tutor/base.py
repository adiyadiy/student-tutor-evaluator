"""
Common tutor interface (CLAUDE.md: treat tutors through a common interface so
the simulator doesn't need to know a tutor's internals).

A tutor receives the student state visible to it, the current problem, and the
response history, and produces a structured `TutorAction` -- no natural-
language generation in this toy (constraint: behavior/interventions come from
explicit, inspectable logic, not an LLM).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from src.simulation.problems import Problem, Skill
from src.student.behavior import StudentResponse
from src.student.state import StudentState


@dataclass(frozen=True)
class TutorAction:
    type: str  # "none" | "explanation" -- only these two toy action types exist
    target_skill: Optional[Skill]
    addresses_misconception: bool
    note: str


class Tutor:
    """Every concrete tutor implementation must provide `respond`."""

    def respond(self, state: StudentState, problem: Problem, history: List[StudentResponse]) -> TutorAction:
        raise NotImplementedError
