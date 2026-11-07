#!/usr/bin/env python3
"""
Argumentation Engine - Main Demonstration

Demonstrates:
1. Abstract argumentation framework semantics.
2. Strategic argumentation and truthful reporting.
3. A small randomised experiment (with an optional full experiment run).

Examples:
    python main.py
    python main.py --skip-experiments
    python main.py --full-experiments
"""

from __future__ import annotations

import argparse
from typing import Iterable, Mapping, Set

from argumentation_framework import ArgumentationFramework, StrategicArgumentation


def _print_labelling(labelling: Mapping[str, str], indent: str = "  ") -> None:
    """Print a labelling grouped by its IN, OUT, and UNDEC labels."""
    for label in ("in", "out", "undec"):
        arguments = {arg for arg, value in labelling.items() if value == label}
        print(f"{indent}{label.upper():5s}: {sorted(arguments)}")


def _print_extensions(title: str, extensions: Iterable[Set[str]]) -> None:
    """Print a named collection of extensions consistently."""
    print(f"\n  {title}:")
    values = list(extensions)
    if not values:
        print("    (none)")
        return
    for extension in values:
        print(f"    {sorted(extension)}")


def demo_part1() -> None:
    """Demonstrate core abstract argumentation framework operations."""
    print("\n" + "=" * 72)
    print("PART 1: ARGUMENTATION FRAMEWORK")
    print("=" * 72)

    framework = ArgumentationFramework()
    for argument in ("a", "b", "c", "d"):
        framework.add_argument(argument)
    for attack in (("a", "b"), ("b", "c"), ("c", "d"), ("d", "c")):
        framework.add_attack(*attack)

    print("\n1. Framework construction")
    print("  Framework:", framework)
    print("  Arguments:", sorted(framework.arguments))
    print("  Attacks:", sorted(framework.attacks))
    print("  Attackers of c:", sorted(framework.get_attackers("c")))
    print("  Arguments attacked by a:", sorted(framework.get_attacked("a")))

    print("\n2. Conflict-free sets")
    for candidate in (
        {"a", "b"}, {"a", "c"}, {"a", "d"}, {"b", "d"}, {"a"}, set()
    ):
        print(
            f"  {sorted(candidate)} -> "
            f"{framework.is_conflict_free(candidate)}"
        )

    print("\n3. Defence")
    # c is attacked by both b and d. Although a attacks b, it does not
    # attack d, so {a} does not defend c in this particular framework.
    defence_examples = (
        ("c", {"a"}),
        ("c", {"d"}),
        ("a", set()),
        ("d", {"a"}),
        ("d", {"b"}),
    )
    for argument, defenders in defence_examples:
        print(
            f"  {argument!r} defended by {sorted(defenders)}? "
            f"{framework.is_defended_by(argument, defenders)}"
        )

    print("\n4. Characteristic function")
    for candidate in (set(), {"a"}, {"a", "d"}, {"a", "c"}, {"a", "c", "d"}):
        result = framework.characteristic_function(candidate)
        print(f"  F({sorted(candidate)}) = {sorted(result)}")

    print("\n5. Admissible and complete sets")
    for candidate in (
        set(), {"a"}, {"a", "c"}, {"a", "d"}, {"a", "c", "d"}, {"b", "d"}
    ):
        admissible = framework.is_admissible(candidate)
        complete = framework.is_complete_extension(candidate)
        print(
            f"  {str(sorted(candidate)):25s} "
            f"admissible={admissible}, complete={complete}"
        )

    print("\n6. Extension semantics")
    print("  Grounded extension:", sorted(framework.grounded_extension()))
    _print_extensions("Complete extensions", framework.all_complete_extensions())
    _print_extensions("Preferred extensions", framework.preferred_extensions())
    _print_extensions("Stable extensions", framework.stable_extensions())
    _print_extensions("Semi-stable extensions", framework.semi_stable_extensions())

    print("\n7. Complete labellings")
    labellings = framework.all_labellings()
    if not labellings:
        print("  (none)")
    for index, labelling in enumerate(labellings, start=1):
        print(f"  Labelling {index}:")
        _print_labelling(labelling, indent="    ")

    print("\n8. Acceptance status (preferred semantics)")
    for argument in sorted(framework.arguments):
        print(f"  {argument!r}: {framework.acceptance_status(argument)}")

    print("\n9. Additional example: mutual attack (a <-> b)")
    mutual = ArgumentationFramework(
        {"a", "b"}, {("a", "b"), ("b", "a")}
    )
    print("  Grounded:", sorted(mutual.grounded_extension()))
    _print_extensions("Complete", mutual.all_complete_extensions())
    _print_extensions("Preferred", mutual.preferred_extensions())
    _print_extensions("Stable", mutual.stable_extensions())
    _print_extensions("Semi-stable", mutual.semi_stable_extensions())
    for labelling in mutual.all_labellings():
        _print_labelling(labelling)

    print("\n10. Additional example: odd cycle (a -> b -> c -> a)")
    odd_cycle = ArgumentationFramework(
        {"a", "b", "c"},
        {("a", "b"), ("b", "c"), ("c", "a")},
    )
    print("  Grounded:", sorted(odd_cycle.grounded_extension()))
    _print_extensions("Complete", odd_cycle.all_complete_extensions())
    _print_extensions("Preferred", odd_cycle.preferred_extensions())
    _print_extensions("Stable", odd_cycle.stable_extensions())
    _print_extensions("Semi-stable", odd_cycle.semi_stable_extensions())


def demo_part2() -> None:
    """Demonstrate the grounded direct argumentation mechanism."""
    print("\n\n" + "=" * 72)
    print("PART 2: STRATEGIC ARGUMENTATION")
    print("=" * 72)

    framework = ArgumentationFramework(
        {"a", "b", "c", "d"},
        {("a", "b"), ("b", "c"), ("c", "d")},
    )
    ownership = {
        "agent1": {"a", "c"},
        "agent2": {"b", "d"},
    }
    mechanism = StrategicArgumentation(framework, ownership)

    print("\n1. Framework and ownership")
    print("  Framework:", framework)
    for agent in mechanism.agents:
        print(f"  {agent} owns: {sorted(ownership[agent])}")

    truthful_reports = {
        agent: set(ownership[agent]) for agent in mechanism.agents
    }
    truthful_outcome = mechanism.mechanism(truthful_reports)
    print("\n2. All agents report truthfully")
    print("  Revealed arguments:", {k: sorted(v) for k, v in truthful_reports.items()})
    print("  Grounded extension:", sorted(truthful_outcome))
    for agent in mechanism.agents:
        print(f"  {agent} utility: {mechanism.utility(agent, truthful_outcome)}")

    hidden_report = {
        "agent1": {"a"},
        "agent2": {"b", "d"},
    }
    hidden_outcome = mechanism.mechanism(hidden_report)
    print("\n3. Agent 1 hides argument c")
    print("  Revealed arguments:", {k: sorted(v) for k, v in hidden_report.items()})
    print("  Grounded extension:", sorted(hidden_outcome))
    for agent in mechanism.agents:
        print(f"  {agent} utility: {mechanism.utility(agent, hidden_outcome)}")

    print("\n4. Best responses when the other agent reports truthfully")
    for agent in mechanism.agents:
        others = {
            other: set(ownership[other])
            for other in mechanism.agents
            if other != agent
        }
        best_reports, best_utility = mechanism.best_responses(agent, others)
        truthful_utility = mechanism.utility(agent, truthful_outcome)
        print(f"  {agent}:")
        print(f"    Best report(s): {[sorted(report) for report in best_reports]}")
        print(f"    Best utility: {best_utility}")
        print(f"    Truthful utility: {truthful_utility}")

    print("\n5. Theorem 5.3: dominant truthfulness")
    dominant, dominant_counterexamples = mechanism.is_truthful_dominant()
    print("  Truthful reporting is a weakly dominant strategy:", dominant)
    for example in dominant_counterexamples[:5]:
        print("  Counterexample:", example)
    if not dominant_counterexamples:
        print("  No profitable deviation was found.")

    print("\n6. Theorem 5.4: odd-length-path condition")
    theorem_condition, violations = mechanism.check_theorem_5_4()
    print("  Sufficient condition holds:", theorem_condition)
    for violation in violations:
        print("  Condition violation:", violation)
    strategyproof, counterexamples = mechanism.is_strategyproof()
    print("  Brute-force strategyproofness:", strategyproof)
    for example in counterexamples[:5]:
        print("  Profitable deviation:", example)

    print("\n7. Three-agent example")
    framework3 = ArgumentationFramework(
        {"a", "b", "c", "d", "e", "f"},
        {
            ("a", "b"), ("b", "c"), ("d", "e"),
            ("e", "f"), ("c", "d"),
        },
    )
    ownership3 = {
        "agent1": {"a", "d"},
        "agent2": {"b", "e"},
        "agent3": {"c", "f"},
    }
    mechanism3 = StrategicArgumentation(framework3, ownership3)
    reports3 = {agent: set(args) for agent, args in ownership3.items()}
    outcome3 = mechanism3.mechanism(reports3)

    print("  Framework:", framework3)
    for agent in mechanism3.agents:
        print(f"  {agent} owns: {sorted(ownership3[agent])}")
    print("  Truthful grounded extension:", sorted(outcome3))
    for agent in mechanism3.agents:
        print(f"  {agent} utility: {mechanism3.utility(agent, outcome3)}")

    sp3, counterexamples3 = mechanism3.is_strategyproof()
    thm3, violations3 = mechanism3.check_theorem_5_4()
    print("  Strategyproof:", sp3)
    print("  Theorem 5.4 condition holds:", thm3)
    for example in counterexamples3[:3]:
        print("  Profitable deviation:", example)
    for violation in violations3[:3]:
        print("  Condition violation:", violation)

    print("\n8. Textbook Example 5.10: Strategic Manipulation via Indirect Self-Defeat")
    af_ex10 = ArgumentationFramework(
        {"a1", "a2", "a3", "a4", "a5"},
        {("a1", "a2"), ("a2", "a3"), ("a3", "a4"), ("a3", "a5")},
    )
    ownership_ex10 = {
        "x": {"a1", "a4", "a5"},
        "y": {"a2"},
        "z": {"a3"},
    }
    sa_ex10 = StrategicArgumentation(af_ex10, ownership_ex10)
    out_10_truth = sa_ex10.mechanism(ownership_ex10)
    u_x_truth = sa_ex10.utility("x", out_10_truth)
    out_10_hide = sa_ex10.mechanism({"x": {"a4", "a5"}, "y": {"a2"}, "z": {"a3"}})
    u_x_hide = sa_ex10.utility("x", out_10_hide)
    sp_10, ce_10 = sa_ex10.is_strategyproof()
    thm_10, viol_10 = sa_ex10.check_theorem_5_4()

    print("  Framework attacks: a1->a2->a3->a4, a3->a5")
    print(f"  Truthful outcome: {sorted(out_10_truth)} | Agent x utility: {u_x_truth}")
    print(f"  Agent x hides a1 (reveals {{a4, a5}}): outcome: {sorted(out_10_hide)} | Agent x utility: {u_x_hide}")
    print(f"  Utility gain from manipulation: {u_x_hide - u_x_truth} (Strategyproof: {sp_10})")
    print(f"  Theorem 5.4 condition: {thm_10} (Violations: {len(viol_10)})")
    print("  * Note on Book Errata: In Example 5.10, the utilities of revealing vs hiding were transposed.")

    print("\n9. Textbook Example 5.11: Cancellation of Indirect Self-Defeat")
    af_ex11 = ArgumentationFramework(
        {"a1", "a2", "a3", "a4", "a5", "a6"},
        {("a1", "a2"), ("a2", "a3"), ("a3", "a4"), ("a3", "a5"), ("a6", "a3")},
    )
    ownership_ex11 = {
        "x": {"a1", "a4", "a5", "a6"},
        "y": {"a2"},
        "z": {"a3"},
    }
    sa_ex11 = StrategicArgumentation(af_ex11, ownership_ex11)
    out_11_truth = sa_ex11.mechanism(ownership_ex11)
    sp_11, ce_11 = sa_ex11.is_strategyproof()
    thm_11, viol_11 = sa_ex11.check_theorem_5_4()

    print("  Added argument a6 with attack (a6, a3) owned by agent x.")
    print(f"  Truthful outcome: {sorted(out_11_truth)} | Agent x utility: {sa_ex11.utility('x', out_11_truth)}")
    print(f"  Strategyproof: {sp_11} | Theorem 5.4 condition holds: {thm_11}")
    print(f"  Violations remaining: {len(viol_11)}")
    print("  * Crucial Insight: Even though Theorem 5.4 fails, strategyproofness holds because")
    print("    argument a6 directly defeats a3, cancelling the indirect defeat of a1 on a4 and a5.")
    print("  * Note on Book Errata: In the post-example text, the cancelling argument is a6, not a5.")


def demo_part3(
    instances: int = 10,
    output_dir: str = "demo_results",
) -> None:
    """Run a deliberately small experiment to demonstrate the experiment code."""
    print("\n\n" + "=" * 72)
    print("PART 3: EXPERIMENTS (QUICK DEMONSTRATION)")
    print("=" * 72)
    print(
        f"Running {instances} instances per probability. "
        "Use --full-experiments for the assignment-scale run."
    )

    from experiments import run_full_experiments

    run_full_experiments(
        num_instances=instances,
        p_values=[0.1, 0.3, 0.5],
        num_agents=3,
        min_args=6,
        max_args=7,
        seed=42,
        output_dir=output_dir,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Demonstrate the argumentation framework and strategic mechanism."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--skip-experiments",
        action="store_true",
        help="Run Parts 1 and 2 only; do not start random experiments.",
    )
    group.add_argument(
        "--full-experiments",
        action="store_true",
        help="Run the full experiment configuration (1000 instances per p).",
    )
    parser.add_argument(
        "--demo-instances",
        type=int,
        default=10,
        help="Instances per p in the quick experiment (default: 10).",
    )
    parser.add_argument(
        "--output-dir",
        default="demo_results",
        help="Directory for quick-demo experiment results.",
    )
    args = parser.parse_args()
    if args.demo_instances < 1:
        parser.error("--demo-instances must be at least 1.")
    return args


def main() -> None:
    args = parse_args()

    print("\n" + "#" * 72)
    print("#" + " " * 70 + "#")
    print("#" + "  ARGUMENTATION ENGINE - COMPLETE DEMONSTRATION".ljust(70) + "#")
    print("#" + "  Assignment 3".ljust(70) + "#")
    print("#" + " " * 70 + "#")
    print("#" * 72)

    demo_part1()
    demo_part2()

    if args.skip_experiments:
        print("\nSkipping Part 3 as requested.")
    elif args.full_experiments:
        print("\n\n" + "=" * 72)
        print("PART 3: FULL ASSIGNMENT-SCALE EXPERIMENTS")
        print("=" * 72)
        from experiments import run_full_experiments
        run_full_experiments()
    else:
        demo_part3(args.demo_instances, args.output_dir)

    print("\n" + "#" * 72)
    print("#" + "  DEMONSTRATION COMPLETE".ljust(70) + "#")
    print("#" * 72)


if __name__ == "__main__":
    main()
