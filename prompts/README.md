# Prompt Files

This directory will hold plain-text prompts that the controller sends to `codex`.

For now, keep prompt files simple:

- one file per prompt,
- plain text,
- small and easy to inspect.

Current example:

```bash
codex-control-agent run-once prompts/example_prompt.txt --sandbox read-only
codex-control-agent run-loop prompts --sandbox read-only
codex-control-agent --target-repo ../other-repo run-loop prompts --sandbox workspace-write
touch state/STOP
cat state/STATUS state/CURRENT_PROMPT state/LAST_PROMPT state/LAST_EXIT_CODE
```

When `run-loop` is given a directory, it reads the top-level `.txt` files in sorted order and keeps cycling through that ordered list until `state/STOP` is present before the next prompt or a prompt exits non-zero. That keeps `README.md` out of the run while still letting the sample `prompts/` directory work as-is.

Prompt files still live under the controller repo even when `--target-repo` points somewhere else.

After stopping the loop, inspect the state files to see whether it stopped on `state/STOP` or blocked on a failed prompt run.
