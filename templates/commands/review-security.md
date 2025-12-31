---
description: Perform a comprehensive security review using the CodeGuard security pack with language-aware rule selection.
handoffs:
  - label: Fix Security Issues
    agent: speckit.fix
    prompt: Fix the security issues identified in the review
  - label: Create Security Tasks
    agent: speckit.tasks
    prompt: Create tasks to address security findings
  - label: Review Implementation
    agent: speckit.review-implementation
    prompt: Complete implementation review including security
scripts:
  sh: scripts/bash/review-feature.sh --json --review-type security --require-spec
  ps: scripts/powershell/review-feature.ps1 -Json -ReviewType security -RequireSpec
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The user may specify:
- Specific areas to focus on (auth, API, file uploads, etc.)
- Known concerns or past vulnerabilities
- Compliance requirements (OWASP, SOC2, etc.)
- Languages to focus on (typescript, python, java, etc.)

## Role

You are the **Security Reviewer** powered by the **CodeGuard Security Pack**. Your job is to perform a comprehensive security pass using curated security rules that are selected based on the project's languages and feature domains.

## CodeGuard Security Pack Integration

This review uses the CodeGuard security ruleset located in `security/` directory:

### Tier 1: Always-Apply Rules (MANDATORY)
These three rules MUST be checked on EVERY security review:

| Rule | File | Description |
|------|------|-------------|
| **Hardcoded Credentials** | `security/rules/codeguard-1-hardcoded-credentials.md` | Never hardcode secrets, passwords, API keys, tokens |
| **Crypto Algorithms** | `security/rules/codeguard-1-crypto-algorithms.md` | Use only modern, secure cryptographic algorithms |
| **Digital Certificates** | `security/rules/codeguard-1-digital-certificates.md` | Validate and manage certificates securely |

### Tier 0: Language-Specific Rules
Selected based on detected languages in the codebase (see `security/index.json`):

**Load applicable rules by scanning for:**
- File extensions (`.ts`, `.js`, `.py`, `.java`, `.go`, `.c`, `.php`, `.rb`, `.swift`, `.kt`)
- Package files (`package.json`, `requirements.txt`, `pom.xml`, `go.mod`, `Gemfile`)
- Config files (`Dockerfile`, `docker-compose.yml`, `*.yaml` in k8s directories)

### Domain-Specific Rules
Additional rules based on feature context (detected from spec.md or code patterns):

| Domain | Trigger | Additional Rules |
|--------|---------|------------------|
| **Authentication** | Login, signup, auth code | `codeguard-0-authentication-mfa.md`, `codeguard-0-session-management-and-cookies.md` |
| **API** | REST/GraphQL endpoints | `codeguard-0-api-web-services.md`, `codeguard-0-authorization-access-control.md` |
| **File Upload** | Upload handlers | `codeguard-0-file-handling-and-uploads.md` |
| **Database** | ORM, SQL queries | `codeguard-0-data-storage.md`, `codeguard-0-input-validation-injection.md` |
| **Infrastructure** | IaC, K8s, Docker | `codeguard-0-iac-security.md`, `codeguard-0-cloud-orchestration-kubernetes.md` |
| **Privacy** | PII, user data | `codeguard-0-privacy-data-protection.md`, `codeguard-0-logging.md` |

## Operating Constraints

**CodeGuard-Powered**: Use the Implementation Checklists from each loaded rule file as your evaluation criteria.

**No Tool Explosions**: Recommend specific scans but don't require running every possible tool.

## Execution Steps

### 1. Initialize Context

Run `{SCRIPT}` from repo root and parse JSON output:

- **FEATURE_DIR**: Directory containing feature spec files
- **SPEC_FILE**: Path to `spec.md`
- **PLAN_FILE**: Path to `implementation-plan.md` (if exists)
- **CONSTITUTION_PATH**: Path to constitution file
- **OUTPUT_FILE**: Where to write the review (`FEATURE_DIR/security-review.md`)

For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

### 2. Load CodeGuard Security Rules

**Step 2a: Load Tier 1 Rules (Always Apply)**

Read and internalize these mandatory rules:
- `security/rules/codeguard-1-hardcoded-credentials.md`
- `security/rules/codeguard-1-crypto-algorithms.md`
- `security/rules/codeguard-1-digital-certificates.md`

**Step 2b: Detect Languages**

Scan the codebase and identify languages present:

| Detection | Languages |
|-----------|-----------|
| `.ts`, `.tsx` files, `tsconfig.json` | TypeScript |
| `.js`, `.jsx` files, `package.json` | JavaScript |
| `.py` files, `requirements.txt`, `pyproject.toml` | Python |
| `.java` files, `pom.xml`, `build.gradle` | Java |
| `.go` files, `go.mod` | Go |
| `.c`, `.h` files, `Makefile` | C |
| `.cs` files, `*.csproj` | C# |
| `.php` files, `composer.json` | PHP |
| `.rb` files, `Gemfile` | Ruby |
| `.swift` files | Swift |
| `.kt` files | Kotlin |
| `Dockerfile`, `docker-compose.yml` | Docker |
| `.yaml` in k8s directories | Kubernetes |
| `*.tf` files | Terraform |

**Step 2c: Load Language-Specific Rules**

Using `security/index.json`, load rules for detected languages. For example:
- TypeScript detected → Load rules from `languageRules.typescript`
- Docker detected → Load rules from `languageRules.yaml`

**Step 2d: Detect Feature Domains**

Scan spec.md and code for domain indicators:
- Authentication mentions → Load `domainRules.authentication`
- API/REST mentions → Load `domainRules.api`
- File upload code → Load `domainRules.fileHandling`
- Database/ORM usage → Load `domainRules.database`
- PII/privacy mentions → Load `domainRules.privacy`
- Container/K8s files → Load `domainRules.infrastructure`

### 3. Load Feature Context

**From spec.md:**
- Security-related requirements (NFR-SEC-###)
- User roles and permissions mentioned
- Data sensitivity indicators
- External integrations

**From implementation-plan.md (if exists):**
- Authentication/authorization approach
- API design and auth mechanisms
- Data storage and encryption plans
- Third-party dependencies

### 4. Execute CodeGuard Checklists

### 4. Execute CodeGuard Checklists

For each loaded rule file, execute the **Implementation Checklist** from that rule against the codebase.

#### A. Tier 1: Mandatory Checks (Always Run)

**From `codeguard-1-hardcoded-credentials.md`:**

| Check | ID | Status | Evidence |
|-------|-----|--------|----------|
| No plaintext secrets in source code | SEC001 | ⬜ | |
| No API keys or tokens in code | SEC002 | ⬜ | |
| All secrets via environment/vault | SEC003 | ⬜ | |
| No secrets in version control history | SEC004 | ⬜ | |
| Secrets not logged or exposed in errors | SEC005 | ⬜ | |

**From `codeguard-1-crypto-algorithms.md`:**

| Check | ID | Status | Evidence |
|-------|-----|--------|----------|
| Using AES-256/ChaCha20 for encryption | SEC006 | ⬜ | |
| Using SHA-256+ for hashing (not MD5/SHA1) | SEC007 | ⬜ | |
| Using bcrypt/Argon2/scrypt for passwords | SEC008 | ⬜ | |
| RSA keys ≥2048 bits, preferring ECDSA | SEC009 | ⬜ | |
| No custom crypto implementations | SEC010 | ⬜ | |

**From `codeguard-1-digital-certificates.md`:**

| Check | ID | Status | Evidence |
|-------|-----|--------|----------|
| TLS certificates validated | SEC011 | ⬜ | |
| No certificate validation disabled | SEC012 | ⬜ | |
| Certificate pinning where appropriate | SEC013 | ⬜ | |
| Certificates not expired | SEC014 | ⬜ | |

#### B. Language-Specific Checks

For each language detected, run the Implementation Checklist from the corresponding CodeGuard rules.

**Example: If TypeScript detected, include checks from:**
- `codeguard-0-input-validation-injection.md`
- `codeguard-0-authorization-access-control.md`
- `codeguard-0-api-web-services.md`
- `codeguard-0-client-side-web-security.md`
- `codeguard-0-session-management-and-cookies.md`
- And other TypeScript-applicable rules from index.json

#### C. Domain-Specific Checks

For domains detected in the feature, run the corresponding Implementation Checklists.

**Authentication Domain (if detected):**

| Check | ID | Status | Evidence |
|-------|-----|--------|----------|
| MFA support implemented | SEC020 | ⬜ | |
| Account lockout after failed attempts | SEC021 | ⬜ | |
| Secure session management | SEC022 | ⬜ | |
| Session invalidation on logout | SEC023 | ⬜ | |
| IDOR vulnerabilities prevented | SEC024 | ⬜ | |

**API Domain (if detected):**

| Check | ID | Status | Evidence |
|-------|-----|--------|----------|
| Rate limiting implemented | SEC030 | ⬜ | |
| Input validation on all endpoints | SEC031 | ⬜ | |
| Authentication required on protected routes | SEC032 | ⬜ | |
| CORS properly configured | SEC033 | ⬜ | |
| SSRF prevention measures | SEC034 | ⬜ | |

**Database Domain (if detected):**

| Check | ID | Status | Evidence |
|-------|-----|--------|----------|
| Parameterized queries used | SEC040 | ⬜ | |
| No string concatenation in queries | SEC041 | ⬜ | |
| Least privilege DB access | SEC042 | ⬜ | |
| Connection strings secured | SEC043 | ⬜ | |

#### D. Dependencies Check

| Check | ID | Status | Evidence |
|-------|-----|--------|----------|
| No critical vulnerabilities | SEC050 | ⬜ | |
| No high vulnerabilities | SEC051 | ⬜ | |
| Dependencies up to date | SEC052 | ⬜ | |
| SBOM available | SEC053 | ⬜ | |

**Commands to suggest:**
```bash
# Node.js
npm audit

# Python  
pip-audit

# General
trivy fs .
```

### 5. Generate Security Report

Create `OUTPUT_FILE`:

```markdown
# Security Review: {Feature Name}

**Date**: {timestamp}
**Reviewer**: AI Security Reviewer (CodeGuard-Powered)
**CodeGuard Version**: 1.0.1
**Scope**: [from user input or inferred]
**Risk Level**: Low | Medium | High | Critical

---

## 1. CodeGuard Rules Applied

### Tier 1 (Always Apply)
- ✅ codeguard-1-hardcoded-credentials
- ✅ codeguard-1-crypto-algorithms  
- ✅ codeguard-1-digital-certificates

### Language-Specific Rules
[List rules loaded based on detected languages]

### Domain-Specific Rules
[List rules loaded based on feature domains]

---

## 2. Executive Summary

**Overall Security Posture**: [assessment]
**Critical Findings**: [count]
**High Findings**: [count]
**Requires Immediate Action**: [yes/no]

### Key Risks
[1-2 paragraph summary of main security concerns]

---

## 3. Findings by Severity

### Critical

#### SEC-CRIT-001: [Finding Title]
- **Category**: [Auth/Injection/Secrets/etc.]
- **CodeGuard Rule**: [rule that flagged this]
- **Location**: `path/to/file.ts:45-67`
- **Issue**: [What's wrong]
- **Impact**: [What could happen]
- **Fix**: [Specific fix, 1-2 lines]
- **Effort**: Low | Medium | High

---

### High

#### SEC-HIGH-001: [Finding Title]
[Same structure with CodeGuard Rule field]

---

### Medium

#### SEC-MED-001: [Finding Title]
[Same structure]

---

### Low

#### SEC-LOW-001: [Finding Title]
[Same structure]

---

## 4. CodeGuard Checklist Results

### Tier 1: Mandatory Checks
| ID | Rule | Check | Status | Notes |
|----|------|-------|--------|-------|
| SEC001 | hardcoded-credentials | No secrets in code | ✅/❌/⚠️ | |
| SEC006 | crypto-algorithms | Modern encryption | ✅/❌/⚠️ | |
| SEC011 | digital-certificates | Valid certificates | ✅/❌/⚠️ | |

### Language-Specific Checks
[Tables for each loaded language rule]

### Domain-Specific Checks
[Tables for authentication, API, database domains if applicable]

---

## 5. Dependency Scan

### Recommended Commands
```bash
npm audit          # Node.js
pip-audit          # Python
trivy fs .         # General
```

### Known Vulnerabilities (if scanned)
| Package | Severity | CVE | Fix Version |
|---------|----------|-----|-------------|
| [package] | Critical/High/Med/Low | [CVE-XXXX-XXXXX] | [version] |

---

## 6. Spec Compliance

### Security Requirements from Spec
| Requirement | ID | Status | Notes |
|-------------|-----|--------|-------|
| [NFR-SEC-001 from spec] | SEC-REQ-001 | ✅/❌ | [notes] |

---

## 7. Recommendations

### Immediate (Before Merge)
1. [Action with file:line reference]
2. [Action with file:line reference]

### Short-term (Before Release)
1. [Action]
2. [Action]

### Long-term (Technical Debt)
1. [Action]
2. [Action]

---

## 8. Verification Tests

Suggested security tests to add:

- [ ] SECTEST001 [Test description]
- [ ] SECTEST002 [Test description]
- [ ] SECTEST003 [Test description]

---

## 9. Sign-off

| Role | Status | Date | Notes |
|------|--------|------|-------|
| Security Review | ⏳ Complete | | CodeGuard-powered review |
| Findings Addressed | ⬜ Pending | | |
| Re-review (if critical) | ⬜ N/A | | |
```

### 6. Severity Classification

| Severity | Criteria | Examples | Action |
|----------|----------|----------|--------|
| **Critical** | Immediate exploitation risk, data breach | SQL injection, auth bypass, exposed secrets | Block merge |
| **High** | Significant risk with some exploitation barrier | Weak session handling, missing auth checks | Fix before release |
| **Medium** | Moderate risk, requires specific conditions | Missing rate limiting, verbose errors | Should fix |
| **Low** | Minor issues, defense in depth | Missing security headers, outdated deps (no CVE) | Can defer |

### 7. Needs Verification

For findings where impact is uncertain:

```markdown
#### SEC-VERIFY-001: [Finding Title]
- **Category**: [Category]
- **Location**: `file:line`
- **Observation**: [What was observed]
- **Potential Issue**: [What might be wrong]
- **Verification Needed**: [Specific test to confirm]
```

## Rules

- **CodeGuard-Powered**: Use the Implementation Checklists from each CodeGuard rule as evaluation criteria
- **Tier 1 First**: Always run the three Tier 1 rules before language-specific checks
- **Surgical focus**: Identify **what to fix** and **where**, not theoretical risks
- **Evidence required**: Every finding must cite file:line and the CodeGuard rule that flagged it
- **Actionable fixes**: 1-2 line fix descriptions, not essays
- **No tool explosions**: Suggest specific scans, don't require running everything
- **Severity discipline**: Only Critical/High if truly exploitable
- **Verify uncertain items**: Mark as "Needs verification" rather than false positive/negative
- **Spec alignment**: Check security requirements from spec.md
