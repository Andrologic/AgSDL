#!/usr/bin/env python3
"""Focused tests for lossless official fixture derivation."""

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("official_builder", HERE / "build-corpus.py")
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


class CorpusBuilderTests(unittest.TestCase):
    def test_regeneration_preserves_native_oracle_bytes_and_historical_cases(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary) / "repository"
            shutil.copytree(HERE.parent, repository,
                            ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__"))
            fixtures = repository / "conformance/fixtures"
            original = json.loads((fixtures / "manifest.json").read_text())
            native_file = fixtures / "official/additional.cases.json"
            native = json.loads((fixtures / "official/minimal.cases.json").read_text())
            native_hash = native[0]["primary"]["sha256"]
            native[0]["name"] = "official-additional-empty-system"
            native_file.write_text(json.dumps(native, indent=4) + "\n")
            before = {p.relative_to(fixtures): p.read_bytes()
                      for p in fixtures.rglob("*") if p.is_file() and p.name != "manifest.json"}
            current_spec = repository / "spec/README.md"
            current_spec.write_text(current_spec.read_text() + "\n")
            command = [sys.executable, "-B", "conformance/build-corpus.py"]
            result = subprocess.run(command, cwd=repository, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            generated = json.loads((fixtures / "manifest.json").read_text())
            self.assertEqual(generated["cases"][:137], original["cases"][:137])
            self.assertIn(native[0], generated["cases"])
            self.assertNotEqual(generated["normativeSources"]["spec/README.md"],
                                original["normativeSources"]["spec/README.md"])
            self.assertEqual(before, {p.relative_to(fixtures): p.read_bytes()
                             for p in fixtures.rglob("*")
                             if p.is_file() and p.name != "manifest.json"})
            self.assertEqual(generated["historicalNormativeSources"],
                             original["historicalNormativeSources"])
            saved_manifest = (fixtures / "manifest.json").read_bytes()
            native[0]["primary"]["sha256"] = "0" * 64
            native_file.write_text(json.dumps(native))
            result = subprocess.run(command, cwd=repository, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("fixture hash/path", result.stderr)
            self.assertEqual((fixtures / "manifest.json").read_bytes(), saved_manifest)
            native[0]["primary"]["sha256"] = native_hash
            native[0]["derivation"]["historicalCase"] = "invented"
            native_file.write_text(json.dumps(native))
            result = subprocess.run(command, cwd=repository, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("closed fields", result.stderr)
            self.assertEqual((fixtures / "manifest.json").read_bytes(), saved_manifest)

    def test_syntax_failure_bytes_are_untouched(self):
        raw = b'{"contract":"proposal-0012-candidate-2","x":1,"x":2}'
        self.assertEqual(builder.convert_document(raw, "validateD", True), raw)

    def test_graph_conversion_preserves_unrelated_number_lexemes(self):
        document = {
            "contract": "proposal-0012-candidate-2",
            "definitions": [{
                "kind": "Interface",
                "payload": {"inputs": {}, "outputs": {}, "action": {"scope": "s", "id": "a", "version": "1"}},
            }],
            "graphs": [{"steps": [
                {"id": "call", "kind": "invoke"},
                {"id": "gate", "kind": "approval", "approved": "call"},
            ]}],
            "annotations": [1e999999, 9007199254740993123456789, 0.100000000000000000001],
        }
        raw = json.dumps(document, separators=(",", ":")).encode()
        raw = raw.replace(b"Infinity", b"1e999999")
        raw = raw.replace(b"0.1", b"0.100000000000000000001")
        converted = builder.convert_document(raw, "validateG")
        self.assertIn(b"1e999999", converted)
        self.assertIn(b"9007199254740993123456789", converted)
        self.assertIn(b"0.100000000000000000001", converted)
        parsed = json.loads(converted)
        self.assertEqual(parsed["contract"], builder.OFFICIAL)
        self.assertEqual(parsed["definitions"][0]["payload"]["operations"][0]["id"], "default")
        self.assertEqual(parsed["graphs"][0]["steps"][0]["operation"], "default")
        self.assertEqual(parsed["graphs"][0]["steps"][1]["call"], "call")

    def test_existing_modular_graph_fields_are_retained(self):
        raw = b'{"contract":"proposal-0013-candidate-1","definitions":[],"graphs":[{"steps":[{"kind":"invoke","operation":"ask"},{"kind":"approval","approved":"next","call":"call"}]}]}'
        parsed = json.loads(builder.convert_document(raw, "validateG"))
        self.assertEqual(parsed["graphs"][0]["steps"][0]["operation"], "ask")
        self.assertEqual(parsed["graphs"][0]["steps"][1]["call"], "call")

    def test_dependency_hash_edit_changes_only_the_value(self):
        old = "0" * 64
        new = "1" * 64
        raw = ('{"dependencies":[{"sha256":"' + old + '"}],"n":1e999999}').encode()
        converted = builder.replace_dependency_hash(raw, 0, new)
        self.assertEqual(converted, raw.replace(old.encode(), new.encode()))


if __name__ == "__main__":
    unittest.main()
