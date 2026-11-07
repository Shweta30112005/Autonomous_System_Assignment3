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


class TestBookExamples(unittest.TestCase):
    """Explicit verification of textbook examples and documented errata.

    From: Gerhard Weiss (ed.), Multiagent Systems (2nd ed.),
    Chapter 5: Argumentation among Agents (Iyad Rahwan & Kate Larson).
    """

    def test_example_5_10_hiding_arguments_gains_utility(self):
        """Example 5.10: Grounded direct mechanism is NOT strategyproof.

        Agent x owns {a1, a4, a5}, Agent y owns {a2}, Agent z owns {a3}.
        Attacks: a1 -> a2 -> a3 -> a4, and a3 -> a5.

        Truthful outcome: {a1, a3} -> u_x = 1 (only a1).
        Hiding a1 (reporting {a4, a5}):
          Revealed: {a2, a3, a4, a5}.
          a2 is unattacked -> a2 is IN -> a3 is OUT -> a4, a5 are IN!
          Outcome: {a2, a4, a5} -> u_x = 2!
        Agent x gains by withholding a1.

        Note on book misprint: In the original text of Example 5.10, the utilities
        were accidentally transposed between the truthful and hiding profiles.
        """
        af = ArgumentationFramework(
            {"a1", "a2", "a3", "a4", "a5"},
            {("a1", "a2"), ("a2", "a3"), ("a3", "a4"), ("a3", "a5")},
        )
        ownership = {
            "x": {"a1", "a4", "a5"},
            "y": {"a2"},
            "z": {"a3"},
        }
        sa = StrategicArgumentation(af, ownership)

        # 1. Truthful revelation
        truthful_reports = {"x": {"a1", "a4", "a5"}, "y": {"a2"}, "z": {"a3"}}
        truthful_outcome = sa.mechanism(truthful_reports)
        self.assertEqual(truthful_outcome, {"a1", "a3"})
        self.assertEqual(sa.utility("x", truthful_outcome), 1)
        self.assertEqual(sa.utility("y", truthful_outcome), 0)
        self.assertEqual(sa.utility("z", truthful_outcome), 1)

        # 2. Strategic manipulation: agent x hides a1
        hidden_reports = {"x": {"a4", "a5"}, "y": {"a2"}, "z": {"a3"}}
        hidden_outcome = sa.mechanism(hidden_reports)
        self.assertEqual(hidden_outcome, {"a2", "a4", "a5"})
        self.assertEqual(sa.utility("x", hidden_outcome), 2)  # Increased from 1 to 2!

        # 3. Strategyproofness fails
        is_sp, counterexamples = sa.is_strategyproof()
        self.assertFalse(is_sp)
        self.assertTrue(any("Agent 'x'" in ce for ce in counterexamples))

        # 4. Theorem 5.4 condition fails due to odd-length paths from a1 to a4 and a5
        thm_holds, violations = sa.check_theorem_5_4()
        self.assertFalse(thm_holds)
        self.assertTrue(any("from 'a1' to 'a4'" in v for v in violations))
        self.assertTrue(any("from 'a1' to 'a5'" in v for v in violations))

    def test_example_5_11_cancellation_of_indirect_defeat(self):
        """Example 5.11: Strategyproof despite violating Theorem 5.4 condition.

        Agent x owns {a1, a4, a5, a6}, Agent y owns {a2}, Agent z owns {a3}.
        Attacks: a1 -> a2 -> a3 -> a4, a3 -> a5, and a6 -> a3.

        Argument a6 directly attacks a3, canceling the indirect self-defeat
        of a1 on {a4, a5}. Because a6 defeats a3, a4 and a5 are always
        accepted whenever a6 is revealed, so agent x has no incentive to hide a1.

        Note on book misprint: In the text discussion following Example 5.11,
        the argument that cancels the indirect self-defeat is a6, not a5.
        """
        af = ArgumentationFramework(
            {"a1", "a2", "a3", "a4", "a5", "a6"},
            {
                ("a1", "a2"),
                ("a2", "a3"),
                ("a3", "a4"),
                ("a3", "a5"),
                ("a6", "a3"),
            },
        )
        ownership = {
            "x": {"a1", "a4", "a5", "a6"},
            "y": {"a2"},
            "z": {"a3"},
        }
        sa = StrategicArgumentation(af, ownership)

        # Truthful outcome
        truthful_outcome = sa.mechanism(ownership)
        self.assertEqual(truthful_outcome, {"a1", "a4", "a5", "a6"})
        self.assertEqual(sa.utility("x", truthful_outcome), 4)

        # Mechanism IS strategyproof!
        is_sp, counterexamples = sa.is_strategyproof()
        self.assertTrue(is_sp)
        self.assertEqual(counterexamples, [])

        # But Theorem 5.4's condition FAILS because odd paths a1 -> ... -> a4, a5 still exist
        thm_holds, violations = sa.check_theorem_5_4()
        self.assertFalse(thm_holds)
        self.assertTrue(len(violations) >= 2)


class TestStandaloneStrategicAPI(unittest.TestCase):
    def setUp(self):
        self.attacks = {("a", "b"), ("b", "c")}
        self.agent_args = {"agent1": {"a", "c"}, "agent2": {"b"}}
        self.af = ArgumentationFramework({"a", "b", "c"}, self.attacks)

    def test_standalone_mechanism(self):
        from argumentation_framework import grounded_direct_mechanism
        outcome = grounded_direct_mechanism(self.attacks, self.agent_args)
        self.assertEqual(outcome, {"a", "c"})

        # Also works when passing framework object
        outcome2 = grounded_direct_mechanism(self.af, self.agent_args)
        self.assertEqual(outcome2, {"a", "c"})

    def test_standalone_find_best_responses(self):
        from argumentation_framework import find_best_responses
        reports, utility = find_best_responses(
            self.af, "agent1", self.agent_args, {"agent2": {"b"}}
        )
        self.assertEqual(utility, 2)
        self.assertIn({"a", "c"}, reports)

    def test_standalone_check_theorems(self):
        from argumentation_framework import (
            check_theorem_5_3,
            check_theorem_5_4,
            is_strategyproof,
        )
        sp, ce = is_strategyproof(self.af, self.agent_args)
        self.assertTrue(sp)
        self.assertEqual(ce, [])

        thm53, ce53 = check_theorem_5_3(self.af, self.agent_args)
        self.assertTrue(thm53)

        thm54, v54 = check_theorem_5_4(self.af, self.agent_args)
        self.assertTrue(thm54)


if __name__ == "__main__":
    unittest.main(verbosity=2)
