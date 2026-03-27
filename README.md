# Codex Control Agent

This repository is a learning-first, bare-bones Python project for controlling a local `codex` CLI workflow.

The long-term goal is simple:

1. Point the controller at a local software repository.
2. Feed the controller prompt files.
3. Let it run `codex`, observe output/activity, and continue until told to stop or until a blocker appears.

Step 5 now separates the controller root from the Codex working tree: prompts, logs, and state stay under `--root`, while `--target-repo` tells `codex` which repository to operate on.

## Current Scope

What exists now:

- A standard-library-only Python package scaffold.
- A minimal CLI with `status`, `run-once`, and a cycling `run-loop`.
- A minimal `--target-repo` option for running Codex outside the controller root.
- Prompt, log, and state folders with a sample prompt file.
- Timestamped transcript logging under `logs/` for every Codex run.
- A simple user stop signal via `state/STOP`.
- An optional `--interval MINUTES` flag on `run-loop` to pause between cycles (stop signal is still checked every second during the wait).
- Minimal loop state files under `state/STATUS`, `state/CURRENT_PROMPT`, `state/LAST_PROMPT`, and `state/LAST_EXIT_CODE`.
- Step-by-step documentation through step 5 and the exact next prompt for step 6.

What does not exist yet:

- No richer blocker classification beyond a simple `blocked` status.
- No resume or skip behavior inside the loop.
- No status view that summarizes the persisted loop state.
- No controller decision-making between prompts.

## Project Layout

```text
.
├── README.md
├── docs
│   ├── NEXT_STEP.md
│   ├── STEP_01.md
│   ├── STEP_02.md
│   ├── STEP_03.md
│   ├── STEP_04.md
│   └── STEP_05.md
├── logs
│   └── .gitkeep
├── prompts
│   ├── README.md
│   └── example_prompt.txt
├── pyproject.toml
├── src
│   └── codex_control_agent
│       ├── __init__.py
│       ├── __main__.py
│       └── cli.py
└── state
    └── .gitkeep
```

## Quick Start

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
codex-control-agent status
codex-control-agent run-once prompts/example_prompt.txt --sandbox read-only
codex-control-agent run-loop prompts --sandbox read-only
codex-control-agent run-loop prompts --sandbox read-only --interval 5
codex-control-agent --target-repo ../other-repo run-loop prompts --sandbox workspace-write
touch state/STOP
cat state/STATUS state/CURRENT_PROMPT state/LAST_PROMPT state/LAST_EXIT_CODE
```

You can also run the package without installing it:

```bash
PYTHONPATH=src python3 -m codex_control_agent status
PYTHONPATH=src python3 -m codex_control_agent run-once prompts/example_prompt.txt --sandbox read-only
PYTHONPATH=src python3 -m codex_control_agent run-loop prompts --sandbox read-only
PYTHONPATH=src python3 -m codex_control_agent run-loop prompts --sandbox read-only --interval 5
PYTHONPATH=src python3 -m codex_control_agent --target-repo ../other-repo run-loop prompts --sandbox workspace-write
```

If `--target-repo` is omitted, Codex still runs in `--root`. If it is provided, prompts, logs, and state remain under the controller root while the Codex subprocess runs in the target repo. `run-loop` accepts either an ordered list of prompt files or one or more directories, expands directory inputs to top-level `.txt` files in sorted order, and keeps cycling through that resolved prompt list until `state/STOP` is present before the next prompt or a prompt exits non-zero. Pass `--interval MINUTES` (floats accepted, e.g. `--interval 0.5`) to pause between cycles; the stop signal is still checked every second during the wait.

## Learning Path

The recommended order is:

1. Finish repo setup and understand the scaffold.
2. Use `run-once` to verify one prompt file can drive one Codex run.
3. Use `run-loop` to verify multiple prompt files keep cycling in order until `state/STOP` or a blocker.
4. Inspect the loop state files to see what ran last and why the loop stopped.
5. Point the controller at an external target repo while keeping prompts, logs, and state local.
6. Surface loop state and blocker details more clearly in `status`.

## Step Documents

- `docs/STEP_01.md`: what this first milestone does and why it stays small.
- `docs/STEP_02.md`: how the one-shot Codex execution works.
- `docs/STEP_03.md`: how the minimal multi-prompt loop works.
- `docs/STEP_04.md`: how loop state tracking works.
- `docs/STEP_05.md`: how controller-root and target-repo separation works.
- `docs/NEXT_STEP.md`: the step 6 milestone, acceptance criteria, and a ready-to-paste prompt for your next session.
