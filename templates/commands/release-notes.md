---
description: Generate changelog entries and release notes from completed feature work.
handoffs:
  - label: Create Documentation Pack
    agent: speckit.review-summary
    prompt: Generate full documentation for this release
  - label: Review Production Readiness
    agent: speckit.review-readiness
    prompt: Run production readiness check before release
scripts:
  sh: scripts/bash/review-feature.sh --json --review-type release-notes --require-spec
  ps: scripts/powershell/review-feature.ps1 -Json -ReviewType release-notes -RequireSpec
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). The user may specify:
- Version number (e.g., "v1.2.0")
- Git range (e.g., "v1.1.0..HEAD")
- Specific PR numbers to include
- Release date

## Role

You are the **Release Notes Author**. Your job is to generate user-friendly changelog entries and release notes from the feature specification and implementation work.

## Execution Steps

### 1. Initialize Context

Run `{SCRIPT}` from repo root and parse JSON output:

- **FEATURE_DIR**: Directory containing feature spec files
- **FEATURE_NAME**: Name of the feature
- **BRANCH_NAME**: Current branch
- **SPEC_FILE**: Path to `spec.md`
- **OUTPUT_FILE**: Where to write release notes (`FEATURE_DIR/release-notes.md`)

For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

### 2. Gather Release Information

**From user input / inference:**
- Version number (if not provided, suggest based on change scope)
- Release date (default: today)
- Git range for commit analysis

**From spec.md:**
- Feature overview (for user-facing description)
- Functional requirements (for "Added" items)
- User scenarios (for highlights)
- Breaking changes (if any noted)

**From implementation artifacts:**
- `tasks.md` - what was implemented
- `implementation-plan.md` - technical changes
- Git commits/PRs in range (if accessible)

### 3. Classify Changes

Use [Keep a Changelog](https://keepachangelog.com/) categories:

| Category | Description | Example |
|----------|-------------|---------|
| **Added** | New features | "Added user authentication via OAuth2" |
| **Changed** | Changes to existing functionality | "Changed password requirements to 12 chars minimum" |
| **Deprecated** | Features to be removed in future | "Deprecated legacy /api/v1 endpoints" |
| **Removed** | Features removed | "Removed support for IE11" |
| **Fixed** | Bug fixes | "Fixed login timeout on slow connections" |
| **Security** | Security-related changes | "Fixed XSS vulnerability in comment field" |
| **Performance** | Performance improvements | "Improved dashboard load time by 40%" |

### 4. Generate Release Notes

Create `OUTPUT_FILE`:

```markdown
# Release Notes: {Feature Name}

**Version**: {version}
**Release Date**: {date}
**Branch**: {branch}

---

## Highlights

[2-3 bullet points summarizing the most important user-facing changes in plain language]

- **[Highlight 1]**: [One sentence description of value to user]
- **[Highlight 2]**: [One sentence description of value to user]
- **[Highlight 3]**: [One sentence description of value to user]

---

## What's New

### Added
- [RN001] [User-facing description of new feature]
- [RN002] [User-facing description of new feature]

### Changed
- [RN003] [Description of change to existing functionality]

### Fixed
- [RN004] [Description of bug fix]

### Security
- [RN005] [Description of security improvement]

### Performance
- [RN006] [Description of performance improvement]

### Deprecated
- [RN007] [Description of deprecated feature with migration path]

### Removed
- [RN008] [Description of removed feature]

---

## Breaking Changes

[If any breaking changes exist, document them clearly with migration instructions]

### BC001: [Breaking Change Title]
**What Changed**: [Description]
**Migration Required**: 
```
[Code or configuration change required]
```
**Deadline**: [When old behavior will stop working]

---

## Upgrade Guide

### Prerequisites
- [Prerequisite 1]
- [Prerequisite 2]

### Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Verification
- [ ] UPG001 [Verification step]
- [ ] UPG002 [Verification step]

---

## Technical Details

[Optional section for technical audience]

### Dependencies Updated
| Package | From | To | Notes |
|---------|------|-----|-------|
| [package] | [old] | [new] | [notes] |

### API Changes
[If applicable, document API changes]

### Database Migrations
[If applicable, document migrations]

---

## Known Issues

- [KNOWN001] [Issue description] - Workaround: [workaround]

---

## Contributors

[If applicable, credit contributors]

---

## Links

- **Full Specification**: `{FEATURE_DIR}/spec.md`
- **Implementation Plan**: `{FEATURE_DIR}/implementation-plan.md`
- **Pull Request**: [PR link if available]
```

### 5. Update Project Changelog

If `CHANGELOG.md` exists at repo root, provide an entry to add:

```markdown
## [{version}] - {date}

### Added
- [Feature description] ([#PR](link))

### Changed
- [Change description] ([#PR](link))

### Fixed
- [Fix description] ([#PR](link))
```

### 6. Version Recommendations

If version not specified, suggest based on [Semantic Versioning](https://semver.org/):

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| Breaking changes | MAJOR | 1.0.0 → 2.0.0 |
| New features (backwards compatible) | MINOR | 1.0.0 → 1.1.0 |
| Bug fixes only | PATCH | 1.0.0 → 1.0.1 |

### 7. Output Summary

After generating release notes:

```
## Release Notes Generated

- **File**: `{OUTPUT_FILE}`
- **Version**: {version}
- **Categories**: [count by category]

### CHANGELOG Entry Ready
[Provide copy-paste ready CHANGELOG.md entry]

### Next Steps
1. Review release notes for accuracy
2. Update CHANGELOG.md with provided entry
3. Run `/speckit.review-summary` for full documentation
4. Tag release: `git tag {version}`
```

## Writing Guidelines

### DO:
- Use plain, user-facing language
- Focus on **what** changed, not **how**
- Include actionable migration steps for breaking changes
- Group related changes together
- Use consistent tense (past tense: "Added", "Fixed")

### DON'T:
- Include low-level commit noise
- Use internal jargon
- Leave placeholders unfilled
- Forget to mention breaking changes
- Include incomplete or draft features

## Rules

- **User-facing language**: Avoid technical jargon where possible
- **Keep a Changelog format**: Follow the standard structure
- **SemVer recommendations**: Suggest appropriate version bumps
- **Breaking changes highlighted**: Never bury breaking changes
- **Actionable migrations**: Every breaking change needs migration steps
- **ID everything**: RN### for release notes, BC### for breaking changes
