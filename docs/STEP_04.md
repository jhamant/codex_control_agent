# Step 4: Track Loop State And Stop Reasons

## Purpose

This step makes `run-loop` easier to inspect after it stops.

The goal stays narrow:

- record what prompt is about to run,
- record what prompt ran last,
- record the latest exit code seen by the loop,
- record whether the loop is running, stopped, or blocked.

## What Was Added

- Four plain-text state files under `state/`.
- Loop-state updates around the existing `run-loop` transitions.
- Preservation of the existing `run-once` execution path for each prompt.
- Simple status values: `running`, `stopped`, and `blocked`.

## State Files

The loop now maintains:

- `state/STATUS`
- `state/CURRENT_PROMPT`
- `state/LAST_PROMPT`
- `state/LAST_EXIT_CODE`

The values are intentionally plain text.

`CURRENT_PROMPT` is blank immediately after a successful prompt finishes. `LAST_PROMPT` and `LAST_EXIT_CODE` stay blank until the loop has something real to record.

## State Transitions

The loop updates state in this order:

1. mark itself as `running`,
2. set `CURRENT_PROMPT` before each prompt begins,
3. update `LAST_PROMPT` and `LAST_EXIT_CODE` after each prompt run,
4. keep cycling until it finishes as `stopped` or `blocked`.

That means:

- a stop signal before the next run leaves `CURRENT_PROMPT` pointing at the prompt that was about to run,
- a failed prompt leaves `STATUS=blocked` and keeps the failed prompt visible in state,
- a successful prompt updates `LAST_PROMPT` and `LAST_EXIT_CODE=0` while the loop continues.

## Command Shape

```bash
codex-control-agent run-loop prompts --sandbox read-only
```

Then inspect the state directly:

```bash
cat state/STATUS state/CURRENT_PROMPT state/LAST_PROMPT state/LAST_EXIT_CODE
```

## Acceptance Criteria

Step 4 is complete if all of the following are true:

- `run-loop` writes the four state files under `state/`,
- the files make it clear what prompt is current or last,
- the loop records `stopped` or `blocked` when it exits,
- a non-zero prompt exit code is written to `LAST_EXIT_CODE`,
- the existing prompt execution path is still reused.

## Explicitly Deferred

These are still not implemented:

- separate controller and target-repository roots,
- resume or skip behavior,
- richer blocker classes than a single `blocked` status,
- any controller reasoning between prompts.

## Why Step 5 Should Be Next

The controller now knows what it did, but it still assumes the controller root is the target repository.

The next useful milestone is to let prompts, logs, and state stay in this repo while Codex operates on a different working tree.
