"""Flow graphs: composition expansion, dominators and join analysis.

Two kinds of graph are built. An expanded graph replaces each compose step by
its body; it follows messages and instances across compositions. A scope graph
keeps the steps of one scope, the flow or one composition body, with each
compose step as one step; joins are deduced there.
"""

from collections import deque


# Shared across scope graphs, expansions and analysis in one validation.
# Construction charges 32 units per stored item to bound memory as well as work.
GRAPH_WORK_LIMIT = 2_000_000
GRAPH_DEPTH_LIMIT = 128
# Building nodes, scopes and edges retains objects for later analysis.
GRAPH_ENTRY_COST = 32


class GraphLimitError(Exception):
    """Graph construction or analysis exceeded the validator's work limit."""


class GraphBudget:
    def __init__(self):
        self.remaining = GRAPH_WORK_LIMIT

    def spend(self, amount=1):
        self.remaining -= amount
        if self.remaining < 0:
            raise GraphLimitError("graph analysis exceeds the validator's work limit")


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


class Node:
    def __init__(self, addr, decl, scope, name):
        self.addr = addr
        self.decl = decl
        self.scope = scope
        self.name = name
        self.type = decl["type"] if decl is not None else "exit"
        self.pointer = scope.pointer + [name] if decl is not None else []
        self.agent = None
        if self.type == "agent":
            ref = decl["agent"]
            self.agent = ref if isinstance(ref, str) else scope.bindings.get(ref["parameter"])


class Edge:
    def __init__(self, src, dst, kind, key, message, pointer, fanout=None):
        self.src = src
        self.dst = dst
        self.kind = kind
        self.key = key
        self.message = message
        self.pointer = pointer
        # The authored fan-out target, with each, concurrency and max, or None.
        self.fanout = fanout
        self.each = fanout["each"] if fanout is not None else None


def route_items(route, pointer):
    """Yield (kind, name, message, pointer, fanout) for each target of an authored
    route; fanout is the target object when it has each, otherwise None."""
    items = route if isinstance(route, list) else [route]
    for index, item in enumerate(items):
        where = pointer + [index] if isinstance(route, list) else pointer
        if isinstance(item, str):
            yield "step", item, None, where, None
        elif "step" in item:
            yield "step", item["step"], item.get("message"), where, item if "each" in item else None
        else:
            yield "output", item["output"], item.get("message"), where, None


def route_targets(route, pointer):
    """Yield (kind, name, message, pointer) for each target of an authored route."""
    for kind, name, message, where, _ in route_items(route, pointer):
        yield kind, name, message, where


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

    def __init__(self, document, in_branch=None, covered=None, budget=None):
        self.document = document
        self.budget = budget if budget is not None else GraphBudget()
        # Names of the steps inside a join branch, per scope (None for the flow).
        self.in_branch = in_branch or {}
        # Top-level steps that use the flow's onError as their own.
        self.covered = covered or set()
        self.compositions = document.get("compositions", {})
        self.nodes = {}
        self.composes = {}
        self.edges = []
        self.root = None

    # Construction -------------------------------------------------------

    @classmethod
    def for_flow(cls, document, in_branch=None, covered=None, budget=None):
        """The flow expanded across compositions. `covered` names the top-level
        steps that use the flow's onError (see flow_error_covered)."""
        graph = cls(document, in_branch, covered, budget)
        flow = document["flow"]
        scope = Scope(flow["steps"], ["flow", "steps"], ())
        graph._add_scope(scope, ())
        graph._connect()
        graph.root = graph.resolve(scope, flow["entry"])
        return graph

    @staticmethod
    def flow_error_covered(document, branch_members=()):
        """The top-level steps that the flow's onError acts for, as if written
        on each: reachable from the entry without following it, not its
        targets, not in a join branch, and without an onError of their own."""
        flow = document["flow"]
        steps = flow["steps"]
        if "onError" not in flow or flow["entry"] not in steps:
            return set()
        targets = {name for kind, name, _, _ in route_targets(flow["onError"], []) if kind == "step"}
        seen = {flow["entry"]}
        queue = deque(seen)
        while queue:
            current = queue.popleft()
            for _, _, route, _ in step_routes(steps[current], []):
                for kind, name, _, _ in route_targets(route, []):
                    if kind == "step" and name in steps and name not in seen:
                        seen.add(name)
                        queue.append(name)
        return {
            name for name in seen
            if name not in targets and name not in branch_members and "onError" not in steps[name]
        }

    @classmethod
    def for_scope(cls, document, composition=None, covered=None, budget=None):
        """The steps of the flow, or of one composition body, with compose steps as one step."""
        graph = cls(document, covered=covered if composition is None else None, budget=budget)
        if composition is None:
            container = document["flow"]
            pointer = ["flow", "steps"]
        else:
            container = graph.compositions[composition]
            pointer = ["compositions", composition, "steps"]
        scope = Scope(container["steps"], pointer, (), composition=composition)
        for name, decl in scope.steps.items():
            graph.budget.spend(GRAPH_ENTRY_COST)
            graph.nodes[(name,)] = Node((name,), decl, scope, name)
        for node in list(graph.nodes.values()):
            for kind, key, route, rpointer in step_routes(node.decl, node.pointer):
                for tkind, tname, message, where, each in route_items(route, rpointer):
                    dst = graph._local_target(scope, tkind, tname)
                    if dst is not None:
                        graph.budget.spend(GRAPH_ENTRY_COST)
                        graph.edges.append(Edge(node.addr, dst, kind, key, message, where, each))
        for name in sorted(graph.covered):
            for tkind, tname, message, where, each in route_items(container["onError"], ["flow", "onError"]):
                dst = graph._local_target(scope, tkind, tname)
                if dst is not None:
                    graph.budget.spend(GRAPH_ENTRY_COST)
                    graph.edges.append(Edge((name,), dst, "error", None, message, where, each))
        entry = (container["entry"],)
        graph.root = entry if entry in graph.nodes else None
        return graph

    def _local_target(self, scope, kind, name):
        if kind == "step":
            return (name,) if (name,) in self.nodes else None
        if scope.composition is None:
            return None
        addr = ("#exit", name)
        if addr not in self.nodes:
            self.budget.spend(GRAPH_ENTRY_COST)
            self.nodes[addr] = Node(addr, None, scope, name)
        return addr

    @classmethod
    def for_composition(cls, document, name, in_branch=None, budget=None):
        graph = cls(document, in_branch, budget=budget)
        composition = graph.compositions[name]
        scope = Scope(composition["steps"], ["compositions", name, "steps"], ("#" + name,), composition=name)
        graph._add_scope(scope, (name,))
        graph._connect()
        graph.root = graph.resolve(scope, composition["entry"])
        return graph

    def _add_scope(self, scope, stack):
        if len(stack) > GRAPH_DEPTH_LIMIT:
            raise GraphLimitError("composition nesting exceeds the validator's depth limit")
        for name, decl in scope.steps.items():
            self.budget.spend(GRAPH_ENTRY_COST)
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

    def _targets(self, scope, kind, name, message, pointer, fanout):
        """Resolve one authored target to (address, message, pointer, fanout).

        A body route that leaves through a compose output carries no message:
        the compose step's route for that output gives the targets, with their
        messages, fan-outs and pointers."""
        self.budget.spend(GRAPH_ENTRY_COST)
        if kind == "step":
            addr = self.resolve(scope, name)
            return [(addr, message, pointer, fanout)] if addr is not None else []
        if scope.compose is None:
            if scope.composition is None:
                return []
            exit_addr = ("#exit", name)
            if exit_addr not in self.nodes:
                self.budget.spend(GRAPH_ENTRY_COST)
                self.nodes[exit_addr] = Node(exit_addr, None, scope, name)
            return [(exit_addr, message, pointer, fanout)]
        decl, _, parent = self.composes[scope.compose]
        route = decl.get("next", {}).get(name)
        if route is None:
            return []
        found = []
        outer = parent.pointer + [scope.compose[-1], "next", name]
        for kind2, name2, message2, where2, fanout2 in route_items(route, outer):
            found.extend(self._targets(parent, kind2, name2, message2, where2, fanout2))
        return found

    def _inherited_error(self, scope, name):
        """The error route of a body step without onError: the nearest enclosing
        join branch takes its failure first, then the compose step, in turn."""
        while scope.compose is not None:
            if name in self.in_branch.get(scope.composition, ()):
                return None
            decl, _, parent = self.composes[scope.compose]
            if "onError" in decl:
                pointer = parent.pointer + [scope.compose[-1], "onError"]
                return parent, decl["onError"], pointer
            name = scope.compose[-1]
            scope = parent
        if scope.composition is None and name in self.covered:
            return scope, self.document["flow"]["onError"], ["flow", "onError"]
        return None

    def _connect(self):
        for node in list(self.nodes.values()):
            if node.decl is None:
                continue
            routes = list(step_routes(node.decl, node.pointer))
            if "onError" not in node.decl:
                inherited = self._inherited_error(node.scope, node.name)
                if inherited is not None:
                    routes.append(("error", None, inherited[1], inherited[2], inherited[0]))
            for entry in routes:
                kind, key, route, pointer = entry[:4]
                scope = entry[4] if len(entry) > 4 else node.scope
                for tkind, tname, message, where, each in route_items(route, pointer):
                    for dst, carried, at, fanout in self._targets(scope, tkind, tname, message, where, each):
                        self.budget.spend(GRAPH_ENTRY_COST)
                        self.edges.append(Edge(node.addr, dst, kind, key, carried, at, fanout))

    # Queries ------------------------------------------------------------

    def successors(self):
        self.budget.spend(len(self.nodes) + len(self.edges))
        result = {addr: [] for addr in self.nodes}
        for edge in self.edges:
            result[edge.src].append(edge)
        return result

    def predecessors(self):
        self.budget.spend(len(self.nodes) + len(self.edges))
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

    def immediate_dominators(self):
        """Compute immediate dominators in reverse postorder with linear storage."""
        if self.root is None:
            return {}
        succ = self.successors()
        pred = self.predecessors()
        seen = {self.root}
        postorder = []
        stack = [(self.root, iter(succ[self.root]))]
        while stack:
            node, edges = stack[-1]
            edge = next(edges, None)
            self.budget.spend()
            if edge is None:
                postorder.append(node)
                stack.pop()
            elif edge.dst not in seen:
                seen.add(edge.dst)
                stack.append((edge.dst, iter(succ[edge.dst])))
        order = list(reversed(postorder))
        rank = {node: index for index, node in enumerate(order)}
        idom = {self.root: self.root}

        def intersect(left, right):
            while left != right:
                self.budget.spend()
                while rank[left] > rank[right]:
                    self.budget.spend()
                    left = idom[left]
                while rank[right] > rank[left]:
                    self.budget.spend()
                    right = idom[right]
            return left

        changed = True
        while changed:
            changed = False
            for node in order[1:]:
                self.budget.spend(len(pred[node]) + 1)
                incoming = [edge.src for edge in pred[node] if edge.src in idom]
                if not incoming:
                    continue
                parent = incoming[0]
                for predecessor in incoming[1:]:
                    parent = intersect(parent, predecessor)
                if idom.get(node) != parent:
                    idom[node] = parent
                    changed = True
        del idom[self.root]
        return idom

    def dominators(self):
        """Return the full dominator sets when a caller explicitly needs them."""
        if self.root is None:
            return {}
        parents = self.immediate_dominators()
        result = {self.root: {self.root}}
        for node in parents:
            path = set()
            current = node
            while current in parents:
                self.budget.spend()
                path.add(current)
                current = parents[current]
            path.add(current)
            result[node] = path
        return result


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
        for (kind, key), dsts in route_groups(graph, addr, succ).items():
            targets = set(dsts)
            fans = any(e.each is not None for e in succ[addr] if (e.kind, e.key) == (kind, key))
            if len(targets) < 2 and not fans:
                continue
            # One join closes the fork: a branch that leaves closes its group,
            # and a branch failure reaches the join, so the body leaves once.
            graph.budget.spend(sum(len(info["branches"]) + 1 for info in infos.values()))
            if any(info["origin"] == addr and targets <= set(info["branches"]) for info in infos.values()):
                continue
            problems.append((node.pointer, addr, f"the fork at '{node.name}' does not start the branches of one join; a composition leaves at most once"))
            break
    return problems


def route_groups(graph, addr, succ):
    """Routes leaving a node, normal or error, as lists of destinations per route."""
    graph.budget.spend(len(succ[addr]) + 1)
    groups = {}
    for edge in succ[addr]:
        groups.setdefault((edge.kind, edge.key), []).append(edge.dst)
    return groups


def join_origin(graph, join, idom, succ):
    """The origin of a join: its immediate dominator, unless that step lies in
    the paths of a fan-out, which run once per element. Then the origin is the
    step whose fan-out the join closes, found by walking up the dominators and
    pairing each join met on the way with the fork it closes."""
    first = idom[join]
    chain = []
    current = first
    while current is not None:
        graph.budget.spend()
        chain.append(current)
        current = idom.get(current)
    dominators = set(chain)

    def fork(step, fanout_only=False):
        graph.budget.spend(len(succ[step]) + 1)
        groups = {}
        for edge in succ[step]:
            groups.setdefault((edge.kind, edge.key), []).append(edge)
        for edges in groups.values():
            if any(e.each is not None and (e.dst in dominators or e.dst == join) for e in edges):
                return True
            if not fanout_only and len(edges) >= 2:
                reaching = {e.dst for e in edges if e.dst == join or join in graph.reachable(e.dst, blocked={step})}
                if len(reaching) >= 2:
                    return True
        return False

    if fork(first):
        return first
    closed = 0
    for step in chain:
        if graph.nodes[step].type == "join":
            closed += 1
        elif fork(step):
            if closed == 0:
                return step if fork(step, fanout_only=True) else first
            closed -= 1
    return first


def analyse_joins(graph):
    """Deduce origin and branches of every join.

    Returns (infos, problems); a problem is (code, pointer, address, message).
    """
    infos = {}
    problems = []
    if graph.root is None or not any(node.type == "join" for node in graph.nodes.values()):
        return infos, problems
    idom = graph.immediate_dominators()
    succ = graph.successors()
    pred = graph.predecessors()
    reach = graph.reachable(graph.root)
    origins = {
        addr: join_origin(graph, addr, idom, succ)
        for addr, node in graph.nodes.items()
        if node.type == "join" and addr in reach and addr in idom
    }
    for addr, origin in origins.items():
        node = graph.nodes[addr]
        joins_to_j = graph.reaching(addr, blocked={origin})
        starts = {}  # Preserve the origin route order when naming branches.
        for dsts in route_groups(graph, origin, succ).values():
            for dst in dsts:
                if dst in starts:
                    continue
                if dst == addr or dst in joins_to_j:
                    starts[dst] = None
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
        # Fan-out branches: started with each, once per element.
        started = [e for e in succ[origin] if e.dst in branches]
        fanout = {e.dst for e in started if e.each is not None}
        infos[addr] = {"origin": origin, "branches": branches, "names": name_of, "fanout": fanout}

        # Real fork.
        groups = route_groups(graph, origin, succ)
        if not fanout and not any(len({d for d in dsts if d in branches}) >= 2 for dsts in groups.values()):
            problems.append(("JOIN", node.pointer, addr, f"no route of the origin '{origin[-1]}' starts two branches or more at once"))
        # Fan-out branches are always started with each.
        for edge in started:
            if edge.dst in fanout and edge.each is None:
                problems.append(("JOIN", edge.pointer, origin, f"branch '{name_of[edge.dst]}' of join '{addr[-1]}' is a fan-out on another route; start it with each on every route"))
        # Disjoint branches.
        listed = list(branches.items())
        for i, (s1, b1) in enumerate(listed):
            for s2, b2 in listed[:i]:
                graph.budget.spend(min(len(b1), len(b2)) + 1)
                shared = b1 & b2
                if shared:
                    step = sorted(shared)[0]
                    problems.append(("JOIN", graph.nodes[step].pointer, step, f"step '{step[-1]}' belongs to two branches of join '{addr[-1]}'"))
        # Single entry.
        for start, members in branches.items():
            for member in members:
                graph.budget.spend(len(pred[member]) + 1)
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
                for (kind, key), dsts in route_groups(graph, member, succ).items():
                    inside = [d for d in dsts if d in members or d == addr]
                    if inside and len(inside) < len(dsts):
                        problems.append(("JOIN", graph.nodes[member].pointer, member, f"a route of '{member[-1]}' starts targets inside and outside branch '{name_of[start]}' of join '{addr[-1]}' at once"))
                        continue
                    fans = any(e.each is not None and e.dst in inside for e in succ[member] if (e.kind, e.key) == (kind, key))
                    if len(set(inside)) < 2 and not fans:
                        continue
                    graph.budget.spend(len(members))
                    closers = {k for k in members if origins.get(k) == member}
                    open_fork = any(
                        d == addr or addr in graph.reachable(d, blocked=closers | {origin})
                        for d in inside
                    )
                    if open_fork:
                        problems.append(("JOIN", graph.nodes[member].pointer, member, f"the fork at '{member[-1]}' is not closed by its own join before join '{addr[-1]}'"))
        # Quorum count.
        quorum = node.decl.get("quorum")
        if quorum and not fanout and quorum["count"] > len(starts):
            problems.append(("JOIN", node.pointer + ["quorum", "count"], addr, f"count {quorum['count']} exceeds the {len(starts)} branches of join '{addr[-1]}'"))
    return infos, problems
