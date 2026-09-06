#!/usr/bin/env python3
"""Regression tests for modular corpus metadata and coverage checks."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("modular_checker", HERE / "check-fixtures.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
BUILDER_SPEC = importlib.util.spec_from_file_location("modular_builder", HERE / "fixtures" / "build-fixtures.py")
builder = importlib.util.module_from_spec(BUILDER_SPEC)
BUILDER_SPEC.loader.exec_module(builder)


class CorpusCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(checker.MANIFEST.read_text())

    def test_reviewed_manifest_passes(self):
        checker.check_manifest(deepcopy(self.manifest))

    def test_contract_digest_is_a_pin(self):
        changed = deepcopy(self.manifest)
        changed["contractSha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "proposal 0013 bytes changed"):
            checker.check_manifest(changed)

    def test_reverse_coverage_index_is_required(self):
        changed = deepcopy(self.manifest)
        changed["coverage"]["G-TARGET"]["positive"] = []
        with self.assertRaises(ValueError):
            checker.check_manifest(changed)

    def test_minimum_scenario_cannot_disappear(self):
        changed = deepcopy(self.manifest)
        target = next(case for case in changed["cases"] if "approval-call-invalid" in case["scenarios"])
        target["scenarios"] = ["coverage-remains-nonempty"]
        changed["requiredScenarios"].remove("approval-call-invalid")
        changed["requiredScenarios"].append("coverage-remains-nonempty")
        with self.assertRaisesRegex(ValueError, "minimum scenario missing"):
            checker.check_manifest(changed)

    def test_result_oracle_domains_are_closed(self):
        changed = deepcopy(self.manifest)
        changed["cases"][0]["expected"]["results"][-1]["verdict"] = "invented-verdict"
        with self.assertRaisesRegex(ValueError, "Result verdict"):
            checker.check_manifest(changed)

    def test_assessment_detail_and_state_are_coupled(self):
        changed = deepcopy(self.manifest)
        target = next(case for case in changed["cases"] if case["name"] == "modular-two-configurations")
        target["expected"]["states"][1]["state"] = "declared"
        with self.assertRaisesRegex(ValueError, "assessment detail/state mismatch"):
            checker.check_manifest(changed)

    def test_absent_state_oracle_is_closed(self):
        changed = deepcopy(self.manifest)
        changed["cases"][0]["expected"]["absentStates"] = [{"garbage": True}]
        with self.assertRaises(ValueError):
            checker.check_manifest(changed)

    def test_rule_must_belong_to_result_unit(self):
        changed = deepcopy(self.manifest)
        target = next(case for case in changed["cases"] if case["name"] == "selection-unknown")
        target["expected"]["findings"]["items"][0]["unit"] = "D"
        with self.assertRaisesRegex(ValueError, "finding oracle"):
            checker.check_manifest(changed)

    def test_builder_checks_pins_before_writing(self):
        with patch.object(builder, "CONTRACT_SHA256", "0" * 64), \
             patch.object(builder.Path, "write_bytes", side_effect=AssertionError("write before pin check")), \
             patch.object(builder.Path, "write_text", side_effect=AssertionError("write before pin check")):
            with self.assertRaisesRegex(RuntimeError, "proposal 0013 changed"):
                builder.main()


if __name__ == "__main__":
    unittest.main()
