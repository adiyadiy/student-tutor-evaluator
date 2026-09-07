"""
TOY / PLACEHOLDER parameters for the vertical-slice prototype.

Every constant in this module is a hand-picked, illustrative value chosen once,
before ever running the scenario, to make the behavioral and learning
mechanisms exercise-able end-to-end. None of these values are calibrated
against real data, and none of them were adjusted after the fact to make any
particular run's outcome look better.

Once FoundationalASSIST is audited, this module should be replaced (or its
values re-estimated) using real student interaction data -- e.g. item-response
fitting for problem difficulty, logistic regression for the p_correct
coefficients, and observed pre/post performance for the learning-update
coefficients.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ToyBehaviorParams:
    # --- compute_p_correct: logit = a*(K - difficulty) - misconception_penalty*strength + hint_bonus ---
    knowledge_gap_scale: float = 4.0
    misconception_penalty: float = 1.5
    hint_bonus: float = 1.0  # added only on the attempt immediately following a tutor explanation targeting this skill

    # --- decide_attempt ---
    attempt_base_logit: float = 2.5  # baseline strongly favors attempting
    attempt_confidence_weight: float = 1.0
    attempt_engagement_weight: float = 2.0

    # --- decide_guess (only considered when knowledge is low) ---
    guess_knowledge_threshold: float = 0.25
    guess_probability: float = 0.3  # P(guessing | knowledge below threshold and attempting)
    guess_correct_rate: float = 0.05  # free-response format: a guess is rarely correct (not multiple-choice chance level)

    # --- decide_help_seeking (only reached after an incorrect attempt) ---
    hint_request_base_logit: float = -0.5
    hint_request_confidence_weight: float = -2.0  # lower confidence -> more likely to ask for a hint
    hint_request_tendency_weight: float = 2.0  # stable_tendencies.help_seeking_propensity

    give_up_base_logit: float = -2.0
    give_up_engagement_weight: float = -3.0  # lower engagement -> more likely to give up

    # --- sample_response_time (lognormal) ---
    response_time_base_seconds: float = 20.0
    response_time_difficulty_weight: float = 25.0
    response_time_speed_log_std: float = 0.4


@dataclass(frozen=True)
class ToyLearningParams:
    # --- knowledge update: new_K = K + learning_rate * (target - K) ---
    learning_rate_unaided: float = 0.15
    learning_rate_aided: float = 0.25
    teaching_effectiveness_bonus: float = 0.15  # extra learning_rate when the tutor's explanation addressed the relevant misconception AND the student then answered correctly

    target_correct_unaided: float = 0.9
    target_correct_aided: float = 0.75
    target_correct_guess: float = 0.4  # a correct GUESS is weak evidence of mastery -- much lower target than a genuine correct answer
    target_incorrect: float = 0.35  # an incorrect answer still pulls knowledge toward a low-but-not-zero target rather than being punished harshly

    # --- misconception update: multiplicative decay toward 0 ---
    misconception_decay_addressed: float = 0.5  # decay when the tutor's explanation addressed this misconception
    misconception_decay_correct_followup: float = 0.3  # additional decay if the student then answers correctly

    # --- confidence update: same moving-target mechanism as knowledge ---
    confidence_learning_rate: float = 0.2
    confidence_target_correct_unaided: float = 0.85
    confidence_target_correct_aided: float = 0.6
    confidence_target_incorrect: float = 0.25

    # --- engagement update: small additive nudges, clipped to [0, 1] ---
    engagement_decay_on_struggle: float = 0.05  # incorrect AND no tutor help this turn
    engagement_recovery_on_support: float = 0.05  # tutor gave an explanation this turn
    engagement_recovery_on_success: float = 0.05  # attempted and correct this turn
