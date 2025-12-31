#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich",
#     "platformdirs",
#     "readchar",
#     "httpx",
# ]
# ///
"""
Specify CLI - Setup tool for Specify projects

Usage:
    uvx specify-cli.py init <project-name>
    uvx specify-cli.py init .
    uvx specify-cli.py init --here

Or install globally:
    uv tool install --from specify-cli.py specify-cli
    specify init <project-name>
    specify init .
    specify init --here
"""

import os
import subprocess
import sys
import zipfile
import tempfile
import shutil
import shlex
import json
from pathlib import Path
from typing import Optional, Tuple

import typer
import httpx
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich.table import Table
from rich.tree import Tree
from typer.core import TyperGroup

# For cross-platform keyboard input
import readchar
import ssl
import truststore
from datetime import datetime, timezone

ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
client = httpx.Client(verify=ssl_context)

def _github_token(cli_token: str | None = None) -> str | None:
    """Return sanitized GitHub token (cli arg takes precedence) or None."""
    return ((cli_token or os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or "").strip()) or None

def _github_auth_headers(cli_token: str | None = None) -> dict:
    """Return Authorization header dict only when a non-empty token exists."""
    token = _github_token(cli_token)
    return {"Authorization": f"Bearer {token}"} if token else {}

def _parse_rate_limit_headers(headers: httpx.Headers) -> dict:
    """Extract and parse GitHub rate-limit headers."""
    info = {}
    
    # Standard GitHub rate-limit headers
    if "X-RateLimit-Limit" in headers:
        info["limit"] = headers.get("X-RateLimit-Limit")
    if "X-RateLimit-Remaining" in headers:
        info["remaining"] = headers.get("X-RateLimit-Remaining")
    if "X-RateLimit-Reset" in headers:
        reset_epoch = int(headers.get("X-RateLimit-Reset", "0"))
        if reset_epoch:
            reset_time = datetime.fromtimestamp(reset_epoch, tz=timezone.utc)
            info["reset_epoch"] = reset_epoch
            info["reset_time"] = reset_time
            info["reset_local"] = reset_time.astimezone()
    
    # Retry-After header (seconds or HTTP-date)
    if "Retry-After" in headers:
        retry_after = headers.get("Retry-After")
        try:
            info["retry_after_seconds"] = int(retry_after)
        except ValueError:
            # HTTP-date format - not implemented, just store as string
            info["retry_after"] = retry_after
    
    return info

def _format_rate_limit_error(status_code: int, headers: httpx.Headers, url: str) -> str:
    """Format a user-friendly error message with rate-limit information."""
    rate_info = _parse_rate_limit_headers(headers)
    
    lines = [f"GitHub API returned status {status_code} for {url}"]
    lines.append("")
    
    if rate_info:
        lines.append("[bold]Rate Limit Information:[/bold]")
        if "limit" in rate_info:
            lines.append(f"  • Rate Limit: {rate_info['limit']} requests/hour")
        if "remaining" in rate_info:
            lines.append(f"  • Remaining: {rate_info['remaining']}")
        if "reset_local" in rate_info:
            reset_str = rate_info["reset_local"].strftime("%Y-%m-%d %H:%M:%S %Z")
            lines.append(f"  • Resets at: {reset_str}")
        if "retry_after_seconds" in rate_info:
            lines.append(f"  • Retry after: {rate_info['retry_after_seconds']} seconds")
        lines.append("")
    
    # Add troubleshooting guidance
    lines.append("[bold]Troubleshooting Tips:[/bold]")
    lines.append("  • If you're on a shared CI or corporate environment, you may be rate-limited.")
    lines.append("  • Consider using a GitHub token via --github-token or the GH_TOKEN/GITHUB_TOKEN")
    lines.append("    environment variable to increase rate limits.")
    lines.append("  • Authenticated requests have a limit of 5,000/hour vs 60/hour for unauthenticated.")
    
    return "\n".join(lines)

# Agent configuration with name, folder, install URL, and CLI tool requirement
AGENT_CONFIG = {
    "copilot": {
        "name": "GitHub Copilot",
        "folder": ".github/",
        "install_url": None,  # IDE-based, no CLI check needed
        "requires_cli": False,
    },
    "claude": {
        "name": "Claude Code",
        "folder": ".claude/",
        "install_url": "https://docs.anthropic.com/en/docs/claude-code/setup",
        "requires_cli": True,
    },
    "gemini": {
        "name": "Gemini CLI",
        "folder": ".gemini/",
        "install_url": "https://github.com/google-gemini/gemini-cli",
        "requires_cli": True,
    },
    "cursor-agent": {
        "name": "Cursor",
        "folder": ".cursor/",
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "qwen": {
        "name": "Qwen Code",
        "folder": ".qwen/",
        "install_url": "https://github.com/QwenLM/qwen-code",
        "requires_cli": True,
    },
    "opencode": {
        "name": "opencode",
        "folder": ".opencode/",
        "install_url": "https://opencode.ai",
        "requires_cli": True,
    },
    "codex": {
        "name": "Codex CLI",
        "folder": ".codex/",
        "install_url": "https://github.com/openai/codex",
        "requires_cli": True,
    },
    "windsurf": {
        "name": "Windsurf",
        "folder": ".windsurf/",
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "kilocode": {
        "name": "Kilo Code",
        "folder": ".kilocode/",
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "auggie": {
        "name": "Auggie CLI",
        "folder": ".augment/",
        "install_url": "https://docs.augmentcode.com/cli/setup-auggie/install-auggie-cli",
        "requires_cli": True,
    },
    "codebuddy": {
        "name": "CodeBuddy",
        "folder": ".codebuddy/",
        "install_url": "https://www.codebuddy.ai/cli",
        "requires_cli": True,
    },
    "qoder": {
        "name": "Qoder CLI",
        "folder": ".qoder/",
        "install_url": "https://qoder.com/cli",
        "requires_cli": True,
    },
    "roo": {
        "name": "Roo Code",
        "folder": ".roo/",
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
    "q": {
        "name": "Amazon Q Developer CLI",
        "folder": ".amazonq/",
        "install_url": "https://aws.amazon.com/developer/learning/q-developer-cli/",
        "requires_cli": True,
    },
    "amp": {
        "name": "Amp",
        "folder": ".agents/",
        "install_url": "https://ampcode.com/manual#install",
        "requires_cli": True,
    },
    "shai": {
        "name": "SHAI",
        "folder": ".shai/",
        "install_url": "https://github.com/ovh/shai",
        "requires_cli": True,
    },
    "bob": {
        "name": "IBM Bob",
        "folder": ".bob/",
        "install_url": None,  # IDE-based
        "requires_cli": False,
    },
}

SCRIPT_TYPE_CHOICES = {"sh": "POSIX Shell (bash/zsh)", "ps": "PowerShell"}

PROJECT_TYPE_CHOICES = {
    "greenfield": "New project - full design freedom",
    "brownfield": "Existing system - legacy constraints apply",
    "bluefield": "Existing platform - adding new components",
}

# Project type descriptions for AI reference file
PROJECT_TYPE_DESCRIPTIONS = {
    "greenfield": (
        "This is a **new project** with no existing codebase. You have full design freedom "
        "and can establish patterns, architecture, and conventions from scratch."
    ),
    "brownfield": (
        "This is an **existing system** with active users and legacy code. Changes must "
        "consider backward compatibility, existing behavior, and migration paths. "
        "Regressions are a primary risk."
    ),
    "bluefield": (
        "This is a **hybrid project**—new components being added to an existing platform. "
        "New code should be isolated where possible, but must integrate with existing "
        "services and respect platform conventions."
    ),
}

# Development implications by project type
PROJECT_TYPE_IMPLICATIONS = {
    "greenfield": """
### When Specifying Features
- Focus on clean architecture and best practices
- Establish patterns that will scale
- No legacy compatibility concerns

### When Planning Implementation
- Choose optimal technical approaches freely
- Set up proper testing infrastructure from the start
- Establish coding standards and conventions

### When Implementing
- Write clean, well-documented code
- Build comprehensive test coverage
- Create proper abstractions from day one
""",
    "brownfield": """
### When Specifying Features
- **ALWAYS ASK**: What existing behavior must remain unchanged?
- **ALWAYS ASK**: Are there known bugs or quirks users depend on?
- **ALWAYS ASK**: What technical debt affects this area?
- Include backward compatibility requirements in acceptance criteria
- Document migration/rollback considerations

### When Planning Implementation
- Identify all touchpoints with existing code
- Plan for feature flags to enable gradual rollout
- Include rollback procedures for each major change
- Consider database migration strategies

### When Implementing
- Implement behind **feature flags** when touching existing behavior
- Add **regression tests** before modifying existing code
- Document **breaking changes** prominently
- Preserve existing APIs unless explicitly changing them
- Test with production-like data

### When Reviewing
- Verify backward compatibility
- Check for unintended side effects
- Validate migration scripts
- Confirm rollback procedures work
""",
    "bluefield": """
### When Specifying Features
- **ALWAYS ASK**: Which components are new vs existing?
- **ALWAYS ASK**: What shared services will this integrate with?
- **ALWAYS ASK**: What platform standards must be followed?
- Define clear integration boundaries
- Document dependencies on existing services

### When Planning Implementation
- Use adapter patterns to isolate new code from legacy
- Plan integration testing with existing services
- Identify shared dependencies and versioning concerns
- Consider deployment coordination with existing components

### When Implementing
- Respect existing platform conventions
- Use dependency injection for existing service integration
- Write contract tests for integration points
- Keep new components loosely coupled
- Test boundary conditions between new and existing

### When Reviewing
- Verify integration contracts are honored
- Check isolation boundaries are maintained
- Validate platform standards compliance
""",
}

# Context-specific guidance and checklists
CONTEXT_GUIDANCE = {
    "greenfield": """
### Questions to Consider
- What patterns will best serve this project long-term?
- What testing strategy fits the project scope?
- What conventions should be established now?

### Red Flags to Watch For
- Over-engineering for hypothetical future needs
- Skipping tests "because it's new code"
- Inconsistent patterns across components
""",
    "brownfield": """
### Questions to Always Ask
1. What existing behavior depends on this code?
2. Who are the current users and how do they use it?
3. What would break if this change goes wrong?
4. How do we rollback if needed?
5. Is there technical debt we should address or avoid?

### Red Flags to Watch For
- Changes without regression tests
- Assumptions about "unused" code
- Breaking API changes without migration paths
- Skipping feature flags for risky changes
- "Big bang" releases instead of incremental rollout

### Before Every Change
- [ ] Identified all callers/consumers of modified code
- [ ] Added regression tests for existing behavior
- [ ] Documented rollback procedure
- [ ] Considered feature flag for gradual rollout
""",
    "bluefield": """
### Questions to Always Ask
1. Is this component truly new, or does it touch existing code?
2. What existing services does this integrate with?
3. Are there platform standards that apply?
4. How will this be deployed alongside existing components?

### Red Flags to Watch For
- Tight coupling between new and existing components
- Ignoring platform conventions "because it's new"
- Missing contract tests for integrations
- Deployment plans that don't consider existing services

### Before Every Integration
- [ ] Contract tests written for integration points
- [ ] Adapter pattern used for legacy integration
- [ ] Deployment coordination planned
- [ ] Rollback won't affect existing components
""",
}

# Description prompt hints by project type
DESCRIPTION_HINTS = {
    "greenfield": (
        "[dim]Examples:[/dim]\n"
        "  • E-commerce platform with React frontend and Node.js API\n"
        "  • Mobile app for fitness tracking with cloud sync\n"
        "  • Internal tool for managing customer support tickets"
    ),
    "brownfield": (
        "[dim]Examples:[/dim]\n"
        "  • Legacy billing system migrating from monolith to microservices\n"
        "  • Adding new features to 10-year-old Java ERP system\n"
        "  • Modernizing PHP application with React components\n"
        "\n"
        "[dim]Consider mentioning:[/dim]\n"
        "  • Key integrations (SAP, Salesforce, legacy databases)\n"
        "  • Known constraints (APIs that can't change, frozen schemas)\n"
        "  • Technical debt areas"
    ),
    "bluefield": (
        "[dim]Examples:[/dim]\n"
        "  • New analytics module for existing SaaS platform\n"
        "  • Adding mobile app to existing web application\n"
        "  • Building new microservice within existing Kubernetes cluster\n"
        "\n"
        "[dim]Consider mentioning:[/dim]\n"
        "  • Which parts are new vs existing\n"
        "  • Shared services you'll integrate with\n"
        "  • Platform constraints or standards"
    ),
}

# Template for AI-readable context reference file
CONTEXT_REFERENCE_TEMPLATE = '''# Project Context

> **This file is auto-generated by Spec Kit.** It provides AI agents with persistent
> project context. Do not edit manually—use `specify context` to update.

## Project Type: {project_type_upper}

{project_type_description}

## Description

{description}

---

## What This Means for Development

{development_implications}

---

## Constraints

{constraints_section}

---

## Linked Artifacts

{artifacts_section}

---

## Context-Specific Guidance

{guidance_section}

---

*Last updated: {timestamp}*
*Context version: {version}*
'''

# Greenfield scaffolding templates
INSTRUCTIONS_TEMPLATE = '''# Getting Started with Spec Kit

Welcome to Spec-Driven Development (SDD)! This guide will help you understand the workflow and get your project off the ground.

## What is Spec-Driven Development?

SDD is a methodology that emphasizes creating clear specifications *before* implementation. Instead of jumping straight into code, you:

1. **Define** what you're building in plain language
2. **Specify** the details with AI assistance
3. **Plan** the implementation approach
4. **Implement** with clear guidance
5. **Review** against the original spec

## The Spec Kit Workflow

### Step 1: Establish Your Constitution

Start by running the `/speckit.constitution` command. This creates your project's guiding principles in `memory/constitution.md`.

The constitution helps AI assistants understand:
- Your project's purpose and goals
- Technical preferences and constraints
- Coding standards and patterns
- What "done" looks like for your project

### Step 2: Specify Features

When you have a feature idea, run `/speckit.specify` with a description:

```
/speckit.specify Add user authentication with OAuth2 support
```

This creates a detailed specification in `specs/features/`.

### Step 3: Plan Implementation

Once a spec is approved, run `/speckit.plan` to create an implementation plan:

```
/speckit.plan specs/features/SPEC-001-user-authentication.md
```

### Step 4: Generate Tasks

Use `/speckit.tasks` to break the plan into discrete tasks:

```
/speckit.tasks specs/plans/PLAN-001-user-authentication.md
```

### Step 5: Implement

Run `/speckit.implement` on individual tasks:

```
/speckit.implement specs/tasks/TASK-001-setup-oauth-provider.md
```

## Project Structure

```
your-project/
├── .specify/           # Spec Kit configuration
│   └── context.yaml    # Project context metadata
├── memory/             # Persistent AI context
│   ├── constitution.md # Project principles
│   └── context.md      # Auto-generated context reference
├── specs/              # All specifications
│   ├── features/       # Feature specifications
│   ├── plans/          # Implementation plans
│   └── tasks/          # Individual tasks
└── docs/               # Project documentation (optional)
    ├── architecture.md # System design decisions
    ├── roadmap.md      # Vision and milestones
    └── ideas.md        # Exploratory thinking
```

## Tips for Success

1. **Be specific in your prompts** - The more context you provide, the better the specs
2. **Review and refine specs** - Use `/speckit.clarify` to iterate on unclear areas
3. **Keep your constitution updated** - As your project evolves, so should your principles
4. **Link related specs** - Reference other specs to maintain consistency

## Next Steps

1. Run `/speckit.constitution` to establish your project principles
2. Describe your first feature and run `/speckit.specify`
3. Iterate on the spec until it captures your intent
4. Plan and implement!

## Need Help?

- Check the [Spec Kit documentation](https://github.com/mb-etc/spec-kit-etc)
- Review example specs in the `specs/` folder
- Ask your AI assistant to explain any command
'''

ARCHITECTURE_TEMPLATE = '''# Architecture Decisions

> This document captures key architectural decisions for the project. Update it as your understanding evolves.

## Overview

<!-- High-level description of the system architecture -->

_Describe the overall system design, major components, and how they interact._

## System Diagram

<!-- ASCII diagram, Mermaid, or link to visual diagram -->

```
┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │
│   Component A   │────▶│   Component B   │
│                 │     │                 │
└─────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│                 │
│   Component C   │
│                 │
└─────────────────┘
```

## Key Architectural Decisions

| # | Decision | Options Considered | Choice | Rationale |
|---|----------|-------------------|--------|----------|
| 1 | _e.g., Database_ | PostgreSQL, MongoDB, SQLite | _TBD_ | _Why this choice_ |
| 2 | _e.g., API Style_ | REST, GraphQL, gRPC | _TBD_ | _Why this choice_ |
| 3 | _e.g., Hosting_ | AWS, Azure, GCP, Self-hosted | _TBD_ | _Why this choice_ |

## Technology Stack

### Languages & Frameworks

| Layer | Technology | Version | Notes |
|-------|------------|---------|-------|
| Backend | _e.g., Python/FastAPI_ | | |
| Frontend | _e.g., React/TypeScript_ | | |
| Database | _e.g., PostgreSQL_ | | |

### Infrastructure

| Component | Technology | Notes |
|-----------|------------|-------|
| Hosting | | |
| CI/CD | | |
| Monitoring | | |

## Design Principles

<!-- Guiding principles for architectural decisions -->

1. **_Principle 1_** - _Description_
2. **_Principle 2_** - _Description_
3. **_Principle 3_** - _Description_

## Constraints

<!-- Known constraints that affect architecture -->

- _e.g., Must run in air-gapped environment_
- _e.g., Budget limited to $X/month for infrastructure_
- _e.g., Team has limited experience with X technology_

## Open Questions

<!-- Architectural decisions still to be made -->

- [ ] _Question 1_
- [ ] _Question 2_

---

*Last updated: <!-- date -->*
'''

ROADMAP_TEMPLATE = '''# Project Roadmap

> This document captures the project vision, milestones, and feature backlog.

## Vision

<!-- What does success look like? What problem are you solving? -->

_Describe the end goal of this project and the value it provides._

## Target Users

<!-- Who is this for? -->

| User Type | Description | Key Needs |
|-----------|-------------|----------|
| _Primary_ | | |
| _Secondary_ | | |

## Milestones

### M0: Foundation _(Current)_

**Goal:** _Establish project structure and core architecture_

- [ ] Project scaffolding complete
- [ ] Architecture decisions documented
- [ ] Development environment setup
- [ ] CI/CD pipeline configured

**Target Date:** _TBD_

### M1: MVP

**Goal:** _Minimum viable product with core functionality_

- [ ] _Core feature 1_
- [ ] _Core feature 2_
- [ ] _Core feature 3_
- [ ] Basic documentation

**Target Date:** _TBD_

### M2: Beta

**Goal:** _Feature-complete for initial users_

- [ ] _Additional feature 1_
- [ ] _Additional feature 2_
- [ ] User feedback integration
- [ ] Performance optimization

**Target Date:** _TBD_

### M3: Launch

**Goal:** _Production-ready release_

- [ ] Security audit complete
- [ ] Documentation complete
- [ ] Deployment automation
- [ ] Monitoring and alerting

**Target Date:** _TBD_

## Feature Backlog

<!-- Features to consider for future milestones -->

| Priority | Feature | Description | Milestone |
|----------|---------|-------------|-----------|
| High | | | |
| Medium | | | |
| Low | | | |

## Non-Goals

<!-- What this project is NOT trying to do -->

- _Explicitly out of scope item 1_
- _Explicitly out of scope item 2_

## Success Metrics

<!-- How will you measure success? -->

| Metric | Target | How Measured |
|--------|--------|-------------|
| | | |

---

*Last updated: <!-- date -->*
'''

IDEAS_TEMPLATE = '''# Ideas & Exploration

> A space for capturing exploratory thinking, brainstorms, and ideas that aren't ready for formal specification.

## Active Explorations

<!-- Ideas currently being explored or researched -->

### _Idea Title_

**Status:** Exploring | Researching | Ready to Spec | Parked

**Description:**
_What is this idea about?_

**Questions to Answer:**
- _Question 1_
- _Question 2_

**Notes:**
_Research findings, sketches, links_

---

## Idea Backlog

<!-- Quick capture of ideas for later consideration -->

| Idea | Category | Priority | Notes |
|------|----------|----------|-------|
| | | | |

## Parked Ideas

<!-- Ideas intentionally set aside (not rejected, just not now) -->

| Idea | Reason Parked | Revisit When |
|------|---------------|--------------|
| | | |

## Rejected Ideas

<!-- Ideas considered but decided against (for reference) -->

| Idea | Reason Rejected | Date |
|------|-----------------|------|
| | | |

## Inspiration & References

<!-- Links, articles, examples that inspire the project -->

- _Link or reference_

---

*Last updated: <!-- date -->*
'''

CLAUDE_LOCAL_PATH = Path.home() / ".claude" / "local" / "claude"

BANNER = """
███████╗██████╗ ███████╗ ██████╗██╗███████╗██╗   ██╗
██╔════╝██╔══██╗██╔════╝██╔════╝██║██╔════╝╚██╗ ██╔╝
███████╗██████╔╝█████╗  ██║     ██║█████╗   ╚████╔╝ 
╚════██║██╔═══╝ ██╔══╝  ██║     ██║██╔══╝    ╚██╔╝  
███████║██║     ███████╗╚██████╗██║██║        ██║   
╚══════╝╚═╝     ╚══════╝ ╚═════╝╚═╝╚═╝        ╚═╝   
"""

TAGLINE = "GitHub Spec Kit - Spec-Driven Development Toolkit"
class StepTracker:
    """Track and render hierarchical steps without emojis, similar to Claude Code tree output.
    Supports live auto-refresh via an attached refresh callback.
    """
    def __init__(self, title: str):
        self.title = title
        self.steps = []  # list of dicts: {key, label, status, detail}
        self.status_order = {"pending": 0, "running": 1, "done": 2, "error": 3, "skipped": 4}
        self._refresh_cb = None  # callable to trigger UI refresh

    def attach_refresh(self, cb):
        self._refresh_cb = cb

    def add(self, key: str, label: str):
        if key not in [s["key"] for s in self.steps]:
            self.steps.append({"key": key, "label": label, "status": "pending", "detail": ""})
            self._maybe_refresh()

    def start(self, key: str, detail: str = ""):
        self._update(key, status="running", detail=detail)

    def complete(self, key: str, detail: str = ""):
        self._update(key, status="done", detail=detail)

    def error(self, key: str, detail: str = ""):
        self._update(key, status="error", detail=detail)

    def skip(self, key: str, detail: str = ""):
        self._update(key, status="skipped", detail=detail)

    def _update(self, key: str, status: str, detail: str):
        for s in self.steps:
            if s["key"] == key:
                s["status"] = status
                if detail:
                    s["detail"] = detail
                self._maybe_refresh()
                return

        self.steps.append({"key": key, "label": key, "status": status, "detail": detail})
        self._maybe_refresh()

    def _maybe_refresh(self):
        if self._refresh_cb:
            try:
                self._refresh_cb()
            except Exception:
                pass

    def render(self):
        tree = Tree(f"[cyan]{self.title}[/cyan]", guide_style="grey50")
        for step in self.steps:
            label = step["label"]
            detail_text = step["detail"].strip() if step["detail"] else ""

            status = step["status"]
            if status == "done":
                symbol = "[green]●[/green]"
            elif status == "pending":
                symbol = "[green dim]○[/green dim]"
            elif status == "running":
                symbol = "[cyan]○[/cyan]"
            elif status == "error":
                symbol = "[red]●[/red]"
            elif status == "skipped":
                symbol = "[yellow]○[/yellow]"
            else:
                symbol = " "

            if status == "pending":
                # Entire line light gray (pending)
                if detail_text:
                    line = f"{symbol} [bright_black]{label} ({detail_text})[/bright_black]"
                else:
                    line = f"{symbol} [bright_black]{label}[/bright_black]"
            else:
                # Label white, detail (if any) light gray in parentheses
                if detail_text:
                    line = f"{symbol} [white]{label}[/white] [bright_black]({detail_text})[/bright_black]"
                else:
                    line = f"{symbol} [white]{label}[/white]"

            tree.add(line)
        return tree

def get_key():
    """Get a single keypress in a cross-platform way using readchar."""
    key = readchar.readkey()

    if key == readchar.key.UP or key == readchar.key.CTRL_P:
        return 'up'
    if key == readchar.key.DOWN or key == readchar.key.CTRL_N:
        return 'down'

    if key == readchar.key.ENTER:
        return 'enter'

    if key == readchar.key.ESC:
        return 'escape'

    if key == readchar.key.CTRL_C:
        raise KeyboardInterrupt

    return key

def select_with_arrows(options: dict, prompt_text: str = "Select an option", default_key: str = None) -> str:
    """
    Interactive selection using arrow keys with Rich Live display.
    
    Args:
        options: Dict with keys as option keys and values as descriptions
        prompt_text: Text to show above the options
        default_key: Default option key to start with
        
    Returns:
        Selected option key
    """
    option_keys = list(options.keys())
    if default_key and default_key in option_keys:
        selected_index = option_keys.index(default_key)
    else:
        selected_index = 0

    selected_key = None

    def create_selection_panel():
        """Create the selection panel with current selection highlighted."""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", justify="left", width=3)
        table.add_column(style="white", justify="left")

        for i, key in enumerate(option_keys):
            if i == selected_index:
                table.add_row("▶", f"[cyan]{key}[/cyan] [dim]({options[key]})[/dim]")
            else:
                table.add_row(" ", f"[cyan]{key}[/cyan] [dim]({options[key]})[/dim]")

        table.add_row("", "")
        table.add_row("", "[dim]Use ↑/↓ to navigate, Enter to select, Esc to cancel[/dim]")

        return Panel(
            table,
            title=f"[bold]{prompt_text}[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )

    console.print()

    def run_selection_loop():
        nonlocal selected_key, selected_index
        with Live(create_selection_panel(), console=console, transient=True, auto_refresh=False) as live:
            while True:
                try:
                    key = get_key()
                    if key == 'up':
                        selected_index = (selected_index - 1) % len(option_keys)
                    elif key == 'down':
                        selected_index = (selected_index + 1) % len(option_keys)
                    elif key == 'enter':
                        selected_key = option_keys[selected_index]
                        break
                    elif key == 'escape':
                        console.print("\n[yellow]Selection cancelled[/yellow]")
                        raise typer.Exit(1)

                    live.update(create_selection_panel(), refresh=True)

                except KeyboardInterrupt:
                    console.print("\n[yellow]Selection cancelled[/yellow]")
                    raise typer.Exit(1)

    run_selection_loop()

    if selected_key is None:
        console.print("\n[red]Selection failed.[/red]")
        raise typer.Exit(1)

    return selected_key

console = Console()

class BannerGroup(TyperGroup):
    """Custom group that shows banner before help."""

    def format_help(self, ctx, formatter):
        # Show banner before help
        show_banner()
        super().format_help(ctx, formatter)


app = typer.Typer(
    name="specify",
    help="Setup tool for Specify spec-driven development projects",
    add_completion=False,
    invoke_without_command=True,
    cls=BannerGroup,
)

def show_banner():
    """Display the ASCII art banner."""
    banner_lines = BANNER.strip().split('\n')
    colors = ["bright_blue", "blue", "cyan", "bright_cyan", "white", "bright_white"]

    styled_banner = Text()
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]
        styled_banner.append(line + "\n", style=color)

    console.print(Align.center(styled_banner))
    console.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))
    console.print()

@app.callback()
def callback(ctx: typer.Context):
    """Show banner when no subcommand is provided."""
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv:
        show_banner()
        console.print(Align.center("[dim]Run 'specify --help' for usage information[/dim]"))
        console.print()

def run_command(cmd: list[str], check_return: bool = True, capture: bool = False, shell: bool = False) -> Optional[str]:
    """Run a shell command and optionally capture output."""
    try:
        if capture:
            result = subprocess.run(cmd, check=check_return, capture_output=True, text=True, shell=shell)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, check=check_return, shell=shell)
            return None
    except subprocess.CalledProcessError as e:
        if check_return:
            console.print(f"[red]Error running command:[/red] {' '.join(cmd)}")
            console.print(f"[red]Exit code:[/red] {e.returncode}")
            if hasattr(e, 'stderr') and e.stderr:
                console.print(f"[red]Error output:[/red] {e.stderr}")
            raise
        return None

def check_tool(tool: str, tracker: StepTracker = None) -> bool:
    """Check if a tool is installed. Optionally update tracker.
    
    Args:
        tool: Name of the tool to check
        tracker: Optional StepTracker to update with results
        
    Returns:
        True if tool is found, False otherwise
    """
    # Special handling for Claude CLI after `claude migrate-installer`
    # See: https://github.com/github/spec-kit/issues/123
    # The migrate-installer command REMOVES the original executable from PATH
    # and creates an alias at ~/.claude/local/claude instead
    # This path should be prioritized over other claude executables in PATH
    if tool == "claude":
        if CLAUDE_LOCAL_PATH.exists() and CLAUDE_LOCAL_PATH.is_file():
            if tracker:
                tracker.complete(tool, "available")
            return True
    
    found = shutil.which(tool) is not None
    
    if tracker:
        if found:
            tracker.complete(tool, "available")
        else:
            tracker.error(tool, "not found")
    
    return found

def is_git_repo(path: Path = None) -> bool:
    """Check if the specified path is inside a git repository."""
    if path is None:
        path = Path.cwd()
    
    if not path.is_dir():
        return False

    try:
        # Use git command to check if inside a work tree
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            capture_output=True,
            cwd=path,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def init_git_repo(project_path: Path, quiet: bool = False) -> Tuple[bool, Optional[str]]:
    """Initialize a git repository in the specified path.
    
    Args:
        project_path: Path to initialize git repository in
        quiet: if True suppress console output (tracker handles status)
    
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        original_cwd = Path.cwd()
        os.chdir(project_path)
        if not quiet:
            console.print("[cyan]Initializing git repository...[/cyan]")
        subprocess.run(["git", "init"], check=True, capture_output=True, text=True)
        subprocess.run(["git", "add", "."], check=True, capture_output=True, text=True)
        subprocess.run(["git", "commit", "-m", "Initial commit from Specify template"], check=True, capture_output=True, text=True)
        if not quiet:
            console.print("[green]✓[/green] Git repository initialized")
        return True, None

    except subprocess.CalledProcessError as e:
        error_msg = f"Command: {' '.join(e.cmd)}\nExit code: {e.returncode}"
        if e.stderr:
            error_msg += f"\nError: {e.stderr.strip()}"
        elif e.stdout:
            error_msg += f"\nOutput: {e.stdout.strip()}"
        
        if not quiet:
            console.print(f"[red]Error initializing git repository:[/red] {e}")
        return False, error_msg
    finally:
        os.chdir(original_cwd)

def handle_vscode_settings(sub_item, dest_file, rel_path, verbose=False, tracker=None) -> None:
    """Handle merging or copying of .vscode/settings.json files."""
    def log(message, color="green"):
        if verbose and not tracker:
            console.print(f"[{color}]{message}[/] {rel_path}")

    try:
        with open(sub_item, 'r', encoding='utf-8') as f:
            new_settings = json.load(f)

        if dest_file.exists():
            merged = merge_json_files(dest_file, new_settings, verbose=verbose and not tracker)
            with open(dest_file, 'w', encoding='utf-8') as f:
                json.dump(merged, f, indent=4)
                f.write('\n')
            log("Merged:", "green")
        else:
            shutil.copy2(sub_item, dest_file)
            log("Copied (no existing settings.json):", "blue")

    except Exception as e:
        log(f"Warning: Could not merge, copying instead: {e}", "yellow")
        shutil.copy2(sub_item, dest_file)

def merge_json_files(existing_path: Path, new_content: dict, verbose: bool = False) -> dict:
    """Merge new JSON content into existing JSON file.

    Performs a deep merge where:
    - New keys are added
    - Existing keys are preserved unless overwritten by new content
    - Nested dictionaries are merged recursively
    - Lists and other values are replaced (not merged)

    Args:
        existing_path: Path to existing JSON file
        new_content: New JSON content to merge in
        verbose: Whether to print merge details

    Returns:
        Merged JSON content as dict
    """
    try:
        with open(existing_path, 'r', encoding='utf-8') as f:
            existing_content = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is invalid, just use new content
        return new_content

    def deep_merge(base: dict, update: dict) -> dict:
        """Recursively merge update dict into base dict."""
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = deep_merge(result[key], value)
            else:
                # Add new key or replace existing value
                result[key] = value
        return result

    merged = deep_merge(existing_content, new_content)

    if verbose:
        console.print(f"[cyan]Merged JSON file:[/cyan] {existing_path.name}")

    return merged

def download_template_from_github(ai_assistant: str, download_dir: Path, *, script_type: str = "sh", verbose: bool = True, show_progress: bool = True, client: httpx.Client = None, debug: bool = False, github_token: str = None) -> Tuple[Path, dict]:
    repo_owner = "mb-etc"
    repo_name = "spec-kit-etc"
    if client is None:
        client = httpx.Client(verify=ssl_context)

    if verbose:
        console.print("[cyan]Fetching latest release information...[/cyan]")
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"

    try:
        response = client.get(
            api_url,
            timeout=30,
            follow_redirects=True,
            headers=_github_auth_headers(github_token),
        )
        status = response.status_code
        if status != 200:
            # Format detailed error message with rate-limit info
            error_msg = _format_rate_limit_error(status, response.headers, api_url)
            if debug:
                error_msg += f"\n\n[dim]Response body (truncated 500):[/dim]\n{response.text[:500]}"
            raise RuntimeError(error_msg)
        try:
            release_data = response.json()
        except ValueError as je:
            raise RuntimeError(f"Failed to parse release JSON: {je}\nRaw (truncated 400): {response.text[:400]}")
    except Exception as e:
        console.print(f"[red]Error fetching release information[/red]")
        console.print(Panel(str(e), title="Fetch Error", border_style="red"))
        raise typer.Exit(1)

    assets = release_data.get("assets", [])
    pattern = f"spec-kit-template-{ai_assistant}-{script_type}"
    matching_assets = [
        asset for asset in assets
        if pattern in asset["name"] and asset["name"].endswith(".zip")
    ]

    asset = matching_assets[0] if matching_assets else None

    if asset is None:
        console.print(f"[red]No matching release asset found[/red] for [bold]{ai_assistant}[/bold] (expected pattern: [bold]{pattern}[/bold])")
        asset_names = [a.get('name', '?') for a in assets]
        console.print(Panel("\n".join(asset_names) or "(no assets)", title="Available Assets", border_style="yellow"))
        raise typer.Exit(1)

    download_url = asset["browser_download_url"]
    filename = asset["name"]
    file_size = asset["size"]

    if verbose:
        console.print(f"[cyan]Found template:[/cyan] {filename}")
        console.print(f"[cyan]Size:[/cyan] {file_size:,} bytes")
        console.print(f"[cyan]Release:[/cyan] {release_data['tag_name']}")

    zip_path = download_dir / filename
    if verbose:
        console.print(f"[cyan]Downloading template...[/cyan]")

    try:
        with client.stream(
            "GET",
            download_url,
            timeout=60,
            follow_redirects=True,
            headers=_github_auth_headers(github_token),
        ) as response:
            if response.status_code != 200:
                # Handle rate-limiting on download as well
                error_msg = _format_rate_limit_error(response.status_code, response.headers, download_url)
                if debug:
                    error_msg += f"\n\n[dim]Response body (truncated 400):[/dim]\n{response.text[:400]}"
                raise RuntimeError(error_msg)
            total_size = int(response.headers.get('content-length', 0))
            with open(zip_path, 'wb') as f:
                if total_size == 0:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
                else:
                    if show_progress:
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                            console=console,
                        ) as progress:
                            task = progress.add_task("Downloading...", total=total_size)
                            downloaded = 0
                            for chunk in response.iter_bytes(chunk_size=8192):
                                f.write(chunk)
                                downloaded += len(chunk)
                                progress.update(task, completed=downloaded)
                    else:
                        for chunk in response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
    except Exception as e:
        console.print(f"[red]Error downloading template[/red]")
        detail = str(e)
        if zip_path.exists():
            zip_path.unlink()
        console.print(Panel(detail, title="Download Error", border_style="red"))
        raise typer.Exit(1)
    if verbose:
        console.print(f"Downloaded: {filename}")
    metadata = {
        "filename": filename,
        "size": file_size,
        "release": release_data["tag_name"],
        "asset_url": download_url
    }
    return zip_path, metadata

def download_and_extract_template(project_path: Path, ai_assistant: str, script_type: str, is_current_dir: bool = False, *, verbose: bool = True, tracker: StepTracker | None = None, client: httpx.Client = None, debug: bool = False, github_token: str = None) -> Path:
    """Download the latest release and extract it to create a new project.
    Returns project_path. Uses tracker if provided (with keys: fetch, download, extract, cleanup)
    """
    current_dir = Path.cwd()

    if tracker:
        tracker.start("fetch", "contacting GitHub API")
    try:
        zip_path, meta = download_template_from_github(
            ai_assistant,
            current_dir,
            script_type=script_type,
            verbose=verbose and tracker is None,
            show_progress=(tracker is None),
            client=client,
            debug=debug,
            github_token=github_token
        )
        if tracker:
            tracker.complete("fetch", f"release {meta['release']} ({meta['size']:,} bytes)")
            tracker.add("download", "Download template")
            tracker.complete("download", meta['filename'])
    except Exception as e:
        if tracker:
            tracker.error("fetch", str(e))
        else:
            if verbose:
                console.print(f"[red]Error downloading template:[/red] {e}")
        raise

    if tracker:
        tracker.add("extract", "Extract template")
        tracker.start("extract")
    elif verbose:
        console.print("Extracting template...")

    try:
        if not is_current_dir:
            project_path.mkdir(parents=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_contents = zip_ref.namelist()
            if tracker:
                tracker.start("zip-list")
                tracker.complete("zip-list", f"{len(zip_contents)} entries")
            elif verbose:
                console.print(f"[cyan]ZIP contains {len(zip_contents)} items[/cyan]")

            if is_current_dir:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    zip_ref.extractall(temp_path)

                    extracted_items = list(temp_path.iterdir())
                    if tracker:
                        tracker.start("extracted-summary")
                        tracker.complete("extracted-summary", f"temp {len(extracted_items)} items")
                    elif verbose:
                        console.print(f"[cyan]Extracted {len(extracted_items)} items to temp location[/cyan]")

                    source_dir = temp_path
                    if len(extracted_items) == 1 and extracted_items[0].is_dir():
                        source_dir = extracted_items[0]
                        if tracker:
                            tracker.add("flatten", "Flatten nested directory")
                            tracker.complete("flatten")
                        elif verbose:
                            console.print(f"[cyan]Found nested directory structure[/cyan]")

                    for item in source_dir.iterdir():
                        dest_path = project_path / item.name
                        if item.is_dir():
                            if dest_path.exists():
                                if verbose and not tracker:
                                    console.print(f"[yellow]Merging directory:[/yellow] {item.name}")
                                for sub_item in item.rglob('*'):
                                    if sub_item.is_file():
                                        rel_path = sub_item.relative_to(item)
                                        dest_file = dest_path / rel_path
                                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                                        # Special handling for .vscode/settings.json - merge instead of overwrite
                                        if dest_file.name == "settings.json" and dest_file.parent.name == ".vscode":
                                            handle_vscode_settings(sub_item, dest_file, rel_path, verbose, tracker)
                                        else:
                                            shutil.copy2(sub_item, dest_file)
                            else:
                                shutil.copytree(item, dest_path)
                        else:
                            if dest_path.exists() and verbose and not tracker:
                                console.print(f"[yellow]Overwriting file:[/yellow] {item.name}")
                            shutil.copy2(item, dest_path)
                    if verbose and not tracker:
                        console.print(f"[cyan]Template files merged into current directory[/cyan]")
            else:
                zip_ref.extractall(project_path)

                extracted_items = list(project_path.iterdir())
                if tracker:
                    tracker.start("extracted-summary")
                    tracker.complete("extracted-summary", f"{len(extracted_items)} top-level items")
                elif verbose:
                    console.print(f"[cyan]Extracted {len(extracted_items)} items to {project_path}:[/cyan]")
                    for item in extracted_items:
                        console.print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")

                if len(extracted_items) == 1 and extracted_items[0].is_dir():
                    nested_dir = extracted_items[0]
                    temp_move_dir = project_path.parent / f"{project_path.name}_temp"

                    shutil.move(str(nested_dir), str(temp_move_dir))

                    project_path.rmdir()

                    shutil.move(str(temp_move_dir), str(project_path))
                    if tracker:
                        tracker.add("flatten", "Flatten nested directory")
                        tracker.complete("flatten")
                    elif verbose:
                        console.print(f"[cyan]Flattened nested directory structure[/cyan]")

    except Exception as e:
        if tracker:
            tracker.error("extract", str(e))
        else:
            if verbose:
                console.print(f"[red]Error extracting template:[/red] {e}")
                if debug:
                    console.print(Panel(str(e), title="Extraction Error", border_style="red"))

        if not is_current_dir and project_path.exists():
            shutil.rmtree(project_path)
        raise typer.Exit(1)
    else:
        if tracker:
            tracker.complete("extract")
    finally:
        if tracker:
            tracker.add("cleanup", "Remove temporary archive")

        if zip_path.exists():
            zip_path.unlink()
            if tracker:
                tracker.complete("cleanup")
            elif verbose:
                console.print(f"Cleaned up: {zip_path.name}")

    return project_path


def ensure_executable_scripts(project_path: Path, tracker: StepTracker | None = None) -> None:
    """Ensure POSIX .sh scripts under .specify/scripts (recursively) have execute bits (no-op on Windows)."""
    if os.name == "nt":
        return  # Windows: skip silently
    scripts_root = project_path / ".specify" / "scripts"
    if not scripts_root.is_dir():
        return
    failures: list[str] = []
    updated = 0
    for script in scripts_root.rglob("*.sh"):
        try:
            if script.is_symlink() or not script.is_file():
                continue
            try:
                with script.open("rb") as f:
                    if f.read(2) != b"#!":
                        continue
            except Exception:
                continue
            st = script.stat(); mode = st.st_mode
            if mode & 0o111:
                continue
            new_mode = mode
            if mode & 0o400: new_mode |= 0o100
            if mode & 0o040: new_mode |= 0o010
            if mode & 0o004: new_mode |= 0o001
            if not (new_mode & 0o100):
                new_mode |= 0o100
            os.chmod(script, new_mode)
            updated += 1
        except Exception as e:
            failures.append(f"{script.relative_to(scripts_root)}: {e}")
    if tracker:
        detail = f"{updated} updated" + (f", {len(failures)} failed" if failures else "")
        tracker.add("chmod", "Set script permissions recursively")
        (tracker.error if failures else tracker.complete)("chmod", detail)
    else:
        if updated:
            console.print(f"[cyan]Updated execute permissions on {updated} script(s) recursively[/cyan]")
        if failures:
            console.print("[yellow]Some scripts could not be updated:[/yellow]")
            for f in failures:
                console.print(f"  - {f}")


def create_greenfield_scaffolding(project_path: Path, tracker: StepTracker | None = None) -> None:
    """Create docs/ folder with greenfield scaffolding templates."""
    docs_dir = project_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    scaffolding_files = {
        "architecture.md": ARCHITECTURE_TEMPLATE,
        "roadmap.md": ROADMAP_TEMPLATE,
        "ideas.md": IDEAS_TEMPLATE,
    }
    
    for filename, content in scaffolding_files.items():
        dest = docs_dir / filename
        if not dest.exists():
            dest.write_text(content)
    
    if tracker:
        tracker.add("scaffolding", "Create greenfield scaffolding")
        tracker.complete("scaffolding", "docs/")


def create_instructions_file(project_path: Path, tracker: StepTracker | None = None) -> None:
    """Create instructions.md in project root."""
    dest = project_path / "instructions.md"
    
    if not dest.exists():
        dest.write_text(INSTRUCTIONS_TEMPLATE)
    
    if tracker:
        tracker.add("instructions", "Create instructions.md")
        tracker.complete("instructions", "created")


def generate_context_reference(
    project_path: Path,
    project_type: str,
    description: str,
    constraints: list,
    linked_artifacts: dict,
    timestamp: str,
    version: int = 1
) -> None:
    """Generate memory/context.md for AI agent reference."""
    memory_dir = project_path / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    # Format constraints section
    if constraints:
        constraints_section = "\n".join(f"- {c}" for c in constraints)
    else:
        constraints_section = "_No constraints defined. Add via `specify context --add-constraint`._"
    
    # Format artifacts section
    artifacts_lines = []
    for category, items in (linked_artifacts or {}).items():
        if items:
            artifacts_lines.append(f"### {category.title()}")
            for item in items:
                artifacts_lines.append(f"- {item}")
    artifacts_section = "\n".join(artifacts_lines) if artifacts_lines else "_No linked artifacts. Edit `.specify/context.yaml` to add._"
    
    content = CONTEXT_REFERENCE_TEMPLATE.format(
        project_type_upper=project_type.upper(),
        project_type_description=PROJECT_TYPE_DESCRIPTIONS.get(project_type, "Unknown project type."),
        description=description if description else "_No description provided._",
        development_implications=PROJECT_TYPE_IMPLICATIONS.get(project_type, ""),
        constraints_section=constraints_section,
        artifacts_section=artifacts_section,
        guidance_section=CONTEXT_GUIDANCE.get(project_type, ""),
        timestamp=timestamp,
        version=version,
    )
    
    context_md = memory_dir / "context.md"
    context_md.write_text(content)


def create_project_context(project_path: Path, project_type: str, description: str = "", tracker: StepTracker | None = None) -> None:
    """Create .specify/context.yaml and memory/context.md with project context metadata."""
    context_dir = project_path / ".specify"
    context_dir.mkdir(parents=True, exist_ok=True)
    context_file = context_dir / "context.yaml"
    
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Escape description for YAML (handle multiline)
    if description:
        # Indent multiline descriptions properly
        if "\n" in description:
            desc_lines = description.split("\n")
            description_yaml = "|\n" + "\n".join(f"  {line}" for line in desc_lines)
        else:
            # Single line - quote if contains special characters
            if any(c in description for c in ":#{}[]&*!|>'\"%@`"):
                description_yaml = f'"{description}"'
            else:
                description_yaml = description
    else:
        description_yaml = '""'
    
    context_content = f"""# Spec Kit Project Context
# This file defines the project context for spec-driven development.
# Context helps AI assistants provide more accurate, realistic specs.

# Project type determines prompting and validation behavior:
#   greenfield - New project with full design freedom
#   brownfield - Existing system with legacy constraints
#   bluefield  - Existing platform with new components
project_type: {project_type}

# Brief description of the project or system
description: {description_yaml}

# Known constraints that must be respected
# Examples:
#   - Must not change existing APIs
#   - Data model changes require migration
#   - Must maintain backward compatibility with v2.x clients
constraints: []

# Links to external artifacts for context (optional)
# These help AI assistants understand existing documentation
linked_artifacts:
  # Issue tracker references
  # jira:
  #   - PROJECT-1234
  #   - PROJECT-5678
  
  # Documentation links
  # confluence:
  #   - Architecture Overview
  #   - API Design Guidelines
  
  # Local documentation paths
  # docs:
  #   - docs/architecture.md
  #   - docs/known-issues.md

# Metadata (auto-populated by Spec Kit)
created: {now}
updated: {now}
version: 1
"""
    
    context_file.write_text(context_content)
    
    # Generate AI-readable reference file
    generate_context_reference(
        project_path=project_path,
        project_type=project_type,
        description=description,
        constraints=[],
        linked_artifacts={},
        timestamp=now,
        version=1
    )
    
    if tracker:
        tracker.add("context", "Create project context")
        tracker.complete("context", project_type)


@app.command()
def init(
    project_name: str = typer.Argument(None, help="Name for your new project directory (optional if using --here, or use '.' for current directory)"),
    ai_assistant: str = typer.Option(None, "--ai", help="AI assistant to use: claude, gemini, copilot, cursor-agent, qwen, opencode, codex, windsurf, kilocode, auggie, codebuddy, amp, shai, q, bob, or qoder "),
    script_type: str = typer.Option(None, "--script", help="Script type to use: sh or ps"),
    ignore_agent_tools: bool = typer.Option(False, "--ignore-agent-tools", help="Skip checks for AI agent tools like Claude Code"),
    no_git: bool = typer.Option(False, "--no-git", help="Skip git repository initialization"),
    here: bool = typer.Option(False, "--here", help="Initialize project in the current directory instead of creating a new one"),
    force: bool = typer.Option(False, "--force", help="Force merge/overwrite when using --here (skip confirmation)"),
    skip_tls: bool = typer.Option(False, "--skip-tls", help="Skip SSL/TLS verification (not recommended)"),
    debug: bool = typer.Option(False, "--debug", help="Show verbose diagnostic output for network and extraction failures"),
    github_token: str = typer.Option(None, "--github-token", help="GitHub token to use for API requests (or set GH_TOKEN or GITHUB_TOKEN environment variable)"),
):
    """
    Initialize a new Specify project from the latest template.
    
    This command will:
    1. Check that required tools are installed (git is optional)
    2. Let you choose your AI assistant
    3. Download the appropriate template from GitHub
    4. Extract the template to a new project directory or current directory
    5. Initialize a fresh git repository (if not --no-git and no existing repo)
    6. Optionally set up AI assistant commands
    
    Examples:
        specify init my-project
        specify init my-project --ai claude
        specify init my-project --ai copilot --no-git
        specify init --ignore-agent-tools my-project
        specify init . --ai claude         # Initialize in current directory
        specify init .                     # Initialize in current directory (interactive AI selection)
        specify init --here --ai claude    # Alternative syntax for current directory
        specify init --here --ai codex
        specify init --here --ai codebuddy
        specify init --here
        specify init --here --force  # Skip confirmation when current directory not empty
    """

    show_banner()

    if project_name == ".":
        here = True
        project_name = None  # Clear project_name to use existing validation logic

    if here and project_name:
        console.print("[red]Error:[/red] Cannot specify both project name and --here flag")
        raise typer.Exit(1)

    if not here and not project_name:
        console.print("[red]Error:[/red] Must specify either a project name, use '.' for current directory, or use --here flag")
        raise typer.Exit(1)

    if here:
        project_name = Path.cwd().name
        project_path = Path.cwd()

        existing_items = list(project_path.iterdir())
        if existing_items:
            console.print(f"[yellow]Warning:[/yellow] Current directory is not empty ({len(existing_items)} items)")
            console.print("[yellow]Template files will be merged with existing content and may overwrite existing files[/yellow]")
            if force:
                console.print("[cyan]--force supplied: skipping confirmation and proceeding with merge[/cyan]")
            else:
                response = typer.confirm("Do you want to continue?")
                if not response:
                    console.print("[yellow]Operation cancelled[/yellow]")
                    raise typer.Exit(0)
    else:
        project_path = Path(project_name).resolve()
        if project_path.exists():
            error_panel = Panel(
                f"Directory '[cyan]{project_name}[/cyan]' already exists\n"
                "Please choose a different project name or remove the existing directory.",
                title="[red]Directory Conflict[/red]",
                border_style="red",
                padding=(1, 2)
            )
            console.print()
            console.print(error_panel)
            raise typer.Exit(1)

    current_dir = Path.cwd()

    setup_lines = [
        "[cyan]Specify Project Setup[/cyan]",
        "",
        f"{'Project':<15} [green]{project_path.name}[/green]",
        f"{'Working Path':<15} [dim]{current_dir}[/dim]",
    ]

    if not here:
        setup_lines.append(f"{'Target Path':<15} [dim]{project_path}[/dim]")

    console.print(Panel("\n".join(setup_lines), border_style="cyan", padding=(1, 2)))

    should_init_git = False
    if not no_git:
        should_init_git = check_tool("git")
        if not should_init_git:
            console.print("[yellow]Git not found - will skip repository initialization[/yellow]")

    if ai_assistant:
        if ai_assistant not in AGENT_CONFIG:
            console.print(f"[red]Error:[/red] Invalid AI assistant '{ai_assistant}'. Choose from: {', '.join(AGENT_CONFIG.keys())}")
            raise typer.Exit(1)
        selected_ai = ai_assistant
    else:
        # Create options dict for selection (agent_key: display_name)
        ai_choices = {key: config["name"] for key, config in AGENT_CONFIG.items()}
        selected_ai = select_with_arrows(
            ai_choices, 
            "Choose your AI assistant:", 
            "copilot"
        )

    if not ignore_agent_tools:
        agent_config = AGENT_CONFIG.get(selected_ai)
        if agent_config and agent_config["requires_cli"]:
            install_url = agent_config["install_url"]
            if not check_tool(selected_ai):
                error_panel = Panel(
                    f"[cyan]{selected_ai}[/cyan] not found\n"
                    f"Install from: [cyan]{install_url}[/cyan]\n"
                    f"{agent_config['name']} is required to continue with this project type.\n\n"
                    "Tip: Use [cyan]--ignore-agent-tools[/cyan] to skip this check",
                    title="[red]Agent Detection Error[/red]",
                    border_style="red",
                    padding=(1, 2)
                )
                console.print()
                console.print(error_panel)
                raise typer.Exit(1)

    if script_type:
        if script_type not in SCRIPT_TYPE_CHOICES:
            console.print(f"[red]Error:[/red] Invalid script type '{script_type}'. Choose from: {', '.join(SCRIPT_TYPE_CHOICES.keys())}")
            raise typer.Exit(1)
        selected_script = script_type
    else:
        default_script = "ps" if os.name == "nt" else "sh"

        if sys.stdin.isatty():
            selected_script = select_with_arrows(SCRIPT_TYPE_CHOICES, "Choose script type (or press Enter)", default_script)
        else:
            selected_script = default_script

    # Project context selection
    if sys.stdin.isatty():
        selected_project_type = select_with_arrows(
            PROJECT_TYPE_CHOICES, 
            "What type of project is this?", 
            "greenfield"
        )
        
        # Show context-specific description hints
        console.print()
        if selected_project_type in DESCRIPTION_HINTS:
            console.print(f"[dim]{DESCRIPTION_HINTS[selected_project_type]}[/dim]")
        
        # Optional description prompt
        project_description = typer.prompt(
            "Brief project description (optional, press Enter to skip)",
            default="",
            show_default=False
        )
    else:
        selected_project_type = "greenfield"
        project_description = ""

    # Check if first time (no .specify folder exists yet) - project-local detection
    is_first_run = not (project_path / ".specify").exists()
    create_instructions = False
    create_scaffolding = False
    
    if sys.stdin.isatty():
        # First-time onboarding prompt
        if is_first_run:
            console.print()
            create_instructions = typer.confirm(
                "Create instructions.md with Spec Kit getting started guide?",
                default=True
            )
        
        # Greenfield scaffolding prompt
        if selected_project_type == "greenfield":
            console.print()
            create_scaffolding = typer.confirm(
                "Create docs/ folder with architecture, roadmap, and ideas templates?",
                default=True
            )

    console.print(f"[cyan]Selected AI assistant:[/cyan] {selected_ai}")
    console.print(f"[cyan]Selected script type:[/cyan] {selected_script}")
    console.print(f"[cyan]Project type:[/cyan] {selected_project_type}")
    if project_description:
        console.print(f"[cyan]Description:[/cyan] {project_description[:50]}{'...' if len(project_description) > 50 else ''}")

    tracker = StepTracker("Initialize Specify Project")

    sys._specify_tracker_active = True

    tracker.add("precheck", "Check required tools")
    tracker.complete("precheck", "ok")
    tracker.add("ai-select", "Select AI assistant")
    tracker.complete("ai-select", f"{selected_ai}")
    tracker.add("script-select", "Select script type")
    tracker.complete("script-select", selected_script)
    tracker.add("context-select", "Select project context")
    tracker.complete("context-select", selected_project_type)
    for key, label in [
        ("fetch", "Fetch latest release"),
        ("download", "Download template"),
        ("extract", "Extract template"),
        ("zip-list", "Archive contents"),
        ("extracted-summary", "Extraction summary"),
        ("chmod", "Ensure scripts executable"),
        ("context", "Create project context"),
        ("cleanup", "Cleanup"),
        ("git", "Initialize git repository"),
        ("final", "Finalize")
    ]:
        tracker.add(key, label)

    # Track git error message outside Live context so it persists
    git_error_message = None

    with Live(tracker.render(), console=console, refresh_per_second=8, transient=True) as live:
        tracker.attach_refresh(lambda: live.update(tracker.render()))
        try:
            verify = not skip_tls
            local_ssl_context = ssl_context if verify else False
            local_client = httpx.Client(verify=local_ssl_context)

            download_and_extract_template(project_path, selected_ai, selected_script, here, verbose=False, tracker=tracker, client=local_client, debug=debug, github_token=github_token)

            ensure_executable_scripts(project_path, tracker=tracker)

            # Create project context file
            create_project_context(project_path, selected_project_type, project_description, tracker=tracker)

            # Create optional scaffolding files
            if create_instructions:
                create_instructions_file(project_path, tracker=tracker)
            
            if create_scaffolding:
                create_greenfield_scaffolding(project_path, tracker=tracker)

            if not no_git:
                tracker.start("git")
                if is_git_repo(project_path):
                    tracker.complete("git", "existing repo detected")
                elif should_init_git:
                    success, error_msg = init_git_repo(project_path, quiet=True)
                    if success:
                        tracker.complete("git", "initialized")
                    else:
                        tracker.error("git", "init failed")
                        git_error_message = error_msg
                else:
                    tracker.skip("git", "git not available")
            else:
                tracker.skip("git", "--no-git flag")

            tracker.complete("final", "project ready")
        except Exception as e:
            tracker.error("final", str(e))
            console.print(Panel(f"Initialization failed: {e}", title="Failure", border_style="red"))
            if debug:
                _env_pairs = [
                    ("Python", sys.version.split()[0]),
                    ("Platform", sys.platform),
                    ("CWD", str(Path.cwd())),
                ]
                _label_width = max(len(k) for k, _ in _env_pairs)
                env_lines = [f"{k.ljust(_label_width)} → [bright_black]{v}[/bright_black]" for k, v in _env_pairs]
                console.print(Panel("\n".join(env_lines), title="Debug Environment", border_style="magenta"))
            if not here and project_path.exists():
                shutil.rmtree(project_path)
            raise typer.Exit(1)
        finally:
            pass

    console.print(tracker.render())
    console.print("\n[bold green]Project ready.[/bold green]")
    
    # Show git error details if initialization failed
    if git_error_message:
        console.print()
        git_error_panel = Panel(
            f"[yellow]Warning:[/yellow] Git repository initialization failed\n\n"
            f"{git_error_message}\n\n"
            f"[dim]You can initialize git manually later with:[/dim]\n"
            f"[cyan]cd {project_path if not here else '.'}[/cyan]\n"
            f"[cyan]git init[/cyan]\n"
            f"[cyan]git add .[/cyan]\n"
            f"[cyan]git commit -m \"Initial commit\"[/cyan]",
            title="[red]Git Initialization Failed[/red]",
            border_style="red",
            padding=(1, 2)
        )
        console.print(git_error_panel)

    # Agent folder security notice
    agent_config = AGENT_CONFIG.get(selected_ai)
    if agent_config:
        agent_folder = agent_config["folder"]
        security_notice = Panel(
            f"Some agents may store credentials, auth tokens, or other identifying and private artifacts in the agent folder within your project.\n"
            f"Consider adding [cyan]{agent_folder}[/cyan] (or parts of it) to [cyan].gitignore[/cyan] to prevent accidental credential leakage.",
            title="[yellow]Agent Folder Security[/yellow]",
            border_style="yellow",
            padding=(1, 2)
        )
        console.print()
        console.print(security_notice)

    steps_lines = []
    if not here:
        steps_lines.append(f"1. Go to the project folder: [cyan]cd {project_name}[/cyan]")
        step_num = 2
    else:
        steps_lines.append("1. You're already in the project directory!")
        step_num = 2

    # Add Codex-specific setup step if needed
    if selected_ai == "codex":
        codex_path = project_path / ".codex"
        quoted_path = shlex.quote(str(codex_path))
        if os.name == "nt":  # Windows
            cmd = f"setx CODEX_HOME {quoted_path}"
        else:  # Unix-like systems
            cmd = f"export CODEX_HOME={quoted_path}"
        
        steps_lines.append(f"{step_num}. Set [cyan]CODEX_HOME[/cyan] environment variable before running Codex: [cyan]{cmd}[/cyan]")
        step_num += 1

    steps_lines.append(f"{step_num}. Start using slash commands with your AI agent:")

    # Show different first step for greenfield projects
    if selected_project_type == "greenfield":
        steps_lines.append("   2.1 [cyan]/speckit.initialize[/] - Bootstrap project vision, architecture & roadmap")
        steps_lines.append("   2.2 [cyan]/speckit.constitution[/] - Establish project principles")
        steps_lines.append("   2.3 [cyan]/speckit.specify[/] - Create baseline specification")
        steps_lines.append("   2.4 [cyan]/speckit.plan[/] - Create implementation plan")
        steps_lines.append("   2.5 [cyan]/speckit.tasks[/] - Generate actionable tasks")
        steps_lines.append("   2.6 [cyan]/speckit.implement[/] - Execute implementation")
    else:
        steps_lines.append("   2.1 [cyan]/speckit.constitution[/] - Establish project principles")
        steps_lines.append("   2.2 [cyan]/speckit.specify[/] - Create baseline specification")
        steps_lines.append("   2.3 [cyan]/speckit.plan[/] - Create implementation plan")
        steps_lines.append("   2.4 [cyan]/speckit.tasks[/] - Generate actionable tasks")
        steps_lines.append("   2.5 [cyan]/speckit.implement[/] - Execute implementation")

    steps_panel = Panel("\n".join(steps_lines), title="Next Steps", border_style="cyan", padding=(1,2))
    console.print()
    console.print(steps_panel)

    enhancement_lines = [
        "Optional commands that you can use for your specs [bright_black](improve quality & confidence)[/bright_black]",
        "",
        f"○ [cyan]/speckit.clarify[/] [bright_black](optional)[/bright_black] - Ask structured questions to de-risk ambiguous areas before planning (run before [cyan]/speckit.plan[/] if used)",
        f"○ [cyan]/speckit.analyze[/] [bright_black](optional)[/bright_black] - Cross-artifact consistency & alignment report (after [cyan]/speckit.tasks[/], before [cyan]/speckit.implement[/])",
        f"○ [cyan]/speckit.checklist[/] [bright_black](optional)[/bright_black] - Generate quality checklists to validate requirements completeness, clarity, and consistency (after [cyan]/speckit.plan[/])",
        f"○ [cyan]/speckit.fix[/] [bright_black](optional)[/bright_black] - Diagnose and fix issues with targeted remediation"
    ]
    enhancements_panel = Panel("\n".join(enhancement_lines), title="Enhancement Commands", border_style="cyan", padding=(1,2))
    console.print()
    console.print(enhancements_panel)

    review_lines = [
        "Quality gates and release preparation [bright_black](run after implementation)[/bright_black]",
        "",
        f"○ [cyan]/speckit.review-implementation[/] - Audit code against spec with compliance matrix",
        f"○ [cyan]/speckit.review-security[/] - CodeGuard-powered security review with language-aware rules",
        f"○ [cyan]/speckit.review-readiness[/] - Production deployment gates with cutover/rollback runbooks",
        f"○ [cyan]/speckit.review-uat[/] - Generate UAT plans and manual checklists from acceptance criteria",
        f"○ [cyan]/speckit.review-summary[/] - Create documentation packs (technical, user, admin guides)",
        f"○ [cyan]/speckit.release-notes[/] - Generate changelog entries and release notes"
    ]
    review_panel = Panel("\n".join(review_lines), title="Review Commands", border_style="magenta", padding=(1,2))
    console.print()
    console.print(review_panel)

    # Greenfield-specific tip
    if selected_project_type == "greenfield":
        console.print()
        greenfield_tip = Panel(
            "Since this is a [bold]greenfield project[/bold], start by running [cyan]/speckit.initialize[/cyan] to have a conversation about your project vision.\n\n"
            "This will populate your [cyan]docs/architecture.md[/cyan], [cyan]docs/roadmap.md[/cyan], and [cyan]docs/ideas.md[/cyan] files, "
            "giving you a solid foundation before establishing your constitution and specifying features.\n\n"
            "[dim]Tip: You can paste an initial idea or project description after the command:[/dim]\n"
            "[cyan]/speckit.initialize I want to build a task management app with real-time collaboration...[/cyan]\n\n"
            "[dim]Feel free to use AI to flesh out your idea first - the more context you provide, the better![/dim]",
            title="[green]💡 Greenfield Tip[/green]",
            border_style="green",
            padding=(1, 2)
        )
        console.print(greenfield_tip)

@app.command()
def check():
    """Check that all required tools are installed."""
    show_banner()
    console.print("[bold]Checking for installed tools...[/bold]\n")

    tracker = StepTracker("Check Available Tools")

    tracker.add("git", "Git version control")
    git_ok = check_tool("git", tracker=tracker)

    agent_results = {}
    for agent_key, agent_config in AGENT_CONFIG.items():
        agent_name = agent_config["name"]
        requires_cli = agent_config["requires_cli"]

        tracker.add(agent_key, agent_name)

        if requires_cli:
            agent_results[agent_key] = check_tool(agent_key, tracker=tracker)
        else:
            # IDE-based agent - skip CLI check and mark as optional
            tracker.skip(agent_key, "IDE-based, no CLI check")
            agent_results[agent_key] = False  # Don't count IDE agents as "found"

    # Check VS Code variants (not in agent config)
    tracker.add("code", "Visual Studio Code")
    code_ok = check_tool("code", tracker=tracker)

    tracker.add("code-insiders", "Visual Studio Code Insiders")
    code_insiders_ok = check_tool("code-insiders", tracker=tracker)

    console.print(tracker.render())

    console.print("\n[bold green]Specify CLI is ready to use![/bold green]")

    if not git_ok:
        console.print("[dim]Tip: Install git for repository management[/dim]")

    if not any(agent_results.values()):
        console.print("[dim]Tip: Install an AI assistant for the best experience[/dim]")

@app.command()
def version():
    """Display version and system information."""
    import platform
    import importlib.metadata
    
    show_banner()
    
    # Get CLI version from package metadata
    cli_version = "unknown"
    try:
        cli_version = importlib.metadata.version("specify-cli")
    except Exception:
        # Fallback: try reading from pyproject.toml if running from source
        try:
            import tomllib
            pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                    cli_version = data.get("project", {}).get("version", "unknown")
        except Exception:
            pass
    
    # Fetch latest template release version
    repo_owner = "mb-etc"
    repo_name = "spec-kit-etc"
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
    
    template_version = "unknown"
    release_date = "unknown"
    
    try:
        response = client.get(
            api_url,
            timeout=10,
            follow_redirects=True,
            headers=_github_auth_headers(),
        )
        if response.status_code == 200:
            release_data = response.json()
            template_version = release_data.get("tag_name", "unknown")
            # Remove 'v' prefix if present
            if template_version.startswith("v"):
                template_version = template_version[1:]
            release_date = release_data.get("published_at", "unknown")
            if release_date != "unknown":
                # Format the date nicely
                try:
                    dt = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                    release_date = dt.strftime("%Y-%m-%d")
                except Exception:
                    pass
    except Exception:
        pass

    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Key", style="cyan", justify="right")
    info_table.add_column("Value", style="white")

    info_table.add_row("CLI Version", cli_version)
    info_table.add_row("Template Version", template_version)
    info_table.add_row("Released", release_date)
    info_table.add_row("", "")
    info_table.add_row("Python", platform.python_version())
    info_table.add_row("Platform", platform.system())
    info_table.add_row("Architecture", platform.machine())
    info_table.add_row("OS Version", platform.version())

    panel = Panel(
        info_table,
        title="[bold cyan]Specify CLI Information[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    )

    console.print(panel)
    console.print()


@app.command()
def context(
    show: bool = typer.Option(False, "--show", help="Display current project context"),
    set_type: str = typer.Option(None, "--set-type", help="Update project type (greenfield, brownfield, bluefield)"),
    set_description: str = typer.Option(None, "--set-description", help="Update project description"),
    add_constraint: str = typer.Option(None, "--add-constraint", help="Add a constraint to the project"),
    remove_constraint: int = typer.Option(None, "--remove-constraint", help="Remove constraint by index (1-based)"),
):
    """
    View or update project context settings.
    
    Project context helps AI assistants understand your project type and provide
    more accurate, realistic specifications and implementations.
    
    Examples:
        specify context --show                                    # View current context
        specify context --set-type brownfield                     # Change to brownfield project
        specify context --set-description "API service"           # Update description
        specify context --add-constraint "Must not change API"    # Add a constraint
        specify context --remove-constraint 1                     # Remove first constraint
    """
    context_file = Path.cwd() / ".specify" / "context.yaml"
    
    if not context_file.exists():
        console.print("[red]Error:[/red] No context.yaml found in current directory")
        console.print("[dim]Run 'specify init .' in a Spec Kit project, or create .specify/context.yaml manually[/dim]")
        raise typer.Exit(1)
    
    # Read current context
    content = context_file.read_text()
    
    # Simple YAML parsing for our known structure
    def get_yaml_value(text: str, key: str) -> str:
        for line in text.split("\n"):
            if line.startswith(f"{key}:"):
                value = line.split(":", 1)[1].strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                return value
        return ""
    
    def set_yaml_value(text: str, key: str, new_value: str) -> str:
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line.startswith(f"{key}:"):
                # Preserve indentation and handle special characters
                if any(c in new_value for c in ":#{}[]&*!|>'\"%@`"):
                    lines[i] = f'{key}: "{new_value}"'
                else:
                    lines[i] = f"{key}: {new_value}"
                break
        return "\n".join(lines)
    
    def get_yaml_list(text: str, key: str) -> list:
        """Extract a YAML list from the text."""
        lines = text.split("\n")
        result = []
        in_list = False
        for line in lines:
            if line.startswith(f"{key}:"):
                in_list = True
                continue
            if in_list:
                if line.strip().startswith("- "):
                    item = line.strip()[2:].strip()
                    # Remove quotes if present
                    if item.startswith('"') and item.endswith('"'):
                        item = item[1:-1]
                    elif item.startswith("'") and item.endswith("'"):
                        item = item[1:-1]
                    result.append(item)
                elif line.strip() and not line.strip().startswith("#") and not line.strip().startswith("-"):
                    break  # End of list
        return result
    
    def set_yaml_list(text: str, key: str, items: list) -> str:
        """Set a YAML list in the text."""
        lines = text.split("\n")
        new_lines = []
        in_list = False
        list_done = False
        
        for line in lines:
            if line.startswith(f"{key}:"):
                new_lines.append(f"{key}:")
                for item in items:
                    # Handle special characters in list items
                    if any(c in item for c in ":#{}[]&*!|>'\"%@`"):
                        new_lines.append(f'  - "{item}"')
                    else:
                        new_lines.append(f"  - {item}")
                if not items:
                    new_lines.append("  # (none)")
                in_list = True
                list_done = True
                continue
            
            if in_list:
                if line.strip().startswith("- ") or (line.strip().startswith("#") and list_done):
                    continue  # Skip old list items and inline comments
                elif line.strip() and not line.strip().startswith("#"):
                    in_list = False
                    new_lines.append(line)
                continue
            
            new_lines.append(line)
        
        return "\n".join(new_lines)
    
    def get_yaml_dict(text: str, key: str) -> dict:
        """Extract a YAML nested dict from the text (for linked_artifacts)."""
        lines = text.split("\n")
        result = {}
        in_dict = False
        current_key = None
        
        for line in lines:
            if line.startswith(f"{key}:"):
                in_dict = True
                continue
            if in_dict:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    continue
                # Check for sub-key (e.g., "jira:" or "docs:")
                if ":" in stripped and not stripped.startswith("-"):
                    sub_key = stripped.split(":")[0].strip()
                    if not sub_key.startswith("#"):
                        current_key = sub_key
                        result[current_key] = []
                elif stripped.startswith("- ") and current_key:
                    item = stripped[2:].strip()
                    if item.startswith('"') and item.endswith('"'):
                        item = item[1:-1]
                    result[current_key].append(item)
                elif not stripped.startswith("-") and not stripped.startswith("#") and line[0] not in " \t":
                    break  # End of dict section
        return result
    
    current_type = get_yaml_value(content, "project_type")
    current_description = get_yaml_value(content, "description")
    current_constraints = get_yaml_list(content, "constraints")
    current_artifacts = get_yaml_dict(content, "linked_artifacts")
    current_version = int(get_yaml_value(content, "version") or "1")
    
    if show or (not set_type and not set_description and not add_constraint and remove_constraint is None):
        # Display current context
        console.print()
        context_table = Table(show_header=False, box=None, padding=(0, 2))
        context_table.add_column("Key", style="cyan", justify="right")
        context_table.add_column("Value", style="white")
        
        type_display = current_type
        if current_type in PROJECT_TYPE_CHOICES:
            type_display = f"{current_type} - {PROJECT_TYPE_CHOICES[current_type]}"
        
        context_table.add_row("Project Type", type_display)
        context_table.add_row("Description", current_description or "[dim](not set)[/dim]")
        
        # Display constraints
        if current_constraints:
            for i, constraint in enumerate(current_constraints, 1):
                label = "Constraints" if i == 1 else ""
                context_table.add_row(label, f"[yellow]{i}.[/yellow] {constraint}")
        else:
            context_table.add_row("Constraints", "[dim](none)[/dim]")
        
        context_table.add_row("Context File", str(context_file))
        
        panel = Panel(
            context_table,
            title="[bold cyan]Project Context[/bold cyan]",
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(panel)
        
        # Show available types
        console.print()
        console.print("[dim]Available project types:[/dim]")
        for key, desc in PROJECT_TYPE_CHOICES.items():
            marker = "●" if key == current_type else "○"
            console.print(f"  {marker} [cyan]{key}[/cyan] - {desc}")
        console.print()
        return
    
    # Update context
    modified = False
    new_type = current_type
    new_description = current_description
    new_constraints = current_constraints.copy()
    
    if set_type:
        if set_type not in PROJECT_TYPE_CHOICES:
            console.print(f"[red]Error:[/red] Invalid project type '{set_type}'")
            console.print(f"[dim]Choose from: {', '.join(PROJECT_TYPE_CHOICES.keys())}[/dim]")
            raise typer.Exit(1)
        
        content = set_yaml_value(content, "project_type", set_type)
        new_type = set_type
        modified = True
        console.print(f"[green]✓[/green] Project type updated to: [cyan]{set_type}[/cyan]")
    
    if set_description:
        content = set_yaml_value(content, "description", set_description)
        new_description = set_description
        modified = True
        console.print(f"[green]✓[/green] Description updated")
    
    if add_constraint:
        new_constraints.append(add_constraint)
        content = set_yaml_list(content, "constraints", new_constraints)
        modified = True
        console.print(f"[green]✓[/green] Constraint added: [yellow]{add_constraint}[/yellow]")
    
    if remove_constraint is not None:
        if remove_constraint < 1 or remove_constraint > len(new_constraints):
            console.print(f"[red]Error:[/red] Invalid constraint index {remove_constraint}")
            console.print(f"[dim]Valid range: 1-{len(new_constraints)}[/dim]")
            raise typer.Exit(1)
        removed = new_constraints.pop(remove_constraint - 1)
        content = set_yaml_list(content, "constraints", new_constraints)
        modified = True
        console.print(f"[green]✓[/green] Constraint removed: [yellow]{removed}[/yellow]")
    
    if modified:
        # Update the updated timestamp and version
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        new_version = current_version + 1
        content = set_yaml_value(content, "updated", now)
        content = set_yaml_value(content, "version", str(new_version))
        context_file.write_text(content)
        console.print(f"[dim]Context saved to {context_file}[/dim]")
        
        # Regenerate the AI reference file
        generate_context_reference(
            project_path=Path.cwd(),
            project_type=new_type,
            description=new_description,
            constraints=new_constraints,
            linked_artifacts=current_artifacts,
            timestamp=now,
            version=new_version
        )
        console.print(f"[dim]AI reference updated at memory/context.md[/dim]")


def main():
    app()

if __name__ == "__main__":
    main()

