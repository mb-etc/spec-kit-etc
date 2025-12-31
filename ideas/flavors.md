# Spec-Kit Flavors – Design Proposal

## Goal
Enable multiple **“flavors” of Spec-Kit** that tailor behavior, templates, and guidance
to different product types, platforms, or languages (e.g., C++, Java, Python),
while maintaining a shared upstream and common core.

Flavors allow teams to standardize how they work **without forking core logic**.

---

## Core Concept
Spec-Kit supports **named flavors** that define:
- Default templates
- Context assumptions
- Prompting behavior
- Optional tooling conventions

Flavors are selectable at init time and changeable later.

---

## Scope
### In Scope
- Flavor declaration and selection
- Flavor-specific templates
- Flavor-aware prompts
- Shared upstream compatibility

### Out of Scope (v1)
- Hard language enforcement
- Per-flavor runtime plugins
- Automatic flavor detection

---

## Flavor Types (Examples)

- Platform flavors (e.g., embedded, web, services)
- Language flavors (e.g., C++, Java, Python)
- Product-line flavors (shared architectural patterns)
- Deployment flavors (cloud-native, on-prem)

Flavors are **descriptive**, not restrictive.

---

## High-Level Workflow

### 1. Flavor selection
On init or first run:

```bash
speckit init

User is prompted:
	•	Select flavor (or “default”)
	•	Optional sub-flavor
	•	Confirm assumptions

⸻

2. Flavor metadata is stored

.specify/
  flavor.yaml

Example:

flavor: python-service
description: >
  Backend service development using Python with API-first design.

assumptions:
  - REST or async messaging
  - CI-based testing
  - Typed interfaces

templates:
  - specs/api.md
  - specs/data-model.md


⸻

3. Flavor-specific templates

Each flavor may provide:
	•	Custom spec skeletons
	•	Pre-filled sections
	•	Language-appropriate terminology

Example:

flavors/
  python-service/
    templates/
      api.md
      data-model.md
  cpp-embedded/
    templates/
      memory.md
      interfaces.md


⸻

Prompting Adjustments

Based on flavor, Spec-Kit may:
	•	Ask language-specific questions
	•	Emphasize platform constraints
	•	Suggest common patterns

Example:
	•	“How will memory ownership be handled?” (C++)
	•	“What async model is used?” (Python)

⸻

Flavor Evolution

Flavors may evolve independently:
	•	New templates added
	•	Prompts refined
	•	Assumptions updated

Existing projects retain their chosen flavor unless changed.

⸻

Safety Constraints (Non-Negotiable)
	•	Core Spec-Kit behavior remains shared
	•	Flavors cannot override safety checks
	•	Flavor selection must be explicit
	•	Default flavor always available

⸻

Design Rationale
	•	Encourages consistency without rigidity
	•	Reduces copy-paste forks
	•	Enables experimentation
	•	Keeps institutional knowledge reusable

⸻

Future Enhancements
	•	Flavor inheritance
	•	Multiple flavors per project
	•	Flavor-aware linting
	•	Flavor-specific review checklists

⸻

Open Questions
	•	Flavor distribution mechanism (branches vs folders)
	•	How strict flavor assumptions should be
	•	Backward compatibility guarantees