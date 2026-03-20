# Step 3: Add A Minimal Controller Loop

## Purpose

This step proves the controller can keep working through more than one prompt file without adding a heavy orchestration layer.

The goal stays narrow:

- expand a prompt directory or accept an ordered prompt list,
- reuse the same one-shot Codex execution path for each prompt,
- keep cycling through the resolved prompt list,
- stop before the next prompt when the user asks it to stop,
- stop immediately on the first failed Codex run.

## What Was Added

- A `run-loop` CLI command.
- Directory expansion for top-level `.txt` prompt files in sorted order.
- Reuse of the existing per-prompt `codex exec -` path and log-writing behavior.
- Repeated cycling through the resolved prompt list until a stop or failure occurs.
- A simple stop signal at `state/STOP`.
- Clear loop summaries for cycle progress, stop, and first-failure cases.

## Command Shapes

Cycle every top-level `.txt` prompt file in `prompts/`:

```bash
codex-control-agent run-loop prompts --sandbox read-only
```

Cycle an explicit ordered list:

```bash
codex-control-agent run-loop prompts/01-plan.txt prompts/02-apply.txt --sandbox read-only
```

The loop preserves the order of explicit file arguments. Directory inputs are expanded in lexicographic filename order. After the last prompt succeeds, the loop starts again from the first prompt.

## Stop And Failure Rules

The loop checks for `state/STOP` before each new prompt begins.

That means:

- if `state/STOP` exists before the first run, nothing starts,
- if `state/STOP` appears during a run, the current run finishes and the next one does not start,
- if every prompt succeeds, the loop keeps cycling back to the start of the prompt list,
- if any Codex run exits non-zero, the loop stops immediately and returns that exit code.

## Logging Behavior

Each prompt run still writes its own timestamped log under `logs/`.

Step 3 does not add a separate loop transcript. It intentionally reuses the existing per-run log format from step 2 even when the loop spans multiple cycles.

## Acceptance Criteria

Step 3 is complete if all of the following are true:

- `run-loop` accepts a prompt directory or an ordered prompt-file list,
- directory inputs expand predictably,
- each prompt run still streams terminal output and writes a transcript log,
- successful prompts cause the loop to keep cycling through the same ordered list,
- `state/STOP` is checked before each new prompt starts,
- the loop stops on the first non-zero Codex exit code,
- the loop prints a clear summary of why it stopped.

## Explicitly Deferred

These are still not implemented:

- a persistent state file that records the last prompt run,
- richer blocker categories beyond the Codex exit code,
- retry, resume, or skip controls,
- target-repo selection separate from the controller root.

## Why Step 4 Should Be Next

Now that the loop exists, the next useful improvement is visibility.

The controller should record what prompt ran last, why the loop stopped, and whether the stop reason came from the user or from Codex failure.
