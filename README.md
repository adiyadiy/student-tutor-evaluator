# Student Tutor Evaluation

Research prototype for evaluating AI math tutors using simulated students.

## Goal

The goal of this project is to investigate whether simulated students can be
used to meaningfully, reliably, and repeatably compare AI math tutors.

The simulator is an evaluation instrument rather than the end product.

The key research questions are:

1. How should a student be represented?
2. Which student characteristics and behaviors matter for tutoring?
3. How should knowledge, misconceptions, confidence, and engagement evolve?
4. Can student behavior be learned from real student interaction data?
5. Can simulated students reproduce important real-student behavior?
6. Can simulated students distinguish between different tutor models?
7. Do simulated students preserve tutor rankings observed with real students?
8. How can we distinguish realistic conversation from realistic learning?

## Research pipeline

Real student data
→ student state estimation
→ behavioral models
→ simulated students
→ controlled interactions with multiple tutors
→ learning assessment
→ tutor comparison
→ simulator validation

## Design principles

The project prioritizes:

- research validity over software complexity
- interpretable models over unnecessary complexity
- probabilistic behavior over deterministic rules
- data-driven assumptions over hand-designed behavior
- learning outcomes over conversational realism
- reproducibility and controlled experiments

## Project structure

```text
student-tutor-evaluation/
│
├── CLAUDE.md
├── README.md
├── requirements.txt
│
├── data/
│   ├── raw/              # raw dataset files; not committed to git
│   └── processed/        # processed data; not committed to git
│
├── src/
│   ├── data/
│   ├── student/
│   ├── tutor/
│   ├── evaluation/
│   └── simulation/
│
├── experiments/
├── tests/
│
└── reports/
    ├── figures/
    └── results/
```

## Data

The project is intended to use real student–tutor interaction data.

The dataset access request is currently pending.

Until access is approved:

do not assume the final dataset schema
do not implement dataset-specific models
do not invent variables that may not exist
do not upload or expose student data externally

The first implementation task after access is approved will be a data audit.

The audit should establish:

available tables/files
schemas
number of students
number of interactions
number of problems
number of skills/concepts
missingness
correctness information
answer types
hints/help signals
timestamps
response-time availability
interaction history
other signals relevant to student modeling


## Student model

The intended student state is:

S(t) = {
knowledge,
misconceptions,
confidence,
engagement,
stable learner tendencies
}

The state is latent and should be inferred from observed interaction history.

Observed behavior may include:

correctness
answer content
response time
hint requests
help requests
answer exposure
persistence
task characteristics
teacher interventions

Correctness should not be treated as equivalent to knowledge.

## Learning

Learning is defined primarily as improvement in the probability of independently
solving new problems requiring the target skill, with persistence beyond the
immediate tutoring interaction where measurable.

Evaluation should distinguish:

immediate performance
transfer
retention
independent performance
misconception reduction
confidence calibration

## Tutor comparison

Tutors should be evaluated under matched conditions.

Where possible, the same simulated student, initial state, task sequence, and
random seed should be used across tutors.

Multiple runs should be used to quantify stochastic variation.

The primary goal is not merely to determine which tutor produces the most
convincing conversation, but whether tutors differ in meaningful learning
outcomes.

## Validation

Simulator validation should occur at several levels:

## Behavioral validity

Do simulated students reproduce important real-student patterns?

Dynamic validity

Do simulated students respond realistically to tutor interventions?

## Learning validity

Do simulated students exhibit realistic learning, transfer, and retention
patterns?

## Decision validity

Does the simulator preserve the relative ranking of tutor models observed with
real students?

Decision validity is especially important because the simulator is intended to
support tutor evaluation.

## Scope

This is a research prototype.

The project intentionally avoids:

production infrastructure
web application development
unnecessary deep learning
large hand-designed ontologies
complex agent architectures
deployment work

Time should be spent primarily on:

modeling
experiments
validation
analysis
visualization
interpretation