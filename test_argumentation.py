"""Automated tests for the Dung-style argumentation framework.

Run from the project directory with:
    python -m unittest -v test_argumentation

The expected results below are calculated for the explicitly defined AFs;
sets are compared without relying on their display order.
"""

import unittest

from argumentation_framework import ArgumentationFramework


class TestFrameworkConstruction(unittest.TestCase):
    def test_empty_framework_is_valid(self):
        af = ArgumentationFramework()
        self.assertEqual(af.arguments, set())
        self.assertEqual(af.attacks, set())
        self.assertEqual(af.grounded_extension(), set())
        self.assertEqual(af.all_complete_extensions(), [set()])
        self.assertEqual(af.preferred_extensions(), [set()])
        self.assertEqual(af.stable_extensions(), [set()])
        self.assertEqual(af.semi_stable_extensions(), [set()])
        self.assertEqual(af.all_labellings(), [{}])

    def test_constructor_rejects_attack_with_unknown_endpoint(self):
        with self.assertRaises(ValueError):
            ArgumentationFramework({"a"}, {("a", "b")})

    def test_add_attack_adds_missing_endpoints(self):
        af = ArgumentationFramework()
        af.add_attack("a", "b")
        self.assertEqual(af.arguments, {"a", "b"})
        self.assertEqual(af.attacks, {("a", "b")})

    def test_invalid_argument_name_is_rejected(self):
        with self.assertRaises(ValueError):
            ArgumentationFramework({""}, set())

    def test_unknown_argument_in_subset_is_rejected(self):
        af = ArgumentationFramework({"a"}, set())
        with self.assertRaises(ValueError):
            af.is_conflict_free({"missing"})


class TestBasicSemantics(unittest.TestCase):
    def setUp(self):
        self.chain = ArgumentationFramework(
            {"a", "b", "c"}, {("a", "b"), ("b", "c")}
        )

    def test_attackers_and_attacked_arguments(self):
        self.assertEqual(self.chain.get_attackers("b"), {"a"})
        self.assertEqual(self.chain.get_attackers("a"), set())
        self.assertEqual(self.chain.get_attacked("a"), {"b"})
        self.assertEqual(self.chain.get_attacked("c"), set())

    def test_conflict_free_sets(self):
        self.assertFalse(self.chain.is_conflict_free({"a", "b"}))
        self.assertFalse(self.chain.is_conflict_free({"b", "c"}))
        self.assertTrue(self.chain.is_conflict_free({"a", "c"}))
        self.assertTrue(self.chain.is_conflict_free(set()))
        self.assertTrue(self.chain.is_conflict_free({"a"}))

    def test_defence(self):
        self.assertTrue(self.chain.is_defended_by("c", {"a"}))
        self.assertFalse(self.chain.is_defended_by("c", {"b"}))
        # An unattacked argument is defended vacuously by the empty set.
        self.assertTrue(self.chain.is_defended_by("a", set()))

    def test_characteristic_function(self):
        self.assertEqual(self.chain.characteristic_function(set()), {"a"})
        self.assertEqual(self.chain.characteristic_function({"a"}), {"a", "c"})
        self.assertEqual(
            self.chain.characteristic_function({"a", "c"}), {"a", "c"}
        )

    def test_admissible_and_complete(self):
        self.assertTrue(self.chain.is_admissible({"a", "c"}))
        self.assertTrue(self.chain.is_complete_extension({"a", "c"}))
        self.assertTrue(self.chain.is_admissible({"a"}))
        self.assertFalse(self.chain.is_complete_extension({"a"}))
        self.assertFalse(self.chain.is_admissible({"a", "b"}))

    def test_grounded_and_other_extensions_for_chain(self):
        expected = [{"a", "c"}]
        self.assertEqual(self.chain.grounded_extension(), {"a", "c"})
        self.assertEqual(self.chain.all_complete_extensions(), expected)
        self.assertEqual(self.chain.preferred_extensions(), expected)
        self.assertEqual(self.chain.stable_extensions(), expected)
        self.assertEqual(self.chain.semi_stable_extensions(), expected)

    def test_complete_labelling_for_chain(self):
        self.assertEqual(
            self.chain.all_labellings(),
            [{"a": "in", "b": "out", "c": "in"}],
        )
        self.assertEqual(
            self.chain.labelling_to_extension(
                {"a": "in", "b": "out", "c": "in"}
            ),
            {"a", "c"},
        )


class TestStandardExamples(unittest.TestCase):
    def test_mutual_attack(self):
        af = ArgumentationFramework(
            {"a", "b"}, {("a", "b"), ("b", "a")}
        )
        self.assertEqual(af.grounded_extension(), set())
        self.assertEqual(af.all_complete_extensions(), [set(), {"a"}, {"b"}])
        self.assertEqual(af.preferred_extensions(), [{"a"}, {"b"}])
        self.assertEqual(af.stable_extensions(), [{"a"}, {"b"}])
        self.assertEqual(af.semi_stable_extensions(), [{"a"}, {"b"}])
        self.assertCountEqual(
            af.all_labellings(),
            [
                {"a": "in", "b": "out"},
                {"a": "out", "b": "in"},
                {"a": "undec", "b": "undec"},
            ],
        )

    def test_odd_three_cycle(self):
        af = ArgumentationFramework(
            {"a", "b", "c"},
            {("a", "b"), ("b", "c"), ("c", "a")},
        )
        self.assertEqual(af.grounded_extension(), set())
        self.assertEqual(af.all_complete_extensions(), [set()])
        self.assertEqual(af.preferred_extensions(), [set()])
        self.assertEqual(af.stable_extensions(), [])
        self.assertEqual(af.semi_stable_extensions(), [set()])
        self.assertEqual(
            af.all_labellings(),
            [{"a": "undec", "b": "undec", "c": "undec"}],
        )

    def test_diamond_framework(self):
        # d attacks a and c; a and c both attack b.
        af = ArgumentationFramework(
            {"a", "b", "c", "d"},
            {("a", "b"), ("c", "b"), ("d", "a"), ("d", "c")},
        )
        expected = [{"b", "d"}]
        self.assertEqual(af.grounded_extension(), {"b", "d"})
        self.assertEqual(af.all_complete_extensions(), expected)
        self.assertEqual(af.preferred_extensions(), expected)
        self.assertEqual(af.stable_extensions(), expected)
        self.assertEqual(af.semi_stable_extensions(), expected)

    def test_reinstatement_example(self):
        af = ArgumentationFramework(
            {"a", "b", "c", "d"},
            {("a", "b"), ("b", "c"), ("d", "b")},
        )
        expected = {"a", "c", "d"}
        self.assertTrue(af.is_defended_by("c", {"a", "d"}))
        self.assertEqual(af.characteristic_function({"a", "d"}), expected)
        self.assertEqual(af.grounded_extension(), expected)
        self.assertEqual(af.preferred_extensions(), [expected])
        self.assertEqual(af.stable_extensions(), [expected])

    def test_self_attacking_argument(self):
        af = ArgumentationFramework(
            {"a", "b"}, {("a", "a"), ("b", "a")}
        )
        self.assertFalse(af.is_conflict_free({"a"}))
        self.assertTrue(af.is_conflict_free({"b"}))
        self.assertEqual(af.grounded_extension(), {"b"})
        self.assertEqual(af.all_complete_extensions(), [{"b"}])
        self.assertEqual(af.stable_extensions(), [{"b"}])

    def test_larger_framework(self):
        af = ArgumentationFramework(
            {"a", "b", "c", "d", "e"},
            {
                ("a", "b"),
                ("b", "c"),
                ("c", "d"),
                ("d", "e"),
                ("e", "c"),
            },
        )
        self.assertEqual(af.grounded_extension(), {"a"})
        self.assertEqual(af.all_complete_extensions(), [{"a"}])
        self.assertEqual(af.preferred_extensions(), [{"a"}])
        self.assertEqual(af.stable_extensions(), [])
        self.assertEqual(af.semi_stable_extensions(), [{"a"}])

    def test_floating_defeat(self):
        af = ArgumentationFramework(
            {"a", "b", "c"},
            {("a", "b"), ("b", "a"), ("b", "c")},
        )
        self.assertEqual(af.grounded_extension(), set())
        self.assertEqual(
            af.all_complete_extensions(), [set(), {"b"}, {"a", "c"}]
        )
        self.assertEqual(af.preferred_extensions(), [{"b"}, {"a", "c"}])
        self.assertEqual(af.stable_extensions(), [{"b"}, {"a", "c"}])


class TestAcceptanceAndLabellingValidation(unittest.TestCase):
    def test_acceptance_status_uses_preferred_semantics(self):
        af = ArgumentationFramework(
            {"a", "b"}, {("a", "b"), ("b", "a")}
        )
        self.assertEqual(af.acceptance_status("a"), "credulously accepted")
        self.assertEqual(af.acceptance_status("b"), "credulously accepted")

        chain = ArgumentationFramework(
            {"a", "b", "c"}, {("a", "b"), ("b", "c")}
        )
        self.assertEqual(chain.acceptance_status("a"), "skeptically accepted")
        self.assertEqual(chain.acceptance_status("c"), "skeptically accepted")
        self.assertEqual(chain.acceptance_status("b"), "rejected")

    def test_unknown_argument_acceptance_raises(self):
        af = ArgumentationFramework({"a"}, set())
        with self.assertRaises(ValueError):
            af.acceptance_status("unknown")

    def test_invalid_labelling_is_rejected(self):
        af = ArgumentationFramework({"a", "b"}, {("a", "b")})
        with self.assertRaises(ValueError):
            af.labelling_to_extension({"a": "in", "b": "in"})
        with self.assertRaises(ValueError):
            af.labelling_to_extension({"a": "in"})
        with self.assertRaises(ValueError):
            af.labelling_to_extension({"a": "in", "b": "maybe"})

    def test_subframework_keeps_only_internal_attacks(self):
        af = ArgumentationFramework(
            {"a", "b", "c"}, {("a", "b"), ("b", "c"), ("c", "a")}
        )
        sub = af.subframework({"a", "b"})
        self.assertEqual(sub.arguments, {"a", "b"})
        self.assertEqual(sub.attacks, {("a", "b")})


class TestStandaloneFunctionalAPI(unittest.TestCase):
    def setUp(self):
        self.af = ArgumentationFramework(
            {"a", "b", "c"}, {("a", "b"), ("b", "c")}
        )

    def test_all_extensions_dictionary(self):
        exts = self.af.all_extensions()
        self.assertIn("grounded", exts)
        self.assertIn("complete", exts)
        self.assertIn("preferred", exts)
        self.assertIn("stable", exts)
        self.assertIn("semi_stable", exts)
        self.assertEqual(exts["grounded"], [{"a", "c"}])
        self.assertEqual(exts["complete"], [{"a", "c"}])
        self.assertEqual(exts["preferred"], [{"a", "c"}])
        self.assertEqual(exts["stable"], [{"a", "c"}])
        self.assertEqual(exts["semi_stable"], [{"a", "c"}])

    def test_admissible_and_complete_tuple(self):
        admissible, complete = self.af.is_admissible_and_complete({"a"})
        self.assertTrue(admissible)
        self.assertFalse(complete)

        admissible2, complete2 = self.af.is_admissible_and_complete({"a", "c"})
        self.assertTrue(admissible2)
        self.assertTrue(complete2)

    def test_standalone_functions_match_class_methods(self):
        import argumentation_framework as af_mod

        self.assertTrue(af_mod.is_conflict_free(self.af, {"a", "c"}))
        self.assertFalse(af_mod.is_conflict_free(self.af, {"a", "b"}))
        self.assertTrue(af_mod.is_defended_by(self.af, "c", {"a"}))
        self.assertEqual(af_mod.characteristic_function(self.af, {"a"}), {"a", "c"})
        self.assertTrue(af_mod.is_admissible(self.af, {"a", "c"}))
        self.assertTrue(af_mod.is_complete_extension(self.af, {"a", "c"}))
        self.assertEqual(
            af_mod.check_admissible_and_complete(self.af, {"a", "c"}),
            (True, True)
        )
        self.assertEqual(af_mod.grounded_extension(self.af), {"a", "c"})
        self.assertEqual(af_mod.all_complete_extensions(self.af), [{"a", "c"}])
        self.assertEqual(af_mod.preferred_extensions(self.af), [{"a", "c"}])
        self.assertEqual(af_mod.stable_extensions(self.af), [{"a", "c"}])
        self.assertEqual(af_mod.semi_stable_extensions(self.af), [{"a", "c"}])
        self.assertEqual(af_mod.all_extensions(self.af), self.af.all_extensions())
        self.assertEqual(af_mod.all_labellings(self.af), self.af.all_labellings())
        self.assertEqual(af_mod.acceptance_status(self.af, "a"), "skeptically accepted")
        self.assertEqual(af_mod.acceptance_status(self.af, "b"), "rejected")


if __name__ == "__main__":
    unittest.main(verbosity=2)
