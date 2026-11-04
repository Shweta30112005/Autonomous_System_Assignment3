# Argumentation Engine — Assignment 3

## Overview

A complete Python implementation of **Dung's Abstract Argumentation Framework** with
extensions, labellings, and a **Strategic Argumentation** module implementing the
grounded direct argumentation mechanism.

## Project Structure

```
Autonomous_System_Assignment3/
├── argumentation_framework.py   # Core library: AF class + Strategic class
├── test_argumentation.py        # Tests for Part 1 (AF operations)
├── test_strategic.py            # Tests for Part 2 (strategic argumentation)
├── experiments.py               # Part 3: Random experiments (1000 instances)
├── main.py                      # Complete demonstration script
├── report.md                    # Detailed report
└── README.md                    # This file
```

## Requirements

- **Python 3.7+** (no external dependencies, only standard library)

## How to Run

### Quick Demo (all parts)
```bash
python3 main.py
```

### Full Experiments (1000 instances, takes longer)
```bash
python3 main.py --full
```
Or directly:
```bash
python3 experiments.py
```

### Individual Test Suites
```bash
python3 test_argumentation.py    # Part 1: AF framework tests
python3 test_strategic.py        # Part 2: Strategic tests
```

## Part 1: Argumentation Framework

### Class: `ArgumentationFramework`

Represents an abstract argumentation framework ⟨A, R⟩.

| Method | Description |
|--------|-------------|
| `__init__(arguments, attacks)` | Create a framework with arguments and attack pairs |
| `is_conflict_free(S)` | Test if set S is conflict-free |
| `is_defended_by(arg, S)` | Test if argument is defended by set S |
| `characteristic_function(S)` | Compute F(S) — all arguments defended by S |
| `is_admissible(S)` | Check if S is admissible |
| `is_complete_extension(S)` | Check if S is a complete extension |
| `grounded_extension()` | Compute the grounded extension (least fixpoint of F) |
| `all_complete_extensions()` | Enumerate all complete extensions |
| `preferred_extensions()` | Compute all preferred (maximal admissible) extensions |
| `stable_extensions()` | Compute all stable extensions |
| `semi_stable_extensions()` | Compute all semi-stable extensions |
| `all_labellings()` | Generate all legal IN/OUT/UNDEC labellings |
| `acceptance_status(arg)` | Report: skeptically / credulously accepted / rejected |

## Part 2: Strategic Argumentation

### Class: `StrategicArgumentation`

Implements the grounded direct argumentation mechanism.

| Method | Description |
|--------|-------------|
| `mechanism(revealed)` | Compute grounded extension from agents' revealed arguments |
| `best_responses(agent, others)` | Find utility-maximizing reports for an agent |
| `is_truthful_dominant()` | Verify Theorem 5.3 (truthfulness as best response) |
| `check_theorem_5_4()` | Check odd-length path condition (Theorem 5.4) |
| `is_strategyproof()` | Brute-force strategyproofness verification |

## Part 3: Experiments

Generates 1000+ random instances with 3 agents, 6–8 arguments, and varying
attack probabilities. Reports:

1. Fraction of strategyproof instances per p
2. Cases where Theorem 5.4 holds but mechanism is not strategyproof
3. Cases where mechanism is strategyproof despite Theorem 5.4 condition failing

## Example Usage

```python
from argumentation_framework import ArgumentationFramework, StrategicArgumentation

# Create framework
af = ArgumentationFramework(
    arguments={'a', 'b', 'c'},
    attacks={('a', 'b'), ('b', 'c')}
)

# Compute extensions
print(af.grounded_extension())       # {'a', 'c'}
print(af.preferred_extensions())      # [{'a', 'c'}]
print(af.acceptance_status('a'))      # 'skeptically accepted'

# Strategic argumentation
sa = StrategicArgumentation(af, {'agent1': {'a'}, 'agent2': {'b', 'c'}})
result = sa.mechanism({'agent1': {'a'}, 'agent2': {'b', 'c'}})
print(result)  # {'a', 'c'}
```

## References

- Dung, P.M. (1995). *On the acceptability of arguments...*
- Caminada, M. (2006). *Semi-stable semantics.*
- Rahwan, I. & Simari, G.R. (Eds.). *Argumentation in Artificial Intelligence.* Springer.
- Multiagent Systems textbook (the-mas-book.info) — Chapter 5.

