# Argumentation Engine – Strategic Argumentation
### Autonomous Systems | Assignment 3

## 1. Overview

This project implements an **Argumentation Engine** based on abstract argumentation frameworks and strategic argumentation mechanisms.

The project explores how arguments interact through attacks, how acceptable arguments are determined using different argumentation semantics, and how strategic agents may influence the outcome by selectively reporting their arguments.

It also investigates the relationship between strategyproofness and the sufficient condition presented in **Theorem 5.4**, using randomized experiments and exhaustive strategy evaluation.

## 2. Objectives

The main objectives of this assignment are:

- Implement an abstract argumentation framework.
- Represent arguments and directed attacks between them.
- Compute different argumentation semantics and extensions.
- Implement a strategic argumentation mechanism based on grounded semantics.
- Model agents with individual ownership of arguments.
- Evaluate utilities under truthful and strategic reports.
- Check strategyproofness through exhaustive enumeration of possible reports.
- Verify the sufficient condition stated in Theorem 5.4.
- Conduct randomized experiments to study how attack probability affects strategyproofness and the theorem's condition.

## 3. Theoretical Background

### 3.1 Abstract Argumentation Framework

An abstract argumentation framework (AF) is represented as:

\[
AF=(A,R)
\]

where:

- \(A\) is a finite set of arguments.
- \(R\subseteq A\times A\) is a binary attack relation.

An attack \((a,b)\in R\) means that argument \(a\) attacks argument \(b\).

The implementation supports the following concepts:

- Conflict-free sets
- Attackers and attacked arguments
- Defence of arguments
- Characteristic function
- Admissible extensions
- Complete extensions
- Grounded extension
- Preferred extensions
- Stable extensions
- Semi-stable extensions
- Complete labellings
- Acceptance status

### 3.2 Strategic Argumentation

In strategic argumentation, multiple agents own different arguments and independently decide which arguments to reveal.

The mechanism:

1. Collects the reports submitted by agents.
2. Constructs the revealed subframework.
3. Computes its grounded extension.
4. Determines the utility received by each agent.

An agent's utility is the number of its owned arguments that belong to the resulting grounded extension.

### 3.3 Strategyproofness

A mechanism is strategyproof if truthful reporting is a weakly dominant strategy for every agent.

The implementation checks this property through exhaustive enumeration of possible reports and compares the utility from truthful reporting against every possible alternative report, for all reports of the other agents.

### 3.4 Theorem 5.4 – Sufficient Condition

Theorem 5.4 establishes a sufficient condition for strategyproofness when agents have individual acceptability-maximizing preferences.

The condition requires that no two arguments owned by the same agent are connected by a direct or indirect defeat.

For this implementation:

- Direct defeat corresponds to a directed path of length 1.
- Indirect defeat corresponds to a directed path of odd length greater than 1 (3, 5, 7, ...).
- Even-length paths represent indirect defence rather than defeat.
- Paths are simple directed paths: vertices and edges cannot repeat.

Therefore, the condition checks whether any two arguments belonging to the same agent are connected by an odd-length simple directed path.

**Important:** Theorem 5.4 provides a sufficient condition, not a necessary condition. Consequently, strategyproofness may still hold even when the theorem's condition is not satisfied.

## 4. Project Structure

```text
Autonomous_System_Assignment3/
│
├── argumentation_framework.py
│   └── Core implementation of argumentation semantics,
│       strategic mechanisms, utilities and theorem checks.
│
├── main.py
│   └── Main demonstration of the implemented features.
│
├── test_argumentation.py
│   └── Unit tests for argumentation framework semantics.
│
├── test_strategic.py
│   └── Unit tests for strategic mechanisms and
│       Theorem 5.4's simple-path condition.
│
├── experiments.py
│   └── Randomized experiment generation, exhaustive
│       strategyproofness evaluation and result analysis.
│
├── experiment_results/
│   ├── experiment_results.json
│   ├── notable_instances.json
│   ├── experiment_summary.txt
│   ├── experiment_summary.csv
│   ├── strategyproofness_vs_probability.png
│   └── theorem_condition_vs_probability.png
│
└── README.md
```

The `experiment_results/` directory is generated automatically when the experiments are executed.

## 5. Requirements

- Python 3.9 or later
- pip
- Matplotlib (required for generating experiment graphs)

Install Matplotlib:

```bash
python3 -m pip install matplotlib
```

The core argumentation implementation and unit tests use Python's standard library.

## 6. Installation and Setup

Clone the repository:

```bash
git clone <repository-url>
```

Navigate to the project directory:

```bash
cd Autonomous_System_Assignment3
```

Install the optional graph dependency:

```bash
python3 -m pip install matplotlib
```

## 7. Running the Project

### 7.1 Run the Complete Demonstration

```bash
python3 main.py
```

This demonstrates the argumentation framework, its semantics, strategic argumentation, utilities, strategyproofness and Theorem 5.4's condition.

To skip the experiment section of the demonstration:

```bash
python3 main.py --skip-experiments
```

### 7.2 Run Unit Tests

Run all tests:

```bash
python3 -m unittest discover -v
```

Alternatively, run the strategic argumentation tests separately:

```bash
python3 -m unittest -v test_strategic
```

Run the argumentation framework tests separately:

```bash
python3 -m unittest -v test_argumentation
```

### 7.3 Run Randomized Experiments

Run a small experiment for quick verification:

```bash
python3 experiments.py --instances 10
```

Run the full experiment with 10,000 instances per attack probability:

```bash
python3 experiments.py --instances 10000
```

The default attack probabilities are:

\[
p\in\{0.1,0.2,0.3,0.4,0.5\}
\]

Each potential directed attack is independently included with probability \(p\).

The experiment configuration can also be customized:

```bash
python3 experiments.py \
    --instances 10000 \
    --p-values 0.1,0.2,0.3,0.4,0.5 \
    --agents 3 \
    --min-args 6 \
    --max-args 8 \
    --seed 42
```

To exclude self-attacks:

```bash
python3 experiments.py --instances 10000 --no-self-attacks
```

## 8. Experimental Methodology

The randomized experiments evaluate the relationship between attack probability, strategyproofness and the sufficient condition of Theorem 5.4.

### 8.1 Instance Generation

For each attack probability:

1. Generate a random argumentation framework containing 6–8 arguments.
2. Consider each eligible ordered pair of arguments as a potential directed attack.
3. Include each potential attack independently with probability \(p\).
4. Randomly assign every argument to one of three agents.
5. Evaluate strategyproofness using exhaustive enumeration.
6. Check whether the ownership assignment satisfies Theorem 5.4's condition.
7. Record and aggregate the results.

The random seed is set to 42 by default to support reproducibility.

### 8.2 Evaluation Metrics

The experiments record:

| Metric | Description |
|---|---|
| Strategyproof fraction | Fraction of generated instances that are strategyproof. |
| Theorem 5.4 fraction | Fraction of instances satisfying the theorem's sufficient condition. |
| Theorem holds, not strategyproof | Instances satisfying the theorem's condition but failing strategyproofness. |
| Strategyproof, theorem fails | Instances that are strategyproof despite not satisfying the sufficient condition. |

### 8.3 Expected Observations

The experiments investigate:

- Whether strategyproofness becomes less frequent as attack probability increases.
- How the density of attacks affects the likelihood of satisfying Theorem 5.4's condition.
- Whether strategyproofness can occur even when the sufficient condition fails.
- Whether any generated instance contradicts the expected implication of the theorem.

## 9. Generated Experimental Outputs

After running `experiments.py`, the following files are created inside `experiment_results/`.

| File | Purpose |
|---|---|
| `experiment_results.json` | Detailed numerical results and experiment data. |
| `notable_instances.json` | Selected instances illustrating interesting outcomes. |
| `experiment_summary.txt` | Human-readable summary containing configuration, results and interpretation. |
| `experiment_summary.csv` | Tabular results for spreadsheet analysis. |
| `strategyproofness_vs_probability.png` | Graph of strategyproofness against attack probability. |
| `theorem_condition_vs_probability.png` | Graph of Theorem 5.4 condition satisfaction against attack probability. |

The TXT file is useful for reading and interpreting the results, while the CSV file can be opened in Excel, Numbers or Google Sheets.

The two graphs provide visual comparisons of the experimental trends.

## 10. Testing and Validation

The project includes unit tests covering:

- Argumentation framework construction and validation.
- Conflict-free sets and defence.
- Characteristic function.
- Admissible and complete extensions.
- Grounded, preferred, stable and semi-stable semantics.
- Complete labellings and acceptance status.
- Strategic report validation.
- Utility calculations.
- Best-response computation.
- Truthful dominance and strategyproofness.
- Direct and indirect defeat detection.
- Odd-length simple directed paths.
- Repeated-vertex exclusion and zero-length path handling.
- Theorem 5.4 condition verification.

Run the complete test suite using:

```bash
python3 -m unittest discover -v
```

## 11. Technologies Used

- **Python:** Core implementation and experiment execution.
- **Unittest:** Automated testing and validation.
- **Random:** Randomized argumentation framework generation.
- **JSON:** Storage of detailed experimental results.
- **CSV:** Tabular result export.
- **Matplotlib:** Experimental visualization.

## 12. Conclusion

This project implements an argumentation engine and extends it to a strategic multi-agent setting.

It provides mechanisms for evaluating argument acceptability, modelling strategic reporting behaviour and checking strategyproofness. It also implements the sufficient condition from Theorem 5.4 using odd-length simple directed paths.

Through randomized experiments, the project investigates how the probability of attacks influences strategyproofness and the satisfaction of the theorem's sufficient condition.

The experimental analysis also helps distinguish between a sufficient theoretical condition and the actual strategyproofness of a mechanism, highlighting that a mechanism can remain strategyproof even when the sufficient condition is not satisfied.

---

**Assignment:** Autonomous Systems – Assignment 3  
**Project:** Argumentation Engine – Strategic Argumentation