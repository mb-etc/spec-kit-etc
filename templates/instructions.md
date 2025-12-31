# Getting Started with Spec Kit

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

Start by running the `/speckit.constitution` command (or `specify constitution` in your agent). This creates your project's guiding principles in `memory/constitution.md`.

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

This creates a detailed specification in `specs/features/` that captures:
- User stories and acceptance criteria
- Technical requirements
- Edge cases and error handling
- Dependencies and constraints

### Step 3: Plan Implementation

Once a spec is approved, run `/speckit.plan` to create an implementation plan:

```
/speckit.plan specs/features/SPEC-001-user-authentication.md
```

This breaks down the spec into actionable steps with clear guidance.

### Step 4: Generate Tasks

Use `/speckit.tasks` to break the plan into discrete, implementable tasks:

```
/speckit.tasks specs/plans/PLAN-001-user-authentication.md
```

### Step 5: Implement

Run `/speckit.implement` on individual tasks to get implementation guidance:

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

- Check the [Spec Kit documentation](https://github.com/github/spec-kit)
- Review example specs in the `specs/` folder
- Ask your AI assistant to explain any command
