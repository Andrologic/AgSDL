"""Official, offline AgSDL 0.1.0 Python reader. No described system runs."""
from grammar import CONTRACT, array, good
from lossless import integer
from _reuse import load


PROCESSOR = {"identity": "agsdl-reference/python-reader", "version": "0.1.0"}
_core = load("_agsdl_010_rule_engine", "reader.py")

# The reused rule engine predates adoption. Its behavior is unchanged, but its
# fallback prose must not identify an official diagnostic as a candidate result.
_core.Result.find.__defaults__ = ("", "official rule violation", "fail", None)


def _remove_finding_detail(result, rule, path, detail, outcome="fail"):
    identifier = (rule, ("pointer", path), outcome)
    details = result.findings.get(identifier)
    if not details or detail not in details:
        return False
    details.remove(detail)
    if not details:
        del result.findings[identifier]
    return True


def _relations(document, agent, relation_name, expected_kind):
    value = document.obj.get("relations")
    if not isinstance(value, list) or not good("Ref", agent):
        return []
    return [
        relation["target"]
        for relation in value
        if good("Relation", relation)
        and relation["source"] == agent
        and relation["relation"] == relation_name
        and relation["expectedKind"] == expected_kind
    ]


def _required_tools(document, agent):
    required = list(_relations(document, agent, "uses", "Tool"))
    queue = _relations(document, agent, "directedBy", "Instructions")
    queue += _relations(document, agent, "directedBy", "Skill")
    visited = set()
    while queue:
        ref = queue.pop(0)
        token = _core.frozen(ref)
        if token in visited:
            continue
        visited.add(token)
        if not good("Ref", ref) or "dependency" in ref:
            continue
        identity = _core.key(ref)
        if identity in document.ambiguous or identity in document.invalid:
            continue
        found = document.index.get(identity)
        if found is None or found[0].get("kind") not in ("Instructions", "Skill"):
            continue
        definition = found[0]
        if definition["kind"] != "Skill" or not isinstance(definition.get("payload"), dict):
            continue
        payload = definition["payload"]
        dependencies = payload.get("dependencies")
        if isinstance(dependencies, list):
            queue.extend(item for item in dependencies if good("Ref", item))
        tools = payload.get("tools")
        if isinstance(tools, list):
            required.extend(item for item in tools if good("Ref", item))
    unique = {}
    for ref in required:
        unique[_core.frozen(ref)] = ref
    return unique


def _correct_binding_locations(document, result):
    """Apply official R duplicate locations without changing the reused engine."""
    runtime = document.obj.get("runtime")
    graphs = document.obj.get("graphs")
    if not isinstance(runtime, dict) or not isinstance(runtime.get("configurations"), list):
        return
    graph_records = graphs if isinstance(graphs, list) else []
    for configuration_index, configuration in enumerate(runtime["configurations"]):
        if not isinstance(configuration, dict):
            continue
        configuration_path = f"/runtime/configurations/{configuration_index}"
        graph_key = configuration.get("graph")
        matches = [
            graph
            for graph in graph_records
            if isinstance(graph, dict)
            and good("Key", graph.get("definition"))
            and good("Key", graph_key)
            and graph["definition"] == graph_key
        ]
        required_agents = {}
        if len(matches) == 1 and isinstance(matches[0].get("steps"), list):
            projection_readable = True
            for step in matches[0]["steps"]:
                if (
                    not isinstance(step, dict)
                    or step.get("kind") not in ("invoke", "condition", "approval", "end")
                ):
                    projection_readable = False
                    break
                if step["kind"] == "invoke":
                    if not good("Ref", step.get("agent")):
                        projection_readable = False
                        break
                    required_agents[_core.frozen(step["agent"])] = step["agent"]
            if not projection_readable:
                required_agents = {}

        bindings = configuration.get("agents")
        if not isinstance(bindings, list):
            continue
        binding_groups = {}
        for binding_index, binding in enumerate(bindings):
            if not isinstance(binding, dict) or not good("Ref", binding.get("agent")):
                continue
            token = _core.frozen(binding["agent"])
            binding_groups.setdefault(token, []).append(
                (binding, f"{configuration_path}/agents/{binding_index}")
            )
        duplicate_agent_groups = [
            group
            for token, group in binding_groups.items()
            if token in required_agents and len(group) > 1
        ]
        parent_detail = "missing or duplicate AgentBinding"
        parent_has_finding = any(
            parent_detail in details
            for (rule, location, outcome), details in result.findings.items()
            if rule == "R-BINDING"
            and location == ("pointer", configuration_path)
            and outcome == "fail"
        )
        if parent_has_finding and duplicate_agent_groups:
            for group in duplicate_agent_groups:
                for _, binding_path in group[1:]:
                    result.find("R-BINDING", binding_path, parent_detail)
            missing_agent = any(token not in binding_groups for token in required_agents)
            if not missing_agent:
                _remove_finding_detail(
                    result,
                    "R-BINDING",
                    configuration_path,
                    parent_detail,
                )

        for binding, binding_path in [
            item for group in binding_groups.values() for item in group
        ]:
            tools = binding.get("tools")
            if not isinstance(tools, list):
                continue
            required_tools = _required_tools(document, binding["agent"])
            tool_groups = {}
            tool_catalog_complete = True
            for tool_index, tool in enumerate(tools):
                if not isinstance(tool, dict) or not good("Ref", tool.get("tool")):
                    tool_catalog_complete = False
                    continue
                token = _core.frozen(tool["tool"])
                tool_groups.setdefault(token, []).append(
                    f"{binding_path}/tools/{tool_index}"
                )
            duplicate_tool_groups = [
                group
                for token, group in tool_groups.items()
                if token in required_tools and len(group) > 1
            ]
            tool_detail = "missing or duplicate required ToolBinding"
            parent_has_tool_finding = any(
                tool_detail in details
                for (rule, location, outcome), details in result.findings.items()
                if rule == "R-TOOL"
                and location == ("pointer", binding_path)
                and outcome == "fail"
            )
            if parent_has_tool_finding and duplicate_tool_groups:
                for group in duplicate_tool_groups:
                    for tool_path in group[1:]:
                        result.find("R-TOOL", tool_path, tool_detail)
                missing_tool = tool_catalog_complete and any(
                    token not in tool_groups for token in required_tools
                )
                if not missing_tool:
                    _remove_finding_detail(
                        result,
                        "R-TOOL",
                        binding_path,
                        tool_detail,
                    )


def _agent_binding_paths(document):
    runtime = document.obj.get("runtime")
    if not isinstance(runtime, dict) or not isinstance(runtime.get("configurations"), list):
        return set()
    return {
        f"/runtime/configurations/{configuration_index}/agents/{binding_index}"
        for configuration_index, configuration in enumerate(runtime["configurations"])
        if isinstance(configuration, dict) and isinstance(configuration.get("agents"), list)
        for binding_index, _ in enumerate(configuration["agents"])
    }


def _validate_d_with_partial_agent_findings(document, annexes):
    """Keep definitive Agent minima failures when other relations are unreadable."""
    result = _reused_validate_d(document, annexes)
    relations = document.obj.get("relations")
    if not isinstance(relations, list):
        return result
    acts_as_counts = {}
    for relation in relations:
        if (
            good("Relation", relation)
            and relation["relation"] == "actsAs"
            and relation["expectedKind"] == "Principal"
        ):
            token = _core.frozen(relation["source"])
            acts_as_counts[token] = acts_as_counts.get(token, 0) + 1
    for index, definition in enumerate(_core.items(document.obj, "definitions")):
        if not good("Definition", definition) or definition["kind"] != "Agent":
            continue
        identity = _core.key(definition["key"])
        if identity in document.ambiguous:
            continue
        if acts_as_counts.get(_core.frozen(definition["key"]), 0) > 1:
            result.find(
                "D-AGENT",
                f"/definitions/{index}",
                "Agent relation minimum not met",
            )
    return result


_reused_validate_d = _core.validate_d
_core.validate_d = _validate_d_with_partial_agent_findings


def _validate_losses(losses):
    if losses is None:
        return
    if not isinstance(losses, list):
        raise ValueError("losses must be an array")
    for loss in losses:
        if (
            not isinstance(loss, dict)
            or set(loss) != {"input", "location", "information", "reason", "permission"}
            or loss["permission"] is not None
            or any(not good("text", loss[name]) for name in ("input", "information", "reason"))
        ):
            raise ValueError("invalid loss record")
        location = loss["location"]
        valid_pointer = (
            isinstance(location, dict)
            and set(location) == {"pointer"}
            and isinstance(location["pointer"], str)
        )
        valid_byte = (
            isinstance(location, dict)
            and set(location) == {"byte"}
            and (
                (
                    type(location["byte"]) is int
                    and 0 <= location["byte"] <= 9007199254740991
                )
                or integer(location["byte"]) is not None
            )
        )
        if not (valid_pointer or valid_byte):
            raise ValueError("invalid loss location")


def read(operation, primary, annexes=None, losses=None):
    """Return an official report and byte artifacts from caller-supplied bytes."""
    annexes = {} if annexes is None else annexes
    if (
        operation not in _core.OPERATIONS
        or not isinstance(primary, bytes)
        or not isinstance(annexes, dict)
        or any(
            not isinstance(name, str) or not name or not isinstance(raw, bytes)
            for name, raw in annexes.items()
        )
    ):
        raise ValueError("invalid AgSDL 0.1.0 request")
    if losses is not None and operation != "lossyExchange":
        raise ValueError("losses only permitted for lossyExchange")
    _validate_losses(losses)

    document = _core.Document(primary)
    input_bytes = {
        "primary": primary,
        **{"annex/" + name: raw for name, raw in sorted(annexes.items())},
    }
    results = []
    artifacts = {}
    loss_records = []
    annex_documents = []
    extra_states = []

    if operation == "inspect":
        result = _core.Result("primary", "inspect", None, ["P-SYNTAX"])
        result.complete("P-SYNTAX")
        if document.syntax:
            result.find(
                "P-SYNTAX",
                detail=str(document.syntax),
                byte=document.syntax.offset,
            )
        results.append(result)
    elif operation in ("exchange", "lossyExchange"):
        rule = "E-PRESERVE" if operation == "exchange" else "E-LOSS"
        result = _core.Result("primary", "exchange", None, [rule])
        if operation == "lossyExchange":
            result.find("E-LOSS", "", "AgSDL 0.1.0 permits no lossy exchange")
            loss_records = losses or [
                {
                    "input": "primary",
                    "location": {"pointer": ""},
                    "information": "unspecified requested loss",
                    "reason": "no omission permission in AgSDL 0.1.0",
                    "permission": None,
                }
            ]
        else:
            result.complete("E-PRESERVE")
            if good(array("Dependency"), document.obj.get("dependencies")):
                _core.dependency_checks(document, annexes, result, exchange=True)
            if result.verdict() == "pass":
                artifacts = dict(input_bytes)
        results.append(result)
    else:
        prerequisite = _core.validate_d(document, annexes)
        results.append(prerequisite)
        if operation == "validateR":
            result = _core.validate_r(document)
            _correct_binding_locations(document, result)
            result.parents.append(prerequisite)
            if prerequisite.verdict() != "pass":
                result.block("P-PREREQUISITE", whole=True)
            results.append(result)
            extra_states = document.r_states
        elif operation in ("validateG", "resolveG"):
            graph = _core.GraphValidation(document, annexes, operation == "resolveG")
            graph.check()
            graph.finish()
            result = graph.result
            result.parents.append(prerequisite)
            if prerequisite.verdict() != "pass":
                result.block("P-PREREQUISITE", whole=True)
            annex_documents = [
                value
                for _, value in sorted(graph.loaded.items())
                if value is not None
            ]
            if any(value.d.verdict() != "pass" for value in annex_documents):
                result.block("P-PREREQUISITE", whole=True)
            results += [value.d for value in annex_documents]
            results += [value for _, value in sorted(graph.annex_results.items())]
            results.append(result)
            extra_states = graph.extra_states

    states, slices = _core.inventory(document, operation, extra_states)
    if operation == "validateR":
        binding_paths = _agent_binding_paths(document)
        states = [
            state
            for state in states
            if not (
                state["pointer"] in binding_paths
                and state["detail"] == "external target excluded"
            )
        ]
    for annex_document in annex_documents:
        annex_states, annex_slices = _core.inventory(
            annex_document,
            "resolveG",
            extra_states,
            primary=False,
        )
        states.extend(annex_states)
        slices.extend(annex_slices)

    report = {
        "contract": CONTRACT,
        "processor": dict(PROCESSOR),
        "operation": operation,
        "inputs": [
            {"id": name, "sha256": _core.digest(raw)}
            for name, raw in input_bytes.items()
        ],
        "results": [result.export() for result in results],
        "inventory": {"tree": document.tree, "states": states, "opaque": slices},
        "losses": loss_records,
        "outputs": [
            {"id": name, "sha256": _core.digest(raw)}
            for name, raw in artifacts.items()
        ],
    }
    return {"report": report, "artifacts": artifacts}


__all__ = ["CONTRACT", "PROCESSOR", "read"]
