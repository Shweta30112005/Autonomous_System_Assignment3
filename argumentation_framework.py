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

    def is_admissible_and_complete(self, arguments: Iterable[Argument]) -> Tuple[bool, bool]:
        """Check if set S is admissible and if S is a complete extension."""
        subset = self._validate_subset(arguments)
        admissible = self.is_admissible(subset)
        complete = admissible and self.characteristic_function(subset) == subset
        return admissible, complete

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

    def all_extensions(self) -> Dict[str, List[Set[Argument]]]:
        """Compute all major extensions: grounded, complete, preferred, stable, and semi-stable."""
        return {
            "grounded": [self.grounded_extension()],
            "complete": self.all_complete_extensions(),
            "preferred": self.preferred_extensions(),
            "stable": self.stable_extensions(),
            "semi_stable": self.semi_stable_extensions(),
        }

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


# ======================================================================
# Standalone Functional API for Assignment 3
# ======================================================================

def is_conflict_free(framework: ArgumentationFramework, arguments: Iterable[Argument]) -> bool:
    """Test if a given set S of arguments is conflict-free in the framework."""
    return framework.is_conflict_free(arguments)


def is_defended_by(framework: ArgumentationFramework, arg: Argument, arguments: Iterable[Argument]) -> bool:
    """Test if a given argument can be defended by a given set S in the framework."""
    return framework.is_defended_by(arg, arguments)


def characteristic_function(framework: ArgumentationFramework, arguments: Iterable[Argument]) -> Set[Argument]:
    """Characteristic function F(S): identify the set of arguments defended by set S."""
    return framework.characteristic_function(arguments)


def is_admissible(framework: ArgumentationFramework, arguments: Iterable[Argument]) -> bool:
    """Check if a given set S of arguments is admissible."""
    return framework.is_admissible(arguments)


def is_complete_extension(framework: ArgumentationFramework, arguments: Iterable[Argument]) -> bool:
    """Check if a given set S of arguments is a complete extension."""
    return framework.is_complete_extension(arguments)


def check_admissible_and_complete(
    framework: ArgumentationFramework, arguments: Iterable[Argument]
) -> Tuple[bool, bool]:
    """Check if a given set S is admissible and if it is a complete extension."""
    return framework.is_admissible_and_complete(arguments)


def grounded_extension(framework: ArgumentationFramework) -> Set[Argument]:
    """Compute the grounded extension of the given argumentation framework."""
    return framework.grounded_extension()


compute_grounded_extension = grounded_extension


def all_complete_extensions(framework: ArgumentationFramework) -> List[Set[Argument]]:
    """Compute all complete extensions of the given argumentation framework."""
    return framework.all_complete_extensions()


compute_all_complete_extensions = all_complete_extensions


def preferred_extensions(framework: ArgumentationFramework) -> List[Set[Argument]]:
    """Compute all preferred extensions of the given argumentation framework."""
    return framework.preferred_extensions()


compute_preferred_extensions = preferred_extensions


def stable_extensions(framework: ArgumentationFramework) -> List[Set[Argument]]:
    """Compute all stable extensions of the given argumentation framework."""
    return framework.stable_extensions()


compute_stable_extensions = stable_extensions


def semi_stable_extensions(framework: ArgumentationFramework) -> List[Set[Argument]]:
    """Compute all semi-stable extensions of the given argumentation framework."""
    return framework.semi_stable_extensions()


compute_semi_stable_extensions = semi_stable_extensions


def all_extensions(framework: ArgumentationFramework) -> Dict[str, List[Set[Argument]]]:
    """Compute a collection of extensions (grounded, complete, preferred, stable, semi-stable)."""
    return framework.all_extensions()


compute_all_extensions = all_extensions


def all_labellings(framework: ArgumentationFramework) -> List[Dict[Argument, Label]]:
    """Generate all legal (in/out/undec) labellings for the argumentation framework."""
    return framework.all_labellings()


generate_all_labellings = all_labellings


def acceptance_status(framework: ArgumentationFramework, arg: Argument) -> str:
    """Report acceptance status of an argument: 'skeptically accepted', 'credulously accepted', or 'rejected'."""
    return framework.acceptance_status(arg)


report_acceptance_status = acceptance_status


# Strategic Argumentation standalone functions

def grounded_direct_mechanism(
    attacks: Iterable[Attack] | ArgumentationFramework,
    revealed_arguments: Mapping[str, Iterable[Argument]],
) -> Set[Argument]:
    """Takes the global attack relation (or framework) and one revealed argument set per agent,
    and returns the grounded extension of the graph induced by the union of revealed arguments.
    """
    if isinstance(attacks, ArgumentationFramework):
        all_attacks = set(attacks.attacks)
    else:
        all_attacks = set(attacks)

    union_args: Set[Argument] = set()
    for args in revealed_arguments.values():
        union_args.update(args)

    induced_attacks = {
        (u, v) for u, v in all_attacks if u in union_args and v in union_args
    }
    af_induced = ArgumentationFramework(union_args, induced_attacks)
    return af_induced.grounded_extension()


def find_best_responses(
    framework_or_attacks: ArgumentationFramework | Iterable[Attack],
    agent: str,
    agent_arguments: Mapping[str, Iterable[Argument]],
    others_revealed: Mapping[str, Iterable[Argument]],
) -> Tuple[List[Set[Argument]], int]:
    """Enumerates every subset of A_i that agent i could reveal, given fixed reports by the others,
    and returns the reports that maximise agent i's utility and the maximum utility.
    """
    if isinstance(framework_or_attacks, ArgumentationFramework):
        fw = framework_or_attacks
    else:
        all_args = set().union(*agent_arguments.values())
        fw = ArgumentationFramework(all_args, framework_or_attacks)
    strategic = StrategicArgumentation(fw, agent_arguments)
    return strategic.best_responses(agent, others_revealed)


def check_theorem_5_3(
    framework_or_attacks: ArgumentationFramework | Iterable[Attack],
    agent_arguments: Mapping[str, Iterable[Argument]],
) -> Tuple[bool, List[str]]:
    """Check Theorem 5.3: verify if revealing all of A_i (truthfulness) is a best response
    against every combination of subsets the other agents could reveal.
    """
    if isinstance(framework_or_attacks, ArgumentationFramework):
        fw = framework_or_attacks
    else:
        all_args = set().union(*agent_arguments.values())
        fw = ArgumentationFramework(all_args, framework_or_attacks)
    strategic = StrategicArgumentation(fw, agent_arguments)
    return strategic.is_truthful_dominant()


verify_theorem_5_3 = check_theorem_5_3


def check_theorem_5_4(
    framework_or_attacks: ArgumentationFramework | Iterable[Attack],
    agent_arguments: Mapping[str, Iterable[Argument]],
) -> Tuple[bool, List[str]]:
    """Check Theorem 5.4: verify that no agent holds two arguments alpha, beta with an
    odd-length directed path from alpha to beta in the full graph.
    """
    if isinstance(framework_or_attacks, ArgumentationFramework):
        fw = framework_or_attacks
    else:
        all_args = set().union(*agent_arguments.values())
        fw = ArgumentationFramework(all_args, framework_or_attacks)
    strategic = StrategicArgumentation(fw, agent_arguments)
    return strategic.check_theorem_5_4()


verify_theorem_5_4 = check_theorem_5_4


def is_strategyproof(
    framework_or_attacks: ArgumentationFramework | Iterable[Attack],
    agent_arguments: Mapping[str, Iterable[Argument]],
) -> Tuple[bool, List[str]]:
    """Check if a grounded direct argumentation mechanism is strategyproof."""
    return check_theorem_5_3(framework_or_attacks, agent_arguments)


if __name__ == "__main__":
    # A compact smoke test; the dedicated test files contain the full suite.
    example = ArgumentationFramework(
        {"a", "b", "c"}, {("a", "b"), ("b", "c")}
    )
    print("Example framework:", example)
    print("Grounded extension:", example.grounded_extension())
    print("Complete extensions:", example.all_complete_extensions())
