"""Unit tests for the strategic argumentation mechanism.

Run with:
    python -m unittest -v test_strategic

The tests use the grounded direct argumentation mechanism. Theorem 5.4's
path condition uses simple directed paths: vertices and edges cannot repeat.
"""

import unittest

from argumentation_framework import ArgumentationFramework, StrategicArgumentation


class TestStrategicMechanism(unittest.TestCase):
    def setUp(self):
        # a -> b -> c. The grounded extension of the full framework is {a, c}.
        self.framework = ArgumentationFramework(
            {"a", "b", "c"}, {("a", "b"), ("b", "c")}
        )
        self.mechanism = StrategicArgumentation(
            self.framework, {"Agent1": {"a", "c"}, "Agent2": {"b"}}
        )

    def test_truthful_reports_produce_grounded_extension(self):
        outcome = self.mechanism.mechanism(
            {"Agent1": {"a", "c"}, "Agent2": {"b"}}
        )
        self.assertEqual(outcome, {"a", "c"})

    def test_reports_induce_only_the_revealed_subframework(self):
        outcome = self.mechanism.mechanism(
            {"Agent1": {"a"}, "Agent2": set()}
        )
        self.assertEqual(outcome, {"a"})

    def test_empty_reports_produce_empty_outcome(self):
        outcome = self.mechanism.mechanism(
            {"Agent1": set(), "Agent2": set()}
        )
        self.assertEqual(outcome, set())

    def test_utility_counts_owned_arguments_in_outcome(self):
        self.assertEqual(self.mechanism.utility("Agent1", {"a", "c"}), 2)
        self.assertEqual(self.mechanism.utility("Agent2", {"a", "c"}), 0)

    def test_unknown_agent_utility_raises(self):
        with self.assertRaises(ValueError):
            self.mechanism.utility("Agent3", set())

    def test_missing_report_key_raises(self):
        with self.assertRaises(ValueError):
            self.mechanism.mechanism({"Agent1": {"a", "c"}})

    def test_extra_report_key_raises(self):
        with self.assertRaises(ValueError):
            self.mechanism.mechanism(
                {"Agent1": {"a", "c"}, "Agent2": {"b"}, "Agent3": set()}
            )

    def test_agent_cannot_report_another_agents_argument(self):
        with self.assertRaises(ValueError):
            self.mechanism.mechanism(
                {"Agent1": {"a", "b"}, "Agent2": set()}
            )

    def test_unknown_argument_in_report_raises(self):
        with self.assertRaises(ValueError):
            self.mechanism.mechanism(
                {"Agent1": {"a", "c", "z"}, "Agent2": set()}
            )

    def test_best_response_returns_all_utility_maximising_reports(self):
        best_reports, best_utility = self.mechanism.best_responses(
            "Agent1", {"Agent2": {"b"}}
        )
        self.assertTrue(best_reports)
        self.assertEqual(best_utility, 2)
        self.assertIn({"a", "c"}, best_reports)

    def test_best_response_uses_only_other_agents_reports(self):
        with self.assertRaises(ValueError):
            self.mechanism.best_responses(
                "Agent1", {"Agent1": {"a", "c"}, "Agent2": {"b"}}
            )

    def test_truthful_dominance_result_matches_bruteforce_best_responses(self):
        # Independently enumerate every other-agent report profile and compare
        # truthful utility with the maximum utility over all own reports.
        expected = True
        for agent in self.mechanism.agents:
            others = [name for name in self.mechanism.agents if name != agent]
            other_report_spaces = [
                list(self.mechanism._subsets(self.mechanism.agent_arguments[name]))
                for name in others
            ]
            from itertools import product
            profiles = product(*other_report_spaces) if other_report_spaces else [()]
            for profile in profiles:
                other_reports = dict(zip(others, profile))
                truthful = dict(other_reports)
                truthful[agent] = set(self.mechanism.agent_arguments[agent])
                truthful_utility = self.mechanism.utility(
                    agent, self.mechanism.mechanism(truthful)
                )
                best_reports, best_utility = self.mechanism.best_responses(
                    agent, other_reports
                )
                self.assertTrue(best_reports)
                self.assertGreaterEqual(best_utility, truthful_utility)
                if best_utility > truthful_utility:
                    expected = False
        result, counterexamples = self.mechanism.is_truthful_dominant()
        self.assertEqual(result, expected)
        self.assertEqual(result, not bool(counterexamples))

    def test_strategyproof_alias_matches_truthful_dominance(self):
        self.assertEqual(
            self.mechanism.is_strategyproof(),
            self.mechanism.is_truthful_dominant(),
        )


class TestStrategicValidation(unittest.TestCase):
    def test_empty_agent_mapping_is_rejected(self):
        af = ArgumentationFramework({"a"}, set())
        with self.assertRaises(ValueError):
            StrategicArgumentation(af, {})

    def test_unassigned_argument_is_rejected(self):
        af = ArgumentationFramework({"a", "b"}, set())
        with self.assertRaises(ValueError):
            StrategicArgumentation(af, {"Agent1": {"a"}})

    def test_duplicate_ownership_is_rejected(self):
        af = ArgumentationFramework({"a"}, set())
        with self.assertRaises(ValueError):
            StrategicArgumentation(af, {"Agent1": {"a"}, "Agent2": {"a"}})

    def test_unknown_owned_argument_is_rejected(self):
        af = ArgumentationFramework({"a"}, set())
        with self.assertRaises(ValueError):
            StrategicArgumentation(af, {"Agent1": {"z"}})


class TestTheorem54PathCondition(unittest.TestCase):
    def setUp(self):
        # Directed chain a -> b -> c -> d.
        af = ArgumentationFramework(
            {"a", "b", "c", "d"},
            {("a", "b"), ("b", "c"), ("c", "d")},
        )
        self.chain = StrategicArgumentation(
            af, {"Agent1": {"a", "b", "c", "d"}}
        )

    def test_odd_length_paths_are_detected(self):
        self.assertTrue(self.chain.has_odd_length_path("a", "b"))
        self.assertTrue(self.chain.has_odd_length_path("a", "d"))

    def test_even_length_paths_are_not_reported_as_odd(self):
        self.assertFalse(self.chain.has_odd_length_path("a", "c"))
        self.assertFalse(self.chain.has_odd_length_path("b", "d"))

    def test_zero_length_path_is_not_odd(self):
        self.assertFalse(self.chain.has_odd_length_path("a", "a"))

    def test_unknown_path_endpoint_raises(self):
        with self.assertRaises(ValueError):
            self.chain.has_odd_length_path("a", "unknown")

    def test_theorem_condition_reports_same_agent_odd_paths(self):
        holds, violations = self.chain.check_theorem_5_4()
        self.assertFalse(holds)
        self.assertTrue(violations)
        self.assertTrue(any("'a'" in item and "'b'" in item for item in violations))

    def test_theorem_condition_holds_when_agents_own_separate_path_vertices(self):
        af = ArgumentationFramework(
            {"a", "b", "c"}, {("a", "b"), ("b", "c")}
        )
        strategic = StrategicArgumentation(
            af, {"Agent1": {"a", "c"}, "Agent2": {"b"}}
        )
        holds, violations = strategic.check_theorem_5_4()
        self.assertTrue(holds)
        self.assertEqual(violations, [])

    def test_cycle_does_not_create_a_path_by_revisiting_vertices(self):
        # In this directed 3-cycle, the only simple path from a to c is
        # a -> b -> c (length 2). A longer odd walk would have to revisit
        # vertices, so it must not count as an odd-length path.
        af = ArgumentationFramework(
            {"a", "b", "c"},
            {( "a", "b"), ("b", "c"), ("c", "a")},
        )
        strategic = StrategicArgumentation(
            af, {"Agent1": {"a", "c"}, "Agent2": {"b"}}
        )
        self.assertFalse(strategic.has_odd_length_path("a", "c"))
        self.assertFalse(strategic.has_odd_length_path("a", "a"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
