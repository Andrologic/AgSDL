# Scope

## Problem

Agent frameworks describe systems through framework-specific code and
configuration. The same concepts are represented differently or left implicit.
This makes systems difficult to inspect, compare, validate, migrate, and govern.

AgSDL aims to define a framework-independent model for an agentic system. The
model must represent both individual agents and the system-level relationships
that determine behavior.

## Repository outputs

As established by [Decision 0003](decisions/0003-repository-boundary.md), this
repository maintains:

- repository governance, contribution, licensing, publication, automation, and
  verification material;
- research, decisions, proposals, and the AgSDL specification;
- schemas, examples, fixtures, and conformance material;
- versioned mappings for external formats and protocols;
- non-normative reference tooling for reading, transforming, and analyzing
  AgSDL artifacts.

Planned tooling operations include parsing, validation, normalization,
reference resolution, and static inspection. Their precise behavior remains
subject to accepted decisions and the normative specification. Documentation
for a reference-tooling report identifies its input and the checks or
transformations it covers.

## In scope

- system identity, boundaries, goals, ownership, and interfaces;
- agent definitions and reusable agent components;
- models, prompts, tools, skills, memory, knowledge, and state;
- orchestration, topology, routing, delegation, handoffs, and protocols;
- permissions, credentials references, policy, guardrails, and approvals;
- declarative runtime and deployment requirements without prescribing an
  implementation;
- observability, evaluation, testing, conformance, and lifecycle metadata;
- references, packages, profiles, extensions, and version compatibility.

## Implementation boundary

Reference tooling may return transformed artifacts, diagnostics, and reports.
It does not execute the systems described by AgSDL artifacts. Conformance
material may include tests and harnesses that exercise implementations against
adopted requirements. Runtime and deployment remain declarative subjects of the
language.

External systems are described through the interfaces and documented behavior
relevant to AgSDL mappings and conformance.

## Out of scope for the first draft

- a universal agent runtime;
- a new agent communication transport;
- a model-provider API;
- a graphical editor contract;
- framework-specific behavior presented as portable semantics;
- claims of interoperability without executable conformance tests.

## Success condition

The first public draft succeeds when two independent implementations can parse
the same conforming document, agree on its portable meaning, report the same
structural validation failures, and identify every implementation-specific
extension.
