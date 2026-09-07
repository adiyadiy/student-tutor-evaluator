"""
Latent student state.

Per CLAUDE.md's modeling philosophy, knowledge, confidence, and engagement are
kept as separate variables rather than collapsed into one. `knowledge` here is
the GROUND-TRUTH generative mastery used by this toy simulator, not an
estimate: in the full pipeline, an estimator would infer K_c (and its own
uncertainty about K_c) from noisy observations of a real or simulated student.
That estimation layer is future work and is intentionally out of scope for
this vertical slice -- this toy plays the role of the "real" (simulated)
student, not the observer.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class StableTendencies:
    """Per-student traits that do not change during a session. Toy placeholders."""

    help_seeking_propensity: float = 0.5  # baseline willingness to ask for a hint when struggling
    guessing_tendency: float = 0.5  # currently unused directly (decide_guess uses a fixed probability); kept for future refinement
    response_speed_factor: float = 1.0  # multiplier on response-time distribution (1.0 = average speed)


@dataclass(frozen=True)
class StudentState:
    knowledge: Dict[object, float]
    misconceptions: Dict[str, float]
    confidence: float
    engagement: float
    stable_tendencies: StableTendencies = field(default_factory=StableTendencies)

    def knowledge_of(self, skill) -> float:
        return self.knowledge.get(skill, 0.0)

    def misconception_strength(self, name: str) -> float:
        return self.misconceptions.get(name, 0.0)
