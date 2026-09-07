# Student Tutor Evaluation — Research Prototype

## Project goal

This project is a research prototype for evaluating AI math tutors using simulated students.

The primary objective is NOT to build the most sophisticated student simulator.
The objective is to investigate whether simulated students can support a meaningful,
repeatable, and reliable comparison between different AI math tutors.

The take-home exercise evaluates:
- modeling depth and rigor
- experimental design
- evaluation methodology
- simulator validation
- understanding of assumptions and limitations
- quality of reasoning
- ability to produce a lightweight working prototype

Software engineering sophistication is secondary.

The project should remain lightweight enough to complete as a research prototype
within approximately 2–3 days.

---

# Core research question

Can we construct simulated students whose behavior and learning dynamics are
realistic enough to distinguish between different AI math tutors in a controlled,
repeatable experiment?

A strong simulator should satisfy two requirements:

1. Behavioral validity:
   simulated students should reproduce important behavioral and learning patterns
   observed in real students.

2. Decision validity:
   when exposed to different tutors, the simulator should produce tutor rankings
   that are reasonably consistent with rankings observed with real students.

Decision validity is ultimately more important than superficial conversational
similarity.

---

# High-level architecture

The intended pipeline is:

REAL STUDENT DATA
        ↓
Student state estimation
        ↓
Behavioral models learned from data
        ↓
Simulated student
        ↓
        ┌───────────────┬───────────────┬───────────────┐
        ↓               ↓               ↓
     Tutor A         Tutor B         Tutor C
        ↓               ↓               ↓
        └───────────────┴───────────────┘
                        ↓
               Learning evaluation
                        ↓
             Tutor comparison/ranking
                        ↓
              Simulator validation

The same initial simulated students, tasks, and random seeds should be used
across tutors whenever possible so that tutor comparisons are paired and
counterfactual.

---

# Student representation

A student is represented by a latent state that evolves over time.

Conceptually:

StudentState(t) = {
    knowledge,
    misconceptions,
    confidence,
    engagement,
    stable learner tendencies
}

Knowledge should initially be represented at the level of a small number of
concepts/skills within the selected math domain.

Do NOT create an enormous ontology manually.

Use the dataset's existing skill/concept structure where possible and keep an
"other/unknown" category for concepts that are not yet represented.

The ontology should be extensible: if a recurring "other" category becomes large
enough, it may later be promoted into the explicit ontology.

---

# Important distinction: knowledge vs confidence vs uncertainty

Do NOT represent knowledge and confidence as the same variable.

For example:

- A student can have low knowledge but high confidence.
- A student can have high knowledge but low confidence.
- Our estimate of the student's knowledge can itself have uncertainty.

Conceptually:

K_c = estimated mastery of concept c
uncertainty(K_c) = how confident WE are in that estimate

Confidence is a property of the simulated student.

Uncertainty is a property of our model.

These should remain separate.

Initially, confidence may be modeled as a general student-level variable.
A more granular topic-specific confidence model can be added later if justified
by the data.

---

# Student observations

The student's latent state is not directly observed.

We observe events such as:

- correctness
- answer content
- response time
- hints requested
- answer revealed / saw answer
- attempts
- question characteristics
- skill/concept
- question difficulty
- interaction history
- teacher action
- persistence / abandonment where observable

These observations provide evidence about the latent state.

Do NOT equate:

correct answer = knowledge

Correctness may result from:
- actual knowledge
- guessing
- question format
- partial understanding
- prior hints
- other factors

Question format should therefore be considered when modeling correctness.

---

# Student response model

Student behavior should be modeled as probabilistic rather than deterministic.

At a high level:

StudentState(t)
        +
Task(t)
        +
TeacherAction(t)
        ↓
Behavioral model
        ↓
Student response
        ↓
State transition

Possible behaviors include:

- attempt the problem
- answer correctly
- answer incorrectly
- produce a partial answer
- ask for a hint
- ask for an explanation
- ask for clarification
- ask for additional help
- answer incorrectly after a hint
- answer correctly after a hint
- say "I don't know"
- produce "???" / confusion
- give up / disengage
- guess

As appropriate, behavior can be decomposed into separate probabilistic decisions
rather than one categorical variable.

For example:

P(request_hint | state, task, teacher_action)

P(correct | state, task, teacher_action)

P(error_type | incorrect, state, task)

P(response_time | state, task, teacher_action)

---

# Response time

Response time is an important observation and may provide evidence about learning
and fluency.

However, response time should NOT be treated as a direct measurement of knowledge.

It may depend on:

- knowledge
- task difficulty
- student-specific speed
- engagement
- confidence
- task format
- teacher intervention

The simulator should preserve realistic variability.

---

# Misconceptions

Misconceptions are an explicit component of the student state.

A student may have multiple misconceptions simultaneously.

Misconceptions should initially be represented only where the data provides
reasonable evidence.

Do not invent a large taxonomy of misconceptions without evidence.

If a previously unseen recurring error pattern appears, the system should be able
to represent it as an "unknown/new misconception" rather than forcing it into an
existing category.

LLMs may be used as a labeling/annotation aid for open-ended student answers,
but such labels should be treated as noisy observations and validated on a
human-annotated subset where feasible.

---

# Learning dynamics

Tutoring changes the student's state over time.

Conceptually:

State(t+1) =
    Transition(
        State(t),
        TeacherAction(t),
        StudentResponse(t),
        Task(t)
    )

Learning should NOT be defined simply as:

correct_before → correct_after

We should distinguish:

- immediate performance
- short-term learning
- retention
- transfer
- independent performance
- fluency

A useful assessment ladder is:

1. immediate response
2. similar problem with a small change
3. new problem testing the same concept
4. more substantial variation / transfer
5. delayed assessment when data permits

This helps distinguish genuine learning from memorization or lucky answers.

---

# Learning evaluation

Do not rely on a single learning metric.

Candidate metrics include:

- correctness
- mastery / knowledge estimate
- normalized knowledge gain
- improvement relative to remaining opportunity
- independent correctness
- response time
- response-time improvement
- hint dependence
- transfer performance
- retention where measurable
- consistency across repeated/similar problems
- misconception reduction
- confidence calibration
- persistence / engagement

The evaluation should examine multiple metrics and assess robustness.

A large absolute gain from a very low baseline should not automatically be
considered better than a smaller gain from an already strong student.

Remaining opportunity / headroom normalization should therefore be considered.

For example:

normalized_gain =
    (post - pre) / (1 - pre)

This should be treated as one metric, not as the single definition of learning.

---

# Tutor evaluation

The tutors are the actual product being evaluated.

The student simulator exists primarily to create a controlled environment in which
different tutors can be compared.

Tutors should receive the same:
- initial student states
- task sequence where possible
- assessment structure
- experimental conditions
- random seeds where applicable

Differences should arise primarily from tutor behavior.

We should NOT assume in advance that one tutoring strategy is best.

Different tutors may:
- give large conceptual explanations
- proceed step-by-step
- use hints
- ask Socratic questions
- adapt difficulty
- repeat concepts
- use visual explanations
- break problems into smaller parts
- change modality
- check understanding frequently

The simulator should allow tutor actions to influence student behavior and learning.

---

# Tutor interface

Treat tutors through a common interface.

The simulator should not need to know the internal implementation of a tutor.

Conceptually:

Tutor receives:
    student conversation/context
    current task
    available student information

Tutor produces:
    natural-language response
    optionally structured action metadata if available

The evaluation layer should record the tutor's intervention and resulting student
trajectory.

---

# Experimental design

Tutor comparison should use paired/counterfactual experiments.

Example:

Student 17, initial state S0
    → Tutor A
    → Tutor B
    → Tutor C

The same initial student should be evaluated against each tutor.

Multiple random seeds should be used to quantify stochastic variation.

Results should report:
- mean
- variance / uncertainty
- confidence intervals where appropriate
- effect sizes where useful
- per-student paired differences
- robustness across seeds and student profiles

Avoid conclusions based on a single simulation run.

---

# Repeatability

Experiments should be reproducible.

Record:
- dataset/version
- experiment configuration
- student population
- task set
- tutor
- number of runs
- random seed
- model configuration
- relevant software/model versions

Avoid uncontrolled randomness.

If an external LLM introduces nondeterminism, document this explicitly.

---

# Real data and simulator training

Real student data should be used to estimate behavioral patterns.

Do NOT simply replay real student trajectories.

The simulator should generate new behavior conditional on:
- latent student state
- task
- teacher intervention
- interaction history

The preferred MVP architecture is:

STATISTICAL / PROBABILISTIC MODEL
    decides WHAT the student does

LLM (optional)
    decides HOW the student expresses it in natural language

Do not make an LLM solely responsible for deciding student behavior in the MVP.

An LLM may be used for:
- labeling/annotating open-ended responses
- natural-language realization of a structured simulated response

Any such use must be documented.

---

# Simulator validation

Validation is important but should be lightweight in the first prototype.

We should eventually compare simulated vs real students on:

Behavioral:
- correctness distribution
- error patterns
- hint-seeking
- persistence
- response time

Interaction:
- number of turns
- help-seeking patterns
- response to tutor interventions
- conversation trajectories

Learning:
- knowledge progression
- improvement
- transfer
- retention where possible
- misconception changes

Most importantly:

Decision validity:
Does the simulator preserve the relative ranking of tutors observed with real
students?

For example:

If real students produce:

Tutor A > Tutor B > Tutor C

does the simulated population produce a similar ranking?

This should be treated as a key validation experiment.

---

# Superficial vs underlying similarity

Do not validate the simulator only by asking whether its generated text "sounds
like a student."

A simulator can produce realistic dialogue while having unrealistic learning
dynamics.

Therefore distinguish:

Surface fidelity:
- wording
- conversational style
- turn length
- linguistic patterns

from:

Behavioral fidelity:
- correctness
- mistakes
- hints
- response time
- persistence

and:

Learning fidelity:
- state progression
- response to interventions
- transfer
- retention

and:

Decision validity:
- preservation of tutor ranking

The latter dimensions are more important for the project's goal.

---

# Data leakage and evaluation discipline

When evaluating predictive models on real student data:

- split by student where appropriate
- avoid leakage from future interactions
- use temporal ordering when predicting future behavior
- clearly distinguish training, validation, and held-out evaluation data

Do not use future student behavior to estimate the state used to predict that
same behavior.

---

# Baselines

Prefer simple baselines before sophisticated models.

Examples:

- population-level correctness baseline
- problem-difficulty baseline
- simple knowledge estimate
- logistic regression
- simple probabilistic transition model

Only introduce more complex models if they demonstrate measurable improvement.

Complexity must be justified experimentally.

---

# Research workflow

The implementation should proceed in this order:

1. Data audit
2. Data preprocessing
3. Establish observable variables and available signals
4. Build simple student-state estimation
5. Test whether student state predicts future behavior
6. Build lightweight simulated student
7. Run multi-turn tutoring simulations
8. Define and compute learning metrics
9. Compare tutors under paired/counterfactual conditions
10. Run robustness experiments
11. Validate simulated vs real student behavior
12. Test tutor-ranking preservation
13. Document failure modes and limitations

Do not skip the data audit.

Do not implement assumptions merely because they were proposed before seeing the
actual dataset.

---

# Current modeling philosophy

We prefer:

- interpretable over opaque
- probabilistic over deterministic
- data-driven over LLM-driven
- modular over monolithic
- simple baselines before complex models
- explicit assumptions
- measurable hypotheses
- reproducible experiments
- robustness analysis

The prototype should make modeling assumptions visible rather than hiding them
inside prompts.

---

# Important implementation rule

Before writing substantial code, inspect the actual dataset and report:

- schemas
- number of rows
- number of students
- number of problems
- number of skills
- missingness
- answer types
- question types
- correctness distribution
- hint distribution
- timestamps
- interaction counts per student
- any other fields relevant to the proposed student model

Do not assume that fields exist merely because they would be useful.

The data audit should determine which parts of the conceptual model are actually
supported by the data.

---

# Scope discipline

This is a research prototype, not a production system.

Do NOT:
- build unnecessary infrastructure
- build a web application unless needed
- over-engineer the simulator
- introduce deep learning without evidence that it is useful
- create a large hand-designed ontology
- create an elaborate LLM agent architecture
- spend time on deployment

Prioritize experiments, analysis, visualizations, and clear reasoning.

Every major modeling choice should have:
1. a rationale
2. an implementation
3. an evaluation or sanity check

---

# Expected deliverables

The final project should support:

1. A working lightweight prototype
2. Multiple simulated student profiles/states
3. Multi-turn tutoring interactions
4. At least one mathematics domain
5. Multiple tutor models through a common interface
6. Learning evaluation
7. Repeatable paired experiments
8. Visualizations of learning trajectories
9. Simulator validation against real data
10. Tutor ranking comparison
11. Limitations and failure-mode analysis

The eventual presentation should tell a coherent story:

Data
→ Student representation
→ Behavioral model
→ Simulation
→ Controlled tutor comparison
→ Learning outcomes
→ Simulator validation
→ Ranking validity
→ Limitations

---

# Current status

At project initialization:

- project directory created
- Python virtual environment created
- dataset access may still be pending
- actual dataset schema is not yet known

Therefore the immediate next task is DATA AUDIT, not simulator implementation.

Do not invent the final schema before inspecting the real data.