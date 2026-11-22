"""Tests for the host-side run input prototype."""

import os
import sys
import unittest
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agsdl.run_input import InputError, MISSING, RunInput  # noqa: E402


class RunInputTest(unittest.TestCase):
    def assert_error(self, code, path, function, *args):
        with self.assertRaises(InputError) as caught:
            function(*args)
        self.assertEqual((caught.exception.code, caught.exception.path), (code, path))

    def test_accept_missing_null_and_schema(self):
        empty = RunInput.accept({})
        self.assertIs(empty.value, MISSING)
        self.assert_error("INPUT_INVALID", "", RunInput.accept, {}, None)
        self.assert_error("INPUT_INVALID", "", RunInput.accept, {"input": {"type": "null"}})
        self.assertIsNone(RunInput.accept({"input": {"type": "null"}}, None).value)
        schema = {"type": "object", "properties": {"a/b~c": {"type": "integer"}}}
        self.assert_error("INPUT_INVALID", "/a~1b~0c", RunInput.accept,
                          {"input": schema}, {"a/b~c": False})
        self.assert_error("INPUT_INVALID", "/extra/0", RunInput.accept,
                          {"input": schema}, {"extra": [float("nan")]})

    def test_snapshot_and_output_are_isolated(self):
        original = {"items": [{"name": "one"}]}
        snapshot = RunInput.accept({"input": {"type": "object"}}, original)
        original["items"][0]["name"] = "changed"
        value = snapshot.value
        value["items"].clear()
        selected = snapshot.select(["items", 0])
        selected["name"] = "changed"
        self.assertEqual(snapshot.select(["items", Decimal("0.0")]), {"name": "one"})

    def test_selection_boundaries(self):
        snapshot = RunInput.accept({"input": {"type": "object"}},
                                   {"a/b": [None], "0": "key"})
        self.assertEqual(snapshot.select(["0"]), "key")
        for path, error_path in [(["a/b", -1], "/a~1b/-1"),
                                 (["a/b", 1], "/a~1b/1"),
                                 (["a/b", True], "/a~1b/True"),
                                 (["a/b", "0"], "/a~1b/0"),
                                 (["a/b", Decimal("0.5")], "/a~1b/0.5"),
                                 (["missing"], "/missing"),
                                 (["a/b", 0, "x"], "/a~1b/0/x")]:
            with self.subTest(path=path):
                self.assert_error("OPERAND", error_path, snapshot.select, path)
        self.assert_error("OPERAND", "", RunInput.accept({}).select, [])

    def test_arguments_and_resources_are_separate(self):
        snapshot = RunInput.accept({"input": {"type": "object"}}, {"x": [1]})
        literal = {"input": ["not a reference"]}
        arguments = {"typed": {"input": ["x"]}, "prior": {"path": ["x"]},
                     "literal": {"value": literal}}
        result = snapshot.resolve_arguments(arguments, {"x": [2]})
        self.assertEqual(result, {"typed": [1], "prior": [2], "literal": literal})
        result["typed"].append(3)
        result["literal"]["input"].clear()
        self.assertEqual(snapshot.select(["x"]), [1])
        self.assertEqual(literal, {"input": ["not a reference"]})
        self.assert_error("OPERAND", "/x", snapshot.resolve_arguments, {"a": {"path": ["x"]}})
        self.assertIsNone(snapshot.resolve_arguments({"a": {"path": []}}, None)["a"])
        resources = {"typed": {"input": ["x"]}, "custom": {"input": [], "mediaType": "text/plain"},
                     "ordinary": {"uri": "file.txt"}}
        bound = snapshot.bind_resources(resources)
        self.assertEqual(bound, {"typed": {"value": [1], "mediaType": "application/json"},
                                 "custom": {"value": {"x": [1]}, "mediaType": "text/plain"},
                                 "ordinary": {"uri": "file.txt"}})
        bound["typed"]["value"].append(4)
        bound["ordinary"]["uri"] = "other"
        self.assertEqual(snapshot.select(["x"]), [1])
        self.assertEqual(resources["ordinary"]["uri"], "file.txt")

    def test_missing_optional_field_reports_the_input_resource(self):
        flow = {"input": {"type": "object", "properties": {"city": {"type": "string"}}}}
        snapshot = RunInput.accept(flow, {})
        with self.assertRaises(InputError) as caught:
            snapshot.bind_resources({"requestedCity": {"input": ["city"]}})
        self.assertEqual((caught.exception.code, caught.exception.path), ("OPERAND", "/city"))
        self.assertIn("run input for resource 'requestedCity'", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
