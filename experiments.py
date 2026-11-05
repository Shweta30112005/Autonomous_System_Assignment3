"""
Randomised experiments for strategic argumentation.

For each attack probability, this module generates random argumentation
frameworks, assigns arguments to agents, and compares:
  1. strategyproofness, checked by exhaustive enumeration of reports; and
  2. the sufficient odd-length-path condition from Theorem 5.4.

The experiment is deliberately configurable. By default, self-attacks are
included among the possible directed attacks, because an argumentation
framework may contain an attack from an argument to itself. Set
--no-self-attacks to reproduce the convention used by the original script.

Results are written to:
  experiment_results.json
  notable_instances.json

Run a quick experiment:
    python experiments.py --instances 10

Run the assignment-scale experiment:
    python experiments.py --instances 1000
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from argumentation_framework import ArgumentationFramework, StrategicArgumentation


DEFAULT_P_VALUES = (0.15, 0.2, 0.25, 0.3, 0.35, 0.4)


def generate_random_instance(
    num_args: int,
    p: float,
    num_agents: int = 3,
    *,
    rng: Optional[random.Random] = None,
    include_self_attacks: bool = True,
) -> Tuple[ArgumentationFramework, Dict[str, set[str]]]:
    """
    Generate one random framework and a random partition of its arguments.

    Every ordered pair of arguments is considered independently as a
    potential attack. If include_self_attacks is False, pairs (a, a) are
    skipped. Every argument is assigned to exactly one agent.

    Args:
        num_args: Number of arguments (must be positive).
        p: Independent probability of each eligible attack (0 <= p <= 1).
        num_agents: Number of agents (must be positive).
        rng: Optional random number generator. Supplying one makes generation
            reproducible without changing Python's global random state.
        include_self_attacks: Whether self-attacks are possible.

    Returns:
        A pair (framework, ownership), where ownership maps each agent name
        to the set of arguments owned by that agent.
    """
    if not isinstance(num_args, int) or isinstance(num_args, bool) or num_args < 1:
        raise ValueError("num_args must be a positive integer.")
    if not isinstance(num_agents, int) or isinstance(num_agents, bool) or num_agents < 1:
        raise ValueError("num_agents must be a positive integer.")
    if not isinstance(p, (int, float)) or isinstance(p, bool) or not 0.0 <= p <= 1.0:
        raise ValueError("p must be a number between 0 and 1.")

    generator = rng if rng is not None else random.Random()
    arguments = {f"a{i}" for i in range(num_args)}
    ordered_arguments = sorted(arguments)

    attacks = {
        (source, target)
        for source in ordered_arguments
        for target in ordered_arguments
        if (include_self_attacks or source != target)
        and generator.random() < p
    }

    ownership: Dict[str, set[str]] = {
        f"agent{i}": set() for i in range(num_agents)
    }
    for argument in ordered_arguments:
        owner_index = generator.randrange(num_agents)
        ownership[f"agent{owner_index}"].add(argument)

    return ArgumentationFramework(arguments, attacks), ownership


def _serialise_instance(
    index: int,
    p: float,
    framework: ArgumentationFramework,
    ownership: Dict[str, Iterable[str]],
) -> Dict[str, Any]:
    """Convert an instance to JSON-compatible data."""
    return {
        "index": index,
        "p": p,
        "num_arguments": len(framework.arguments),
        "arguments": sorted(framework.arguments),
        "attacks": [list(edge) for edge in sorted(framework.attacks)],
        "agent_arguments": {
            agent: sorted(arguments) for agent, arguments in sorted(ownership.items())
        },
    }


def _print_progress(index: int, total: int, started_at: float) -> None:
    elapsed = time.perf_counter() - started_at
    print(f"  Instance {index}/{total} completed ({elapsed:.1f}s elapsed)")



def _build_interpretation(results: Dict[str, Any], probabilities: Sequence[float],
                          anomaly_count: int) -> List[str]:
    """Create concise, data-dependent interpretation statements."""
    lines = [
        "Theorem 5.4 gives a sufficient condition for strategyproofness, not a necessary one.",
        "Therefore, strategyproof instances may exist even when the theorem condition fails.",
    ]
    sp_values = [results[str(p)]["strategyproof_fraction"] for p in probabilities]
    thm_values = [results[str(p)]["theorem_5_4_holds_fraction"] for p in probabilities]
    if len(sp_values) >= 2:
        if all(a >= b for a, b in zip(sp_values, sp_values[1:])) and sp_values[0] > sp_values[-1]:
            lines.append("In this run, the strategyproofness fraction decreases as attack probability increases.")
        elif all(a <= b for a, b in zip(sp_values, sp_values[1:])) and sp_values[0] < sp_values[-1]:
            lines.append("In this run, the strategyproofness fraction increases as attack probability increases.")
        else:
            lines.append("The strategyproofness fraction does not change monotonically across the tested probabilities.")
        if all(a >= b for a, b in zip(thm_values, thm_values[1:])) and thm_values[0] > thm_values[-1]:
            lines.append("The fraction satisfying Theorem 5.4 also decreases as attack probability increases in this run.")
        elif all(a <= b for a, b in zip(thm_values, thm_values[1:])) and thm_values[0] < thm_values[-1]:
            lines.append("The fraction satisfying Theorem 5.4 increases as attack probability increases in this run.")
        else:
            lines.append("The Theorem 5.4 satisfaction fraction is not monotonic across the tested probabilities.")
    sp_but_not_thm = sum(v["strategyproof_but_theorem_fails_count"] for v in results.values())
    thm_but_not_sp = sum(v["theorem_holds_but_not_strategyproof_count"] for v in results.values())
    lines.append(f"Strategyproof but theorem condition fails: {sp_but_not_thm} instance(s) across all tested probabilities.")
    if anomaly_count:
        lines.append(f"WARNING: {anomaly_count} instance(s) satisfy the coded theorem condition but are not strategyproof; investigate before drawing conclusions.")
    else:
        lines.append("No instance violated the expected sufficient-condition implication in this run. This is empirical evidence, not a mathematical proof.")
    if thm_but_not_sp == 0:
        lines.append("There were no instances where the theorem condition held but strategyproofness failed.")
    return lines


def _write_readable_summary(destination: Path, summary: Dict[str, Any],
                            results: Dict[str, Any], probabilities: Sequence[float],
                            interpretation: Sequence[str]) -> Path:
    """Write a plain-text report that is easy to open and read."""
    path = destination / "experiment_summary.txt"
    rows = [
        "STRATEGIC ARGUMENTATION - EXPERIMENT SUMMARY",
        "=" * 76,
        f"Instances per attack probability: {summary['num_instances_per_probability']}",
        f"Number of agents: {summary['num_agents']}",
        f"Arguments per instance: {summary['min_arguments']}-{summary['max_arguments']}",
        f"Attack probabilities: {', '.join(f'{p:g}' for p in probabilities)}",
        f"Self-attacks included: {summary['include_self_attacks']}",
        f"Random seed: {summary['seed']}",
        "",
        "RESULTS",
        "-" * 76,
        f"{'p':>6} | {'SP fraction':>12} | {'Thm 5.4 fraction':>16} | {'Thm holds, not SP':>17} | {'SP, Thm fails':>14}",
        "-" * 76,
    ]
    for p in probabilities:
        item = results[str(p)]
        rows.append(
            f"{float(p):6.2f} | {item['strategyproof_fraction']:12.4f} | "
            f"{item['theorem_5_4_holds_fraction']:16.4f} | "
            f"{item['theorem_holds_but_not_strategyproof_count']:17d} | "
            f"{item['strategyproof_but_theorem_fails_count']:14d}"
        )
    rows.extend(["", "INTERPRETATION", "-" * 76])
    rows.extend(f"- {line}" for line in interpretation)
    rows.extend([
        "", "OUTPUT FILES", "- experiment_results.json: complete machine-readable experiment results.",
        "- notable_instances.json: selected example frameworks for inspection.",
        "- experiment_summary.csv: tabular data for spreadsheets.",
        "- strategyproofness_vs_probability.png and theorem_condition_vs_probability.png: plots, if matplotlib is installed.",
    ])
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def _write_csv_summary(destination: Path, results: Dict[str, Any],
                       probabilities: Sequence[float]) -> Path:
    """Write one row per attack probability for spreadsheet analysis."""
    path = destination / "experiment_summary.csv"
    fields = [
        "attack_probability", "instances", "strategyproof_count", "strategyproof_fraction",
        "theorem_5_4_holds_count", "theorem_5_4_holds_fraction",
        "theorem_holds_but_not_strategyproof_count", "strategyproof_but_theorem_fails_count",
        "total_profitable_deviation_counterexamples", "elapsed_seconds",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for p in probabilities:
            item = results[str(p)]
            writer.writerow({field: item[field] if field in item else item["p"] if field == "attack_probability" else item["num_instances"] if field == "instances" else "" for field in fields})
    return path


def _write_plots(destination: Path, results: Dict[str, Any],
                 probabilities: Sequence[float]) -> List[Path]:
    """Save two separate, report-friendly line charts when matplotlib is available."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Plots skipped: matplotlib is not installed (install with: python3 -m pip install matplotlib).")
        return []

    x = [float(p) for p in probabilities]
    outputs: List[Path] = []
    charts = [
        ("strategyproof_fraction", "Strategyproofness vs. attack probability",
         "Strategyproof instances (%)", "strategyproofness_vs_probability.png"),
        ("theorem_5_4_holds_fraction", "Theorem 5.4 condition vs. attack probability",
         "Instances satisfying Theorem 5.4 (%)", "theorem_condition_vs_probability.png"),
    ]
    for key, title, ylabel, filename in charts:
        y = [results[str(p)][key] * 100 for p in probabilities]
        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        ax.plot(x, y, marker="o", linewidth=2)
        ax.set_title(title)
        ax.set_xlabel("Attack probability (p)")
        ax.set_ylabel(ylabel)
        ax.set_ylim(0, 100)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        output = destination / filename
        fig.savefig(output, dpi=200, bbox_inches="tight")
        plt.close(fig)
        outputs.append(output)
    return outputs

def run_full_experiments(
    num_instances: int = 1000,
    p_values: Optional[Sequence[float]] = None,
    num_agents: int = 3,
    min_args: int = 6,
    max_args: int = 8,
    seed: int = 42,
    output_dir: str | Path = "experiment_results",
    *,
    include_self_attacks: bool = True,
    progress_interval: int = 100,
    max_saved_examples: int = 20,
) -> Tuple[Dict[str, Any], Dict[str, List[Dict[str, Any]]]]:
    """
    Run the experiment suite and save machine-readable results.

    Strategyproofness is checked exactly by exhaustive enumeration using
    StrategicArgumentation.is_strategyproof(). This is computationally
    expensive, so the assignment-scale run may take some time.

    Theorem 5.4 is a sufficient condition. Consequently, an instance for
    which the condition is reported as holding but strategyproofness fails
    is recorded as an anomaly that should be investigated; it is not silently
    discarded.

    Returns:
        (results_by_probability, notable_instances)
    """
    if not isinstance(num_instances, int) or isinstance(num_instances, bool) or num_instances < 1:
        raise ValueError("num_instances must be a positive integer.")
    if not isinstance(num_agents, int) or isinstance(num_agents, bool) or num_agents < 1:
        raise ValueError("num_agents must be a positive integer.")
    if not isinstance(min_args, int) or not isinstance(max_args, int):
        raise ValueError("min_args and max_args must be integers.")
    if min_args < 1 or max_args < min_args:
        raise ValueError("Require 1 <= min_args <= max_args.")
    if progress_interval < 0:
        raise ValueError("progress_interval cannot be negative.")
    if max_saved_examples < 0:
        raise ValueError("max_saved_examples cannot be negative.")

    probabilities = list(DEFAULT_P_VALUES if p_values is None else p_values)
    if not probabilities:
        raise ValueError("p_values must contain at least one probability.")
    for probability in probabilities:
        if (
            not isinstance(probability, (int, float))
            or isinstance(probability, bool)
            or not 0.0 <= probability <= 1.0
        ):
            raise ValueError(f"Invalid attack probability: {probability!r}")

    rng = random.Random(seed)
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    all_results: Dict[str, Any] = {}
    notable: Dict[str, List[Dict[str, Any]]] = {
        "theorem_condition_holds_but_not_strategyproof": [],
        "strategyproof_but_theorem_condition_fails": [],
    }
    anomaly_count = 0

    print("=" * 76)
    print("STRATEGIC ARGUMENTATION: RANDOMISED EXPERIMENTS")
    print(f"Instances per p: {num_instances}")
    print(f"Agents: {num_agents}")
    print(f"Arguments per instance: {min_args}-{max_args}")
    print(f"Attack probabilities: {probabilities}")
    print(f"Self-attacks included: {include_self_attacks}")
    print(f"Random seed: {seed}")
    print("=" * 76)

    for p in probabilities:
        print(f"\nAttack probability p = {p:.3f}")
        started_at = time.perf_counter()

        strategyproof_count = 0
        theorem_condition_count = 0
        theorem_holds_not_sp: List[Dict[str, Any]] = []
        sp_but_theorem_fails: List[Dict[str, Any]] = []
        total_counterexamples = 0

        for index in range(1, num_instances + 1):
            number_of_arguments = rng.randint(min_args, max_args)
            framework, ownership = generate_random_instance(
                number_of_arguments,
                float(p),
                num_agents,
                rng=rng,
                include_self_attacks=include_self_attacks,
            )
            mechanism = StrategicArgumentation(framework, ownership)

            theorem_holds, theorem_violations = mechanism.check_theorem_5_4()
            strategyproof, counterexamples = mechanism.is_strategyproof()

            strategyproof_count += int(strategyproof)
            theorem_condition_count += int(theorem_holds)
            total_counterexamples += len(counterexamples)

            if theorem_holds and not strategyproof:
                instance = _serialise_instance(index, float(p), framework, ownership)
                instance["counterexamples"] = counterexamples
                instance["theorem_violations"] = theorem_violations
                theorem_holds_not_sp.append(instance)
                anomaly_count += 1

            if strategyproof and not theorem_holds:
                instance = _serialise_instance(index, float(p), framework, ownership)
                instance["theorem_violations"] = theorem_violations
                sp_but_theorem_fails.append(instance)

            if progress_interval and index % progress_interval == 0:
                _print_progress(index, num_instances, started_at)

        elapsed = time.perf_counter() - started_at
        strategyproof_fraction = strategyproof_count / num_instances
        theorem_fraction = theorem_condition_count / num_instances

        per_probability = {
            "p": float(p),
            "num_instances": num_instances,
            "num_agents": num_agents,
            "min_arguments": min_args,
            "max_arguments": max_args,
            "include_self_attacks": include_self_attacks,
            "strategyproof_count": strategyproof_count,
            "strategyproof_fraction": strategyproof_fraction,
            "theorem_5_4_holds_count": theorem_condition_count,
            "theorem_5_4_holds_fraction": theorem_fraction,
            "theorem_holds_but_not_strategyproof_count": len(theorem_holds_not_sp),
            "strategyproof_but_theorem_fails_count": len(sp_but_theorem_fails),
            "total_profitable_deviation_counterexamples": total_counterexamples,
            "elapsed_seconds": round(elapsed, 4),
        }
        all_results[str(p)] = per_probability

        notable["theorem_condition_holds_but_not_strategyproof"].extend(
            theorem_holds_not_sp
        )
        notable["strategyproof_but_theorem_condition_fails"].extend(
            sp_but_theorem_fails
        )

        print(f"  Strategyproof: {strategyproof_count}/{num_instances} "
              f"({strategyproof_fraction:.4f})")
        print(f"  Theorem 5.4 condition holds: {theorem_condition_count}/{num_instances} "
              f"({theorem_fraction:.4f})")
        print(f"  Theorem holds but not strategyproof: {len(theorem_holds_not_sp)}")
        print(f"  Strategyproof but theorem condition fails: {len(sp_but_theorem_fails)}")
        print(f"  Elapsed time: {elapsed:.2f}s")

    summary = {
        "experiment": "Strategic argumentation: strategyproofness vs Theorem 5.4",
        "seed": seed,
        "num_instances_per_probability": num_instances,
        "num_agents": num_agents,
        "min_arguments": min_args,
        "max_arguments": max_args,
        "attack_probabilities": [float(p) for p in probabilities],
        "include_self_attacks": include_self_attacks,
        "results": all_results,
    }

    results_path = destination / "experiment_results.json"
    with results_path.open("w", encoding="utf-8") as output_file:
        json.dump(summary, output_file, indent=2)

    limited_notable = {
        category: examples[:max_saved_examples]
        for category, examples in notable.items()
    }
    notable_path = destination / "notable_instances.json"
    with notable_path.open("w", encoding="utf-8") as output_file:
        json.dump(limited_notable, output_file, indent=2)

    print("\n" + "=" * 76)
    print("SUMMARY")
    print(f"{'p':>6} | {'SP fraction':>12} | {'Thm 5.4 fraction':>16} | "
          f"{'Thm holds, not SP':>17} | {'SP, Thm fails':>14}")
    print("-" * 76)
    for p in probabilities:
        result = all_results[str(p)]
        print(
            f"{float(p):6.2f} | "
            f"{result['strategyproof_fraction']:12.4f} | "
            f"{result['theorem_5_4_holds_fraction']:16.4f} | "
            f"{result['theorem_holds_but_not_strategyproof_count']:17d} | "
            f"{result['strategyproof_but_theorem_fails_count']:14d}"
        )

    interpretation = _build_interpretation(all_results, probabilities, anomaly_count)
    print("\nInterpretation:")
    for line in interpretation:
        print(f"- {line}")

    readable_path = _write_readable_summary(
        destination, summary, all_results, probabilities, interpretation
    )
    csv_path = _write_csv_summary(destination, all_results, probabilities)
    plot_paths = _write_plots(destination, all_results, probabilities)

    print(f"\nDetailed results: {results_path}")
    print(f"Saved examples:   {notable_path}")
    print(f"Readable summary: {readable_path}")
    print(f"CSV table:        {csv_path}")
    for plot_path in plot_paths:
        print(f"Plot:             {plot_path}")

    return all_results, notable


def _parse_probabilities(value: str) -> List[float]:
    try:
        probabilities = [float(part.strip()) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Probabilities must be comma-separated numbers, e.g. 0.1,0.2,0.3."
        ) from exc
    if not probabilities or any(p < 0.0 or p > 1.0 for p in probabilities):
        raise argparse.ArgumentTypeError("Provide one or more probabilities in [0, 1].")
    return probabilities


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run random experiments for strategic argumentation."
    )
    parser.add_argument("--instances", type=int, default=1000,
                        help="Number of random instances per attack probability (default: 1000).")
    parser.add_argument("--p-values", type=_parse_probabilities,
                        default=list(DEFAULT_P_VALUES),
                        help="Comma-separated attack probabilities.")
    parser.add_argument("--agents", type=int, default=3,
                        help="Number of agents (default: 3).")
    parser.add_argument("--min-args", type=int, default=6,
                        help="Minimum number of arguments (default: 6).")
    parser.add_argument("--max-args", type=int, default=8,
                        help="Maximum number of arguments (default: 8).")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42).")
    parser.add_argument("--output-dir", default="experiment_results",
                        help="Directory in which JSON results are saved.")
    parser.add_argument("--no-self-attacks", action="store_true",
                        help="Exclude attacks from an argument to itself.")
    parser.add_argument("--progress-interval", type=int, default=100,
                        help="Print progress every N instances; use 0 to disable.")
    args = parser.parse_args()

    run_full_experiments(
        num_instances=args.instances,
        p_values=args.p_values,
        num_agents=args.agents,
        min_args=args.min_args,
        max_args=args.max_args,
        seed=args.seed,
        output_dir=args.output_dir,
        include_self_attacks=not args.no_self_attacks,
        progress_interval=args.progress_interval,
    )


if __name__ == "__main__":
    main()
