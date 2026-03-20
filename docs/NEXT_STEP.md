# Step 6: Surface Loop State In Status

## Goal

Teach `status` to read the persisted loop state files so the controller can explain what happened without forcing the user to inspect `state/` by hand.

Do not build a dashboard or a background monitor yet. The purpose of step 6 is only to make the existing state easier to read from the CLI.

The controller should be able to:

1. show the current `STATUS`,
2. show the current or last prompt path when available,
3. show the last exit code when available,
4. distinguish a user stop from a blocked run clearly.

## Suggested Command Shape

```bash
codex-control-agent status
```

## Acceptance Criteria

Step 6 should be considered complete when:

- `status` reads the loop state files when they exist,
- `status` prints the saved status, last prompt, and last exit code clearly,
- missing state files are handled cleanly,
- the existing `run-once` and `run-loop` behavior is unchanged.

## Constraints

Keep the same project style:

- standard library only,
- reuse the current `subprocess`-based execution behavior,
- no background worker,
- no async framework,
- no file watcher,
- no extra configuration system unless absolutely necessary.

## Suggested Shape

Keep it bare bones. Reading the existing text files is enough. For example:

- `state/STATUS`
- `state/CURRENT_PROMPT`
- `state/LAST_PROMPT`
- `state/LAST_EXIT_CODE`

You do not need a database or a background service unless you decide it is clearly worth it.

## Ready-to-Paste Prompt For The Next Session

Use this as your next prompt after reviewing step 5:

```text
Implement step 6 for this repo. Update `status` so it reads the persisted loop state files and reports the current status, current or last prompt, and last exit code clearly. Keep it standard-library Python only, reuse the existing state files, update the docs, and verify it against the sample prompt directory.
```

## Notes For Step 7

After `status` surfaces state cleanly, the next milestone should focus on controller ergonomics such as resume behavior or richer blocker reporting.
