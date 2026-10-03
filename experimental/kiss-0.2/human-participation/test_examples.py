"""Static witnesses for 0018 using unchanged 0017 readers and report rules."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("kiss_compare", HERE.parent / "compare.py")
compare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compare)


class HumanParticipationExamples(unittest.TestCase):
    def test_six_scenarios_against_both_readers(self):
        compare.load_cases()  # Verify the frozen candidate and corpus hashes.
        review = json.loads((HERE / "review.json").read_bytes())
        publication = json.loads((HERE / "publication.json").read_bytes())
        human = copy.deepcopy(review)
        human["selected"] = "human-assisted"
        self.assertEqual(review["agents"], human["agents"])
        self.assertEqual(review["graphs"], human["graphs"])
        bypass = copy.deepcopy(publication)
        bypass["graphs"]["publication"]["steps"][1]["failure"] = "publish"
        wrong_type = copy.deepcopy(publication)
        wrong_type["agents"]["reviewer"]["interface"]["value"]["operations"]["review"]["outputs"]["text"] = "boolean"
        unfamiliar = copy.deepcopy(human)
        unfamiliar["configurations"]["human-assisted"]["agents"][0]["engine"]["identity"] = "example/unfamiliar-provider"
        cases = [
            ("automated-review", review, "automated", 1, []),
            ("human-review", human, "human-assisted", 1, []),
            ("publication", publication, "human-review", 2, []),
            ("approval-bypass", bypass, "human-review", 2,
             [["flow", "APPROVAL", "/graphs/publication/steps/1", "fail"]]),
            ("wrong-result-type", wrong_type, "human-review", 2,
             [["flow", "APPROVAL-DATA", "/graphs/publication/steps/1", "fail"],
              ["flow", "DATA", "/graphs/publication/steps/2", "fail"]]),
            ("unfamiliar-engine", unfamiliar, "human-assisted", 1, []),
        ]
        with tempfile.TemporaryDirectory(prefix="agsdl-human-examples-") as temporary:
            for name, document, selected, bindings, flow_diagnostics in cases:
                raw = compare.encoded(document)
                sha = compare.digest(raw)
                path = Path(temporary) / (name + ".json")
                path.write_bytes(raw)
                diagnostics = flow_diagnostics + [
                    ["compatibility", "ENGINE", f"/configurations/{selected}/agents/{i}", "inconclusive"]
                    for i in range(bindings)]
                expectation = dict(sha256=sha, diagnostics=diagnostics, gaps=[],
                                   presence={u: "absent" if u == "external" else "present" for u in compare.SUBJECTS})
                expected = compare.normalize(compare.encoded(compare.expected_report(expectation)), sha)
                for reader, command in compare.READERS.items():
                    with self.subTest(scenario=name, reader=reader):
                        process = subprocess.run([*command, str(path)], cwd=compare.ROOT,
                                                 capture_output=True, timeout=30, check=True)
                        self.assertEqual(compare.normalize(process.stdout, sha), expected)


if __name__ == "__main__":
    unittest.main()
