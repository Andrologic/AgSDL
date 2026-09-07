#!/usr/bin/env python3
"""Focused tests for official corpus provenance and oracle checks."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("official_checker", HERE / "check-corpus.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class CorpusCheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(checker.MANIFEST.read_text())

    def test_checked_in_manifest_passes(self):
        checker.check_manifest(deepcopy(self.manifest))

    def test_rejects_fixture_hash_change(self):
        changed = deepcopy(self.manifest)
        changed["cases"][0]["primary"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "fixture hash/path"):
            checker.check_manifest(changed)

    def test_rejects_non_normative_oracle_source(self):
        changed = deepcopy(self.manifest)
        changed["cases"][0]["source"] = [{
            "document": "../../proposals/0013-modular-mvp-contract.md",
            "section": "Closed record inventory",
        }]
        with self.assertRaisesRegex(ValueError, "normative section"):
            checker.check_manifest(changed)

    def test_rejects_unbacked_coverage_variant(self):
        changed = deepcopy(self.manifest)
        case = changed["cases"][0]
        case["coverage"].append("E-LOSS:positive")
        changed["coverage"]["E-LOSS"].setdefault("positive", []).append(case["name"])
        with self.assertRaisesRegex(ValueError, "coverage lacks oracle evidence"):
            checker.check_manifest(changed)

    def test_rejects_missing_operation_family(self):
        changed = deepcopy(self.manifest)
        changed["cases"] = [case for case in changed["cases"]
                            if case["operation"] != "lossyExchange"]
        with self.assertRaisesRegex(ValueError, "seven operations"):
            checker.check_manifest(changed)

    def test_main_reports_invalid_manifest(self):
        class InvalidManifest:
            @staticmethod
            def read_text():
                return "{}"

        with patch.object(checker, "MANIFEST", InvalidManifest()):
            self.assertEqual(checker.main([]), 1)


if __name__ == "__main__":
    unittest.main()
