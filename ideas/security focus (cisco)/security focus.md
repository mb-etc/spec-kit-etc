# Security Pack (Curated) – Design Proposal

concept taken from https://github.com/project-codeguard/rules

## Goal
Ship a curated, org-specific security ruleset inside Spec-Kit to improve spec quality,
reduce security misses, and provide consistent review checklists.

## Core Concept
A versioned “security pack” lives in-repo and drives:
- injected spec sections
- checklists for Review UI
- optional Copilot instructions exports

## Workflow
1) Project selects context/flavor
2) Spec-Kit chooses a security pack
3) Spec generation includes required sections + checklists
4) Review UI renders security checklist and captures feedback
5) Dev applies changes and commits

## Safety Constraints
- No network dependency required
- Packs are versioned and reviewed like code
- Pack changes are explicit and changelogged

## Future Enhancements
- Pack inheritance / overrides per flavor
- Security linting for spec completeness
- Traceability: spec → checklist → tests

## Open Questions
- Baseline pack scope (Top 10 vs by-flavor)
- Ownership and update cadence
- Where to export Copilot-facing instructions