# Integration Outline: Additional Agents into Spec Kit

## ✅ IMPLEMENTATION COMPLETE

**Completed**: December 31, 2025

All 7 review agents have been converted and integrated into Spec Kit.

---

## Summary of Changes

### New Command Files Created

| File | Description |
|------|-------------|
| `templates/commands/review-uat.md` | UAT Coordinator - Create UAT plans and checklists |
| `templates/commands/review-implementation.md` | Implementation Reviewer - Audit code vs spec |
| `templates/commands/fix.md` | Spec-Aligned Fixer - Diagnose and fix issues |
| `templates/commands/review-readiness.md` | Production Readiness - Deploy gates and runbooks |
| `templates/commands/release-notes.md` | Release Notes Author - Generate changelogs |
| `templates/commands/review-summary.md` | Project Summarizer - Documentation pack |
| `templates/commands/review-security.md` | Security Reviewer - Vulnerability scan |

### New Script Files Created

| File | Description |
|------|-------------|
| `scripts/bash/review-feature.sh` | Bash script for review context |
| `scripts/powershell/review-feature.ps1` | PowerShell script for review context |

### Updated Files

| File | Change |
|------|--------|
| `templates/commands/constitution.md` | Added review command references to propagation checklist |

---

## Workflow Integration

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SPEC-DRIVEN DEVELOPMENT                         │
├─────────────────────────────────────────────────────────────────────────┤
│  SPECIFICATION PHASE                                                    │
│  ├── /speckit.specify     → Create feature spec                        │
│  ├── /speckit.clarify     → Clarify requirements                       │
│  └── /speckit.plan        → Create technical plan                      │
├─────────────────────────────────────────────────────────────────────────┤
│  IMPLEMENTATION PHASE                                                   │
│  ├── /speckit.tasks       → Generate implementation tasks              │
│  ├── /speckit.implement   → Implement code changes                     │
│  ├── /speckit.fix         → ✅ NEW: Diagnose and fix issues            │
│  └── /speckit.analyze     → Analyze codebase                           │
├─────────────────────────────────────────────────────────────────────────┤
│  REVIEW PHASE  ✅ NEW                                                   │
│  ├── /speckit.review-implementation → Audit code vs spec               │
│  ├── /speckit.review-security       → Security vulnerability scan      │
│  └── /speckit.review-uat            → Generate UAT plan/checklist      │
├─────────────────────────────────────────────────────────────────────────┤
│  RELEASE PHASE  ✅ NEW                                                  │
│  ├── /speckit.review-readiness → Deploy readiness check                │
│  ├── /speckit.release-notes    → Generate changelog/release notes      │
│  └── /speckit.review-summary   → Create documentation pack             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Checklist ID Formats Adopted

| Command | ID Format | Example |
|---------|-----------|---------|
| review-uat | UAT### | UAT001, UAT002 |
| review-implementation | IMP### | IMP001, IMP002 |
| review-security | SEC### | SEC001, SEC-CRIT-001 |
| review-readiness | RDY###, CON###, etc. | RDY001, CON001, SEC001 |
| release-notes | RN###, BC### | RN001, BC001 |
| fix | FIX### | FIX001, FIX002 |

---

## Original Document

This document outlines the plan for integrating the "additional agents" (specialized review chat modes) from `ideas/additional agents/` into the Spec Kit installation process. These agents complement the core SDD workflow by providing specialized review, documentation, and release capabilities.

---

## 1. Current State Analysis

### Existing Agent Files (7 total)

| File | Agent Role | Purpose |
|------|------------|---------|
| `5-Release Notes.chatmode.md` | Release Notes Author | Generate changelogs, release notes, and version updates |
| `Review-Implementation Reviewier.chatmode.md` | Implementation Reviewer | Audit code against tech specs, produce compliance matrix |
| `Review-Problem Solver.chatmode.md` | Engineer (Fixer) | Diagnose issues, propose targeted fixes with evidence |
| `Review-Production Readiness.chatmode.md` | Production Readiness Reviewer | Deploy-readiness gates, cutover/rollback runbooks |
| `Review-Project Summary.chatmode.md` | Project Summarizer | Generate doc packs for tech + end users |
| `Review-Security.chatmode.md` | Security Reviewer | Lightweight security pass, vulnerability findings |
| `Review-UAT Coordinator.chatmode.md` | UAT Coordinator | Create UAT plans and manual checklists |

### Current Spec Kit Command Structure

- **Location**: `templates/commands/*.md`
- **Naming**: `speckit.<command>.md` (e.g., `speckit.plan.md`)
- **Format**: Markdown with YAML frontmatter (description, scripts, handoffs)
- **Installation**: Commands are transformed per-agent and placed in agent-specific directories

---

## 2. Design Decisions Required

### 2.1 Naming Convention

**Option A: Unified `speckit.` prefix (Recommended)**
```
speckit.review-implementation.md
speckit.review-security.md
speckit.review-uat.md
speckit.review-readiness.md
speckit.review-summary.md
speckit.fix.md
speckit.release-notes.md
```

**Option B: Grouped `speckit.review.*` namespace**
```
speckit.review.implementation.md
speckit.review.security.md
speckit.review.uat.md
speckit.review.readiness.md
speckit.review.summary.md
speckit.fix.md
speckit.release.notes.md
```

**Recommendation**: Option A - maintains flat structure consistent with existing commands.

### 2.2 File Location

**New structure**:
```
templates/
├── commands/
│   ├── analyze.md          # Existing
│   ├── checklist.md        # Existing
│   ├── clarify.md          # Existing
│   ├── constitution.md     # Existing
│   ├── implement.md        # Existing
│   ├── plan.md             # Existing
│   ├── specify.md          # Existing
│   ├── tasks.md            # Existing
│   ├── taskstoissues.md    # Existing
│   ├── fix.md              # NEW - Problem Solver
│   ├── release-notes.md    # NEW - Release Notes Author
│   ├── review-implementation.md  # NEW - Implementation Reviewer
│   ├── review-readiness.md       # NEW - Production Readiness
│   ├── review-security.md        # NEW - Security Reviewer
│   ├── review-summary.md         # NEW - Project Summarizer
│   └── review-uat.md             # NEW - UAT Coordinator
```

### 2.3 Installation Behavior

**Options**:
- **A. Always install all agents** (simplest)
- **B. Add `--include-review-agents` flag** (opt-in)
- **C. Add `--minimal` flag** (opt-out, install all by default)

**Recommendation**: Option A initially - these are lightweight files and provide value without complexity.

---

## 3. Required Modifications

### 3.1 Convert `.chatmode.md` to Spec Kit Command Format

Each file needs to be converted from VS Code chat mode format to Spec Kit command format:

**Current format (chatmode)**:
```markdown
---
description: 'Quick description'
tools: ['codebase', 'usages', ...]
---
# Role
You are the **Role Name**.
...
```

**Target format (Spec Kit command)**:
```markdown
---
description: Quick description for this review command
handoffs:
  - label: Follow-up Action
    agent: speckit.implement
    prompt: Implement the recommended fixes
scripts:
  sh: echo "No script required for review-only commands"
  ps: Write-Host "No script required for review-only commands"
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Role
You are the **Role Name**.

## Inputs
...

## Deliverables
...

## Rules
...
```

### 3.2 Add Handoffs Between Commands

Create logical workflow connections:

| Command | Logical Handoffs |
|---------|------------------|
| `review-implementation` | → `speckit.fix` (fix gaps), `speckit.tasks` (create tasks) |
| `review-security` | → `speckit.fix` (apply fixes), `speckit.tasks` (create tasks) |
| `review-uat` | → `speckit.checklist` (generate test checklist) |
| `review-readiness` | → `speckit.release-notes` (create release notes) |
| `fix` | → `speckit.implement` (apply fixes), `speckit.analyze` (verify) |
| `release-notes` | → (terminal - generates final artifacts) |
| `review-summary` | → (terminal - generates documentation) |

### 3.3 Script Placeholders

For review-only commands without scripts, use placeholder scripts:
```yaml
scripts:
  sh: echo "Review command - no automated script"
  ps: Write-Host "Review command - no automated script"
```

Alternatively, make scripts optional in the command format (requires CLI changes).

### 3.4 Update Release Package Scripts

**Files to modify**:
- `.github/workflows/scripts/create-release-packages.sh`
- `.github/workflows/scripts/create-release-packages.ps1`

The `generate_commands()` function already processes all `templates/commands/*.md` files, so new commands will be automatically included.

---

## 4. Integration with SDD Workflow

### 4.1 Workflow Phases

Position the new agents in the SDD lifecycle:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SPEC-DRIVEN DEVELOPMENT                         │
├─────────────────────────────────────────────────────────────────────────┤
│  SPECIFICATION PHASE                                                    │
│  ├── /speckit.specify     → Create feature spec                        │
│  ├── /speckit.clarify     → Clarify requirements                       │
│  └── /speckit.plan        → Create technical plan                      │
├─────────────────────────────────────────────────────────────────────────┤
│  IMPLEMENTATION PHASE                                                   │
│  ├── /speckit.tasks       → Generate implementation tasks              │
│  ├── /speckit.implement   → Implement code changes                     │
│  ├── /speckit.fix         → [NEW] Diagnose and fix issues              │
│  └── /speckit.analyze     → Analyze codebase                           │
├─────────────────────────────────────────────────────────────────────────┤
│  REVIEW PHASE  [NEW]                                                    │
│  ├── /speckit.review-implementation → Audit code vs spec               │
│  ├── /speckit.review-security       → Security vulnerability scan      │
│  └── /speckit.review-uat            → Generate UAT plan/checklist      │
├─────────────────────────────────────────────────────────────────────────┤
│  RELEASE PHASE  [NEW]                                                   │
│  ├── /speckit.review-readiness → Deploy readiness check                │
│  ├── /speckit.release-notes    → Generate changelog/release notes      │
│  └── /speckit.review-summary   → Create documentation pack             │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Update Constitution Command

Add reference to new agents in `templates/commands/constitution.md` so the AI knows about available review commands.

---

## 5. Implementation Checklist

### Phase 1: Prepare Command Files

- [ ] Create `templates/commands/fix.md` from `Review-Problem Solver.chatmode.md`
- [ ] Create `templates/commands/release-notes.md` from `5-Release Notes.chatmode.md`
- [ ] Create `templates/commands/review-implementation.md` from `Review-Implementation Reviewier.chatmode.md`
- [ ] Create `templates/commands/review-readiness.md` from `Review-Production Readiness.chatmode.md`
- [ ] Create `templates/commands/review-security.md` from `Review-Security.chatmode.md`
- [ ] Create `templates/commands/review-summary.md` from `Review-Project Summary.chatmode.md`
- [ ] Create `templates/commands/review-uat.md` from `Review-UAT Coordinator.chatmode.md`

### Phase 2: Update Existing Files

- [ ] Update `templates/commands/constitution.md` to reference new review commands
- [ ] Update `templates/commands/implement.md` with handoff to `speckit.fix`
- [ ] Update `README.md` to document new commands

### Phase 3: Testing

- [ ] Run `specify init . --ai copilot` and verify new commands appear
- [ ] Run `specify init . --ai claude` and verify new commands appear
- [ ] Test each new command works correctly in VS Code
- [ ] Verify handoffs work between commands

### Phase 4: Documentation

- [ ] Update `docs/quickstart.md` with review workflow
- [ ] Add `docs/review-agents.md` explaining the review phase
- [ ] Update `CHANGELOG.md` with new features

### Phase 5: Version & Release

- [ ] Bump version in `pyproject.toml`
- [ ] Add CHANGELOG entry
- [ ] Create PR with all changes
- [ ] Tag release after merge

---

## 6. Command Conversion Templates

### 6.1 Template: Review Command (No Script)

```markdown
---
description: [Brief description of what this reviewer does]
handoffs:
  - label: [Action to take after review]
    agent: speckit.[next-command]
    prompt: [Prompt for handoff]
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Role

You are the **[Role Name]**.

## Inputs

[What this command needs as input - files, context, etc.]

## Deliverables

[What this command produces - files, reports, etc.]

## Process

1. [Step 1]
2. [Step 2]
...

## Rules

- [Rule 1]
- [Rule 2]
...
```

### 6.2 Template: Action Command (With Script Optional)

```markdown
---
description: [Brief description]
handoffs:
  - label: [Follow-up action]
    agent: speckit.[command]
scripts:
  sh: [bash command or placeholder]
  ps: [powershell command or placeholder]
---

## User Input

```text
$ARGUMENTS
```

[Rest of command content...]
```

---

## 7. Open Questions

1. **Tool dependencies**: The chatmode files specify VS Code tools (`codebase`, `usages`, etc.). Should we translate these to a tool requirements section for documentation purposes?

2. **Agent-specific variations**: Do any review commands need agent-specific customization (like TOML format for Gemini/Qwen)?

3. **Output directories**: Several review commands create files in `docs/` subdirectories. Should we standardize these paths?

4. **Script requirements**: Should review commands have scripts that create the expected output directories?

5. **Spec file integration**: Should review commands reference the current feature's spec file automatically (like other SDD commands)?

---

## 8. Success Criteria

- [ ] All 7 new commands install correctly with `specify init`
- [ ] Commands work across all supported AI agents (Claude, Copilot, Gemini, etc.)
- [ ] Handoffs between commands work correctly
- [ ] Documentation clearly explains the review workflow
- [ ] No breaking changes to existing Spec Kit functionality
