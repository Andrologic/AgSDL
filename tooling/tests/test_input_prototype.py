"""Exercise the venue fixture through the prototype host API and command."""

from contextlib import redirect_stderr, redirect_stdout
from decimal import Decimal
from io import StringIO
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

TOOLING = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLING))

from agsdl import jsoninput
from agsdl.input_prototype import json_text, main
from agsdl.run_input import RunInput


class VenueInputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = TOOLING.parent / "conformance/prototypes/venue-input.json"
        cls.cases = jsoninput.load(fixture)
        cls.document = fixture.parent / cls.cases["document"]
        cls.flow = jsoninput.load(cls.document)["flow"]

    def command(self, command, *options):
        output = StringIO()
        with redirect_stdout(output):
            status = main([command, str(self.document), *options])
        return status, jsoninput.parse_bytes(output.getvalue().encode())

    def test_one_snapshot_from_entry_to_record(self):
        expected = self.cases["accepted"]
        status, report = self.command("check")
        self.assertEqual(status, 0, report)
        snapshot = RunInput.accept(self.flow, expected["input"])
        lookup = self.flow["steps"][self.flow["entry"]]
        self.assertEqual(snapshot.resolve_arguments(lookup["arguments"]), expected["lookupArguments"])
        route = lookup["next"]["passed"]
        resources = snapshot.bind_resources(route["message"]["resources"])
        self.assertEqual(resources["requestedCity"], expected["requestedCityResource"])
        self.assertEqual(resources["quotes"], {"from": ["data"]})
        # Resume from the saved launch value after the reviewer has finished.
        saved = json_text(snapshot.value).encode()
        resumed = RunInput.accept(self.flow, jsoninput.parse_bytes(saved))
        record = self.flow["steps"][self.flow["steps"][route["step"]]["next"]]
        self.assertEqual(resumed.resolve_arguments(record["arguments"], expected["compareOutput"]),
                         expected["recordArguments"])

    def test_preview_cli(self):
        status, response = self.command("preview", "--input", '{"city":"Paris"}', "--call", "record",
                                        "--previous", '{"results":{"city":"Lyon"}}')
        self.assertEqual((status, response), (0, {"launch": "accepted",
                                                  "arguments": self.cases["accepted"]["recordArguments"]}))

    def test_preview_preserves_exact_json_numbers(self):
        value = {"arguments": {"amount": [Decimal("12345678901234567890.123456789")]}}
        self.assertEqual(jsoninput.parse_bytes(json_text(value).encode()), value)

    def test_preview_identifies_missing_or_malformed_samples(self):
        for options, hint in [
            (["--input", '{"city":"Paris"}', "--call", "record"], "--previous"),
            (["--input", "{"], "--input"),
            (["--call", "record", "--previous", "{"], "--previous"),
        ]:
            with self.subTest(options=options):
                errors = StringIO()
                with redirect_stderr(errors), self.assertRaises(SystemExit) as caught:
                    self.command("preview", *options)
                self.assertEqual(caught.exception.code, 2)
                self.assertIn(hint, errors.getvalue().splitlines()[-1])

    def test_accepted_launch_with_incomplete_previous_output(self):
        status, response = self.command("preview", "--input", '{"city":"Paris"}', "--call", "record",
                                        "--previous", '{"results":{}}')
        self.assertEqual((status, response["launch"], response["step"], response["code"], response["path"]),
                         (1, "accepted", "record", "OPERAND", "/results/city"))
        self.assertIn("previous output for argument 'chosenCity'", response["message"])

    def test_launch_refused_before_binding_entry_call(self):
        expected = self.cases["rejected"]
        with patch.object(RunInput, "resolve_arguments") as bind_call:
            status, response = self.command("preview", "--input", json.dumps(expected["input"]),
                                            "--call", self.flow["entry"])
        self.assertEqual((status, response["launch"], response["code"], response["path"]),
                         (1, "rejected", expected["code"], expected["path"]))
        bind_call.assert_not_called()
