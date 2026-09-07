"""
Tutor A ("effective tutor") for the two-tutor comparison experiment.

Pure subclass of SimpleTutor with NO overridden behavior -- no new logic.
SimpleTutor already matches the "effective tutor" spec: reacts to struggle,
gives a targeted explanation, and addresses the relevant misconception when
the (oracle-accessed -- see RESEARCH_NOTES.md) latent state shows the student
holds one.

Subclassing (rather than running SimpleTutor directly) exists ONLY so that
`type(tutor).__name__` records "EffectiveTutor" in experiment results,
giving the two tutors compared here parallel, self-explanatory labels. It
changes no behavior.
"""

from src.tutor.simple_tutor import SimpleTutor


class EffectiveTutor(SimpleTutor):
    pass
