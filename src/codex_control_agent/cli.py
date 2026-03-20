from __future__ import annotations

import argparse
import os
import selectors
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class AppLayout:
    root: Path
    prompts_dir: Path
    logs_dir: Path
    state_dir: Path

    @classmethod
    def from_root(cls, root: Path) -> "AppLayout":
        resolved_root = root.resolve()
        return cls(
            root=resolved_root,
            prompts_dir=resolved_root / "prompts",
            logs_dir=resolved_root / "logs",
            state_dir=resolved_root / "state",
        )


@dataclass(frozen=True)
class LoopState:
    status: str
    current_prompt: str
    last_prompt: str
    last_exit_code: str


@dataclass(frozen=True)
class LoopStatePaths:
    status_path: Path
    current_prompt_path: Path
    last_prompt_path: Path
    last_exit_code_path: Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bare-bones controller scaffold for Codex CLI workflows."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Controller project root. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--target-repo",
        type=Path,
        default=None,
        help=(
            "Repository where Codex should run. Relative paths are resolved from "
            "--root. Defaults to --root."
        ),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser(
        "status", help="Show the current scaffold status."
    )
    status_parser.set_defaults(handler=handle_status)

    run_once_parser = subparsers.add_parser(
        "run-once",
        help="Read one prompt file, send it to codex once, and save a transcript log.",
    )
    run_once_parser.add_argument(
        "prompt_file",
        type=Path,
        help="Path to a plain-text prompt file. Relative paths are resolved from --root.",
    )
    run_once_parser.add_argument(
        "--sandbox",
        choices=["read-only", "workspace-write", "danger-full-access"],
        default="read-only",
        help="Sandbox mode passed to `codex exec`. Defaults to read-only.",
    )
    run_once_parser.set_defaults(handler=handle_run_once)

    run_loop_parser = subparsers.add_parser(
        "run-loop",
        help="Cycle through prompt files by reusing the run-once execution path.",
    )
    run_loop_parser.add_argument(
        "prompt_paths",
        nargs="+",
        type=Path,
        help=(
            "One prompt directory or an ordered list of prompt files. Relative paths "
            "are resolved from --root. Directory inputs expand to top-level .txt files "
            "in sorted order."
        ),
    )
    run_loop_parser.add_argument(
        "--sandbox",
        choices=["read-only", "workspace-write", "danger-full-access"],
        default="read-only",
        help="Sandbox mode passed to `codex exec`. Defaults to read-only.",
    )
    run_loop_parser.set_defaults(handler=handle_run_loop)

    return parser


def handle_status(args: argparse.Namespace) -> int:
    layout = AppLayout.from_root(args.root)
    codex_path = shutil.which("codex")
    target_repo = resolve_target_repo(layout, args.target_repo)

    lines = [
        "Codex Control Agent",
        f"controller_root: {layout.root}",
        f"target_repo: {target_repo} ({describe_path(target_repo)})",
        f"prompts_dir: {layout.prompts_dir} ({describe_path(layout.prompts_dir)})",
        f"logs_dir: {layout.logs_dir} ({describe_path(layout.logs_dir)})",
        f"state_dir: {layout.state_dir} ({describe_path(layout.state_dir)})",
        f"codex_cli: {codex_path or 'not found on PATH'}",
        (
            "implemented: step 5 scaffold, target-repo routing, "
            "run-loop state tracking, and cycling loop control"
        ),
        "next_step: surface loop state and blocker details more clearly",
    ]

    print("\n".join(lines))
    return 0


def handle_run_once(args: argparse.Namespace) -> int:
    layout = AppLayout.from_root(args.root)
    codex_path = require_codex_path()
    if codex_path is None:
        return 1

    target_repo = resolve_target_repo(layout, args.target_repo)
    if not validate_target_repo(target_repo):
        return 1

    prompt_path = resolve_prompt_path(layout, args.prompt_file)
    return run_prompt_file(
        layout=layout,
        codex_path=codex_path,
        target_repo=target_repo,
        prompt_path=prompt_path,
        sandbox=args.sandbox,
    ).exit_code


def handle_run_loop(args: argparse.Namespace) -> int:
    layout = AppLayout.from_root(args.root)
    state = LoopState(
        status="running",
        current_prompt="",
        last_prompt="",
        last_exit_code="",
    )
    if not persist_loop_state(layout, state):
        return 1

    codex_path = require_codex_path()
    if codex_path is None:
        if not persist_loop_state(
            layout,
            replace(state, status="blocked", last_exit_code="1"),
        ):
            return 1
        return 1

    target_repo = resolve_target_repo(layout, args.target_repo)
    if not validate_target_repo(target_repo):
        if not persist_loop_state(
            layout,
            replace(state, status="blocked", last_exit_code="1"),
        ):
            return 1
        return 1

    prompt_paths = collect_prompt_paths(layout, args.prompt_paths)
    if prompt_paths is None:
        if not persist_loop_state(
            layout,
            replace(state, status="blocked", last_exit_code="1"),
        ):
            return 1
        return 1

    stop_path = build_stop_signal_path(layout)
    completed_runs = 0
    completed_cycles = 0
    total_runs = len(prompt_paths)

    while True:
        cycle_number = completed_cycles + 1

        for index, prompt_path in enumerate(prompt_paths, start=1):
            state = replace(
                state,
                status="running",
                current_prompt=str(prompt_path),
            )
            if not persist_loop_state(layout, state):
                return 1

            if stop_path.exists():
                state = replace(state, status="stopped")
                if not persist_loop_state(layout, state):
                    return 1
                print(
                    (
                        "run-loop stopped: stop signal detected at "
                        f"{stop_path} before cycle {cycle_number} prompt {index} "
                        f"of {total_runs}; completed {completed_runs} prompt(s) "
                        f"across {completed_cycles} full cycle(s)"
                    ),
                    file=sys.stderr,
                )
                return 0

            print(
                (
                    f"run-loop: cycle {cycle_number} prompt {index} "
                    f"of {total_runs}: {prompt_path}"
                ),
                file=sys.stderr,
            )
            outcome = run_prompt_file(
                layout=layout,
                codex_path=codex_path,
                target_repo=target_repo,
                prompt_path=prompt_path,
                sandbox=args.sandbox,
            )
            state = replace(
                state,
                current_prompt="" if outcome.exit_code == 0 else str(prompt_path),
                last_prompt=(
                    str(prompt_path) if outcome.started_prompt else state.last_prompt
                ),
                last_exit_code=str(outcome.exit_code),
                status="running" if outcome.exit_code == 0 else "blocked",
            )
            if not persist_loop_state(layout, state):
                return 1

            if outcome.exit_code != 0:
                print(
                    (
                        "run-loop stopped: prompt failed with exit code "
                        f"{outcome.exit_code} at cycle {cycle_number} prompt "
                        f"{index} of {total_runs}: {prompt_path}; "
                        f"completed {completed_runs} prompt(s) across "
                        f"{completed_cycles} full cycle(s)"
                    ),
                    file=sys.stderr,
                )
                return outcome.exit_code

            completed_runs += 1

        completed_cycles += 1
        print(
            f"run-loop: completed cycle {completed_cycles}; continuing",
            file=sys.stderr,
        )


def require_codex_path() -> str | None:
    codex_path = shutil.which("codex")
    if codex_path is not None:
        return codex_path

    print(
        "error: `codex` was not found on PATH. Install or expose the Codex CLI first.",
        file=sys.stderr,
    )
    return None


def run_prompt_file(
    layout: AppLayout,
    codex_path: str,
    target_repo: Path,
    prompt_path: Path,
    sandbox: str,
) -> PromptRunOutcome:
    if not prompt_path.exists():
        print(f"error: prompt file does not exist: {prompt_path}", file=sys.stderr)
        return PromptRunOutcome(exit_code=1, started_prompt=False)
    if not prompt_path.is_file():
        print(f"error: prompt path is not a file: {prompt_path}", file=sys.stderr)
        return PromptRunOutcome(exit_code=1, started_prompt=False)

    try:
        ensure_directory(layout.logs_dir, "logs")
        prompt_text = prompt_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: unable to prepare run inputs: {exc}", file=sys.stderr)
        return PromptRunOutcome(exit_code=1, started_prompt=False)

    log_path = build_log_path(layout.logs_dir)
    command = build_codex_command(codex_path, target_repo, sandbox)

    print(f"log_file: {log_path}", file=sys.stderr)
    print(f"prompt_file: {prompt_path}", file=sys.stderr)
    print(f"target_repo: {target_repo}", file=sys.stderr)

    try:
        result = run_command_with_streaming(
            command=command,
            prompt_text=prompt_text,
            cwd=target_repo,
        )
    except OSError as exc:
        print(f"error: failed to start codex: {exc}", file=sys.stderr)
        return PromptRunOutcome(exit_code=1, started_prompt=False)

    try:
        write_run_log(
            log_path=log_path,
            prompt_path=prompt_path,
            prompt_text=prompt_text,
            command=command,
            sandbox=sandbox,
            result=result,
            controller_root=layout.root,
            target_repo=target_repo,
        )
    except OSError as exc:
        print(f"error: failed to write log file: {exc}", file=sys.stderr)
        return PromptRunOutcome(exit_code=1, started_prompt=True)

    if result.returncode != 0:
        print(
            f"error: codex exited with status {result.returncode}. See log: {log_path}",
            file=sys.stderr,
        )
    else:
        print(f"log_saved: {log_path}", file=sys.stderr)

    return PromptRunOutcome(exit_code=result.returncode, started_prompt=True)


def describe_path(path: Path) -> str:
    if path.exists() and path.is_dir():
        return "exists"
    if path.exists():
        return "exists but is not a directory"
    return "missing"


def resolve_prompt_path(layout: AppLayout, prompt_file: Path) -> Path:
    if prompt_file.is_absolute():
        return prompt_file.resolve()
    return (layout.root / prompt_file).resolve()


def resolve_target_repo(layout: AppLayout, target_repo: Path | None) -> Path:
    if target_repo is None:
        return layout.root
    if target_repo.is_absolute():
        return target_repo.resolve()
    return (layout.root / target_repo).resolve()


def validate_target_repo(target_repo: Path) -> bool:
    if not target_repo.exists():
        print(f"error: target repo does not exist: {target_repo}", file=sys.stderr)
        return False
    if not target_repo.is_dir():
        print(f"error: target repo is not a directory: {target_repo}", file=sys.stderr)
        return False
    return True


def collect_prompt_paths(layout: AppLayout, prompt_sources: list[Path]) -> list[Path] | None:
    prompt_paths: list[Path] = []

    for prompt_source in prompt_sources:
        resolved_source = resolve_prompt_path(layout, prompt_source)
        if not resolved_source.exists():
            print(
                f"error: prompt path does not exist: {resolved_source}",
                file=sys.stderr,
            )
            return None

        if resolved_source.is_dir():
            directory_prompt_paths = collect_directory_prompt_paths(resolved_source)
            if not directory_prompt_paths:
                print(
                    (
                        "error: prompt directory does not contain any top-level .txt "
                        f"files: {resolved_source}"
                    ),
                    file=sys.stderr,
                )
                return None
            prompt_paths.extend(directory_prompt_paths)
            continue

        if resolved_source.is_file():
            prompt_paths.append(resolved_source)
            continue

        print(
            f"error: prompt path is neither a file nor a directory: {resolved_source}",
            file=sys.stderr,
        )
        return None

    return prompt_paths


def collect_directory_prompt_paths(prompt_dir: Path) -> list[Path]:
    return sorted(
        (
            child.resolve()
            for child in prompt_dir.iterdir()
            if child.is_file() and child.suffix.lower() == ".txt"
        ),
        key=lambda child: child.name.casefold(),
    )


def build_stop_signal_path(layout: AppLayout) -> Path:
    return layout.state_dir / "STOP"


def build_loop_state_paths(layout: AppLayout) -> LoopStatePaths:
    return LoopStatePaths(
        status_path=layout.state_dir / "STATUS",
        current_prompt_path=layout.state_dir / "CURRENT_PROMPT",
        last_prompt_path=layout.state_dir / "LAST_PROMPT",
        last_exit_code_path=layout.state_dir / "LAST_EXIT_CODE",
    )


def persist_loop_state(layout: AppLayout, state: LoopState) -> bool:
    try:
        write_loop_state(layout, state)
    except OSError as exc:
        print(f"error: failed to update state files: {exc}", file=sys.stderr)
        return False
    return True


def write_loop_state(layout: AppLayout, state: LoopState) -> None:
    ensure_directory(layout.state_dir, "state")
    state_paths = build_loop_state_paths(layout)
    write_state_value(state_paths.status_path, state.status)
    write_state_value(state_paths.current_prompt_path, state.current_prompt)
    write_state_value(state_paths.last_prompt_path, state.last_prompt)
    write_state_value(state_paths.last_exit_code_path, state.last_exit_code)


def write_state_value(path: Path, value: str) -> None:
    text = f"{value}\n" if value else ""
    path.write_text(text, encoding="utf-8")


def ensure_directory(path: Path, label: str) -> None:
    if path.exists() and not path.is_dir():
        raise NotADirectoryError(f"{label} path is not a directory: {path}")
    path.mkdir(parents=True, exist_ok=True)


def build_log_path(logs_dir: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return logs_dir / f"run-once-{timestamp}.log"


def build_codex_command(codex_path: str, target_repo: Path, sandbox: str) -> list[str]:
    return [
        codex_path,
        "exec",
        "-",
        "--color",
        "never",
        "--sandbox",
        sandbox,
        "-C",
        str(target_repo),
    ]


@dataclass(frozen=True)
class RunResult:
    command: list[str]
    returncode: int
    stdout_text: str
    stderr_text: str
    started_at_utc: str
    finished_at_utc: str


@dataclass(frozen=True)
class PromptRunOutcome:
    exit_code: int
    started_prompt: bool


def run_command_with_streaming(
    command: list[str], prompt_text: str, cwd: Path
) -> RunResult:
    started_at_utc = iso_timestamp()
    process = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
    )

    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None

    process.stdin.write(prompt_text.encode("utf-8"))
    process.stdin.close()

    stdout_chunks, stderr_chunks = stream_process_output(process)
    returncode = process.wait()

    return RunResult(
        command=command,
        returncode=returncode,
        stdout_text=b"".join(stdout_chunks).decode("utf-8", errors="replace"),
        stderr_text=b"".join(stderr_chunks).decode("utf-8", errors="replace"),
        started_at_utc=started_at_utc,
        finished_at_utc=iso_timestamp(),
    )


def stream_process_output(
    process: subprocess.Popen[bytes],
) -> tuple[list[bytes], list[bytes]]:
    assert process.stdout is not None
    assert process.stderr is not None

    stdout_chunks: list[bytes] = []
    stderr_chunks: list[bytes] = []
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, ("stdout", stdout_chunks))
    selector.register(process.stderr, selectors.EVENT_READ, ("stderr", stderr_chunks))

    try:
        while selector.get_map():
            for key, _ in selector.select():
                chunk = os.read(key.fileobj.fileno(), 4096)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue

                stream_name, collected_chunks = key.data
                collected_chunks.append(chunk)

                if stream_name == "stdout":
                    write_terminal_bytes(sys.stdout, chunk)
                else:
                    write_terminal_bytes(sys.stderr, chunk)
    finally:
        selector.close()

    return stdout_chunks, stderr_chunks


def write_terminal_bytes(stream: object, chunk: bytes) -> None:
    buffer = getattr(stream, "buffer", None)
    if buffer is not None:
        buffer.write(chunk)
        buffer.flush()
        return

    text = chunk.decode("utf-8", errors="replace")
    stream.write(text)
    stream.flush()


def write_run_log(
    log_path: Path,
    prompt_path: Path,
    prompt_text: str,
    command: list[str],
    sandbox: str,
    result: RunResult,
    controller_root: Path,
    target_repo: Path,
) -> None:
    log_contents = [
        "Codex Control Agent Run Log",
        f"started_at_utc: {result.started_at_utc}",
        f"finished_at_utc: {result.finished_at_utc}",
        f"controller_root: {controller_root}",
        f"target_repo: {target_repo}",
        f"prompt_file: {prompt_path}",
        f"sandbox: {sandbox}",
        f"command: {format_command(command)}",
        f"exit_code: {result.returncode}",
        "",
        "=== prompt ===",
        prompt_text,
        "",
        "=== stdout ===",
        result.stdout_text,
        "",
        "=== stderr ===",
        result.stderr_text,
    ]
    log_path.write_text("\n".join(log_contents), encoding="utf-8")


def format_command(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def iso_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)
