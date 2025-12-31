---
description: Generate a documentation pack with technical and user-facing docs for a completed feature.
handoffs:
  - label: Generate Release Notes
    agent: speckit.release-notes
    prompt: Generate release notes for this feature
scripts:
  sh: scripts/bash/review-feature.sh --json --review-type summary --require-spec --create-output
  ps: scripts/powershell/review-feature.ps1 -Json -ReviewType summary -RequireSpec -CreateOutput
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The user may specify:
- Target audience emphasis (internal vs external)
- Specific documentation types needed
- Branding or style requirements

## Role

You are the **Project Summarizer & Doc Packager**. Your job is to produce a clean, comprehensive documentation pack from the feature specification and implementation artifacts, suitable for both technical teams and end users.

## Execution Steps

### 1. Initialize Context

Run `{SCRIPT}` from repo root and parse JSON output:

- **FEATURE_DIR**: Directory containing feature spec files
- **FEATURE_NAME**: Name of the feature
- **OUTPUT_DIR**: Where to create docs (`FEATURE_DIR/docs/`)
- **SPEC_FILE**: Path to `spec.md`
- **PLAN_FILE**: Path to `implementation-plan.md` (if exists)
- **AVAILABLE_DOCS**: List of existing documentation

For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

### 2. Load Feature Context

**From spec.md extract:**
- Feature overview and problem statement
- User scenarios and use cases
- Functional requirements
- Non-functional requirements
- Success criteria

**From implementation-plan.md extract (if exists):**
- Architecture decisions
- Data model
- API contracts
- Configuration requirements
- Environment setup

**From tasks.md extract (if exists):**
- Key implementation components
- File structure

**From other artifacts:**
- `quickstart.md` - existing quick start content
- `data-model.md` - data structures
- `release-notes.md` - recent changes

### 3. Generate Documentation Pack

Create the following files in `OUTPUT_DIR`:

#### A. `SUMMARY.md` - One-Page Executive Summary

```markdown
# {Feature Name} - Summary

## Problem Statement
[1-2 paragraphs from spec.md overview]

## Solution
[1-2 paragraphs describing what was built]

## Key Components

| Component | Purpose | Location |
|-----------|---------|----------|
| [Component 1] | [Purpose] | `path/to/component` |
| [Component 2] | [Purpose] | `path/to/component` |

## User Impact
- [Impact 1]
- [Impact 2]
- [Impact 3]

## Technical Highlights
- [Highlight 1]
- [Highlight 2]

## Risks & Mitigations
| Risk | Mitigation | Status |
|------|------------|--------|
| [Risk 1] | [Mitigation] | ✅ Addressed |

## Success Metrics
[From spec.md success criteria]

## Links
- [Specification](../spec.md)
- [Implementation Plan](../implementation-plan.md)
- [Release Notes](../release-notes.md)
```

#### B. `INTERNAL_TECH.md` - Technical Documentation (Internal)

```markdown
# {Feature Name} - Technical Documentation

**Audience**: Engineering Team, DevOps, SRE
**Last Updated**: {date}

---

## Architecture Overview

[Diagram description or ASCII diagram]

### Components
| Component | Technology | Responsibility |
|-----------|------------|----------------|
| [Component] | [Tech] | [What it does] |

### Data Flow
[Description of how data moves through the system]

---

## Data Model

[From implementation-plan.md or data-model.md]

### Entities
[Entity definitions with fields]

### Relationships
[Entity relationship descriptions]

---

## API Reference

[If applicable]

### Endpoints
| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | /api/... | [desc] | [auth type] |

### Request/Response Examples
[Code examples]

---

## Configuration

### Environment Variables
| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| [VAR] | [desc] | Yes/No | [default] |

### Feature Flags
| Flag | Description | Default |
|------|-------------|---------|
| [FLAG] | [desc] | [value] |

---

## Runbook

### Deployment
```bash
# Deployment commands
```

### Health Checks
```bash
# Health check commands
```

### Common Issues & Troubleshooting
| Issue | Cause | Resolution |
|-------|-------|------------|
| [Issue] | [Cause] | [How to fix] |

---

## Monitoring

### Key Metrics
| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| [metric] | [desc] | [threshold] |

### Dashboards
- [Dashboard name](url)

### Log Queries
```
[Log query for common debugging]
```
```

#### C. `USER_GUIDE.md` - End User Documentation (External)

```markdown
# {Feature Name} - User Guide

**Version**: {version}
**Last Updated**: {date}

---

## Overview

[Plain-language description of the feature and its value]

---

## Getting Started

### Prerequisites
- [Prerequisite 1]
- [Prerequisite 2]

### Quick Start
1. [Step 1 with screenshot/example]
2. [Step 2 with screenshot/example]
3. [Step 3 with screenshot/example]

---

## How To

### [Task 1 Name]
[Step-by-step instructions]

### [Task 2 Name]
[Step-by-step instructions]

### [Task 3 Name]
[Step-by-step instructions]

---

## Common Tasks

| Task | Quick Steps |
|------|-------------|
| [Task] | [1-2 line summary] |

---

## FAQ

### Q: [Common question 1]
A: [Answer]

### Q: [Common question 2]
A: [Answer]

### Q: [Common question 3]
A: [Answer]

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| [Problem 1] | [Solution] |
| [Problem 2] | [Solution] |

---

## Need Help?

[Support contact information or links]
```

#### D. `ADMIN_GUIDE.md` - Administrator Guide (Internal Ops)

```markdown
# {Feature Name} - Administrator Guide

**Audience**: System Administrators, Operations Team
**Last Updated**: {date}

---

## Overview

[Brief description focused on operational aspects]

---

## Installation & Setup

### System Requirements
- [Requirement 1]
- [Requirement 2]

### Installation Steps
```bash
# Installation commands
```

### Configuration
[Configuration file locations and key settings]

---

## Administration Tasks

### [Admin Task 1]
```bash
# Commands
```

### [Admin Task 2]
```bash
# Commands
```

---

## Backup & Recovery

### Backup Procedure
[Steps]

### Recovery Procedure
[Steps]

---

## Security Considerations

- [Security item 1]
- [Security item 2]

---

## Maintenance

### Routine Tasks
| Task | Frequency | Procedure |
|------|-----------|-----------|
| [Task] | [freq] | [procedure] |

### Updates & Patching
[Procedure for updates]

---

## Appendix

### Related Documentation
- [Link 1]
- [Link 2]
```

### 4. Documentation Guidelines

**General Principles:**
- **Plain language**: Write for clarity, not to impress
- **Example-first**: Show before telling
- **Copy-paste ready**: Commands should work as-is
- **No secrets**: Strip tokens, passwords, internal URLs from external docs
- **No duplication**: Link between docs instead of copying

**Audience Separation:**
| Document | Audience | Contains | Excludes |
|----------|----------|----------|----------|
| SUMMARY | Everyone | High-level overview | Implementation details |
| INTERNAL_TECH | Engineers | Architecture, APIs, config | User workflows |
| USER_GUIDE | End users | How-to, tasks, FAQ | Technical internals |
| ADMIN_GUIDE | Ops/Admin | Setup, maintenance, security | User features |

### 5. Output Summary

After generating documentation:

```
## Documentation Pack Generated

**Location**: `{OUTPUT_DIR}/`

### Files Created
- `SUMMARY.md` - Executive summary (1 page)
- `INTERNAL_TECH.md` - Technical documentation
- `USER_GUIDE.md` - End user guide
- `ADMIN_GUIDE.md` - Administrator guide

### Coverage
- Spec sections covered: [list]
- API documented: [yes/no]
- Runbook included: [yes/no]
- FAQ generated: [count] items

### Next Steps
1. Review documentation for accuracy
2. Add screenshots/diagrams where noted
3. Validate commands/examples work
4. Publish to documentation platform
```

## Rules

- **No secrets**: Never include tokens, passwords, or internal-only URLs in external docs
- **Plain language**: Avoid jargon, especially in user-facing docs
- **Example-first**: Lead with examples, follow with explanation
- **Copy-paste ready**: All commands must be executable as-is
- **Link, don't duplicate**: Reference other docs instead of copying content
- **Audience awareness**: Each doc has a specific audience
