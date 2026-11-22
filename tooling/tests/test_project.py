"""Project folder conformance and CLI regression tests."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLING = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLING))
from agsdl import ProjectError, jsoninput, load_project, validate_path

REPO = TOOLING.parent
EXAMPLE = REPO / "examples/review-project"
EXPECTED = REPO / "conformance/projects/review.json"


class ProjectTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = shutil.copytree(EXAMPLE, Path(temp.name) / "edited")
        self.entry = self.root / "agsdl.json"
        self.manifest = jsoninput.load(self.entry)

    def save(self):
        self.entry.write_text(json.dumps(self.manifest), encoding="utf-8")

    def cli(self, module, path):
        return subprocess.run([sys.executable, "-m", module, str(path)], cwd=TOOLING,
                              capture_output=True, text=True, check=True).stdout

    def test_relocated_project_and_commands(self):
        (self.root / "draft.json").write_bytes(b"not JSON")
        project = load_project(self.root)
        self.assertEqual(project.document, jsoninput.load(EXPECTED))
        self.assertEqual(project.secrets, {"issues": ["ISSUES_TOKEN"]})
        self.assertTrue(validate_path(self.entry).valid)
        self.assertIn("valid (0 errors, 0 warnings)", self.cli("agsdl", self.root))
        self.assertEqual(self.cli("agsdl.mermaid", self.entry), self.cli("agsdl.mermaid", EXPECTED))

        (self.root / "agents/reviewer").rename(self.root / "reviewer")
        self.manifest["agents"]["reviewer"]["file"] = "reviewer/agent.json"
        self.save()
        moved = load_project(self.root)
        uri = moved.document["agents"]["reviewer"]["instructions"][0]["uri"]
        self.assertEqual((moved.root / uri).read_bytes(),
                         (EXAMPLE / "agents/reviewer/instructions.md").read_bytes())
        self.assertEqual(moved.document["flow"], project.document["flow"])

    def test_splitting_an_existing_document_preserves_validation(self):
        original = REPO / "examples/write-and-review.json"
        self.manifest = jsoninput.load(original)
        self.manifest["projectFormat"] = "agsdl-project-1"
        for name, agent in self.manifest["agents"].items():
            filename = f"agents/{name}.json"
            (self.root / filename).write_text(json.dumps(agent))
            self.manifest["agents"][name] = {"file": filename}
        self.save()
        self.assertEqual(load_project(self.root).document, jsoninput.load(original))
        self.assertEqual(validate_path(self.root).as_json(), validate_path(original).as_json())

    def test_inline_graphless_and_ordinary_document(self):
        document = {"contract": "agsdl-0.4.0", "id": "empty", "agents": {}}
        self.manifest = dict(document, projectFormat="agsdl-project-1")
        self.save()
        self.assertEqual(load_project(self.root).document, document)
        self.manifest = document
        self.save()
        self.assertTrue(validate_path(self.entry).valid)

    def test_only_content_uris_are_rebased(self):
        raw = {"uri": "literal.json", "field": {"file": "../../outside"}}
        prompt = [{"uri": "../agents/reviewer/instructions.md?#section"}]
        uri = "agents/reviewer/instructions.md?#section"
        step = {"type": "agent", "agent": "reviewer", "prompt": prompt,
                "next": {"done": {"step": "last", "message": {
                    "resources": {"literal": {"value": raw}, "guide": prompt[0]}}}}}
        scope = {"entry": "start", "steps": {"start": step, "last": {
            "type": "agent", "agent": "reviewer"}}}
        self.manifest["compositions"] = {"work": {"file": "flows/body.json"}}
        (self.root / "flows/body.json").write_text(json.dumps(dict(scope, outputs=["done"])))
        (self.root / "flows/review.json").write_text(json.dumps(scope))
        self.save()
        doc = load_project(self.root).document
        for body in (doc["flow"], doc["compositions"]["work"]):
            item = body["steps"]["start"]
            self.assertEqual(item["prompt"], [{"uri": uri}])
            resources = item["next"]["done"]["message"]["resources"]
            self.assertEqual(resources, {"literal": {"value": raw}, "guide": {"uri": uri}})

    def test_script_assets_and_skill_paths(self):
        self.manifest["skills"] = {"review": {"file": "agents/skill.json"}}
        (self.root / "agents/skill.json").write_text('{"uri":"reviewer/SKILL.md"}')
        (self.root / "agents/reviewer/SKILL.md").write_text("Review changes.")
        self.manifest["mcpServers"]["issues"] = {"command": ["node", "mcp/worker.mjs"]}
        self.manifest["mcpFiles"] = {"issues": ["mcp/worker.mjs"]}
        (self.root / "mcp/worker.mjs").touch()
        self.save()
        project = load_project(self.root)
        self.assertEqual(project.document["skills"]["review"]["uri"], "agents/reviewer/SKILL.md")
        self.assertEqual(project.mcp_files, self.manifest["mcpFiles"])
        self.assertEqual(project.document["mcpServers"], self.manifest["mcpServers"])

    def test_missing_and_escaping_files(self):
        outside = self.root.parent / "outside"
        outside.write_text("{}")
        (self.root / "link").symlink_to(outside)
        for path in ("missing", "../outside", "link", str(outside), "C:\\outside", "https://example.org/a"):
            with self.subTest(path=path):
                self.manifest["flow"] = {"file": path}
                self.save()
                with self.assertRaises(ProjectError):
                    load_project(self.root)
        for uri in ("%2e%2e/outside", "link", "file:///tmp/elsewhere"):
            with self.subTest(uri=uri):
                self.manifest.pop("flow", None)
                self.manifest["content"] = {"x": {"uri": uri}}
                self.save()
                with self.assertRaises(ProjectError):
                    load_project(self.root)

    def test_invalid_component_reports_its_own_file(self):
        agent = self.root / "agents/reviewer/agent.json"
        for data, expected in ((b'{"a":1,"a":2}', "duplicate"),
                               (b'{}', "missing field")):
            agent.write_bytes(data)
            message = validate_path(self.root).diagnostics[0]["message"]
            self.assertIn("agents/reviewer/agent.json", message)
            self.assertIn(expected, message)
        shutil.copyfile(EXAMPLE / "agents/reviewer/agent.json", agent)
        flow = self.root / "flows/review.json"
        value = jsoninput.load(flow)
        value["steps"]["review"]["agent"] = "absent"
        flow.write_text(json.dumps(value))
        report = validate_path(self.root)
        self.assertFalse(report.valid)
        self.assertIn("flows/review.json#/steps/review", report.diagnostics[0]["message"])

    def test_secret_names_only_and_known_server_required(self):
        path = self.root / "secrets/requirements.json"
        for value in ({"issues": {"ISSUES_TOKEN": "private"}}, {"absent": ["TOKEN"]},
                      {"issues": ["SAME", "SAME"]}):
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ProjectError, "requirements.json"):
                load_project(self.root)
