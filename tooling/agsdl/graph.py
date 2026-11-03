"""Flow graphs: composition expansion, dominators and join analysis.

Two kinds of graph are built. An expanded graph replaces each compose step by
its body; it follows messages and instances across compositions. A scope graph
keeps the steps of one scope, the flow or one composition body, with each
compose step as one step; joins are deduced there.
"""

from collections import deque


class Scope:
    """A set of authored steps: the top-level flow, or one use of a composition."""

    def __init__(self, steps, pointer, prefix, composition=None, bindings=None, compose=None, parent=None):
        self.steps = steps
        self.pointer = pointer
        self.prefix = prefix
        self.composition = composition
        self.bindings = bindings or {}
        self.compose = compose
        self.parent = parent


START = ("#start",)


class Node:
    def __init__(self, addr, decl, scope, name):
        self.addr = addr
        self.decl = decl
        self.scope = scope
        self.name = name
        self.type = decl["type"] if decl is not None else ("start" if addr == START else "exit")
        self.pointer = scope.pointer + [name] if decl is not None else []
        self.agent = None
        if self.type == "agent":
            ref = decl["agent"]
            self.agent = ref if isinstance(ref, str) else scope.bindings.get(ref["parameter"])


class Edge:
    def __init__(self, src, dst, kind, key, message, pointer):
        self.src = src
        self.dst = dst
        self.kind = kind
        self.key = key
        self.message = message
        self.pointer = pointer


def route_targets(route, pointer):
    """Yield (kind, name, message, pointer) for each target of an authored route."""
    items = route if isinstance(route, list) else [route]
    for index, item in enumerate(items):
        where = pointer + [index] if isinstance(route, list) else pointer
        if isinstance(item, str):
            yield "step", item, None, where
        elif "step" in item:
            yield "step", item["step"], item.get("message"), where
        else:
            yield "output", item["output"], item.get("message"), where


def step_routes(decl, pointer):
    """Yield (kind, key, route, pointer) for the normal and error routes of a step."""
    if "next" in decl:
        nxt = decl["next"]
        if isinstance(nxt, dict) and "step" not in nxt and "output" not in nxt:
            for key, route in nxt.items():
                yield "normal", key, route, pointer + ["next", key]
        else:
            yield "normal", None, nxt, pointer + ["next"]
    if "onError" in decl:
        yield "error", None, decl["onError"], pointer + ["onError"]


class Graph:
    """The expanded graph of a flow, or of one composition analysed on its own."""

    def __init__(self, document):
        self.document = document
        self.compositions = document.get("compositions", {})
        self.nodes = {}
        self.composes = {}
        self.edges = []
        self.root = None

    # Construction -------------------------------------------------------

    @classmethod
    def for_flow(cls, document):
        graph = cls(document)
        flow = document["flow"]
        scope = Scope(flow["steps"], ["flow", "steps"], ())
        graph._add_scope(scope, ())
        graph._connect()
        entry = graph.resolve(scope, flow["entry"])
        if "onError" not in flow or entry is None:
            graph.root = entry
            return graph
        # The flow's onError is a second root: a virtual start leads to the
        # entry and, through an error route, to the handler.
        graph.nodes[START] = Node(START, None, scope, "start")
        graph.edges.append(Edge(START, entry, "entry", None, None, ["flow", "entry"]))
        for tkind, tname, message, where in route_targets(flow["onError"], ["flow", "onError"]):
            for dst in graph._resolve_target(scope, tkind, tname):
                graph.edges.append(Edge(START, dst, "error", None, message, where))
        graph.root = START
        return graph

    @classmethod
    def for_scope(cls, document, composition=None):
        """The steps of the flow, or of one composition body, with compose steps as one step."""
        graph = cls(document)
        if composition is None:
            container = document["flow"]
            pointer = ["flow", "steps"]
        else:
            container = graph.compositions[composition]
            pointer = ["compositions", composition, "steps"]
        scope = Scope(container["steps"], pointer, (), composition=composition)
        for name, decl in scope.steps.items():
            graph.nodes[(name,)] = Node((name,), decl, scope, name)
        for node in list(graph.nodes.values()):
            for kind, key, route, rpointer in step_routes(node.decl, node.pointer):
                for tkind, tname, message, where in route_targets(route, rpointer):
                    dst = graph._local_target(scope, tkind, tname)
                    if dst is not None:
                        graph.edges.append(Edge(node.addr, dst, kind, key, message, where))
        entry = (container["entry"],)
        graph.root = entry if entry in graph.nodes else None
        if composition is None and "onError" in container and graph.root is not None:
            graph.nodes[START] = Node(START, None, scope, "start")
            graph.edges.append(Edge(START, entry, "entry", None, None, ["flow", "entry"]))
            for tkind, tname, message, where in route_targets(container["onError"], ["flow", "onError"]):
                dst = graph._local_target(scope, tkind, tname)
                if dst is not None:
                    graph.edges.append(Edge(START, dst, "error", None, message, where))
            graph.root = START
        return graph

    def _local_target(self, scope, kind, name):
        if kind == "step":
            return (name,) if (name,) in self.nodes else None
        if scope.composition is None:
            return None
        addr = ("#exit", name)
        if addr not in self.nodes:
            self.nodes[addr] = Node(addr, None, scope, name)
        return addr

    @classmethod
    def for_composition(cls, document, name):
        graph = cls(document)
        composition = graph.compositions[name]
        scope = Scope(composition["steps"], ["compositions", name, "steps"], ("#" + name,), composition=name)
        graph._add_scope(scope, (name,))
        graph._connect()
        graph.root = graph.resolve(scope, composition["entry"])
        return graph

    def _add_scope(self, scope, stack):
        for name, decl in scope.steps.items():
            addr = scope.prefix + (name,)
            if decl["type"] == "compose":
                target = decl["composition"]
                composition = self.compositions.get(target)
                if composition is None or target in stack:
                    self.composes[addr] = (decl, None, scope)
                    continue
                bindings = {}
                for parameter, value in decl.get("agents", {}).items():
                    bindings[parameter] = value if isinstance(value, str) else scope.bindings.get(value["parameter"])
                child = Scope(
                    composition["steps"],
                    ["compositions", target, "steps"],
                    addr,
                    composition=target,
                    bindings=bindings,
                    compose=addr,
                    parent=scope,
                )
                self.composes[addr] = (decl, child, scope)
                self._add_scope(child, stack + (target,))
            else:
                self.nodes[addr] = Node(addr, decl, scope, name)

    def resolve(self, scope, name):
        addr = scope.prefix + (name,)
        if addr in self.composes:
            decl, child, _ = self.composes[addr]
            if child is None:
                return None
            return self.resolve(child, self.compositions[decl["composition"]]["entry"])
        return addr if addr in self.nodes else None

    def _resolve_target(self, scope, kind, name):
        if kind == "step":
            addr = self.resolve(scope, name)
            return [addr] if addr is not None else []
        if scope.compose is None:
            if scope.composition is None:
                return []
            exit_addr = ("#exit", name)
            if exit_addr not in self.nodes:
                self.nodes[exit_addr] = Node(exit_addr, None, scope, name)
            return [exit_addr]
        decl, _, parent = self.composes[scope.compose]
        route = decl.get("next", {}).get(name)
        if route is None:
            return []
        found = []
        for kind2, name2, _, _ in route_targets(route, []):
            found.extend(self._resolve_target(parent, kind2, name2))
        return found

    def _outer_message(self, scope, kind, name, message):
        """The message carried when a body route leaves through a compose output."""
        if kind != "output" or scope.compose is None:
            return [message]
        decl, _, parent = self.composes[scope.compose]
        route = decl.get("next", {}).get(name)
        if route is None:
            return []
        messages = []
        for kind2, name2, message2, _ in route_targets(route, []):
            messages.extend(self._outer_message(parent, kind2, name2, message2))
        return messages

    def _inherited_error(self, scope):
        """Error routes a body step inherits from the compose steps enclosing it."""
        while scope.compose is not None:
            decl, _, parent = self.composes[scope.compose]
            if "onError" in decl:
                pointer = parent.pointer + [scope.compose[-1], "onError"]
                return parent, decl["onError"], pointer
            scope = parent
        return None

    def _connect(self):
        for node in list(self.nodes.values()):
            if node.decl is None:
                continue
            routes = list(step_routes(node.decl, node.pointer))
            if "onError" not in node.decl:
                inherited = self._inherited_error(node.scope)
                if inherited is not None:
                    routes.append(("error", None, inherited[1], inherited[2], inherited[0]))
            for entry in routes:
                kind, key, route, pointer = entry[:4]
                scope = entry[4] if len(entry) > 4 else node.scope
                for tkind, tname, message, where in route_targets(route, pointer):
                    dsts = self._resolve_target(scope, tkind, tname)
                    messages = self._outer_message(scope, tkind, tname, message)
                    for index, dst in enumerate(dsts):
                        carried = messages[index] if index < len(messages) else None
                        self.edges.append(Edge(node.addr, dst, kind, key, carried, where))

    # Queries ------------------------------------------------------------

    def successors(self):
        result = {addr: [] for addr in self.nodes}
        for edge in self.edges:
            result[edge.src].append(edge)
        return result

    def predecessors(self):
        result = {addr: [] for addr in self.nodes}
        for edge in self.edges:
            result[edge.dst].append(edge)
        return result

    def reachable(self, start, blocked=()):
        succ = self.successors()
        seen = {start}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            for edge in succ[current]:
                if edge.dst in blocked or edge.dst in seen:
                    continue
                seen.add(edge.dst)
                queue.append(edge.dst)
        return seen

    def reaching(self, target, blocked=()):
        pred = self.predecessors()
        seen = set()
        queue = deque([target])
        while queue:
            current = queue.popleft()
            for edge in pred[current]:
                if edge.src in blocked or edge.src in seen or edge.src == target:
                    continue
                seen.add(edge.src)
                queue.append(edge.src)
        return seen

    def dominators(self):
        if self.root is None:
            return {}
        reach = self.reachable(self.root)
        pred = self.predecessors()
        dom = {n: set(reach) for n in reach}
        dom[self.root] = {self.root}
        changed = True
        while changed:
            changed = False
            for n in reach:
                if n == self.root:
                    continue
                incoming = [dom[e.src] for e in pred[n] if e.src in reach]
                new = set.intersection(*incoming) if incoming else set()
                new = new | {n}
                if new != dom[n]:
                    dom[n] = new
                    changed = True
        return dom

    def immediate_dominators(self):
        dom = self.dominators()
        idom = {}
        for n, ds in dom.items():
            strict = ds - {n}
            if strict:
                idom[n] = max(strict, key=lambda d: len(dom[d]))
        return idom


def local_name(addr, prefix):
    """The name, in the scope with this prefix, of the step at addr or containing it."""
    if len(addr) > len(prefix) and addr[: len(prefix)] == prefix:
        return addr[len(prefix)]
    return addr[-1]


def open_body_forks(graph, infos):
    """Forks of a composition body that do not start the branches of one join.

    graph is the body's scope graph and infos its joins, from analyse_joins.
    Returns (pointer, address, message) problems.
    """
    if graph.root is None:
        return []
    succ = graph.successors()
    problems = []
    for addr in sorted(graph.reachable(graph.root)):
        node = graph.nodes[addr]
        if node.decl is None:
            continue
        for dsts in route_groups(graph, addr, succ).values():
            targets = set(dsts)
            if len(targets) < 2:
                continue
            # One join closes the fork: a branch that leaves closes its group,
            # and a branch failure reaches the join, so the body leaves once.
            if any(info["origin"] == addr and targets <= set(info["branches"]) for info in infos.values()):
                continue
            problems.append((node.pointer, addr, f"the fork at '{node.name}' does not start the branches of one join; a composition leaves at most once"))
            break
    return problems


def route_groups(graph, addr, succ):
    """Routes leaving a node, normal or error, as lists of destinations per route."""
    groups = {}
    for edge in succ[addr]:
        groups.setdefault((edge.kind, edge.key), []).append(edge.dst)
    return groups


def analyse_joins(graph):
    """Deduce origin and branches of every join.

    Returns (infos, problems); a problem is (code, pointer, address, message).
    """
    infos = {}
    problems = []
    if graph.root is None:
        return infos, problems
    idom = graph.immediate_dominators()
    succ = graph.successors()
    pred = graph.predecessors()
    reach = graph.reachable(graph.root)
    for addr, node in graph.nodes.items():
        if node.type != "join" or addr not in reach or addr not in idom:
            continue
        origin = idom[addr]
        joins_to_j = graph.reaching(addr, blocked={origin})
        starts = []
        for dsts in route_groups(graph, origin, succ).values():
            for dst in dsts:
                if dst in starts:
                    continue
                if dst == addr or dst in joins_to_j:
                    starts.append(dst)
        branches = {}
        for start in starts:
            if start == addr:
                branches[start] = set()
            else:
                forward = graph.reachable(start, blocked={origin, addr})
                branches[start] = forward & (joins_to_j | {start})
        # A branch is named after its first step; a direct route after the origin.
        prefix = node.scope.prefix
        name_of = {s: local_name(origin if s == addr else s, prefix) for s in starts}
        infos[addr] = {"origin": origin, "branches": branches, "names": name_of}

        # Real fork.
        groups = route_groups(graph, origin, succ)
        if not any(len({d for d in dsts if d in branches}) >= 2 for dsts in groups.values()):
            problems.append(("JOIN", node.pointer, addr, f"no route of the origin '{origin[-1]}' starts two branches or more at once"))
        # Disjoint branches.
        listed = list(branches.items())
        for i, (s1, b1) in enumerate(listed):
            for s2, b2 in listed[:i]:
                shared = b1 & b2
                if shared:
                    step = sorted(shared)[0]
                    problems.append(("JOIN", graph.nodes[step].pointer, step, f"step '{step[-1]}' belongs to two branches of join '{addr[-1]}'"))
        # Single entry.
        for start, members in branches.items():
            for member in members:
                for edge in pred[member]:
                    if edge.src in members:
                        continue
                    if edge.src == origin and member == start:
                        continue
                    problems.append(("JOIN", edge.pointer, edge.src, f"a route from '{edge.src[-1]}' enters branch '{name_of[start]}' of join '{addr[-1]}' from outside"))
        # Join inputs.
        all_members = set().union(*branches.values()) if branches else set()
        for edge in pred[addr]:
            if edge.kind == "normal" and (edge.src == origin or edge.src in all_members):
                continue
            problems.append(("JOIN", edge.pointer, edge.src, f"join '{addr[-1]}' receives a route from '{edge.src[-1]}', which is not one of its branches"))
        # Closed forks.
        for start, members in branches.items():
            for member in members:
                for dsts in route_groups(graph, member, succ).values():
                    inside = [d for d in dsts if d in members or d == addr]
                    if len(set(inside)) < 2:
                        continue
                    closers = {k for k in members if graph.nodes[k].type == "join" and idom.get(k) == member}
                    open_fork = any(
                        d == addr or addr in graph.reachable(d, blocked=closers | {origin})
                        for d in inside
                    )
                    if open_fork:
                        problems.append(("JOIN", graph.nodes[member].pointer, member, f"the fork at '{member[-1]}' is not closed by its own join before join '{addr[-1]}'"))
        # Quorum count.
        quorum = node.decl.get("quorum")
        if quorum and quorum["count"] > len(starts):
            problems.append(("JOIN", node.pointer + ["quorum", "count"], addr, f"count {quorum['count']} exceeds the {len(starts)} branches of join '{addr[-1]}'"))
    return infos, problems
