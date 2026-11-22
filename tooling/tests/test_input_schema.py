"""Tests for the isolated run-input validation experiment."""

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agsdl.input_schema import PROTOTYPE_CONTRACT, validate_prototype
from agsdl.validator import DOCUMENT_SCHEMA, validate_document


def document():
    return {
        "contract": PROTOTYPE_CONTRACT, "id": "example", "agents": {},
        "mcpServers": {"s": {"command": ["server"]}},
        "flow": {
            "input": {"type": "object", "properties": {
                "optional": {"type": "array", "items": {"type": "string"}, "maxItems": 2}},
                "additionalProperties": False},
            "entry": "call", "steps": {"call": {
                "type": "call", "mcp": {"server": "s", "tool": "run"},
                "arguments": {"arg": {"input": ["optional", 1]}}}},
        },
    }


def errors(report):
    return [item for item in report.diagnostics if item["severity"] == "error"]


class InputSchemaTest(unittest.TestCase):
    def test_contract_isolation_and_default_fallback(self):
        doc = document()
        before = copy.deepcopy(DOCUMENT_SCHEMA.root)
        self.assertTrue(validate_prototype(doc, {}).valid)
        self.assertEqual(validate_prototype(doc, {}).as_json()["contract"], PROTOTYPE_CONTRACT)
        self.assertFalse(validate_document(doc, {}).valid)
        for marker in ("agsdl-0.4.0", "other"):
            doc["contract"] = marker
            self.assertEqual(validate_prototype(doc, {}).as_json(), validate_document(doc, {}).as_json())
        self.assertEqual(before, DOCUMENT_SCHEMA.root)

    def test_paths_and_schema_consistency(self):
        doc = document()
        arg = doc["flow"]["steps"]["call"]["arguments"]["arg"]
        for path in (["optional", 2], ["missing"], ["optional", "bad"], ["optional", 0, "x"]):
            arg["input"] = path
            self.assertTrue(any(d["code"] == "MESSAGE_PATH" for d in errors(validate_prototype(doc, {}))), path)
        arg["input"] = []
        self.assertTrue(validate_prototype(doc, {}).valid)
        doc["flow"]["input"]["required"] = ["missing"]
        self.assertTrue(any(d["code"] == "SCHEMA" for d in errors(validate_prototype(doc, {}))))
        del doc["flow"]["input"]
        self.assertTrue(any(d["code"] == "MESSAGE_PATH" for d in errors(validate_prototype(doc, {}))))

    def test_resources_and_flow_error(self):
        doc = document()
        flow = doc["flow"]
        flow["steps"]["call"]["next"] = {"step": "approve", "message": {"resources": {"r": {"input": ["optional", 0], "mediaType": "text/plain"}}}}
        flow["steps"]["approve"] = {"type": "approval", "next": {"yes": "call"}}
        flow["onError"] = {"step": "approve", "message": {"resources": {"r": {"input": ["missing"]}}}}
        found = errors(validate_prototype(doc, {}))
        self.assertTrue(any(d["path"] == "/flow/onError/message/resources/r/input" for d in found), found)
        flow["onError"]["message"]["resources"]["r"]["input"] = []
        self.assertTrue(validate_prototype(doc, {}).valid, errors(validate_prototype(doc, {})))

    def test_entry_path_and_composition_restrictions(self):
        doc = document()
        call = doc["flow"]["steps"]["call"]
        call["arguments"]["arg"] = {"path": []}
        call["next"] = "call"
        self.assertTrue(any("first activation" in d["message"] for d in errors(validate_prototype(doc, {}))))
        doc["flow"]["steps"] = {"start": {"type": "compose", "composition": "body", "next": {"done": "start"}}}
        doc["flow"]["entry"] = "start"
        call["next"] = {"output": "done"}
        doc["compositions"] = {"body": {"entry": "call", "steps": {"call": call}, "outputs": ["done"]}}
        self.assertTrue(any("first activation" in d["message"] for d in errors(validate_prototype(doc, {}))))
        call["arguments"]["arg"] = {"input": []}
        self.assertTrue(any("inside a composition" in d["message"] for d in errors(validate_prototype(doc, {}))))

    def test_published_semantics_and_ordinary_documents(self):
        doc = document()
        doc["flow"]["steps"]["call"]["mcp"]["server"] = "missing"
        self.assertTrue(any(d["code"] == "REFERENCE" for d in errors(validate_prototype(doc, {}))))
        doc = document()
        doc["contract"] = "agsdl-0.4.0"
        del doc["flow"]["input"]
        doc["flow"]["steps"]["call"]["arguments"]["arg"] = {"path": []}
        ordinary = validate_document(doc, {})
        self.assertTrue(ordinary.valid, errors(ordinary))
        self.assertEqual(validate_prototype(doc, {}).as_json(), ordinary.as_json())

    def test_composition_resource_input_is_rejected(self):
        doc = document()
        doc["compositions"] = {"body": {"entry": "one", "outputs": ["done"], "steps": {
            "one": {"type": "call", "command": "true", "next": {
                "step": "two", "message": {"resources": {"r": {"input": []}}}}},
            "two": {"type": "approval", "next": {"yes": {"output": "done"}}},
        }}}
        found = errors(validate_prototype(doc, {}))
        self.assertTrue(any("inside a composition" in d["message"] for d in found), found)


if __name__ == "__main__":
    unittest.main()
