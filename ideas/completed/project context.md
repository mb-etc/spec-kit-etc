Below is the same Copilot-friendly Markdown format, tuned specifically for Context-Aware Spec-Kit. You can drop this in alongside the review UI doc (e.g. .specify/ideas/context-aware-speckit.md).

⸻


# Context-Aware Spec-Kit – Design Proposal

## Goal
Enable Spec-Kit to understand **project context** (greenfield, brownfield, bluefield) and adapt
its prompting, validation, and spec generation behavior accordingly.

The intent is to produce **more accurate, realistic, and intention-aligned specs**, especially
when working in existing or partially existing systems.

---

## Core Concept
Spec-Kit captures and persists **project context metadata** and uses it to:

- Adjust required inputs
- Prompt for additional artifacts
- Change generation and review behavior
- Allow projects to evolve from one context to another over time

Context is **explicit**, not inferred.

---

## Context Types

### Greenfield
- No existing system
- Minimal historical constraints
- Full design freedom

### Brownfield
- Existing system with active usage
- Legacy behavior and constraints matter
- Risk of regressions

### Bluefield
- Existing platform with new components
- Hybrid of greenfield and brownfield concerns

---

## Scope
### In Scope
- Explicit context declaration
- Context stored in-repo
- Context-aware prompting
- Optional artifact linking
- Context change over time

### Out of Scope (v1)
- Automatic system discovery
- Deep Jira / Confluence API integrations
- Enforcement of artifact correctness

---

## High-Level Workflow

### 1. Context is declared
On project init or first Spec-Kit run:

```bash
speckit init

User is prompted:
	•	Project type (green / brown / blue)
	•	Brief system description
	•	Known constraints

Context is saved.

⸻

2. Context metadata is stored

.specify/
  context.yaml

Example:

project_type: brownfield
description: >
  Enhancements to an existing manufacturing quality tracking system
  integrated with SAP ECC.

constraints:
  - Must not change existing APIs
  - Data model changes require migration

linked_artifacts:
  jira:
    - QM-1234
    - QM-1256
  confluence:
    - Legacy Quality Workflow Overview
  docs:
    - docs/known-issues.md


⸻

3. Spec-Kit adapts behavior

Greenfield
	•	Minimal historical prompts
	•	Emphasis on clean architecture
	•	No legacy validation steps

Brownfield
	•	Prompts for:
	•	Existing behavior
	•	Known bugs
	•	Technical debt
	•	Encourages:
	•	Backward compatibility notes
	•	Migration considerations
	•	Risk sections in specs

Bluefield
	•	Prompts for:
	•	Integration points
	•	Shared services
	•	Separates:
	•	New components vs existing ones

⸻

Prompting Adjustments

Based on context, Spec-Kit may ask:
	•	“What existing behavior must remain unchanged?”
	•	“Are there known failure modes or bugs?”
	•	“Which components are considered untouchable?”

These prompts are context-gated.

⸻

Context Evolution

Context may change over time.

Example:

speckit context update

Allows:
	•	green → brown
	•	blue → brown

History is preserved (append-only).

⸻

Safety Constraints (Non-Negotiable)
	•	Context must be explicit and versioned
	•	Context changes require confirmation
	•	Specs must reference context
	•	No silent behavior changes

⸻

Design Rationale
	•	Prevents “greenfield thinking” in brownfield systems
	•	Makes assumptions explicit
	•	Improves AI grounding
	•	Encourages better stakeholder alignment

⸻

Future Enhancements
	•	Context-based linting of specs
	•	API-backed artifact validation
	•	Context-aware test generation
	•	Risk scoring by context

⸻

Open Questions
	•	Default context on init
	•	Required vs optional artifacts
	•	Context enforcement strictness
	•	UI vs CLI editing of context

---

If you want, next we can:
- Merge this with the **Review UI** doc into a single Spec-Kit roadmap
- Turn this into a **Spec-Kit RFC**
- Break it into **v1/v2 milestones**
- Generate **Copilot prompts** that consume `context.yaml` directly