---
description: Bootstrap a greenfield project by exploring your vision and populating architecture, roadmap, and ideas documents.
handoffs:
  - label: Establish Constitution
    agent: speckit.constitution
    prompt: Create the project constitution based on our architectural decisions
    send: true
  - label: Start First Feature
    agent: speckit.specify
    prompt: Let's specify our first feature
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Purpose

This command helps you bootstrap a greenfield project by having a structured conversation about what you're building. The goal is to **capture decisions in documentation** - not to create any files or code yet.

By the end of this conversation, you'll have populated three key documents:

1. **docs/architecture.md** - Technical decisions, system design, technology stack, and **project structure**
2. **docs/roadmap.md** - Vision, milestones, and feature priorities  
3. **docs/ideas.md** - Explorations, possibilities, and future considerations

After this conversation, you'll have a solid foundation to establish your project constitution and begin specifying features - including the scaffolding itself.

## Conversation Flow

### Phase 1: Understanding the Vision

Start by understanding what the user wants to build. Ask open-ended questions:

**Initial Questions:**
- "What are you building? Describe your project in a few sentences."
- "Who is this for? Who are your target users?"
- "What problem does this solve for them?"
- "What does success look like for this project?"

Listen actively and ask clarifying follow-ups. Don't rush to solutions.

### Phase 2: Exploring the Scope

Once you understand the vision, explore the scope:

**Scope Questions:**
- "What are the 2-3 core features that make this valuable?"
- "What's the simplest version that would be useful (MVP)?"
- "What features are you explicitly NOT building (at least initially)?"
- "Are there any hard constraints? (timeline, budget, team size, existing systems)"

### Phase 3: Technical Direction

Explore technical preferences and constraints:

**Technical Questions:**
- "Do you have preferences for programming languages or frameworks?"
- "Any existing systems this needs to integrate with?"
- "What are your deployment preferences? (cloud provider, self-hosted, etc.)"
- "Any specific requirements around data, security, or compliance?"
- "What's your experience level with different technologies?"

Be collaborative here - offer suggestions based on the project needs, but respect stated preferences.

### Phase 4: Project Structure

Explore what the project structure should look like:

**Structure Questions:**
- "Is this a monorepo or single project?"
- "What are the main components or packages?"
- "Any specific folder conventions you prefer?"
- "Will you use a generator (create-next-app, vite, etc.) or build from scratch?"

Capture the intended structure in architecture.md - don't create files yet.

### Phase 5: Prioritization

Help prioritize the work:

**Priority Questions:**
- "If you could only ship ONE thing, what would it be?"
- "What would make users come back after their first use?"
- "Are there any external deadlines or dependencies?"
- "What's your appetite for experimentation vs. proven solutions?"

## Document Updates

Based on the conversation, update the three documents. **Do not create any project files** - only update the documentation.

### Update: docs/architecture.md

Populate:
- **Overview**: High-level system description based on the vision
- **System Diagram**: Sketch out major components and their relationships
- **Key Architectural Decisions**: Fill in actual decisions discussed (database, API style, hosting, etc.)
- **Technology Stack**: Languages, frameworks, and infrastructure choices
- **Project Structure**: Document the intended folder structure, package organization, and file conventions
- **Design Principles**: Extract guiding principles from the conversation

Leave sections as TBD if not yet decided, but add notes about what needs to be resolved.

**Example Project Structure Section:**
```markdown
## Project Structure

### Intended Layout
\`\`\`
├── apps/
│   ├── web/          # Next.js frontend
│   └── api/          # Express API server
├── packages/
│   └── shared/       # Shared types and utilities
├── docs/             # Project documentation (Spec Kit)
├── specs/            # Feature specifications (Spec Kit)
└── scripts/          # Build and utility scripts
\`\`\`

### Package Manager
pnpm with workspaces

### Scaffolding Approach
- Use `create-next-app` for web app
- Manual setup for API with Express + TypeScript
- Turborepo for monorepo orchestration
```

### Update: docs/roadmap.md

Populate:
- **Vision**: Capture the project vision and success criteria
- **Target Users**: Document user types and their needs
- **Milestones**: Structure discussed features into milestones:
  - **M0 (Foundation)**: Project scaffolding, CI/CD, dev environment, initial architecture
  - **M1 (MVP)**: Core user-facing features
  - **M2 (Beta)**: Additional features, polish
  - **M3 (Launch)**: Production readiness
- **Feature Backlog**: List features discussed, organized by priority

**Important**: M0 should include the scaffolding work as explicit tasks:
- [ ] Create project structure per architecture.md
- [ ] Set up package.json / pyproject.toml / etc.
- [ ] Configure TypeScript / linting / formatting
- [ ] Set up CI/CD pipeline
- [ ] Configure development environment

### Update: docs/ideas.md

Populate:
- **Active Explorations**: Ideas that need more research before becoming specs
- **Idea Backlog**: Interesting possibilities mentioned but not prioritized
- **Parked Ideas**: Things explicitly deferred ("not now, but maybe later")
- **Inspiration & References**: Any examples, competitors, or references mentioned

This is the "parking lot" for ideas that surfaced during the conversation but aren't immediate priorities.

## Completing the Session

After updating the documents, summarize what was captured:

```
## Project Bootstrap Complete! 🚀

I've documented your project vision and decisions:

### docs/architecture.md
- [Summary of technical decisions]
- [Project structure defined]
- [Areas still needing decisions]

### docs/roadmap.md  
- [Vision statement captured]
- [M0 scaffolding tasks listed]
- [M1+ features organized]

### docs/ideas.md
- [Ideas captured for future exploration]

## What We Documented (Not Created Yet)

Everything is captured in documentation. No project files have been created.
The actual scaffolding will happen when you specify and implement M0 tasks.

## Recommended Next Steps

1. **Review the documents** - Make sure I captured your intent accurately
2. **Run `/speckit.constitution`** - Establish the guiding principles for AI collaboration
3. **Start M0** - Run `/speckit.specify` to create the project scaffolding:
   
   \`\`\`
   /speckit.specify Create the initial project structure based on docs/architecture.md
   \`\`\`

4. **Continue with M1** - Once scaffolding is complete, pick your first user-facing feature

Your M0 priority: [Suggest scaffolding as first task]
Your first M1 feature: [Suggest the highest-priority user-facing feature]
```

## Important Guidelines

- **Document, don't create** - This command captures decisions in docs. File creation happens via `/speckit.specify` → `/speckit.implement`
- **Be conversational, not interrogative** - This should feel like brainstorming with a colleague, not filling out a form
- **Offer suggestions but don't dictate** - Provide options and recommendations, but the user makes decisions
- **Capture uncertainty** - It's fine to mark things as TBD or add questions to explore later
- **Keep momentum** - Don't get stuck on any one decision. Capture what's known, note what needs research
- **Stay high-level** - This isn't the time for implementation details. Focus on direction and priorities
- **Respect existing content** - If documents already have content, build on it rather than replacing it
- **Structure informs scaffolding** - The project structure in architecture.md becomes the spec for M0 scaffolding work
