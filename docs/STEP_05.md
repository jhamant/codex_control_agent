# Step 5: Separate Controller Root From Target Repository

## Purpose

This step lets the controller keep its own files in one place while pointing Codex at a different repository.

The goal stays narrow:

- keep prompt resolution under the controller root,
- keep logs and state under the controller root,
- run `codex` in a separate target repository when asked,
- preserve the existing execution path and cycling loop behavior.

## What Was Added

- A minimal global `--target-repo` CLI option.
- Target-repo reporting in `status`.
- Shared prompt execution that now runs `codex` in the target repo.
- Log metadata that records both the controller root and the target repo.

## Command Shape

If no target repo is provided, the controller behaves as before:

```bash
codex-control-agent run-loop prompts --sandbox read-only
```

To point Codex somewhere else:

```bash
codex-control-agent --root /path/to/controller run-loop prompts --target-repo /path/to/project --sandbox workspace-write
```

Relative `--target-repo` values are resolved from `--root`.

## What Stays Under The Controller Root

These still live under `--root`:

- prompt file resolution,
- `logs/`,
- `state/`,
- the `state/STOP` signal.

Only the Codex subprocess working directory changes.

## Logging Behavior

Per-run logs still use the existing format and file naming, but now include:

- `controller_root`,
- `target_repo`,
- the exact `codex` command.

That makes it obvious which repository was actually targeted.

## Acceptance Criteria

Step 5 is complete if all of the following are true:

- `run-once` and `run-loop` accept `--target-repo`,
- prompt files still resolve from the controller root,
- logs and state still write under the controller root,
- Codex runs in the target repository,
- `status` prints both locations clearly.

## Explicitly Deferred

These are still not implemented:

- richer blocker reporting in `status`,
- resume or skip behavior,
- persistent target-repo configuration,
- any controller reasoning between prompts.

## Why Step 6 Should Be Next

The controller now records useful state and can point Codex at the right repository, but `status` still mostly shows directory existence.

The next useful milestone is to make `status` summarize the current loop state, last prompt, and last blocker so the controller can explain itself without manual file inspection.
