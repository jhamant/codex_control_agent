# Step 2: Run One Prompt File Through Codex

## Purpose

This step proves the controller can perform one real Codex run end to end.

The goal is intentionally narrow:

- load one prompt file,
- send that prompt to the local `codex` CLI,
- stream output to the terminal while the run is happening,
- save a transcript for later review.

## What Was Added

- A `run-once` CLI command.
- Prompt-file loading relative to the controller root.
- A direct `codex exec -` invocation that sends the prompt through stdin.
- Live streaming of both stdout and stderr.
- A timestamped log file under `logs/`.

## Command Shape

```bash
codex-control-agent run-once prompts/example_prompt.txt --sandbox read-only
```

The command resolves the prompt file from `--root`, runs `codex` once, and returns the same exit code that `codex` returns.

## Logging Behavior

Each run writes a file like:

```text
logs/run-once-20260318T052134784697Z.log
```

The log includes:

- timestamps,
- the root directory,
- the prompt file path,
- the exact `codex` command used,
- the exit code,
- the prompt body,
- captured stdout,
- captured stderr.

That separation matters because the local `codex` CLI may emit warnings or session metadata on stderr even when the run succeeds.

## Acceptance Criteria

Step 2 is complete if all of the following are true:

- one prompt file can be executed with `run-once`,
- terminal output is visible while `codex` is running,
- a transcript log is written under `logs/`,
- the command exits non-zero if `codex` exits non-zero,
- the command prints a clear error if `codex` is unavailable.

## Explicitly Deferred

These are still not implemented:

- a multi-prompt loop,
- a user stop command,
- blocker detection beyond process failure,
- target-repo selection separate from the controller root,
- any controller decision-making between prompts.

## Why Step 3 Should Be Next

Now that single-run execution is stable, the next useful milestone is a tiny loop.

That loop should stay simple: run prompt files in order, stop cleanly when asked, and stop immediately on the first real failure.
