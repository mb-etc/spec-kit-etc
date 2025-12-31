# Spec-Kit Review UI – Design Proposal

## Goal
Enable **non-developers** to review and suggest edits to Spec-Kit-generated documentation  
(specs, requirements, plans) **without requiring git, VS Code, or direct access to the repo**.

The solution must be:
- Safe (no arbitrary file writes)
- Auditable
- Local-first
- Compatible with existing Spec-Kit workflows

---

## Core Concept
Spec-Kit provides a **local Review UI** that:
- Serves rendered Markdown files for review
- Allows reviewers to edit **copies** of `.md` files
- Saves review output separately
- Requires the developer to explicitly apply changes

No reviewer edits files in-place.

---

## Scope
### In Scope
- Markdown files only (`*.md`)
- Spec / requirements / planning documents
- Local web UI started from developer machine
- Multiple concurrent reviewers
- Review artifacts stored on disk

### Out of Scope (v1)
- Editing source code
- Executing commands from UI
- Direct Copilot / IDE control
- Auto-merging conflicting reviews

---

## High-Level Workflow

### 1. Developer starts review session
```bash
speckit review

	•	Launches local web UI
	•	Displays whitelisted Markdown files only
	•	Generates a review session ID

⸻

2. Reviewer interacts via browser

Reviewer can:
	•	Read rendered Markdown
	•	Edit file contents (editor + preview)
	•	Leave optional comments
	•	Mark review as:
	•	Approved
	•	Changes requested

Reviewer actions:
	•	NEVER modify repo files directly
	•	Edits are saved as review copies

⸻

3. Review output is written to disk

reviews/
  2025-01-02_anna/
    manifest.json
    copies/
      specs/feature-x.md
      docs/requirements.md

manifest.json

{
  "reviewer": "Anna",
  "timestamp": "2025-01-02T15:30:00Z",
  "files": [
    {
      "original_path": "specs/feature-x.md",
      "original_hash": "abc123",
      "copy_path": "copies/specs/feature-x.md",
      "copy_hash": "def456"
    }
  ]
}


⸻

Applying Reviews

Validate

speckit review validate reviews/2025-01-02_anna

Validation rules:
	•	Only .md files
	•	Only allowed directories
	•	Manifest matches disk
	•	Original hashes match repo (warn on drift)

⸻

Apply

speckit review apply reviews/2025-01-02_anna

Behavior:
	•	Creates a new git branch (e.g. review/2025-01-02_anna)
	•	Copies reviewed files into place
	•	Creates a commit with summary
	•	Prints list of files changed

⸻

Safety Constraints (Non-Negotiable)
	•	No in-place file edits from UI
	•	No command execution
	•	No path traversal outside allowed dirs
	•	No binary files
	•	Developer must explicitly apply changes
	•	All changes are git-tracked

⸻

Design Rationale
	•	Keeps developer machine safe
	•	Enables true non-dev participation
	•	Preserves audit trail
	•	Works offline
	•	Avoids forcing reviewers into tooling they don’t use

⸻

Future Enhancements
	•	AI-assisted merge when hashes drift
	•	Structured feedback forms
	•	Multiple reviewer aggregation
	•	Read-only “approval-only” mode
	•	Optional tunneling for remote review links

⸻

Open Questions
	•	CLI framework alignment (Typer / Click)
	•	UI framework (FastAPI + HTMX? React?)
	•	Default allowed directories
	•	Review retention / cleanup policy

