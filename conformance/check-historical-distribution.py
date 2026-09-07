#!/usr/bin/env python3
"""Run unchanged modular checks against distributed files, without Git evidence.

The historical checker couples three `git show` reads to its structural checks.
This adapter supplies those three distributed files through a module-local
subprocess interface. It does not claim to verify the historical revisions.
All digest comparisons and all historical regression tests still execute.
"""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest

sys.dont_write_bytecode = True
REPOSITORY = Path(__file__).resolve().parent.parent
MODULAR = REPOSITORY / "experimental/modular-candidate-1"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def distribution_interface():
    manifest = json.loads((MODULAR / "fixtures/manifest.json").read_text())
    paths = {
        manifest["contractBase"] + ":proposals/0013-modular-mvp-contract.md":
            "proposals/0013-modular-mvp-contract.md",
        manifest["inheritedContract"]["base"] + ":proposals/0012-minimal-0.1.0-contract.md":
            "proposals/0012-minimal-0.1.0-contract.md",
        manifest["contractBase"] + ":experimental/modular-candidate-1/schemas/modular.schema.json":
            "experimental/modular-candidate-1/schemas/modular.schema.json",
    }

    def read_distribution(command, *, check, stdout):
        if (len(command) != 3 or command[:2] != ["git", "show"] or
                command[2] not in paths or check is not True or stdout != subprocess.PIPE):
            raise ValueError("unsupported historical distribution read")
        return SimpleNamespace(stdout=(REPOSITORY / paths[command[2]]).read_bytes())

    return SimpleNamespace(run=read_distribution, PIPE=subprocess.PIPE,
                           CalledProcessError=subprocess.CalledProcessError)


def main():
    print("Modular distribution checks; historical Git provenance omitted.", flush=True)
    if sys.argv[1:] == ["--tests"]:
        tests = load("historical_distribution_tests", MODULAR / "test_check_fixtures.py")
        tests.checker.subprocess = distribution_interface()
        suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1
    if sys.argv[1:]:
        raise ValueError("expected no arguments or --tests")
    checker = load("historical_distribution_checker", MODULAR / "check-fixtures.py")
    checker.subprocess = distribution_interface()
    return checker.main([])


if __name__ == "__main__":
    raise SystemExit(main())
