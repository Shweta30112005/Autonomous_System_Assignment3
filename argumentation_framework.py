"""Argumentation engine for Assignment 3.

Implements Dung-style abstract argumentation semantics and the grounded direct
argumentation mechanism used in the strategic part of the assignment. The
strategic concepts follow the course-assigned textbook: Gerhard Weiss (ed.),
*Multiagent Systems*, Chapter 5, “Argumentation among Agents” (Iyad Rahwan).

The strategic path checker below follows the project's original convention:
it detects odd-length directed *walks* (vertices may be revisited). If the
assigned statement of Theorem 5.4 defines a path as a simple path, that
interpretation must be changed consistently in the theorem checker and tests.
"""

from __future__ import annotations

from itertools import combinations, product
from typing import Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Set, Tuple

Argument = str
Attack = Tuple[Argument, Argument]
Label = str


class ArgumentationFramework:
    """A finite abstract argumentation framework ``(A, R)``.

    ``arguments`` is the set A and ``attacks`` is the binary relation R.
    Every endpoint in R must already belong to A. Self-attacks are allowed.
    """

    VALID_LABELS = frozenset({"in", "out", "undec"})

    def __init__(
        self,
        arguments: Optional[Iterable[Argument]] = None,
        attacks: Optional[Iterable[Attack]] = None,
    ) -> None:
        self.arguments: Set[Argument] = set(arguments or ())
        self.attacks: Set[Attack] = set(attacks or ())
        self._validate_framework()

    def _validate_framework(self) -> None:
        if any(not isinstance(arg, str) or not arg for arg in self.arguments):
            raise ValueError("Arguments must be non-empty strings.")
        for attack in self.attacks:
            if not isinstance(attack, tuple) or len(attack) != 2:
                raise ValueError(f"Each attack must be a pair; got {attack!r}.")
            attacker, target = attack
            if attacker not in self.arguments or target not in self.arguments:
                raise ValueError(
                    f"Attack {attack!r} has an endpoint not present in arguments."
                )

    @staticmethod
    def _as_set(values: Iterable[Argument], name: str) -> Set[Argument]:
        try:
            result = set(values)
        except TypeError as exc:
            raise TypeError(f"{name} must be an iterable of argument names.") from exc
        return result

    def _validate_subset(self, subset: Iterable[Argument], name: str = "S") -> Set[Argument]:
        result = self._as_set(subset, name)
        unknown = result - self.arguments
        if unknown:
            raise ValueError(f"{name} contains unknown arguments: {sorted(unknown)}")
        return result

    def add_argument(self, arg: Argument) -> None:
        if not isinstance(arg, str) or not arg:
            raise ValueError("Argument names must be non-empty strings.")
        self.arguments.add(arg)

    def add_attack(self, attacker: Argument, target: Argument) -> None:
        """Add an attack; endpoints are added if they are not present yet."""
        self.add_argument(attacker)
        self.add_argument(target)
        self.attacks.add((attacker, target))

    def get_attackers(self, arg: Argument) -> Set[Argument]:
        if arg not in self.arguments:
            raise ValueError(f"Unknown argument: {arg!r}")
        return {attacker for attacker, target in self.attacks if target == arg}

    def get_attacked(self, arg: Argument) -> Set[Argument]:
        if arg not in self.arguments:
            raise ValueError(f"Unknown argument: {arg!r}")
        return {target for attacker, target in self.attacks if attacker == arg}

    def get_attackers_of_set(self, arguments: Iterable[Argument]) -> Set[Argument]:
        subset = self._validate_subset(arguments)
        return {attacker for attacker, target in self.attacks if target in subset}

    def is_attacked_by(self, arg: Argument, arguments: Iterable[Argument]) -> bool:
        if arg not in self.arguments:
            raise ValueError(f"Unknown argument: {arg!r}")
        subset = self._validate_subset(arguments)
        return any((attacker, arg) in self.attacks for attacker in subset)

    def __repr__(self) -> str:
        args = ", ".join(sorted(self.arguments))
        attacks = ", ".join(f"({a}, {b})" for a, b in sorted(self.attacks))
        return f"AF(A={{{args}}}, R={{{attacks}}})"

    __str__ = __repr__

    # ------------------------------------------------------------------
    # Conflict-freeness, defence, and characteristic function
    # ------------------------------------------------------------------

    def is_conflict_free(self, arguments: Iterable[Argument]) -> bool:
        subset = self._validate_subset(arguments)
        return not any(a in subset and b in subset for a, b in self.attacks)

    def is_defended_by(self, arg: Argument, arguments: Iterable[Argument]) -> bool:
        """Return whether every attacker of ``arg`` is attacked by S."""
        if arg not in self.arguments:
            raise ValueError(f"Unknown argument: {arg!r}")
        defenders = self._validate_subset(arguments)
        for attacker in self.get_attackers(arg):
            if not any((defender, attacker) in self.attacks for defender in defenders):
                return False
        return True

    def characteristic_function(self, arguments: Iterable[Argument]) -> Set[Argument]:
        subset = self._validate_subset(arguments)
        return {arg for arg in self.arguments if self.is_defended_by(arg, subset)}

    # ------------------------------------------------------------------
    # Admissible and complete extensions
    # ------------------------------------------------------------------

    def is_admissible(self, arguments: Iterable[Argument]) -> bool:
        subset = self._validate_subset(arguments)
        return self.is_conflict_free(subset) and subset.issubset(
            self.characteristic_function(subset)
        )

    def is_complete_extension(self, arguments: Iterable[Argument]) -> bool:
        subset = self._validate_subset(arguments)
        return self.is_admissible(subset) and self.characteristic_function(subset) == subset

    def _all_subsets(self) -> Iterator[Set[Argument]]:
        ordered = sorted(self.arguments)
        for size in range(len(ordered) + 1):
            for values in combinations(ordered, size):
                yield set(values)

    def all_admissible_sets(self) -> List[Set[Argument]]:
        return [subset for subset in self._all_subsets() if self.is_admissible(subset)]

    def all_complete_extensions(self) -> List[Set[Argument]]:
        return [subset for subset in self._all_subsets() if self.is_complete_extension(subset)]

    def grounded_extension(self) -> Set[Argument]:
        """Compute the least fixed point of the characteristic function."""
        current: Set[Argument] = set()
        while True:
            following = self.characteristic_function(current)
            if following == current:
                return current
            current = following

    def preferred_extensions(self) -> List[Set[Argument]]:
        admissible = self.all_admissible_sets()
        return [
            candidate
            for candidate in admissible
            if not any(candidate < other for other in admissible)
        ]

    def _range_of(self, arguments: Iterable[Argument]) -> Set[Argument]:
        subset = self._validate_subset(arguments)
        attacked = {target for attacker, target in self.attacks if attacker in subset}
        return subset | attacked

    def stable_extensions(self) -> List[Set[Argument]]:
        return [
            subset
            for subset in self._all_subsets()
            if self.is_conflict_free(subset) and self._range_of(subset) == self.arguments
        ]

    def semi_stable_extensions(self) -> List[Set[Argument]]:
        """Return complete extensions with inclusion-maximal ranges."""
        complete = self.all_complete_extensions()
        ranges = [(extension, self._range_of(extension)) for extension in complete]
        result: List[Set[Argument]] = []
        for extension, extension_range in ranges:
            if not any(
                extension_range < other_range
                for _, other_range in ranges
            ):
                result.append(extension)
        return result

    # ------------------------------------------------------------------
    # Complete labellings and acceptance status
    # ------------------------------------------------------------------

    def _is_legal_labelling(self, labelling: Mapping[Argument, Label]) -> bool:
        if set(labelling) != self.arguments:
            return False
        if any(label not in self.VALID_LABELS for label in labelling.values()):
            return False

        for arg in self.arguments:
            attacker_labels = [labelling[a] for a in self.get_attackers(arg)]
            label = labelling[arg]
            if label == "in":
                if any(value != "out" for value in attacker_labels):
                    return False
            elif label == "out":
                if "in" not in attacker_labels:
                    return False
            else:  # undec
                if "in" in attacker_labels or all(value == "out" for value in attacker_labels):
                    return False
        return True

    def all_labellings(self) -> List[Dict[Argument, Label]]:
        ordered = sorted(self.arguments)
        labellings: List[Dict[Argument, Label]] = []
        for assignment in product(("in", "out", "undec"), repeat=len(ordered)):
            candidate = dict(zip(ordered, assignment))
            if self._is_legal_labelling(candidate):
                labellings.append(candidate)
        return labellings

    def labelling_to_extension(self, labelling: Mapping[Argument, Label]) -> Set[Argument]:
        if not self._is_legal_labelling(labelling):
            raise ValueError("The supplied labelling is not a legal complete labelling.")
        return {arg for arg, label in labelling.items() if label == "in"}

    def acceptance_status(self, arg: Argument) -> str:
        """Classify acceptance under preferred semantics."""
        if arg not in self.arguments:
            raise ValueError(f"Unknown argument: {arg!r}")
        preferred = self.preferred_extensions()
        if not preferred or not any(arg in extension for extension in preferred):
            return "rejected"
        if all(arg in extension for extension in preferred):
            return "skeptically accepted"
        return "credulously accepted"

    def subframework(self, subset: Iterable[Argument]) -> "ArgumentationFramework":
        selected = self._validate_subset(subset)
        attacks = {
            (attacker, target)
            for attacker, target in self.attacks
            if attacker in selected and target in selected
        }
        return ArgumentationFramework(selected, attacks)


class StrategicArgumentation:
    """Grounded direct argumentation mechanism with privately owned arguments.

    Each agent may reveal any subset of its own arguments. The mechanism
    computes the grounded extension of the framework induced by all revealed
    arguments. An agent's utility is the number of its owned arguments in that
    extension.
    """

    def __init__(
        self,
        framework: ArgumentationFramework,
        agent_arguments: Mapping[str, Iterable[Argument]],
    ) -> None:
        if not isinstance(framework, ArgumentationFramework):
            raise TypeError("framework must be an ArgumentationFramework.")
        if not agent_arguments:
            raise ValueError("At least one agent must be provided.")

        self.framework = framework
        self.agent_arguments: Dict[str, Set[Argument]] = {}
        for agent, owned in agent_arguments.items():
            if not isinstance(agent, str) or not agent:
                raise ValueError("Agent names must be non-empty strings.")
            self.agent_arguments[agent] = framework._validate_subset(owned, f"arguments of {agent}")
        self.agents = list(self.agent_arguments)

        owners: Dict[Argument, str] = {}
        for agent, owned in self.agent_arguments.items():
            for arg in owned:
                if arg in owners:
                    raise ValueError(
                        f"Argument {arg!r} is assigned to both {owners[arg]!r} and {agent!r}."
                    )
                owners[arg] = agent
        unassigned = framework.arguments - set(owners)
        if unassigned:
            raise ValueError(f"Arguments not assigned to any agent: {sorted(unassigned)}")

    def _validate_reports(
        self,
        revealed: Mapping[str, Iterable[Argument]],
        expected_agents: Optional[Set[str]] = None,
    ) -> Dict[str, Set[Argument]]:
        expected = set(self.agents) if expected_agents is None else expected_agents
        supplied = set(revealed)
        if supplied != expected:
            missing = expected - supplied
            extra = supplied - expected
            raise ValueError(f"Invalid report keys; missing={sorted(missing)}, extra={sorted(extra)}")
        validated: Dict[str, Set[Argument]] = {}
        for agent in expected:
            report = self.framework._validate_subset(revealed[agent], f"report from {agent}")
            not_owned = report - self.agent_arguments[agent]
            if not_owned:
                raise ValueError(f"Agent {agent!r} reported arguments it does not own: {sorted(not_owned)}")
            validated[agent] = report
        return validated

    def mechanism(self, revealed: Mapping[str, Iterable[Argument]]) -> Set[Argument]:
        reports = self._validate_reports(revealed)
        union: Set[Argument] = set().union(*reports.values())
        return self.framework.subframework(union).grounded_extension()

    def utility(self, agent: str, grounded_ext: Iterable[Argument]) -> int:
        if agent not in self.agent_arguments:
            raise ValueError(f"Unknown agent: {agent!r}")
        selected = self.framework._validate_subset(grounded_ext, "grounded extension")
        return len(self.agent_arguments[agent] & selected)

    @staticmethod
    def _subsets(arguments: Iterable[Argument]) -> Iterator[Set[Argument]]:
        ordered = sorted(arguments)
        for size in range(len(ordered) + 1):
            for values in combinations(ordered, size):
                yield set(values)

    def best_responses(
        self,
        agent: str,
        others_revealed: Mapping[str, Iterable[Argument]],
    ) -> Tuple[List[Set[Argument]], int]:
        if agent not in self.agent_arguments:
            raise ValueError(f"Unknown agent: {agent!r}")
        other_agents = set(self.agents) - {agent}
        others = self._validate_reports(others_revealed, expected_agents=other_agents)

        best_utility = -1
        best_reports: List[Set[Argument]] = []
        for report in self._subsets(self.agent_arguments[agent]):
            complete_reports = dict(others)
            complete_reports[agent] = report
            outcome = self.mechanism(complete_reports)
            utility = self.utility(agent, outcome)
            if utility > best_utility:
                best_utility = utility
                best_reports = [report]
            elif utility == best_utility:
                best_reports.append(report)
        return best_reports, best_utility

    def is_truthful_dominant(self) -> Tuple[bool, List[str]]:
        """Exhaustively verify that truth-telling is a weak best response.

        For every agent and every possible profile of reports by the other
        agents, no alternative report may yield strictly greater utility.
        Ties are allowed, as required by the weak-dominance formulation.
        """
        counterexamples: List[str] = []
        for agent in self.agents:
            others = [other for other in self.agents if other != agent]
            report_spaces = [list(self._subsets(self.agent_arguments[other])) for other in others]
            profiles = product(*report_spaces) if report_spaces else [()]

            for profile in profiles:
                others_revealed = dict(zip(others, profile))
                truthful_reports = dict(others_revealed)
                truthful_reports[agent] = set(self.agent_arguments[agent])
                truthful_outcome = self.mechanism(truthful_reports)
                truthful_utility = self.utility(agent, truthful_outcome)

                best_reports, best_utility = self.best_responses(agent, others_revealed)
                if best_utility > truthful_utility:
                    counterexamples.append(
                        f"Agent {agent!r}: others report {others_revealed}; "
                        f"truthful utility={truthful_utility}, best utility={best_utility}, "
                        f"best report(s)={best_reports}."
                    )
        return not counterexamples, counterexamples

    def has_odd_length_path(self, source: Argument, target: Argument) -> bool:
        """Return whether a simple odd-length directed path exists.

        A path may not repeat vertices (and therefore cannot repeat edges).
        Length 1 is a direct defeat; odd lengths greater than 1 are indirect
        defeats. A zero-length path is not a defeat, and no non-zero path from
        a vertex to itself is accepted under this simple-path convention.
        """
        if source not in self.framework.arguments or target not in self.framework.arguments:
            raise ValueError("source and target must be arguments in the framework.")

        # Backtracking DFS enumerates only simple paths by keeping every
        # vertex on the current path in `visited`. The search is finite because
        # no vertex can be added twice to one path.
        def search(current: Argument, length: int, visited: Set[Argument]) -> bool:
            neighbours = self.framework.get_attacked(current)
            for neighbour in neighbours:
                if neighbour in visited:
                    continue

                next_length = length + 1
                if neighbour == target:
                    if next_length % 2 == 1:
                        return True
                    # A path ends when it reaches the target. Continuing past
                    # the target and returning later would repeat that vertex.
                    continue

                visited.add(neighbour)
                if search(neighbour, next_length, visited):
                    return True
                visited.remove(neighbour)

            return False

        return search(source, 0, {source})

    def check_theorem_5_4(self) -> Tuple[bool, List[str]]:
        """Check Theorem 5.4's no-direct-or-indirect-defeat condition.

        For each agent, every ordered pair of distinct owned arguments is
        checked. A defeat exists exactly when a simple directed path (no
        repeated vertices or edges) of odd length connects the pair: length 1
        is direct defeat, and lengths 3, 5, ... are indirect defeat. Even
        lengths represent indirect defence and do not violate this condition.

        Since a simple path cannot repeat its starting vertex, a non-zero
        self-defeating path from an argument back to itself is not considered.
        """
        violations: List[str] = []
        for agent in self.agents:
            owned = sorted(self.agent_arguments[agent])
            for alpha in owned:
                for beta in owned:
                    if alpha == beta:
                        continue
                    if self.has_odd_length_path(alpha, beta):
                        kind = "direct defeat" if (alpha, beta) in self.framework.attacks else "indirect defeat"
                        violations.append(
                            f"Agent {agent!r}: {kind} via an odd-length simple path "
                            f"from {alpha!r} to {beta!r}."
                        )
        return not violations, violations

    def is_strategyproof(self) -> Tuple[bool, List[str]]:
        """Brute-force strategyproofness check (alias for dominant truthfulness)."""
        return self.is_truthful_dominant()


if __name__ == "__main__":
    # A compact smoke test; the dedicated test files contain the full suite.
    example = ArgumentationFramework(
        {"a", "b", "c"}, {("a", "b"), ("b", "c")}
    )
    print("Example framework:", example)
    print("Grounded extension:", example.grounded_extension())
    print("Complete extensions:", example.all_complete_extensions())
