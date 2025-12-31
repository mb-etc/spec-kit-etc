# Spec Kit Security Pack (CodeGuard)

A curated, language-aware security ruleset based on [Project CodeGuard](https://github.com/project-codeguard/rules) integrated into Spec Kit for secure-by-default development.

## Version

| Field | Value |
|-------|-------|
| **Pack Version** | 1.0.0 |
| **CodeGuard Version** | 1.0.1 |
| **Last Updated** | 2025-12-31 |

## Overview

This security pack provides comprehensive security guidance organized into two tiers:

### Tier 1: Always-Apply Rules (Mandatory)
These rules MUST be checked on every code operation:

| Rule | Description |
|------|-------------|
| `codeguard-1-hardcoded-credentials` | Never hardcode secrets, passwords, API keys, or tokens |
| `codeguard-1-crypto-algorithms` | Use only modern, secure cryptographic algorithms |
| `codeguard-1-digital-certificates` | Validate and manage digital certificates securely |

### Tier 0: Context-Specific Rules (19 rules)
Applied based on language and feature context:

| Rule | Description |
|------|-------------|
| `codeguard-0-input-validation-injection` | SQL/LDAP/OS injection defense, parameterization |
| `codeguard-0-authentication-mfa` | Authentication and MFA best practices |
| `codeguard-0-authorization-access-control` | RBAC/ABAC, IDOR, mass assignment prevention |
| `codeguard-0-api-web-services` | REST/GraphQL/SOAP security, SSRF controls |
| `codeguard-0-session-management-and-cookies` | Session security and cookie handling |
| `codeguard-0-data-storage` | Database security and isolation |
| `codeguard-0-client-side-web-security` | XSS, CSP, DOM security |
| `codeguard-0-file-handling-and-uploads` | File upload validation and storage |
| `codeguard-0-additional-cryptography` | Encryption, key management, TLS |
| `codeguard-0-xml-and-serialization` | XXE, deserialization attacks |
| `codeguard-0-logging` | Secure logging practices |
| `codeguard-0-privacy-data-protection` | PII handling, GDPR, data minimization |
| `codeguard-0-cloud-orchestration-kubernetes` | K8s security, pod policies |
| `codeguard-0-devops-ci-cd-containers` | Container security, CI/CD hardening |
| `codeguard-0-iac-security` | Infrastructure as Code security |
| `codeguard-0-supply-chain-security` | Dependency security, SBOM |
| `codeguard-0-mobile-apps` | iOS/Android security |
| `codeguard-0-framework-and-languages` | Framework-specific security |
| `codeguard-0-safe-c-functions` | Safe C/C++ function usage |

## Language Coverage

Rules are automatically selected based on detected project languages:

| Language | Rule Count |
|----------|------------|
| JavaScript | 17 rules |
| TypeScript | 9 rules |
| Python | 9 rules |
| Java | 10 rules |
| C | 14 rules |
| Go | 8 rules |
| PHP | 10 rules |
| Ruby | 10 rules |
| YAML/Docker | 11 rules |
| Swift/Kotlin | 3-4 rules |

## Integration with Spec Kit

### Commands Using Security Pack

| Command | Usage |
|---------|-------|
| `/speckit.review-security` | Full security review using all applicable rules |
| `/speckit.implement` | Checks Tier 1 rules during implementation |
| `/speckit.checklist` | Generates security-focused checklists |
| `/speckit.review-readiness` | Security gate in release readiness |

### How Rules Are Applied

1. **Language Detection**: Scans codebase for file extensions, package files
2. **Rule Selection**: Loads rules from `index.json` based on detected languages
3. **Domain Detection**: Adds domain-specific rules (auth, API, etc.)
4. **Always-Apply**: Tier 1 rules are always included
5. **Checklist Generation**: Uses each rule's Implementation Checklist

## File Structure

```
security/
├── README.md           # This file
├── index.json          # Rule metadata and language mappings
└── rules/
    ├── codeguard-1-hardcoded-credentials.md
    ├── codeguard-1-crypto-algorithms.md
    ├── codeguard-1-digital-certificates.md
    ├── codeguard-0-input-validation-injection.md
    ├── codeguard-0-authentication-mfa.md
    └── ... (22 rule files total)
```

## Rule Format

Each rule file contains:

```yaml
---
description: Brief description
languages: [list of applicable languages]
alwaysApply: true/false
---

rule_id: codeguard-X-name

## Section Title

Content with:
- Core principles
- Detailed guidance
- Code examples
- Implementation Checklist
- Test Plan
```

## Customization

### Adding Custom Rules

1. Create a new `.md` file in `rules/` following the format above
2. Add the rule to `index.json` under appropriate language/domain sections
3. Set `alwaysApply: true` if it should always be checked

### Overriding Rules

To disable a rule for your project, create `.specify/security-overrides.json`:

```json
{
  "disabled": ["codeguard-0-mobile-apps"],
  "severity": {
    "codeguard-0-logging": "low"
  }
}
```

## Attribution

This security pack is based on [Project CodeGuard](https://github.com/project-codeguard/rules), an open-source, model-agnostic security framework that embeds secure-by-default practices into AI coding workflows.

## License

Security rules are provided under the same license as Project CodeGuard.
