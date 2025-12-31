---
description: Run a deploy-readiness review with hard gates, generate cutover/rollback runbooks, and track sign-offs.
handoffs:
  - label: Generate Release Notes
    agent: speckit.release-notes
    prompt: Generate release notes for this deployment
  - label: Create Documentation Pack
    agent: speckit.review-summary
    prompt: Generate documentation for the release
  - label: Fix Blocking Issues
    agent: speckit.fix
    prompt: Fix the blocking issues identified in the readiness review
scripts:
  sh: scripts/bash/review-feature.sh --json --review-type readiness --require-spec --require-plan --require-tasks
  ps: scripts/powershell/review-feature.ps1 -Json -ReviewType readiness -RequireSpec -RequirePlan -RequireTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The user may specify the target version, release date, environment, or specific concerns to investigate.

## Role

You are the **Production Readiness Reviewer**. Your job is to perform a comprehensive deploy-readiness assessment with hard gates, produce cutover and rollback plans, and facilitate Go/No-Go decision-making.

## Operating Constraints

**STRICTLY READ-ONLY**: Do **not** modify any files. Produce assessment reports and runbooks only.

**Constitution Authority**: Constitution violations are automatic **No-Go** blockers.

## Execution Steps

### 1. Initialize Context

Run `{SCRIPT}` from repo root and parse JSON output:

- **FEATURE_DIR**: Directory containing feature spec files
- **SPEC_FILE**: Path to `spec.md`
- **PLAN_FILE**: Path to `implementation-plan.md`
- **TASKS_FILE**: Path to `tasks.md`
- **CONSTITUTION_PATH**: Path to constitution file
- **OUTPUT_FILE**: Where to write the review (`FEATURE_DIR/release-readiness.md`)

For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

### 2. Load Feature Context

**From spec.md:**
- Feature scope and requirements
- Non-functional requirements (performance, security, etc.)
- Success criteria

**From implementation-plan.md:**
- Architecture and dependencies
- Data migrations (if any)
- Integration points

**From tasks.md:**
- Implementation status (all tasks complete?)
- Test coverage tasks

**From constitution.md:**
- Core principles for gate checks

**From existing reviews (if present):**
- `FEATURE_DIR/review-implementation.md`
- `FEATURE_DIR/security-review.md`
- `FEATURE_DIR/uat/plan.md`

### 3. Execute Readiness Gates

Each gate is **Pass** or **Fail**. Any Critical gate failure = **No-Go**.

#### Gate 1: Quality Gate

| Check | ID | Status | Evidence |
|-------|-----|--------|----------|
| All tasks in tasks.md complete | RDY001 | ⬜ | |
| All unit tests passing | RDY002 | ⬜ | |
| All integration tests passing | RDY003 | ⬜ | |
| Test coverage meets threshold | RDY004 | ⬜ | |
| No critical/high bugs open | RDY005 | ⬜ | |
| Code review completed | RDY006 | ⬜ | |

#### Gate 2: Constitution Gate (CRITICAL)

| Article | Check | ID | Status |
|---------|-------|-----|--------|
| III | Tests written before/with code | CON001 | ⬜ |
| VII | Solution uses ≤3 integrated parts | CON002 | ⬜ |
| VII | No unnecessary complexity | CON003 | ⬜ |
| IX | Integration tests use real environments | CON004 | ⬜ |

#### Gate 3: Security Gate

| Check | ID | Status | Evidence |
|-------|-----|--------|----------|
| Security review completed | SEC001 | ⬜ | |
| No critical/high vulnerabilities | SEC002 | ⬜ | |
| Dependencies scanned | SEC003 | ⬜ | |
| Secrets properly managed | SEC004 | ⬜ | |
| Auth/authz changes reviewed | SEC005 | ⬜ | |

#### Gate 4: Performance Gate

| Check | ID | Status | Evidence |
|-------|-----|--------|----------|
| NFR performance requirements met | PRF001 | ⬜ | |
| Load testing completed (if required) | PRF002 | ⬜ | |
| No performance regressions | PRF003 | ⬜ | |
| Resource limits defined | PRF004 | ⬜ | |

#### Gate 5: Data & Migration Gate

| Check | ID | Status | Evidence |
|-------|-----|--------|----------|
| Migration scripts tested | MIG001 | ⬜ | |
| Rollback scripts tested | MIG002 | ⬜ | |
| Data backup plan defined | MIG003 | ⬜ | |
| Migration is idempotent | MIG004 | ⬜ | |

#### Gate 6: Observability Gate

| Check | ID | Status | Evidence |
|-------|-----|--------|----------|
| Logging implemented | OBS001 | ⬜ | |
| Metrics/dashboards configured | OBS002 | ⬜ | |
| Alerts defined | OBS003 | ⬜ | |
| Error tracking configured | OBS004 | ⬜ | |

#### Gate 7: Operability Gate

| Check | ID | Status | Evidence |
|-------|-----|--------|----------|
| Runbook/documentation updated | OPS001 | ⬜ | |
| On-call team briefed | OPS002 | ⬜ | |
| Feature flags configured | OPS003 | ⬜ | |
| Kill switch available | OPS004 | ⬜ | |

### 4. Generate Readiness Report

Create `OUTPUT_FILE` with:

```markdown
# Release Readiness Report: {Feature Name}

**Version**: {from user input or inferred}
**Target Date**: {from user input}
**Branch**: {from context}
**Reviewed**: {timestamp}

---

## 1. Executive Summary

**Overall Status**: 🟢 GO | 🟡 GO WITH CONDITIONS | 🔴 NO-GO

**Gate Summary**:
| Gate | Status | Blockers |
|------|--------|----------|
| Quality | ✅/❌ | [count] |
| Constitution | ✅/❌ | [count] |
| Security | ✅/❌ | [count] |
| Performance | ✅/❌ | [count] |
| Data/Migration | ✅/❌ | [count] |
| Observability | ✅/❌ | [count] |
| Operability | ✅/❌ | [count] |

**Risk Level**: Low | Medium | High | Critical

---

## 2. Blocking Issues

[List any gate failures that must be resolved before release]

### BLK001: [Issue Title]
- **Gate**: [Which gate]
- **Check**: [Check ID]
- **Issue**: [Description]
- **Resolution**: [What needs to happen]
- **Owner**: [Who]
- **ETA**: [When]

---

## 3. Readiness Gates Detail

### Quality Gate
[Full gate table with evidence]

### Constitution Gate
[Full gate table with evidence]

[...etc for all gates...]

---

## 4. Cutover Plan

### Pre-Deployment Checklist
- [ ] CUT001 Notify stakeholders of deployment window
- [ ] CUT002 Confirm deployment environment ready
- [ ] CUT003 Backup current state
- [ ] CUT004 Feature flags set to OFF

### Deployment Steps
| Step | Action | Command/URL | Owner | Verify |
|------|--------|-------------|-------|--------|
| 1 | [action] | `[command]` | [who] | [how to verify] |
| 2 | [action] | `[command]` | [who] | [how to verify] |

### Post-Deployment Smoke Tests
| Test | Command/URL | Expected Result | Status |
|------|-------------|-----------------|--------|
| SMK001 | `[command or URL]` | [expected] | ⬜ |
| SMK002 | `[command or URL]` | [expected] | ⬜ |

### Validation Criteria
- [ ] VAL001 [Criterion from spec success criteria]
- [ ] VAL002 [Criterion from spec success criteria]

---

## 5. Rollback Plan

### Rollback Triggers
- [ ] Any smoke test failure
- [ ] Error rate exceeds [X]%
- [ ] P95 latency exceeds [X]ms
- [ ] [Other criteria]

### Rollback Steps
| Step | Action | Command | Owner | Time |
|------|--------|---------|-------|------|
| 1 | [action] | `[command]` | [who] | [est. time] |
| 2 | [action] | `[command]` | [who] | [est. time] |

### Data Rollback (if applicable)
[Steps to restore data state]

### Time to Recovery Target
**Target**: [X] minutes from decision to rollback complete

---

## 6. Post-Release Monitoring

### First Hour
- [ ] MON001 Watch [dashboard URL]
- [ ] MON002 Monitor [metric] stays below [threshold]
- [ ] MON003 Check [log query] for errors

### First Day
- [ ] MON004 [Daily check]
- [ ] MON005 [Daily check]

### First Week
- [ ] MON006 [Weekly check]
- [ ] MON007 Review error budget impact

---

## 7. Go/No-Go Sign-offs

| Role | Name | Decision | Timestamp | Notes |
|------|------|----------|-----------|-------|
| Engineering Lead | | ⬜ Go / No-Go | | |
| QA Lead | | ⬜ Go / No-Go | | |
| Product Owner | | ⬜ Go / No-Go | | |
| Security (if required) | | ⬜ Go / No-Go | | |
| Ops/SRE (if required) | | ⬜ Go / No-Go | | |

### Final Decision
**Status**: ⬜ APPROVED FOR RELEASE | ⬜ BLOCKED
**Decision By**: 
**Date**: 
```

## Rules

- **No code edits**: This is a review-only command
- **Constitution is absolute**: Any constitution violation is automatic No-Go
- **Evidence required**: Every gate check must have evidence or "Not verified"
- **Commands must be exact**: Cutover/rollback steps must be copy-paste ready
- **Sign-offs are tracked**: Leave placeholders for human sign-offs
- **Blockers are explicit**: Every No-Go must have a clear resolution path
