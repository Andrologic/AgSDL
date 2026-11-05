# Scope

## Problem

Agent harnesses configure agents in their own formats, and multi-agent work is
usually wired in code. The same concepts — instructions, models, permissions,
handing work from one agent to another — are expressed differently by each
tool, or left implicit. Agent setups are hard to inspect, compare, move between
harnesses and review for safety.

AgSDL defines one harness-independent language for agents and the flows that
connect them.

## What this repository maintains

- the specification of the current edition, in `spec/`;
- the JSON Schemas that enforce its shapes, in `schema/`;
- harness modules, one per supported harness, in `harnesses/`;
- examples, conformance cases and run scenarios;
- reference tooling that reads, validates and draws documents;
- the decisions that explain the design, and the project's governance.

Only the current edition is kept in the tree. Earlier editions remain
available from their Git tags.

## In scope

- agent definitions: identity, instructions, model, skills, MCP servers,
  permissions, results and how an agent conducts its work;
- flows: steps, routes, messages, delivery to running agents, parallel
  branches, approvals, reusable compositions and failures;
- harness modules: what each harness supports, and how it enforces
  permissions;
- static validation and its diagnostics.

## Out of scope

- running agents or flows. Tooling here reads documents; it never executes
  them. Hosts such as Macro run them;
- exporters that write a harness's native files, and adapters that connect a
  harness to a host. They live beside the modules, in the projects that need
  them;
- a model-provider API, a transport protocol or a graphical editor contract;
- features that no harness has. AgSDL standardizes what harnesses do.

## Success condition

AgSDL 1.0 succeeds when two independent validators agree on every
conformance case, and when at least two hosts run the same documents across
several harnesses with the meaning the specification gives them.
