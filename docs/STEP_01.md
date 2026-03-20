# Step 1: Start the Repository

## Purpose

This step creates the smallest useful starting point for the project.

You want to learn the process slowly, so this milestone avoids any hidden automation. The focus is on:

- establishing a clean Python repository,
- naming the core directories you will need later,
- creating one tiny CLI entry point,
- writing down the boundaries of the system before building it.

## What Was Added

- Git repository initialization.
- A Python package scaffold under `src/`.
- A minimal CLI with a `status` command.
- `prompts/`, `logs/`, and `state/` folders.
- A sample prompt file for future testing.
- Step-tracking documentation.

## Why This Is the Right First Step

The future agent will need at least four responsibilities:

1. Read prompt files.
2. Start `codex` in a controlled way.
3. Watch output and decide what to do next.
4. Stop when the user says stop or when a blocker is detected.

If you try to build all four at once, the project becomes harder to reason about. Step 1 keeps the structure visible while keeping the code surface small.

## Current CLI

The current command is:

```bash
codex-control-agent status
```

It reports:

- the controller root directory,
- the prompt/log/state directories,
- whether those directories exist,
- whether `codex` is currently available on your `PATH`.

## Acceptance Criteria for Step 1

Step 1 is complete if all of the following are true:

- the repository has a clean Python package layout,
- the minimal CLI runs successfully,
- the runtime directories exist,
- the next step is clearly documented.

## Explicitly Deferred

These are intentionally not implemented yet:

- prompt execution,
- subprocess management,
- log streaming,
- iterative prompting,
- stop signals,
- blocker detection.

That separation is deliberate. The next milestone should add only one core behavior: run one prompt file once.
