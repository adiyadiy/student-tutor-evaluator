"""
TOY / PLACEHOLDER domain content: skills, misconception, and a fixed problem
bank for basic linear equations.

This is a flat, hand-picked set of 3 skills and 1 misconception chosen only to
exercise the pipeline end-to-end. It is not a claim about how linear-equation
skills or misconceptions should actually be decomposed. The real skill/concept
taxonomy will be derived from FoundationalASSIST's own labels once the data is
available (per CLAUDE.md: do not build a large hand-designed ontology).
"""

from dataclasses import dataclass
from enum import Enum


class Skill(str, Enum):
    S1_ONE_STEP_ADD_SUB = "S1_one_step_add_sub"  # e.g. x + a = b
    S2_ONE_STEP_MUL_DIV = "S2_one_step_mul_div"  # e.g. a*x = b
    S3_TWO_STEP_LINEAR = "S3_two_step_linear"  # e.g. a*x + b = c


@dataclass(frozen=True)
class Problem:
    id: str
    prompt: str
    skill: Skill
    difficulty: float  # hand-set toy value in [0, 1]; real difficulty would be calibrated (e.g. via IRT) from response data
    answer: str


PROBLEM_BANK = [
    Problem("P1", "x + 4 = 9", Skill.S1_ONE_STEP_ADD_SUB, 0.15, "5"),
    Problem("P2", "x - 3 = 5", Skill.S1_ONE_STEP_ADD_SUB, 0.20, "8"),
    Problem("P3", "4x = 12", Skill.S2_ONE_STEP_MUL_DIV, 0.25, "3"),
    Problem("P4", "3x + 2 = 11", Skill.S3_TWO_STEP_LINEAR, 0.50, "3"),
    Problem("P5", "2x - 5 = 9", Skill.S3_TWO_STEP_LINEAR, 0.55, "7"),
]

# Only one toy misconception is modeled, per CLAUDE.md: don't invent a taxonomy
# without evidence. If a recurring error pattern shows up in real data later,
# it gets its own entry here rather than being forced into this one.
MISCONCEPTION_SIGN_ERROR = "sign_error_moving_terms"

# Maps each toy misconception to the skill it's relevant for. Behavior/tutor
# code looks this up generically instead of hardcoding "if skill == S3 and
# name == ...", so adding a second misconception later doesn't require new
# branches in behavior.py or tutor code.
MISCONCEPTION_RELEVANT_SKILL = {
    MISCONCEPTION_SIGN_ERROR: Skill.S3_TWO_STEP_LINEAR,
}


def find_problem(problem_id: str) -> Problem:
    return next(p for p in PROBLEM_BANK if p.id == problem_id)
