#!/usr/bin/env python3
"""Build the reviewed modular candidate fixtures and manifest without readers."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
CONTRACT = "proposal-0013-candidate-1"
CONTRACT_BASE = "280347eec4e2e051d296f9271bfccc86c98d4d40"
CONTRACT_SHA256 = "7c9e2aa8e5c6d7c8c0b419aaf3afb666f9ad3510057c98dc7f0f3ac3e904773b"
INHERITED_BASE = "009a51eb301688f06d29bb7e2f1784e3c4a4cc98"
INHERITED_SHA256 = "9f0ead2cbe9a5e158e3017f1ba692cbd3cba69e9240048130dc49c19c1222e07"
SCHEMA_SHA256 = "fa56fd4e723be942a8d089b5da479415e28fa170a32c9edf9f0f1f84b75da74a"
ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64


def document_bytes(document):
    return (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode()


def document_hash(document):
    return hashlib.sha256(document_bytes(document)).hexdigest()


def key(name):
    return {"scope": "mvp", "id": name, "version": "1"}


def ref(name):
    return key(name)


def scoped_key(scope, name):
    return {"scope": scope, "id": name, "version": "1"}


def external_ref(dependency, scope, name):
    return {"dependency": dependency, "key": scoped_key(scope, name)}


def edition(name, version="1"):
    return {"identity": name, "version": version}


def definition(name, kind, payload):
    return {"key": key(name), "kind": kind, "owner": key("system"), "payload": payload}


def relation(source, relation_name, target, expected_kind):
    return {"source": ref(source), "relation": relation_name, "target": ref(target), "expectedKind": expected_kind}


def implementation(name, engine):
    return {
        "id": name,
        "implementation": edition(engine),
        "parameters": {"endpoint": "local", "retries": 2, "vendor": {"mode": "strict"}},
        "claims": [{"capability": edition("example/tool-api"), "status": "supported", "evidence": ONE_HASH}],
    }


def agent_binding(agent, engine, tool_choice):
    return {
        "agent": ref(agent),
        "engine": edition(engine),
        "parameters": {"temperature": 0, "engineOptions": {"trace": False}},
        "requires": [edition("example/base")],
        "claims": [
            {"capability": edition("example/base"), "status": "supported", "evidence": ONE_HASH},
            {"capability": edition("example/text"), "status": "supported", "evidence": ONE_HASH},
            {"capability": edition("example/skill"), "status": "supported", "evidence": ONE_HASH},
            {"capability": edition("example/plain-adapter"), "status": "supported", "evidence": ONE_HASH},
        ],
        "tools": [{"tool": ref("search-tool"), "choices": [implementation(tool_choice, "example/search-adapter")], "selected": tool_choice}],
        "applications": [
            {"content": ref("common-instructions"), "adapter": edition("example/plain-adapter"), "parameters": {"channel": "system"}},
            {"content": ref("research-skill"), "adapter": edition("example/plain-adapter"), "parameters": {"channel": "skill", "priority": 2}},
        ],
    }


def invoke(step_id, agent, principal, operation, success):
    return {
        "id": step_id,
        "kind": "invoke",
        "agent": ref(agent),
        "interface": ref("work-interface"),
        "action": ref("ask-action" if operation == "ask" else "notify-action"),
        "resources": [ref("resource")],
        "principal": ref(principal),
        "context": {"input": "context"},
        "inputs": {"x": "string"},
        "outputs": {"y": "string"},
        "bindings": {"x": {"input": "x"}},
        "success": success,
        "failure": "bad",
        "operation": operation,
    }


def base_document():
    operations = [
        {"id": "ask", "direction": "inbound", "mode": "request-response", "action": ref("ask-action"), "inputs": {"x": "string"}, "outputs": {"y": "string"}},
        {"id": "notify", "direction": "bidirectional", "mode": "request-response", "action": ref("notify-action"), "inputs": {"x": "string"}, "outputs": {"y": "string"}},
    ]
    definitions = [
        definition("agent-a", "Agent", {}),
        definition("agent-b", "Agent", {}),
        definition("principal-a", "Principal", {}),
        definition("principal-b", "Principal", {}),
        definition("work-interface", "Interface", {"operations": operations}),
        definition("ask-action", "Action", {}),
        definition("notify-action", "Action", {}),
        definition("resource", "Resource", {}),
        definition("flow", "ControlFlow", {}),
        definition("search-tool", "Tool", {"action": ref("tool-action"), "inputs": {"query": "string"}, "outputs": {"items": "json"}, "effects": "external", "failures": ["unavailable"], "requires": [edition("example/tool-api")]}),
        definition("tool-action", "Action", {}),
        definition("common-instructions", "Instructions", {"target": "Agent", "at": "before-invoke", "format": edition("example/text"), "body": "Answer from cited material.", "requires": []}),
        definition("research-skill", "Skill", {"inputs": {"query": "string"}, "outputs": {"answer": "string"}, "preconditions": "A query is available.", "completion": "A cited answer is produced.", "dependencies": [ref("common-instructions")], "tools": [ref("search-tool")], "requires": [edition("example/skill")]}),
        definition("approval-requirement", "ApprovalRequirement", {"approvers": [ref("principal-a")], "validForMs": 60000}),
    ]
    relations = []
    for agent, principal in (("agent-a", "principal-a"), ("agent-b", "principal-b")):
        relations.extend([
            relation(agent, "actsAs", principal, "Principal"),
            relation(agent, "exposes", "work-interface", "Interface"),
            relation(agent, "directedBy", "research-skill", "Skill"),
            relation(agent, "uses", "search-tool", "Tool"),
        ])
    graph = {
        "definition": key("flow"), "entry": "call-a", "inputs": {"x": "string", "context": "json"}, "outputs": {"y": "string"},
        "steps": [
            invoke("call-a", "agent-a", "principal-a", "ask", "call-b"),
            invoke("call-b", "agent-b", "principal-b", "notify", "ok"),
            {"id": "ok", "kind": "end", "outcome": "success", "bindings": {"y": {"step": "call-b", "port": "y"}}},
            {"id": "bad", "kind": "end", "outcome": "failure", "reason": "call failed"},
        ],
    }
    cfg_a = {"id": "portable", "graph": key("flow"), "agents": [agent_binding("agent-a", "example/engine-a", "search-a"), agent_binding("agent-b", "example/engine-b", "search-b")]}
    cfg_b = {"id": "alternate", "graph": key("flow"), "agents": [agent_binding("agent-a", "example/engine-b", "search-b"), agent_binding("agent-b", "example/engine-a", "search-a")]}
    return {
        "contract": CONTRACT,
        "root": {"key": key("system"), "kind": "System"},
        "definitions": definitions,
        "relations": relations,
        "exports": [], "dependencies": [], "unresolved": [], "extensions": [],
        "graphs": [graph],
        "runtime": {"configurations": [cfg_a, cfg_b], "selected": "portable"},
    }


def approval_document():
    doc = base_document()
    call = invoke("call", "agent-a", "principal-a", "ask", "ok")
    first = {"id": "legal", "kind": "approval", "requirement": ref("approval-requirement"), "timeoutMs": 30000, "approved": "finance", "denied": "denied", "failure": "failed", "call": "call"}
    second = {"id": "finance", "kind": "approval", "requirement": ref("approval-requirement"), "timeoutMs": 20000, "approved": "call", "denied": "denied", "failure": "failed", "call": "call"}
    doc["graphs"][0]["entry"] = "legal"
    doc["graphs"][0]["steps"] = [first, second, call,
        {"id": "ok", "kind": "end", "outcome": "success", "bindings": {"y": {"step": "call", "port": "y"}}},
        {"id": "denied", "kind": "end", "outcome": "failure", "reason": "approval denied"},
        {"id": "failed", "kind": "end", "outcome": "failure", "reason": "approval failed"},
        {"id": "bad", "kind": "end", "outcome": "failure", "reason": "call failed"},
    ]
    doc["runtime"]["configurations"][0]["agents"] = [doc["runtime"]["configurations"][0]["agents"][0]]
    doc["runtime"]["configurations"][1]["agents"] = [doc["runtime"]["configurations"][1]["agents"][0]]
    return doc


def interface_annex(scope="annex", export_interface=True, transitive=False):
    root = scoped_key(scope, "annex-root")
    ask_action = external_ref("next", "next", "ask-action") if transitive else scoped_key(scope, "ask-action")
    operations = [
        {"id": "notify", "direction": "outbound", "mode": "request-response", "action": scoped_key(scope, "notify-action"), "inputs": {"x": "string"}, "outputs": {"y": "string"}},
        {"id": "ask", "direction": "inbound", "mode": "request-response", "action": ask_action, "inputs": {"x": "string"}, "outputs": {"y": "string"}},
    ]
    definitions = [
        {"key": scoped_key(scope, "work-interface"), "kind": "Interface", "owner": root, "payload": {"operations": operations}},
        {"key": scoped_key(scope, "ask-action"), "kind": "Action", "owner": root, "payload": {}},
        {"key": scoped_key(scope, "notify-action"), "kind": "Action", "owner": root, "payload": {}},
    ]
    exports = [scoped_key(scope, "ask-action"), scoped_key(scope, "notify-action")]
    if export_interface:
        exports.insert(0, scoped_key(scope, "work-interface"))
    dependencies = []
    if transitive:
        dependencies.append({
            "id": "next", "rootKey": scoped_key("next", "root"), "status": "external",
            "requiredFor": [], "sha256": ZERO_HASH,
        })
    return {
        "contract": CONTRACT,
        "root": {"key": root, "kind": "PackageVersion"},
        "definitions": definitions,
        "relations": [], "exports": exports, "dependencies": dependencies,
        "unresolved": [], "extensions": [],
    }


def primary_with_interface_annex(annex, scope="annex"):
    document = base_document()
    interface = external_ref("dep", scope, "work-interface")
    action = external_ref("dep", scope, "ask-action")
    exposure = next(item for item in document["relations"]
                    if item["source"] == ref("agent-a") and item["relation"] == "exposes")
    exposure["target"] = interface
    call = document["graphs"][0]["steps"][0]
    call["interface"] = interface
    call["action"] = action
    document["dependencies"] = [{
        "id": "dep", "rootKey": scoped_key(scope, "annex-root"), "status": "included",
        "requiredFor": [], "sha256": document_hash(annex),
    }]
    return document


def expected(operation, verdict, findings=(), checks=(), states=(), opaque=(), absent_states=(), absent_opaque=(), preservation="no-output", prerequisite_results=(), finding_mode="contains"):
    unit_phase = {"validateG": ("G", "unresolved-document"), "resolveG": ("G", "resolved-graph"), "validateR": ("R", "unresolved-document"), "exchange": ("exchange", None), "inspect": ("inspect", None)}
    unit, phase = unit_phase[operation]
    results = [{"input": "primary", "unit": unit, "phase": phase, "verdict": verdict}]
    if unit in {"G", "R"}:
        results = [{"input": "primary", "unit": "D", "phase": "unresolved-document", "verdict": "pass"}, *prerequisite_results, *results]
    return {
        "results": results,
        "findings": {"mode": finding_mode, "items": list(findings)},
        "checks": list(checks), "states": list(states), "absentStates": list(absent_states),
        "opaque": list(opaque), "absentOpaque": list(absent_opaque), "preservation": preservation,
    }


def finding(unit, rule, pointer, outcome, input_id="primary"):
    return {"input": input_id, "unit": unit, "rule": rule, "location": {"pointer": pointer}, "outcome": outcome}


def check(unit, rule, state, *pointers, input_id="primary"):
    return {"input": input_id, "unit": unit, "rule": rule, "state": state, "locations": [{"pointer": p} for p in pointers]}


def state(pointer, state_name, detail=None):
    item = {"input": "primary", "pointer": pointer, "state": state_name}
    if detail is not None:
        item["detail"] = detail
    return item


def exchange_inventory(doc):
    states = [
        state("/graphs", "unchecked"),
        state("/runtime", "unchecked"),
        state("/dependencies", "declared"),
    ]
    opaque = [{"input": "primary", "pointer": f"/definitions/{index}/payload"}
              for index, item in enumerate(doc["definitions"]) if "payload" in item]
    opaque.extend([
        {"input": "primary", "pointer": "/graphs"},
        {"input": "primary", "pointer": "/runtime"},
    ])
    return states, opaque


def case(name, operation, doc, expected_value, coverage, scenarios, schema_assertions=(), fixture="modular-system.json", annexes=None, inherited_sections=()):
    headings = {
        "P-SHAPE": "Closed record inventory",
        "G-TARGET": "G operation and approval records",
        "G-DATA": "Sequential approvals for one call",
        "G-APPROVAL": "Sequential approvals for one call",
        "G-RESOLVE": "Scope, authority and continuity",
        "R-SELECTION": "Configuration selection and assignments",
        "R-BINDING": "Configuration selection and assignments",
        "R-TOOL": "Configuration selection and assignments",
        "R-CONTENT": "Content composition, application and prerequisites",
        "R-COMPATIBILITY": "Declared compatibility, not readiness",
        "E-PRESERVE": "Scope, authority and continuity",
    }
    scope = {"validateG": ("Graphs", "/graphs"), "resolveG": ("Graphs", "/graphs"), "validateR": ("RuntimeDeclaration", "/runtime")}.get(operation, ("Document", ""))
    assertions = [{"entry": "Document", "pointer": "", "valid": True}]
    if scope != ("Document", ""):
        assertions.append({"entry": scope[0], "pointer": scope[1], "valid": True})
    assertions.extend(schema_assertions)
    annexes = annexes or {}
    source = {"document": "../../../proposals/0013-modular-mvp-contract.md", "sections": sorted({headings[x.split(":")[0]] for x in coverage})}
    if inherited_sections:
        source["inherited"] = {
            "document": "../../../proposals/0012-minimal-0.1.0-contract.md",
            "sections": list(inherited_sections),
        }
    return {"name": name, "status": "ready", "primary": fixture,
            "annexes": {name: path for name, (path, _) in annexes.items()}, "operation": operation,
            "source": source, "coverage": coverage, "scenarios": scenarios,
            "schemaAssertions": assertions, "expected": expected_value, "_doc": doc,
            "_annex_docs": {path: annex for path, annex in annexes.values()}}


def build_cases():
    base = base_document()
    cases = []
    full_states = [state("/runtime/selected", "declared"), state("/runtime/configurations/0/agents/0", "unchecked", "declared-supported"), state("/runtime/configurations/0/agents/1", "unchecked", "declared-supported")]
    full_opaque = [{"input": "primary", "pointer": p} for p in (
        "/runtime/configurations/0/agents/0/parameters",
        "/runtime/configurations/0/agents/0/tools/0/choices/0/parameters",
        "/runtime/configurations/0/agents/0/applications/0/parameters",
        "/definitions/11/payload/body", "/definitions/12/payload/preconditions", "/definitions/12/payload/completion")]
    cases.append(case("modular-two-configurations", "validateR", base,
        expected("validateR", "pass", checks=[check("R", r, "completed") for r in ("P-SHAPE", "R-SELECTION", "R-BINDING", "R-TOOL", "R-CONTENT", "R-COMPATIBILITY")] + [check("R", "X-READINESS", "excluded", "/runtime"), check("R", "X-EVIDENCE-ASSESSMENT", "excluded", "/runtime")], states=full_states, opaque=full_opaque),
        ["P-SHAPE:positive", "R-SELECTION:positive", "R-BINDING:positive", "R-TOOL:positive", "R-CONTENT:positive", "R-COMPATIBILITY:positive"],
        ["two-configurations", "two-agents-different-engines", "declared-supported", "tool-specific-parameters", "content-reuse-order"],
        [{"entry": "ToolPayload", "pointer": "/definitions/9/payload", "valid": True}, {"entry": "InstructionsPayload", "pointer": "/definitions/11/payload", "valid": True}, {"entry": "SkillPayload", "pointer": "/definitions/12/payload", "valid": True}] ))

    doc = deepcopy(base); del doc["runtime"]["selected"]
    cases.append(case("selection-absent", "validateR", doc,
        expected("validateR", "pass", checks=[check("R", "R-SELECTION", "completed"), check("R", "R-COMPATIBILITY", "excluded", "/runtime")], states=[state("/runtime/selected", "absent")]),
        ["R-SELECTION:positive", "R-COMPATIBILITY:excluded"], ["selection-absent-no-fallback"], fixture="selection-absent.json"))

    doc = deepcopy(base); doc["runtime"]["selected"] = "missing"
    cases.append(case("selection-unknown", "validateR", doc,
        expected("validateR", "fail", findings=[finding("R", "R-SELECTION", "/runtime", "fail")], checks=[check("R", "R-SELECTION", "completed"), check("R", "R-COMPATIBILITY", "blocked", "/runtime")], states=[state("/runtime/selected", "declared")]),
        ["R-SELECTION:negative", "R-COMPATIBILITY:blocked"], ["selection-unknown-no-fallback"], fixture="selection-unknown.json"))

    doc = deepcopy(base); binding = doc["runtime"]["configurations"][0]["agents"][0]; binding["engine"] = None
    cases.append(case("engine-not-provided", "validateR", doc,
        expected("validateR", "inconclusive", findings=[finding("R", "R-COMPATIBILITY", "/runtime/configurations/0/agents/0", "inconclusive")], checks=[check("R", "R-COMPATIBILITY", "completed")], states=[state("/runtime/configurations/0/agents/0/engine", "absent"), state("/runtime/configurations/0/agents/0", "absent", "not-provided")]),
        ["R-COMPATIBILITY:inconclusive"], ["engine-absent-no-fallback"], fixture="engine-not-provided.json"))

    doc = deepcopy(base); tool = doc["runtime"]["configurations"][0]["agents"][0]["tools"][0]; del tool["selected"]
    cases.append(case("tool-choice-not-provided", "validateR", doc,
        expected("validateR", "inconclusive", findings=[finding("R", "R-COMPATIBILITY", "/runtime/configurations/0/agents/0/tools/0", "inconclusive")], checks=[check("R", "R-TOOL", "completed"), check("R", "R-COMPATIBILITY", "completed")], states=[state("/runtime/configurations/0/agents/0/tools/0/selected", "absent"), state("/runtime/configurations/0/agents/0/tools/0", "absent", "not-provided")]),
        ["R-TOOL:positive", "R-COMPATIBILITY:inconclusive"], ["tool-choice-absent-no-fallback"], fixture="tool-choice-not-provided.json"))

    doc = deepcopy(base); claim = doc["runtime"]["configurations"][0]["agents"][0]["claims"][0]; claim["status"] = "unsupported"
    cases.append(case("compatibility-incompatible", "validateR", doc,
        expected("validateR", "fail", findings=[finding("R", "R-COMPATIBILITY", "/runtime/configurations/0/agents/0", "fail")], states=[state("/runtime/configurations/0/agents/0", "declared", "incompatible")]),
        ["R-COMPATIBILITY:negative"], ["declared-incompatible-not-readiness"], fixture="compatibility-incompatible.json"))

    doc = deepcopy(base); claim = doc["runtime"]["configurations"][0]["agents"][0]["claims"][0]; claim["status"] = "unknown"; claim["evidence"] = None
    cases.append(case("compatibility-unknown", "validateR", doc,
        expected("validateR", "inconclusive", findings=[finding("R", "R-COMPATIBILITY", "/runtime/configurations/0/agents/0", "inconclusive")], states=[state("/runtime/configurations/0/agents/0", "unknown", "unknown"), state("/runtime/configurations/0/agents/0/claims/0/evidence", "unknown")]),
        ["R-COMPATIBILITY:unknown"], ["declared-unknown-not-readiness"], fixture="compatibility-unknown.json"))

    doc = deepcopy(base); binding = doc["runtime"]["configurations"][0]["agents"][0]; binding["applications"] = []; binding["claims"][2]["status"] = "unsupported"
    cases.append(case("missing-application-keeps-incompatibility", "validateR", doc,
        expected("validateR", "fail", findings=[finding("R", "R-CONTENT", "/runtime/configurations/0/agents/0", "fail"), finding("R", "R-COMPATIBILITY", "/runtime/configurations/0/agents/0", "fail"), finding("R", "R-COMPATIBILITY", "/runtime/configurations/0/agents/0", "inconclusive")], states=[state("/runtime/configurations/0/agents/0", "declared", "incompatible")]),
        ["R-CONTENT:negative", "R-COMPATIBILITY:negative", "R-COMPATIBILITY:inconclusive"], ["missing-application-preserves-incompatibility"], fixture="missing-application-keeps-incompatibility.json"))

    doc = deepcopy(base); doc["runtime"]["configurations"][0]["agents"][0]["tools"] = []
    cases.append(case("missing-tool-binding", "validateR", doc,
        expected("validateR", "fail", findings=[finding("R", "R-TOOL", "/runtime/configurations/0/agents/0", "fail")]),
        ["R-TOOL:negative"], ["required-tool-binding"], fixture="missing-tool-binding.json"))

    doc = deepcopy(base); doc["runtime"]["configurations"][0]["agents"] = doc["runtime"]["configurations"][0]["agents"][:1]
    cases.append(case("missing-agent-binding", "validateR", doc,
        expected("validateR", "fail", findings=[finding("R", "R-BINDING", "/runtime/configurations/0", "fail")]),
        ["R-BINDING:negative"], ["exact-agent-binding-coverage"], fixture="missing-agent-binding.json"))

    doc = deepcopy(base); apps = doc["runtime"]["configurations"][0]["agents"][0]["applications"]; apps.reverse()
    cases.append(case("skill-dependency-after-dependent", "validateR", doc,
        expected("validateR", "fail", findings=[finding("R", "R-CONTENT", "/runtime/configurations/0/agents/0/applications/0", "fail")]),
        ["R-CONTENT:negative"], ["content-dependency-order"], fixture="skill-dependency-after-dependent.json"))

    doc = deepcopy(base); doc["definitions"][12]["payload"]["dependencies"] = [ref("research-skill")]
    cases.append(case("skill-dependency-cycle", "validateR", doc,
        expected("validateR", "fail", findings=[finding("R", "R-CONTENT", "/definitions/12/payload", "fail")]),
        ["R-CONTENT:negative"], ["content-dependency-cycle"], fixture="skill-dependency-cycle.json"))

    doc = deepcopy(base); doc["definitions"][12]["payload"]["dependencies"] = None; doc["runtime"]["configurations"][0]["agents"][0]["claims"][0]["status"] = "unsupported"
    cases.append(case("partial-content-prerequisite", "validateR", doc,
        expected("validateR", "fail", findings=[finding("R", "P-SHAPE", "/definitions/12/payload/dependencies", "fail"), finding("R", "R-COMPATIBILITY", "/runtime/configurations/0/agents/0", "fail")], checks=[check("R", "P-SHAPE", "completed"), check("R", "R-CONTENT", "blocked", "/definitions/12/payload"), check("R", "R-COMPATIBILITY", "completed"), check("R", "R-COMPATIBILITY", "blocked", "/runtime/configurations/0/agents/0")], states=[state("/runtime/configurations/0/agents/0", "unchecked", "blocked")]),
        ["P-SHAPE:negative", "R-CONTENT:blocked", "R-COMPATIBILITY:blocked"], ["partial-prerequisite-keeps-independent-failure"], [{"entry": "SkillPayload", "pointer": "/definitions/12/payload", "valid": False}], "partial-content-prerequisite.json"))

    doc = deepcopy(base)
    external = {"dependency": "shared", "key": {"scope": "shared", "id": "instructions", "version": "1"}}
    doc["relations"][2]["target"] = external
    doc["dependencies"] = [{"id": "shared", "rootKey": {"scope": "shared", "id": "root", "version": "1"}, "status": "external", "requiredFor": [], "sha256": ZERO_HASH}]
    for configuration in doc["runtime"]["configurations"]:
        app = configuration["agents"][0]["applications"][1]
        app["content"] = external
        configuration["agents"][0]["applications"] = [app]
    cases.append(case("external-runtime-content", "validateR", doc,
        expected("validateR", "inconclusive", findings=[finding("R", "R-COMPATIBILITY", "/runtime/configurations/0/agents/0", "inconclusive")], checks=[check("R", "R-CONTENT", "excluded", "/runtime/configurations/0/agents/0/applications/0"), check("R", "R-COMPATIBILITY", "completed")], states=[state("/runtime/configurations/0/agents/0/applications/0/content", "unchecked"), state("/runtime/configurations/0/agents/0", "unknown", "unknown")]),
        ["R-CONTENT:excluded", "R-COMPATIBILITY:unknown"], ["external-runtime-reference-excluded"], fixture="external-runtime-content.json"))

    inherited_resolution = (
        "Dependencies, unknowns and extension handling",
        "Exact results, locations and experimental diagnostics",
        "Rule execution and exact exclusion records",
    )
    annex_results = [
        {"input": "annex/dep", "unit": "D", "phase": "unresolved-document", "verdict": "pass"},
        {"input": "annex/dep", "unit": "G", "phase": "resolved-graph", "verdict": "pass"},
    ]
    annex = interface_annex()
    doc = primary_with_interface_annex(annex)
    cases.append(case("annex-interface-operation", "resolveG", doc,
        expected("resolveG", "pass", checks=[
            check("G", "P-SHAPE", "completed", input_id="annex/dep"),
            check("G", "G-TARGET", "completed", input_id="annex/dep"),
            check("G", "G-RESOLVE", "completed"), check("G", "G-TARGET", "completed"),
            check("G", "G-DATA", "completed"),
        ], opaque=[
            {"input": "annex/dep", "pointer": "/definitions/1/payload"},
            {"input": "annex/dep", "pointer": "/definitions/2/payload"},
        ], absent_opaque=[
            {"input": "annex/dep", "pointer": "/definitions/0/payload"},
        ], prerequisite_results=annex_results, finding_mode="exact"),
        ["G-RESOLVE:positive", "G-TARGET:positive"], ["direct-annex-interface-operation"],
        schema_assertions=[
            {"input": "annex/dep", "entry": "Document", "pointer": "", "valid": True},
            {"input": "annex/dep", "entry": "InterfacePayload", "pointer": "/definitions/0/payload", "valid": True},
        ],
        fixture="annex-interface-operation.json",
        annexes={"dep": ("annex-interface-operation--dep.json", annex)},
        inherited_sections=inherited_resolution))

    annex = interface_annex(export_interface=False)
    doc = primary_with_interface_annex(annex)
    cases.append(case("annex-interface-unexported", "resolveG", doc,
        expected("resolveG", "fail", findings=[
            finding("G", "G-RESOLVE", "/graphs/0/steps/0", "fail"),
        ], checks=[check("G", "G-RESOLVE", "completed")], opaque=[
            {"input": "annex/dep", "pointer": "/definitions/0/payload"},
            {"input": "annex/dep", "pointer": "/definitions/1/payload"},
            {"input": "annex/dep", "pointer": "/definitions/2/payload"},
        ], prerequisite_results=[annex_results[0]], finding_mode="exact"),
        ["G-RESOLVE:negative"], ["annex-target-unexported"],
        schema_assertions=[
            {"input": "annex/dep", "entry": "Document", "pointer": "", "valid": True},
            {"input": "annex/dep", "entry": "InterfacePayload", "pointer": "/definitions/0/payload", "valid": True},
        ],
        fixture="annex-interface-unexported.json",
        annexes={"dep": ("annex-interface-unexported--dep.json", annex)},
        inherited_sections=inherited_resolution))

    annex = interface_annex(transitive=True)
    doc = primary_with_interface_annex(annex)
    cases.append(case("annex-interface-transitive", "resolveG", doc,
        expected("resolveG", "unsupported", findings=[
            finding("G", "G-RESOLVE", "/graphs/0/steps/0", "unsupported"),
        ], checks=[
            check("G", "P-SHAPE", "completed", input_id="annex/dep"),
            check("G", "G-TARGET", "completed", input_id="annex/dep"),
            check("G", "G-TARGET", "excluded", "/definitions/0/payload/operations/1", input_id="annex/dep"),
            check("G", "G-RESOLVE", "completed"), check("G", "G-TARGET", "completed"),
            check("G", "G-TARGET", "excluded", "/graphs/0/steps/0"), check("G", "G-DATA", "completed"),
        ], absent_states=[
            {"input": "annex/dep", "pointerPrefix": "/definitions/0/payload"},
        ], opaque=[
            {"input": "annex/dep", "pointer": "/definitions/1/payload"},
            {"input": "annex/dep", "pointer": "/definitions/2/payload"},
        ], absent_opaque=[
            {"input": "annex/dep", "pointer": "/definitions/0/payload"},
        ], prerequisite_results=annex_results, finding_mode="exact"),
        ["G-RESOLVE:unsupported", "G-TARGET:excluded"], ["transitive-annex-reference-unsupported"],
        schema_assertions=[
            {"input": "annex/dep", "entry": "Document", "pointer": "", "valid": True},
            {"input": "annex/dep", "entry": "InterfacePayload", "pointer": "/definitions/0/payload", "valid": True},
        ],
        fixture="annex-interface-transitive.json",
        annexes={"dep": ("annex-interface-transitive--dep.json", annex)},
        inherited_sections=inherited_resolution))

    annex = interface_annex(scope="mvp")
    doc = primary_with_interface_annex(annex, scope="mvp")
    graph = doc["graphs"][0]
    call, _, success, failure = graph["steps"]
    call["success"] = "ok"
    success["bindings"]["y"]["step"] = "call-a"
    graph["steps"] = [call, success, failure]
    cases.append(case("annex-interface-key-collision", "resolveG", doc,
        expected("resolveG", "fail", findings=[
            finding("G", "G-RESOLVE", "/graphs/0/steps/0", "fail"),
        ], checks=[
            check("G", "P-SHAPE", "completed", input_id="annex/dep"),
            check("G", "G-TARGET", "completed", input_id="annex/dep"),
            check("G", "G-RESOLVE", "completed"), check("G", "G-TARGET", "completed"),
            check("G", "G-TARGET", "blocked", "/graphs/0/steps/0"), check("G", "G-DATA", "completed"),
        ], absent_states=[
            {"input": "annex/dep", "pointerPrefix": "/definitions/0/payload"},
        ], opaque=[
            {"input": "annex/dep", "pointer": "/definitions/1/payload"},
            {"input": "annex/dep", "pointer": "/definitions/2/payload"},
        ], absent_opaque=[
            {"input": "annex/dep", "pointer": "/definitions/0/payload"},
        ], prerequisite_results=annex_results, finding_mode="exact"),
        ["G-RESOLVE:negative", "G-TARGET:blocked"], ["cross-boundary-selected-key-collision"],
        schema_assertions=[
            {"input": "annex/dep", "entry": "Document", "pointer": "", "valid": True},
            {"input": "annex/dep", "entry": "InterfacePayload", "pointer": "/definitions/0/payload", "valid": True},
        ],
        fixture="annex-interface-key-collision.json",
        annexes={"dep": ("annex-interface-key-collision--dep.json", annex)},
        inherited_sections=inherited_resolution))

    cases.append(case("interface-two-operations", "validateG", base,
        expected("validateG", "pass", checks=[check("G", "P-SHAPE", "completed"), check("G", "G-TARGET", "completed")], absent_opaque=[{"input": "primary", "pointer": "/definitions/4/payload"}]),
        ["G-TARGET:positive", "P-SHAPE:positive"], ["interface-two-operations-selected-individually"], [{"entry": "InterfacePayload", "pointer": "/definitions/4/payload", "valid": True}], "modular-system.json"))

    doc = deepcopy(base); doc["graphs"][0]["steps"][0]["operation"] = "missing"
    cases.append(case("operation-not-found", "validateG", doc,
        expected("validateG", "fail", findings=[finding("G", "G-TARGET", "/graphs/0/steps/0", "fail")]),
        ["G-TARGET:negative"], ["interface-operation-required"], fixture="operation-not-found.json"))

    approval = approval_document()
    cases.append(case("approval-two-gates-success-refusal", "validateG", approval,
        expected("validateG", "pass", checks=[check("G", "G-APPROVAL", "completed"), check("G", "G-DATA", "completed")]),
        ["G-APPROVAL:positive", "G-DATA:positive"], ["approval-two-gates", "approval-success-refusal"], fixture="approval-two-gates.json"))

    doc = deepcopy(approval); doc["graphs"][0]["steps"][0]["denied"] = "call"
    cases.append(case("approval-refusal-bypass", "validateG", doc,
        expected("validateG", "fail", findings=[finding("G", "G-APPROVAL", "/graphs/0/steps/1", "fail")]),
        ["G-APPROVAL:negative"], ["approval-refusal-bypass"], fixture="approval-refusal-bypass.json"))

    doc = deepcopy(approval); doc["graphs"][0]["steps"][0]["call"] = "unknown-call"
    cases.append(case("approval-call-invalid", "validateG", doc,
        expected("validateG", "fail", findings=[finding("G", "G-APPROVAL", "/graphs/0/steps/0", "fail")]),
        ["G-APPROVAL:negative"], ["approval-call-invalid"], fixture="approval-call-invalid.json"))

    doc = deepcopy(approval); doc["graphs"][0]["steps"][2]["bindings"]["x"] = {"step": "call", "port": "y"}
    cases.append(case("approval-input-unavailable", "validateG", doc,
        expected("validateG", "fail", findings=[finding("G", "G-DATA", "/graphs/0/steps/0", "fail"), finding("G", "G-DATA", "/graphs/0/steps/1", "fail")]),
        ["G-DATA:negative"], ["approval-input-unavailable"], fixture="approval-input-unavailable.json"))

    exchange_states, exchange_opaque = exchange_inventory(base)
    cases.append(case("modular-exact-exchange", "exchange", base,
        expected("exchange", "pass", checks=[check("exchange", "E-PRESERVE", "completed")], states=exchange_states, opaque=exchange_opaque, preservation="exact-input-boundary"),
        ["E-PRESERVE:positive"], ["exact-exchange-new-payload-slices"], fixture="modular-system.json"))

    doc = deepcopy(base)
    doc["dependencies"] = [{"id": "missing", "rootKey": {"scope": "missing", "id": "root", "version": "1"}, "status": "included", "requiredFor": [], "sha256": ZERO_HASH}]
    exchange_states, exchange_opaque = exchange_inventory(doc)
    cases.append(case("modular-exchange-accounting-refusal", "exchange", doc,
        expected("exchange", "fail", findings=[finding("exchange", "E-PRESERVE", "", "fail")], checks=[check("exchange", "E-PRESERVE", "completed")], states=exchange_states, opaque=exchange_opaque),
        ["E-PRESERVE:negative"], ["exact-exchange-accounting-refusal"], fixture="modular-exchange-accounting-refusal.json"))
    return cases


def main():
    contract = HERE / "../../../proposals/0013-modular-mvp-contract.md"
    schema_path = (HERE / "../schemas/modular.schema.json").resolve()
    if hashlib.sha256(contract.resolve().read_bytes()).hexdigest() != CONTRACT_SHA256:
        raise RuntimeError("proposal 0013 changed; review the oracles before updating the pinned digest")
    if hashlib.sha256(schema_path.read_bytes()).hexdigest() != SCHEMA_SHA256:
        raise RuntimeError("modular schema changed; review shape assertions before updating the pinned digest")
    cases = build_cases()
    documents = {}
    for item in cases:
        path = item["primary"]
        document = item.pop("_doc")
        if path in documents and documents[path] != document:
            raise RuntimeError(f"fixture collision: {path}")
        documents[path] = document
        for annex_path, annex_document in item.pop("_annex_docs").items():
            if annex_path in documents and documents[annex_path] != annex_document:
                raise RuntimeError(f"fixture collision: {annex_path}")
            documents[annex_path] = annex_document
    artifacts = {}
    for name, document in sorted(documents.items()):
        data = document_bytes(document)
        (HERE / name).write_bytes(data)
        artifacts[name] = hashlib.sha256(data).hexdigest()
    for item in cases:
        path = item["primary"]
        item["primary"] = {"path": path, "sha256": artifacts[path]}
        item["annexes"] = {
            name: {"path": annex_path, "sha256": artifacts[annex_path]}
            for name, annex_path in item["annexes"].items()
        }
    manifest = {
        "format": "agsdl-modular-corpus-1", "contract": CONTRACT,
        "contractBase": CONTRACT_BASE, "contractSha256": CONTRACT_SHA256,
        "inheritedContract": {"marker": "proposal-0012-candidate-2", "base": INHERITED_BASE, "sha256": INHERITED_SHA256},
        "schema": {"path": "../schemas/modular.schema.json", "sha256": SCHEMA_SHA256},
        "requiredScenarios": sorted({scenario for item in cases for scenario in item["scenarios"]}),
        "coverage": {}, "cases": cases,
    }
    for item in cases:
        for entry in item["coverage"]:
            rule, variant = entry.split(":")
            manifest["coverage"].setdefault(rule, {}).setdefault(variant, []).append(item["name"])
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(documents)} fixtures and {len(cases)} cases")


if __name__ == "__main__":
    main()
