#!/usr/bin/env python3

# HOW TO RUN
# 1) Install Python dependencies:
#    py -m pip install -r requirements.txt
#
# 2) Install Git and Codex CLI separately.
#
# 2.1) Create minimal Codex config at:
#      $env:USERPROFILE
#      with content:
#      personality = "pragmatic"
#      sandbox_mode = "workspace-write"
#      approval_policy = "never"
#
#      [windows]
#      sandbox = "elevated"
#
#      [projects.'D:\current\coding\MetaPlatform']
#      trust_level = "trusted"
#
#      [notice.model_migrations]
#      "gpt-5.3-codex" = "gpt-5.4"
#
# 3) Create .env from .env.example
#
# 4) Create config.yaml
#
# 5) Create instructions.md with reviewer instructions
#
# 6) Create folders near run.py manually:
#    - ./attachments
#    - ./inbox
#
# 7) Put first-iteration reference files into ./attachments
#
# 8) Codex login
#    $env:OPENAI_API_KEY="YOUR_API_KEY"
#    $env:OPENAI_API_KEY | codex login --with-api-key
#
# 9) Run:
#    py MetaFlow.py -instructions instructions.md -input .\projects\MetaPlatform\reminder.md -config .\projects\MetaPlatform\config.yaml
#
# 10) If reviewer asks a question:
#     - answer in console
#     - optionally put any files into ./inbox
#     - submit an empty line to finish your answer
#
# 11) On iteration 1, run.py will automatically attach everything currently present
#     in ./attachments.
#
# 12) After a question, run.py will automatically attach everything currently present
#     in ./inbox to the NEXT reviewer request.
#
# 13) run.py DOES NOT create ./attachments or ./inbox.
#     User is responsible for creating and maintaining these folders.

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import locale
import re
import shlex
import shutil
import subprocess
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import yaml
from dotenv import load_dotenv


REVIEWER_OUTPUT_SCHEMA: Dict[str, Any] = {
    "name": "reviewer_response",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "status": {
                "type": "string",
                "enum": ["continue", "done", "escalate", "question"],
            },
            "summary": {"type": "string"},
            "codex_task_md": {"type": "string"},
            "should_run_all_tests": {"type": "boolean"},
            "extra_test_commands": {
                "type": "array",
                "items": {"type": "string"},
            },
            "review_notes": {"type": "string"},
            "question_for_user": {"type": "string"},
        },
        "required": [
            "status",
            "summary",
            "codex_task_md",
            "should_run_all_tests",
            "extra_test_commands",
            "review_notes",
            "question_for_user",
        ],
    },
    "strict": True,
}

CODEX_SUMMARY_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "what_changed": {
            "type": "array",
            "items": {"type": "string"},
        },
        "risks": {
            "type": "array",
            "items": {"type": "string"},
        },
        "notes": {
            "type": "array",
            "items": {"type": "string"},
        },
        "high_risk_areas_touched": {"type": "boolean"},
        "high_risk_areas": {
            "type": "array",
            "items": {"type": "string"},
        },
        "verification_notes": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "summary",
        "what_changed",
        "risks",
        "notes",
        "high_risk_areas_touched",
        "high_risk_areas",
        "verification_notes",
    ],
}

RETRIABLE_HTTP_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}
CODEX_NON_REPORT_ITEM_TYPES = {
    "command_execution",
    "reasoning",
    "tool_call",
    "function_call",
    "bash",
    "shell",
}


@dataclass
class RetryPolicy:
    max_retries: Optional[int]
    sleep_sec: int


@dataclass
class IterationArtifacts:
    iteration_dir: Path
    codex_prompt_path: Path
    codex_summary_schema_path: Path
    codex_summary_json_path: Path
    codex_trace_path: Path
    codex_stderr_path: Path
    codex_report_fallback_path: Path
    git_diff_path: Path
    git_diff_stat_path: Path
    changed_files_path: Path
    test_log_path: Path
    tests_summary_path: Path
    reviewer_response_path: Path
    reviewer_request_path: Path
    user_answer_path: Path
    inbox_manifest_path: Path
    inbox_attachments_payload_path: Path
    first_iteration_attachments_manifest_path: Path
    first_iteration_attachments_payload_path: Path


@dataclass
class CodexMonitorState:
    started_at: float
    last_stdout_at: float = field(default_factory=time.time)
    last_stderr_at: float = field(default_factory=time.time)
    saw_turn_completed: bool = False
    saw_agent_message: bool = False
    turn_completed_at: Optional[float] = None
    last_output_at: float = field(default_factory=time.time)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def mark_stdout_line(self, line: str) -> None:
        now = time.time()
        with self.lock:
            self.last_stdout_at = now
            self.last_output_at = now

        stripped = line.strip()
        if not stripped:
            return

        try:
            event = json.loads(stripped)
        except json.JSONDecodeError:
            return

        event_type = str(event.get("type", "")).strip().lower()
        item = event.get("item")
        item_type = item.get("type") if isinstance(item, dict) else None

        with self.lock:
            if event_type == "turn.completed":
                self.saw_turn_completed = True
                if self.turn_completed_at is None:
                    self.turn_completed_at = now

            if item_type == "agent_message":
                self.saw_agent_message = True

    def mark_stderr_line(self) -> None:
        now = time.time()
        with self.lock:
            self.last_stderr_at = now
            self.last_output_at = now

    def snapshot(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "started_at": self.started_at,
                "last_stdout_at": self.last_stdout_at,
                "last_stderr_at": self.last_stderr_at,
                "last_output_at": self.last_output_at,
                "saw_turn_completed": self.saw_turn_completed,
                "saw_agent_message": self.saw_agent_message,
                "turn_completed_at": self.turn_completed_at,
            }


def banner(title: str) -> None:
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)


def info(msg: str) -> None:
    print(f"[INFO] {msg}")


def warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def fail(msg: str, exit_code: int = 1) -> None:
    print(f"[ERROR] {msg}")
    raise SystemExit(exit_code)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(content)


def save_json(path: Path, obj: Any) -> None:
    write_text(path, json.dumps(obj, ensure_ascii=False, indent=2))


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_tool_path(name: str) -> str:
    path = shutil.which(name)
    if not path:
        fail(f"Tool not found in PATH: {name}")
    return path


def normalize_newlines(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def preview_text(text: Optional[str], max_chars: int = 12000) -> str:
    if not text:
        return "[EMPTY]\n"

    normalized = normalize_newlines(text)
    if len(normalized) <= max_chars:
        return normalized + "\n"

    omitted = len(normalized) - max_chars
    head_len = max_chars // 2
    tail_len = max_chars - head_len
    head = normalized[:head_len]
    tail = normalized[-tail_len:]
    return (
        f"{head}\n\n"
        f"[... TRUNCATED, OMITTED {omitted} CHARS ...]\n\n"
        f"{tail}\n"
    )


def print_reviewer_payload_preview(
    iteration: int,
    reviewer_instructions: str,
    primary_input_text: str,
    attachments_text: str,
    technical_channel_text: Optional[str],
    model_channel_text: Optional[str],
    user_answer: Optional[str],
    user_followup_attachments_text: Optional[str],
    reviewer_input: str,
) -> None:
    banner("REVIEWER PAYLOAD PREVIEW")

    print("[INSTRUCTIONS]")
    print(preview_text(reviewer_instructions))

    print("[TASK]")
    print(preview_text(primary_input_text))

    if iteration == 1:
        print("[ATTACHMENTS]")
        print(preview_text(attachments_text))
    else:
        print("[ATTACHMENTS]")
        print("[SKIPPED AFTER ITERATION 1]\n")

    print("[TECHNICAL_CHANNEL]")
    print(preview_text(technical_channel_text, max_chars=16000))

    print("[MODEL_CHANNEL]")
    print(preview_text(model_channel_text, max_chars=12000))

    print("[USER_ANSWER_TO_PREVIOUS_QUESTION]")
    print(preview_text(user_answer))

    print("[USER_FOLLOWUP_ATTACHMENTS_FROM_INBOX]")
    print(preview_text(user_followup_attachments_text))

    print("[FULL_REVIEWER_INPUT]")
    print(preview_text(reviewer_input, max_chars=24000))


def parse_retry_policy(retry_raw: Any, sleep_sec_raw: Any, name: str) -> RetryPolicy:
    try:
        sleep_sec = int(sleep_sec_raw)
    except (TypeError, ValueError):
        fail(f"Invalid {name}_retry_sleep_sec value: {sleep_sec_raw}")

    if sleep_sec < 0:
        fail(f"{name}_retry_sleep_sec must be >= 0")

    if retry_raw in (None, "", 0, "0", -1, "-1"):
        return RetryPolicy(max_retries=None, sleep_sec=sleep_sec)

    try:
        retries = int(retry_raw)
    except (TypeError, ValueError):
        fail(f"Invalid {name}_retry_count value: {retry_raw}")

    if retries <= 0:
        return RetryPolicy(max_retries=None, sleep_sec=sleep_sec)

    return RetryPolicy(max_retries=retries, sleep_sec=sleep_sec)


def retry_attempt_label(attempt: int, policy: RetryPolicy) -> str:
    if policy.max_retries is None:
        return f"{attempt}/∞"
    return f"{attempt}/{policy.max_retries}"


def should_stop_retrying(attempt: int, policy: RetryPolicy) -> bool:
    return policy.max_retries is not None and attempt >= policy.max_retries




def decode_subprocess_output(data: Optional[bytes]) -> str:
    if data is None:
        return ""

    encodings: List[str] = []

    if os.name == "nt":
        for candidate in (
            os.device_encoding(1),
            os.device_encoding(2),
            locale.getpreferredencoding(False),
            "cp866",
            "cp1251",
            "utf-8",
        ):
            if candidate and candidate not in encodings:
                encodings.append(candidate)
    else:
        preferred = locale.getpreferredencoding(False)
        if preferred:
            encodings.append(preferred)
        encodings.append("utf-8")

    for encoding in encodings:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue

    return data.decode(encodings[0] if encodings else "utf-8", errors="replace")


def run_subprocess_capture(
    args: Any,
    cwd: Optional[Path] = None,
    shell: bool = False,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        shell=shell,
        check=False,
        text=False,
        capture_output=True,
        env=env,
    )

    stdout_text = decode_subprocess_output(proc.stdout)
    stderr_text = decode_subprocess_output(proc.stderr)

    return subprocess.CompletedProcess(
        args=proc.args,
        returncode=proc.returncode,
        stdout=stdout_text,
        stderr=stderr_text,
    )
def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    check: bool = True,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess:
    proc = run_subprocess_capture(cmd, cwd=cwd, shell=False, env=env)

    if proc.stdout and proc.stdout.strip():
        print(proc.stdout)
    if proc.stderr and proc.stderr.strip():
        warn(proc.stderr)

    if check and proc.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {proc.returncode}: {' '.join(cmd)}\n"
            f"STDOUT:\n{proc.stdout}\n"
            f"STDERR:\n{proc.stderr}"
        )

    return proc


def run_shell_command(
    command: str,
    cwd: Optional[Path] = None,
    check: bool = True,
    env: Optional[Dict[str, str]] = None,
) -> subprocess.CompletedProcess:
    proc = run_subprocess_capture(command, cwd=cwd, shell=True, env=env)

    if proc.stdout and proc.stdout.strip():
        print(proc.stdout)
    if proc.stderr and proc.stderr.strip():
        warn(proc.stderr)

    if check and proc.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {proc.returncode}: {command}\n"
            f"STDOUT:\n{proc.stdout}\n"
            f"STDERR:\n{proc.stderr}"
        )

    return proc


def run_command_with_retries(
    cmd: List[str],
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    retry_policy: Optional[RetryPolicy] = None,
) -> subprocess.CompletedProcess:
    policy = retry_policy or RetryPolicy(max_retries=4, sleep_sec=5)
    last_exc: Optional[Exception] = None
    attempt = 0

    while True:
        attempt += 1
        try:
            info(f"Command attempt {retry_attempt_label(attempt, policy)}: {' '.join(cmd)}")
            return run_command(cmd, cwd=cwd, check=True, env=env)
        except Exception as exc:
            last_exc = exc
            if should_stop_retrying(attempt, policy):
                raise
            warn(f"Command failed, retrying after {policy.sleep_sec}s: {exc}")
            time.sleep(policy.sleep_sec)

    raise RuntimeError(str(last_exc) if last_exc else "Unknown command retry failure")


def run_shell_command_with_retries(
    command: str,
    cwd: Optional[Path] = None,
    env: Optional[Dict[str, str]] = None,
    retry_policy: Optional[RetryPolicy] = None,
) -> subprocess.CompletedProcess:
    policy = retry_policy or RetryPolicy(max_retries=4, sleep_sec=5)
    last_exc: Optional[Exception] = None
    attempt = 0

    while True:
        attempt += 1
        try:
            info(f"Shell command attempt {retry_attempt_label(attempt, policy)}: {command}")
            return run_shell_command(command, cwd=cwd, check=True, env=env)
        except Exception as exc:
            last_exc = exc
            if should_stop_retrying(attempt, policy):
                raise
            warn(f"Shell command failed, retrying after {policy.sleep_sec}s: {exc}")
            time.sleep(policy.sleep_sec)

    raise RuntimeError(str(last_exc) if last_exc else "Unknown shell command retry failure")


def is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def ensure_repo(
    git_path: str,
    repo_url: str,
    branch: str,
    repo_dir: Path,
    retry_policy: RetryPolicy,
) -> None:
    if repo_dir.exists():
        if not is_git_repo(repo_dir):
            contents = list(repo_dir.iterdir())
            if contents:
                fail(
                    f"Repo directory exists and is not a git repository: {repo_dir}\n"
                    f"Delete or rename this folder, or set another repo_dir in config.yaml."
                )
            info(f"Empty repo directory exists, cloning into it: {repo_dir}")
            run_command_with_retries(
                [git_path, "clone", repo_url, str(repo_dir)],
                retry_policy=retry_policy,
            )
        else:
            info(f"Using existing git repository: {repo_dir}")
    else:
        info(f"Cloning repo: {repo_url}")
        run_command_with_retries(
            [git_path, "clone", repo_url, str(repo_dir)],
            retry_policy=retry_policy,
        )

    info(f"Fetching repo and switching to branch: {branch}")
    run_command_with_retries([git_path, "fetch", "--all"], cwd=repo_dir, retry_policy=retry_policy)
    run_command_with_retries([git_path, "checkout", branch], cwd=repo_dir, retry_policy=retry_policy)
    run_command_with_retries(
        [git_path, "pull", "--ff-only", "origin", branch],
        cwd=repo_dir,
        retry_policy=retry_policy,
    )



def normalize_windows_workspace_acl(
    repo_dir: Path,
    retry_policy: RetryPolicy,
) -> None:
    if os.name != "nt":
        return

    computer_name = os.environ.get("COMPUTERNAME", "").strip()
    user_name = os.environ.get("USERNAME", "").strip()

    if not computer_name or not user_name:
        fail("Cannot resolve Windows COMPUTERNAME/USERNAME for workspace ACL normalization.")

    current_user = f"{computer_name}\\{user_name}"
    codex_group = f"{computer_name}\\CodexSandboxUsers"

    banner("WINDOWS WORKSPACE ACL")
    info(f"Normalizing ACL for workspace: {repo_dir}")
    info(f"Granting FullControl to current user: {current_user}")
    info("Granting FullControl to local Administrators SID: *S-1-5-32-544")
    info("Granting FullControl to local SYSTEM SID: *S-1-5-18")
    info("Granting FullControl to Authenticated Users SID: *S-1-5-11")
    info(f"Granting FullControl to Codex sandbox group: {codex_group}")

    def run_acl_command(cmd: List[str]) -> None:
        info(f"Running ACL command: {' '.join(cmd)}")
        proc = subprocess.run(
            cmd,
            cwd=str(repo_dir),
            check=False,
            text=True,
            encoding="oem",
            errors="replace",
            capture_output=True,
        )

        if proc.stdout and proc.stdout.strip():
            print(proc.stdout)
        if proc.stderr and proc.stderr.strip():
            warn(proc.stderr)

        if proc.returncode != 0:
            fail(
                "Windows workspace ACL normalization failed.\n"
                f"Command: {' '.join(cmd)}\n"
                f"Exit code: {proc.returncode}\n"
                f"STDOUT:\n{proc.stdout}\n"
                f"STDERR:\n{proc.stderr}"
            )

    commands = [
        ["icacls", str(repo_dir), "/inheritance:e"],
        ["icacls", str(repo_dir), "/reset", "/t", "/c"],
        ["icacls", str(repo_dir), "/grant", f"{current_user}:(OI)(CI)F", "/t", "/c"],
        ["icacls", str(repo_dir), "/grant", "*S-1-5-32-544:(OI)(CI)F", "/t", "/c"],
        ["icacls", str(repo_dir), "/grant", "*S-1-5-18:(OI)(CI)F", "/t", "/c"],
        ["icacls", str(repo_dir), "/grant", "*S-1-5-11:(OI)(CI)F", "/t", "/c"],
        ["icacls", str(repo_dir), "/grant", f"{codex_group}:(OI)(CI)F", "/t", "/c"],
    ]

    for cmd in commands:
        run_acl_command(cmd)

    probe_root = repo_dir / ".metaflow-acl-probe"
    probe_child = probe_root / uuid.uuid4().hex

    try:
        if probe_root.exists():
            shutil.rmtree(probe_root, ignore_errors=False)

        probe_child.mkdir(parents=True, exist_ok=False)
        write_text(probe_child / "probe.txt", "acl-ok\n")
        shutil.rmtree(probe_root, ignore_errors=False)
        info("Workspace ACL probe succeeded.")
    except Exception as exc:
        fail(
            "Windows workspace ACL probe failed after ACL normalization.\n"
            f"Repo dir: {repo_dir}\n"
            f"Probe path: {probe_child}\n"
            f"Reason: {exc}"
        )



def run_setup_commands(repo_dir: Path, setup_commands: List[str], retry_policy: RetryPolicy) -> None:
    if not setup_commands:
        return

    banner("SETUP")
    for index, cmd in enumerate(setup_commands, start=1):
        info(f"Running setup command {index}/{len(setup_commands)}: {cmd}")
        run_shell_command_with_retries(cmd, cwd=repo_dir, retry_policy=retry_policy)


def create_iteration_artifacts(base_dir: Path, iteration: int) -> IterationArtifacts:
    iteration_dir = base_dir / f"iteration_{iteration:03d}"
    iteration_dir.mkdir(parents=True, exist_ok=True)
    return IterationArtifacts(
        iteration_dir=iteration_dir,
        codex_prompt_path=iteration_dir / "codex_task.md",
        codex_summary_schema_path=iteration_dir / "codex_summary_schema.json",
        codex_summary_json_path=iteration_dir / "codex_summary.json",
        codex_trace_path=iteration_dir / "codex_trace.jsonl",
        codex_stderr_path=iteration_dir / "codex_stderr.txt",
        codex_report_fallback_path=iteration_dir / "codex_report_fallback.txt",
        git_diff_path=iteration_dir / "git_diff.patch",
        git_diff_stat_path=iteration_dir / "git_diff_stat.txt",
        changed_files_path=iteration_dir / "changed_files.txt",
        test_log_path=iteration_dir / "test_results.txt",
        tests_summary_path=iteration_dir / "tests_summary.json",
        reviewer_response_path=iteration_dir / "reviewer_response.json",
        reviewer_request_path=iteration_dir / "reviewer_request.txt",
        user_answer_path=iteration_dir / "user_answer.txt",
        inbox_manifest_path=iteration_dir / "reviewer_inbox_manifest.json",
        inbox_attachments_payload_path=iteration_dir / "reviewer_inbox_attachments.txt",
        first_iteration_attachments_manifest_path=iteration_dir / "first_iteration_attachments_manifest.json",
        first_iteration_attachments_payload_path=iteration_dir / "first_iteration_attachments.txt",
    )


def get_git_diff(git_path: str, repo_dir: Path) -> str:
    proc = run_command(
        [git_path, "diff", "--binary", "--no-ext-diff"],
        cwd=repo_dir,
        check=False,
    )
    return proc.stdout or ""


def get_git_diff_stat(git_path: str, repo_dir: Path) -> str:
    proc = run_command(
        [git_path, "diff", "--stat", "--no-ext-diff"],
        cwd=repo_dir,
        check=False,
    )
    return proc.stdout or ""


def get_changed_files(git_path: str, repo_dir: Path) -> str:
    proc = run_command(
        [git_path, "diff", "--name-only", "--no-ext-diff"],
        cwd=repo_dir,
        check=False,
    )
    return proc.stdout or ""


def summarize_text_tail(text: str, max_lines: int = 80, max_chars: int = 12000) -> str:
    cleaned = normalize_newlines(text)
    if not cleaned:
        return ""
    lines = cleaned.splitlines()
    tail = "\n".join(lines[-max_lines:])
    if len(tail) > max_chars:
        tail = tail[-max_chars:]
    return tail


def run_test_commands(
    repo_dir: Path,
    test_commands: List[str],
    extra_test_commands: List[str],
    test_log_path: Path,
    tests_summary_path: Path,
) -> Dict[str, Any]:
    banner("TEST RUN")
    all_cmds = list(test_commands) + list(extra_test_commands)
    raw_chunks: List[str] = []
    command_summaries: List[Dict[str, Any]] = []

    if not all_cmds:
        warn("No test commands configured.")
        write_text(test_log_path, "[NO TEST COMMANDS]\n")
        summary = {
            "overall_status": "no_commands",
            "all_passed": True,
            "commands": [],
        }
        save_json(tests_summary_path, summary)
        return summary

    all_passed = True

    for index, cmd in enumerate(all_cmds, start=1):
        info(f"Running test command {index}/{len(all_cmds)}: {cmd}")
        raw_chunks.append(f"{'=' * 80}\nCOMMAND {index}: {cmd}\n{'=' * 80}\n")

        started = time.time()
        try:
            proc = run_shell_command(cmd, cwd=repo_dir, check=False)
            duration_sec = round(time.time() - started, 2)
            stdout_text = proc.stdout or ""
            stderr_text = proc.stderr or ""

            raw_chunks.append(stdout_text)
            if stderr_text:
                raw_chunks.append("\n[STDERR]\n")
                raw_chunks.append(stderr_text)
            raw_chunks.append(f"\n[EXIT_CODE] {proc.returncode}\n\n")

            passed = proc.returncode == 0
            if not passed:
                all_passed = False

            item: Dict[str, Any] = {
                "command": cmd,
                "status": "passed" if passed else "failed",
                "exit_code": proc.returncode,
                "duration_sec": duration_sec,
            }

            if not passed:
                stdout_tail = summarize_text_tail(stdout_text)
                stderr_tail = summarize_text_tail(stderr_text)
                if stdout_tail:
                    item["stdout_tail"] = stdout_tail
                if stderr_tail:
                    item["stderr_tail"] = stderr_tail

            command_summaries.append(item)

        except Exception as exc:
            duration_sec = round(time.time() - started, 2)
            raw_chunks.append(f"\n[EXCEPTION] {exc}\n\n")
            warn(str(exc))
            all_passed = False
            command_summaries.append(
                {
                    "command": cmd,
                    "status": "failed",
                    "exit_code": -1,
                    "duration_sec": duration_sec,
                    "stderr_tail": summarize_text_tail(str(exc)),
                }
            )

    write_text(test_log_path, "".join(raw_chunks))
    summary = {
        "overall_status": "passed" if all_passed else "failed",
        "all_passed": all_passed,
        "commands": command_summaries,
    }
    save_json(tests_summary_path, summary)
    info(f"Raw test log saved to: {test_log_path}")
    info(f"Test summary saved to: {tests_summary_path}")
    return summary


def read_attachment_any(path: Path) -> Tuple[str, str, int]:
    data = path.read_bytes()
    size = len(data)

    try:
        text = data.decode("utf-8")
        return "text", text, size
    except UnicodeDecodeError:
        encoded = base64.b64encode(data).decode("ascii")
        return "base64", encoded, size


def build_single_attachment_block(path: Path, label_prefix: str = "ATTACHMENT") -> str:
    mode, content, size = read_attachment_any(path)
    mime_type, _ = mimetypes.guess_type(str(path))
    mime_type = mime_type or "application/octet-stream"

    rel_name = path.name

    if mode == "text":
        return (
            f"[{label_prefix}:{rel_name}]\n"
            f"[PATH]\n{path}\n"
            f"[MIME_TYPE]\n{mime_type}\n"
            f"[SIZE_BYTES]\n{size}\n"
            f"[ENCODING]\nutf-8\n"
            f"[CONTENT]\n{content}\n"
        )

    return (
        f"[{label_prefix}:{rel_name}]\n"
        f"[PATH]\n{path}\n"
        f"[MIME_TYPE]\n{mime_type}\n"
        f"[SIZE_BYTES]\n{size}\n"
        f"[ENCODING]\nbase64\n"
        f"[CONTENT_BASE64]\n{content}\n"
    )


def list_files_recursive(dir_path: Path) -> List[Path]:
    if not dir_path.exists() or not dir_path.is_dir():
        return []
    return sorted([p for p in dir_path.rglob("*") if p.is_file()])


def build_attachments_from_files(files: List[Path], label_prefix: str) -> str:
    chunks: List[str] = []
    for path in files:
        chunks.append(build_single_attachment_block(path, label_prefix=label_prefix))
    return "\n".join(chunks)


def collect_directory_attachments(
    source_dir: Path,
    manifest_path: Path,
    payload_path: Path,
    label_prefix: str,
) -> str:
    files = list_files_recursive(source_dir)

    manifest = []
    blocks: List[str] = []

    for path in files:
        mode, _, size = read_attachment_any(path)
        mime_type, _ = mimetypes.guess_type(str(path))
        manifest.append(
            {
                "name": path.name,
                "path": str(path.resolve()),
                "size_bytes": size,
                "mime_type": mime_type or "application/octet-stream",
                "encoding_mode": mode,
            }
        )
        blocks.append(build_single_attachment_block(path, label_prefix=label_prefix))

    save_json(manifest_path, manifest)
    payload = "\n".join(blocks)
    write_text(payload_path, payload)
    return payload


def build_reviewer_input(
    primary_input_text: str,
    attachments_text: str,
    iteration: int,
    technical_channel: Optional[Dict[str, Any]],
    codex_model_summary: Optional[Dict[str, Any]],
    user_answer: Optional[str],
    user_followup_attachments_text: Optional[str],
) -> str:
    blocks: List[str] = []

    blocks.append(f"[ITERATION]\n{iteration}\n")
    blocks.append(f"[TASK]\n{primary_input_text}\n")

    if iteration == 1 and attachments_text:
        blocks.append(attachments_text)

    if technical_channel is not None:
        blocks.append(
            "[TECHNICAL_CHANNEL]\n"
            + json.dumps(technical_channel, ensure_ascii=False, indent=2)
            + "\n"
        )

    if codex_model_summary is not None:
        blocks.append(
            "[MODEL_CHANNEL]\n"
            + json.dumps(codex_model_summary, ensure_ascii=False, indent=2)
            + "\n"
        )

    if user_answer:
        blocks.append(f"[USER_ANSWER_TO_PREVIOUS_QUESTION]\n{user_answer}\n")

    if user_followup_attachments_text:
        blocks.append(f"[USER_FOLLOWUP_ATTACHMENTS]\n{user_followup_attachments_text}\n")

    return "\n".join(blocks)


def extract_output_text(data: Dict[str, Any]) -> str:
    output_text = data.get("output_text")
    if output_text:
        return output_text

    texts: List[str] = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and "text" in content:
                texts.append(content["text"])
    return "".join(texts)


def build_reviewer_text_format() -> Dict[str, Any]:
    return {
        "type": "json_schema",
        "name": REVIEWER_OUTPUT_SCHEMA["name"],
        "schema": REVIEWER_OUTPUT_SCHEMA["schema"],
        "strict": REVIEWER_OUTPUT_SCHEMA["strict"],
    }


def call_reviewer_api(
    api_key: str,
    model: str,
    reviewer_input: str,
    reviewer_instructions: str,
    previous_response_id: Optional[str],
    timeout_sec: int = 600,
    retry_policy: Optional[RetryPolicy] = None,
) -> Dict[str, Any]:
    policy = retry_policy or RetryPolicy(max_retries=None, sleep_sec=5)

    url = "https://api.openai.com/v1/responses"
    client_request_id = str(uuid.uuid4())

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Client-Request-Id": client_request_id,
    }

    payload: Dict[str, Any] = {
        "model": model,
        "instructions": reviewer_instructions,
        "input": reviewer_input,
        "text": {
            "format": build_reviewer_text_format(),
        },
    }

    if previous_response_id:
        payload["previous_response_id"] = previous_response_id

    attempt = 0
    while True:
        attempt += 1
        try:
            info(
                f"Reviewer request attempt {retry_attempt_label(attempt, policy)} "
                f"(client_request_id={client_request_id})"
            )

            response = requests.post(url, headers=headers, json=payload, timeout=timeout_sec)

            if response.status_code in RETRIABLE_HTTP_STATUS_CODES:
                request_id = response.headers.get("x-request-id", "n/a")
                warn(
                    f"Reviewer API returned retriable status {response.status_code}. "
                    f"x-request-id={request_id}, client_request_id={client_request_id}. "
                    f"Retry after {policy.sleep_sec}s."
                )
                warn(f"Response body:\n{response.text[:8000]}")
                if should_stop_retrying(attempt, policy):
                    raise RuntimeError(
                        f"Reviewer API returned retriable status {response.status_code}, "
                        f"retry limit reached. client_request_id={client_request_id}"
                    )
                time.sleep(policy.sleep_sec)
                continue

            if response.status_code >= 400:
                request_id = response.headers.get("x-request-id", "n/a")
                raise requests.exceptions.HTTPError(
                    f"Reviewer API error {response.status_code}. "
                    f"x-request-id={request_id}, client_request_id={client_request_id}\n"
                    f"Response body:\n{response.text[:8000]}",
                    response=response,
                )

            data = response.json()
            output_text = extract_output_text(data)
            if not output_text:
                fail(
                    "Reviewer returned no text.\n"
                    f"client_request_id={client_request_id}\n"
                    f"Raw response: {json.dumps(data, ensure_ascii=False)[:4000]}"
                )

            parsed = json.loads(output_text)
            parsed["_response_id"] = data.get("id")
            return parsed

        except requests.exceptions.Timeout as exc:
            if should_stop_retrying(attempt, policy):
                raise RuntimeError(
                    f"Reviewer request timed out after {attempt} attempts. "
                    f"client_request_id={client_request_id}"
                ) from exc
            warn(
                f"Reviewer request timeout: {exc}. "
                f"client_request_id={client_request_id}. Retry after {policy.sleep_sec}s."
            )
            time.sleep(policy.sleep_sec)

        except requests.exceptions.ConnectionError as exc:
            if should_stop_retrying(attempt, policy):
                raise RuntimeError(
                    f"Reviewer connection error after {attempt} attempts. "
                    f"client_request_id={client_request_id}"
                ) from exc
            warn(
                f"Reviewer connection error: {exc}. "
                f"client_request_id={client_request_id}. Retry after {policy.sleep_sec}s."
            )
            time.sleep(policy.sleep_sec)

        except requests.exceptions.HTTPError:
            raise

        except requests.exceptions.RequestException as exc:
            if should_stop_retrying(attempt, policy):
                raise RuntimeError(
                    f"Reviewer request failed after {attempt} attempts. "
                    f"client_request_id={client_request_id}"
                ) from exc
            warn(
                f"Reviewer request failed: {exc}. "
                f"client_request_id={client_request_id}. Retry after {policy.sleep_sec}s."
            )
            time.sleep(policy.sleep_sec)
    return {}


def extract_text_fragments(value: Any) -> List[str]:
    fragments: List[str] = []

    if value is None:
        return fragments

    if isinstance(value, str):
        text = value.strip()
        if text:
            fragments.append(text)
        return fragments

    if isinstance(value, list):
        for item in value:
            fragments.extend(extract_text_fragments(item))
        return fragments

    if isinstance(value, dict):
        content = value.get("content")
        if content is not None:
            fragments.extend(extract_text_fragments(content))

        for key in ("text", "message", "output_text", "aggregated_output"):
            if isinstance(value.get(key), str) and value[key].strip():
                fragments.append(value[key].strip())

        return fragments

    return fragments


def extract_codex_report_from_trace(trace_text: str) -> str:
    candidates: List[str] = []

    for raw_line in trace_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        item = event.get("item")
        item_type = item.get("type") if isinstance(item, dict) else None
        event_type = str(event.get("type", "")).strip().lower()

        if item_type in CODEX_NON_REPORT_ITEM_TYPES:
            continue

        if "command_execution" in event_type:
            continue

        if isinstance(item, dict):
            for fragment in extract_text_fragments(item):
                cleaned = normalize_newlines(fragment)
                if cleaned:
                    candidates.append(cleaned)

        for fragment in extract_text_fragments(event.get("content")):
            cleaned = normalize_newlines(fragment)
            if cleaned:
                candidates.append(cleaned)

        for key in ("output_text", "text", "message"):
            value = event.get(key)
            if isinstance(value, str) and value.strip():
                candidates.append(normalize_newlines(value))

    unique_candidates: List[str] = []
    seen: set[str] = set()

    for candidate in candidates:
        if candidate and candidate not in seen:
            unique_candidates.append(candidate)
            seen.add(candidate)

    if unique_candidates:
        unique_candidates.sort(key=len)
        return unique_candidates[-1]

    return ""


def build_codex_report_fallback(stdout_text: str, stderr_text: str) -> str:
    parts: List[str] = []

    cleaned_stdout = normalize_newlines(stdout_text)
    cleaned_stderr = normalize_newlines(stderr_text)

    if cleaned_stdout:
        parts.append("[RAW_CODEX_STDOUT]\n" + cleaned_stdout)
    if cleaned_stderr:
        parts.append("[RAW_CODEX_STDERR]\n" + cleaned_stderr)

    if not parts:
        return "[NO CODEX REPORT EXTRACTED]"

    return "\n\n".join(parts)


def load_json_if_exists(path: Path) -> Optional[Any]:
    if not path.exists():
        return None
    raw = read_text(path).strip()
    if not raw:
        return None
    return json.loads(raw)


def ensure_codex_summary_file(
    codex_summary_json_path: Path,
    trace_path: Path,
    stderr_path: Path,
    fallback_path: Path,
) -> Dict[str, Any]:
    structured = load_json_if_exists(codex_summary_json_path)
    if isinstance(structured, dict):
        return structured

    stdout_text = read_text(trace_path) if trace_path.exists() else ""
    stderr_text = read_text(stderr_path) if stderr_path.exists() else ""
    extracted_report = extract_codex_report_from_trace(stdout_text)
    if not extracted_report:
        extracted_report = build_codex_report_fallback(stdout_text, stderr_text)

    fallback_obj = {
        "summary": extracted_report,
        "what_changed": [],
        "risks": ["Structured Codex summary was not produced; fallback report used."],
        "notes": [],
        "high_risk_areas_touched": False,
        "high_risk_areas": [],
        "verification_notes": [],
    }
    save_json(codex_summary_json_path, fallback_obj)
    write_text(fallback_path, extracted_report + "\n")
    return fallback_obj


def trace_indicates_turn_completed(trace_path: Path) -> bool:
    if not trace_path.exists():
        return False

    try:
        with trace_path.open("r", encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if str(event.get("type", "")).strip().lower() == "turn.completed":
                    return True
    except Exception:
        return False

    return False


def codex_logical_completion_observed(
    monitor_state: CodexMonitorState,
    codex_summary_json_path: Path,
    trace_path: Path,
) -> bool:
    snapshot = monitor_state.snapshot()
    if snapshot["saw_turn_completed"] and isinstance(load_json_if_exists(codex_summary_json_path), dict):
        return True

    if trace_indicates_turn_completed(trace_path) and isinstance(load_json_if_exists(codex_summary_json_path), dict):
        return True

    return False


def _collect_pipe(
    pipe: Any,
    collector: List[str],
    path: Path,
    echo_stderr_prefix: Optional[str],
    monitor_state: Optional[CodexMonitorState],
    stream_name: str,
) -> None:
    try:
        while True:
            line = pipe.readline()
            if not line:
                break

            if isinstance(line, bytes):
                text = line.decode("utf-8", errors="replace")
            else:
                text = str(line)

            collector.append(text)
            append_text(path, text)

            if monitor_state is not None:
                if stream_name == "stdout":
                    monitor_state.mark_stdout_line(text)
                else:
                    monitor_state.mark_stderr_line()

            stripped = text.rstrip()
            if stripped:
                if echo_stderr_prefix is not None:
                    warn(f"{echo_stderr_prefix}{stripped}")
                else:
                    print(stripped)
    finally:
        pipe.close()


def _codex_heartbeat(proc: subprocess.Popen, heartbeat_interval_sec: int) -> None:
    start_time = time.time()
    tick = 0

    while proc.poll() is None:
        tick += 1
        elapsed = int(time.time() - start_time)
        info(
            f"Codex is still running... "
            f"elapsed={elapsed}s, heartbeat={tick}, pid={proc.pid}"
        )
        time.sleep(heartbeat_interval_sec)


def command_has_flag(parts: List[str], long_flag: str, short_flag: Optional[str] = None) -> bool:
    for part in parts:
        if part == long_flag or (short_flag and part == short_flag):
            return True
        if part.startswith(long_flag + "="):
            return True
        if short_flag and part.startswith(short_flag) and part != short_flag and not part.startswith("--"):
            return True
    return False


def build_codex_command_parts(
    codex_executable: str,
    codex_command_template: str,
    schema_path: Path,
    output_json_path: Path,
) -> Tuple[List[str], bool]:
    try:
        parts = shlex.split(codex_command_template)
    except ValueError as exc:
        fail(f"Invalid codex_command in config.yaml: {exc}")

    if not parts:
        fail("codex_command is empty in config.yaml")

    if parts[0].lower() == "codex":
        parts[0] = codex_executable

    use_stdin = "-" in parts
    if use_stdin:
        stripped_parts: List[str] = []
        removed_placeholder = False
        for part in parts:
            if part == "-" and not removed_placeholder:
                removed_placeholder = True
                continue
            stripped_parts.append(part)
        parts = stripped_parts

    if not command_has_flag(parts, "--output-schema"):
        parts.extend(["--output-schema", str(schema_path)])

    if not command_has_flag(parts, "--output-last-message", "-o"):
        parts.extend(["-o", str(output_json_path)])

    return parts, use_stdin


def terminate_process_tree_best_effort(
    proc: subprocess.Popen,
    terminate_wait_sec: int,
) -> None:
    if proc.poll() is not None:
        return

    try:
        warn(f"Attempting graceful Codex terminate (pid={proc.pid})...")
        proc.terminate()
        deadline = time.time() + max(0, terminate_wait_sec)
        while time.time() < deadline:
            if proc.poll() is not None:
                return
            time.sleep(0.2)
    except Exception as exc:
        warn(f"Graceful terminate failed: {exc}")

    if proc.poll() is not None:
        return

    try:
        warn(f"Force killing Codex process (pid={proc.pid})...")
        proc.kill()
        deadline = time.time() + 5
        while time.time() < deadline:
            if proc.poll() is not None:
                return
            time.sleep(0.2)
    except Exception as exc:
        warn(f"Force kill failed: {exc}")


def run_codex(
    codex_executable: str,
    repo_dir: Path,
    codex_task_path: Path,
    codex_summary_schema_path: Path,
    codex_summary_json_path: Path,
    trace_path: Path,
    stderr_path: Path,
    fallback_path: Path,
    codex_command_template: str,
    codex_env: Dict[str, str],
    heartbeat_interval_sec: int,
    retry_policy: RetryPolicy,
    max_runtime_sec: int,
    post_turn_grace_sec: int,
    idle_timeout_sec: int,
    terminate_wait_sec: int,
) -> Tuple[int, Dict[str, Any]]:
    banner("CODEX RUN")

    prompt_text = read_text(codex_task_path)
    prompt_bytes = prompt_text.encode("utf-8")

    save_json(codex_summary_schema_path, CODEX_SUMMARY_SCHEMA)
    write_text(trace_path, "")
    write_text(stderr_path, "")
    write_text(fallback_path, "")
    write_text(codex_summary_json_path, "")

    command_parts, use_stdin = build_codex_command_parts(
        codex_executable=codex_executable,
        codex_command_template=codex_command_template,
        schema_path=codex_summary_schema_path,
        output_json_path=codex_summary_json_path,
    )

    last_return_code = 1
    last_stdout = ""
    last_stderr = ""
    attempt = 0

    while True:
        attempt += 1

        if use_stdin:
            info(
                f"Running Codex attempt {retry_attempt_label(attempt, retry_policy)}: "
                f"{' '.join(command_parts)} [PROMPT_VIA_STDIN_UTF8_STREAM]"
            )
        else:
            info(
                f"Running Codex attempt {retry_attempt_label(attempt, retry_policy)}: "
                f"{' '.join(command_parts)} [PROMPT_AS_ARGUMENT_STREAM]"
            )

        try:
            if use_stdin:
                proc = subprocess.Popen(
                    command_parts,
                    cwd=str(repo_dir),
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=codex_env,
                )
            else:
                proc = subprocess.Popen(
                    command_parts + [prompt_text],
                    cwd=str(repo_dir),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    env=codex_env,
                )
        except FileNotFoundError as exc:
            fail(
                f"Failed to start Codex CLI: {exc}\n"
                f"Command attempted: {' '.join(command_parts)}\n"
                f"Resolved codex path: {codex_executable}\n"
                f"Check that Codex CLI is installed and available in PATH."
            )
        except Exception as exc:
            fail(
                "Unexpected error while starting Codex CLI:\n"
                f"{exc}\n\n"
                f"{traceback.format_exc()}"
            )

        stdout_chunks: List[str] = []
        stderr_chunks: List[str] = []
        monitor_state = CodexMonitorState(started_at=time.time())

        stdout_thread = threading.Thread(
            target=_collect_pipe,
            args=(proc.stdout, stdout_chunks, trace_path, None, monitor_state, "stdout"),
            daemon=True,
        )
        stderr_thread = threading.Thread(
            target=_collect_pipe,
            args=(proc.stderr, stderr_chunks, stderr_path, "", monitor_state, "stderr"),
            daemon=True,
        )
        heartbeat_thread = threading.Thread(
            target=_codex_heartbeat,
            args=(proc, heartbeat_interval_sec),
            daemon=True,
        )

        stdout_thread.start()
        stderr_thread.start()
        heartbeat_thread.start()

        if use_stdin:
            assert proc.stdin is not None
            proc.stdin.write(prompt_bytes)
            proc.stdin.close()

        forced_shutdown = False
        forced_shutdown_reason: Optional[str] = None

        while True:
            return_code = proc.poll()
            snapshot = monitor_state.snapshot()
            now = time.time()
            elapsed = now - snapshot["started_at"]
            last_output_age = now - snapshot["last_output_at"]
            summary_ready = isinstance(load_json_if_exists(codex_summary_json_path), dict)
            logical_completion = codex_logical_completion_observed(
                monitor_state=monitor_state,
                codex_summary_json_path=codex_summary_json_path,
                trace_path=trace_path,
            )

            if return_code is not None:
                break

            if logical_completion and snapshot["turn_completed_at"] is not None:
                completed_for = now - snapshot["turn_completed_at"]
                if completed_for >= post_turn_grace_sec:
                    forced_shutdown = True
                    forced_shutdown_reason = (
                        f"logical completion observed and process still alive after "
                        f"{post_turn_grace_sec}s grace period"
                    )
                    warn(
                        "Codex produced a completed turn and summary but the CLI process "
                        "did not exit. Ending the process and accepting the logical result."
                    )
                    terminate_process_tree_best_effort(proc, terminate_wait_sec=terminate_wait_sec)
                    break

            if max_runtime_sec > 0 and elapsed >= max_runtime_sec:
                forced_shutdown = True
                forced_shutdown_reason = f"max runtime exceeded ({max_runtime_sec}s)"
                warn(
                    f"Codex exceeded max runtime of {max_runtime_sec}s. "
                    "Ending the process."
                )
                terminate_process_tree_best_effort(proc, terminate_wait_sec=terminate_wait_sec)
                break

            if idle_timeout_sec > 0 and last_output_age >= idle_timeout_sec:
                forced_shutdown = True
                if logical_completion or summary_ready:
                    forced_shutdown_reason = (
                        f"idle timeout exceeded after logical completion ({idle_timeout_sec}s)"
                    )
                    warn(
                        f"Codex became idle for {idle_timeout_sec}s after producing a result. "
                        "Ending the process and accepting the logical result if present."
                    )
                else:
                    forced_shutdown_reason = f"idle timeout exceeded without result ({idle_timeout_sec}s)"
                    warn(
                        f"Codex became idle for {idle_timeout_sec}s without a completed result. "
                        "Ending the process; retry policy will decide whether to retry."
                    )
                terminate_process_tree_best_effort(proc, terminate_wait_sec=terminate_wait_sec)
                break

            time.sleep(0.5)

        if proc.poll() is None:
            terminate_process_tree_best_effort(proc, terminate_wait_sec=terminate_wait_sec)

        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)
        heartbeat_thread.join(timeout=0.1)

        if proc.poll() is None:
            terminate_process_tree_best_effort(proc, terminate_wait_sec=terminate_wait_sec)

        last_return_code = proc.poll() if proc.poll() is not None else 1
        last_stdout = "".join(stdout_chunks)
        last_stderr = "".join(stderr_chunks)

        structured_summary = ensure_codex_summary_file(
            codex_summary_json_path=codex_summary_json_path,
            trace_path=trace_path,
            stderr_path=stderr_path,
            fallback_path=fallback_path,
        )

        logical_completion = codex_logical_completion_observed(
            monitor_state=monitor_state,
            codex_summary_json_path=codex_summary_json_path,
            trace_path=trace_path,
        )

        if last_return_code == 0:
            info(f"Codex exit code: {last_return_code}")
            info(f"Codex structured summary saved to: {codex_summary_json_path}")
            info(f"Codex trace saved to: {trace_path}")
            info(f"Codex stderr saved to: {stderr_path}")
            return last_return_code, structured_summary

        if logical_completion:
            warn(
                f"Codex exited with non-zero code {last_return_code}, "
                "but a completed turn and structured summary were already produced. "
                "Accepting the result without retry."
            )
            if forced_shutdown_reason:
                warn(f"Codex forced shutdown reason: {forced_shutdown_reason}")
            info(f"Codex exit code: {last_return_code}")
            info(f"Codex structured summary saved to: {codex_summary_json_path}")
            info(f"Codex trace saved to: {trace_path}")
            info(f"Codex stderr saved to: {stderr_path}")
            return last_return_code, structured_summary

        if should_stop_retrying(attempt, retry_policy):
            break

        warn(
            f"Codex failed with exit code {last_return_code}. "
            f"Retry after {retry_policy.sleep_sec}s."
        )
        time.sleep(retry_policy.sleep_sec)

    write_text(fallback_path, build_codex_report_fallback(last_stdout, last_stderr) + "\n")
    structured_summary = ensure_codex_summary_file(
        codex_summary_json_path=codex_summary_json_path,
        trace_path=trace_path,
        stderr_path=stderr_path,
        fallback_path=fallback_path,
    )
    info(f"Codex exit code: {last_return_code}")
    info(f"Codex structured summary saved to: {codex_summary_json_path}")
    info(f"Codex trace saved to: {trace_path}")
    info(f"Codex stderr saved to: {stderr_path}")
    return last_return_code, structured_summary


def ask_user(question: str, reviewer_inbox_dir: Path) -> str:
    banner("QUESTION FROM REVIEWER")
    print(question.strip())
    print(f"\nreviewer_inbox: {reviewer_inbox_dir}")
    print("After you finish your answer, run.py will attach everything currently present in reviewer_inbox to the NEXT reviewer request.")
    print("Inbox is not auto-cleared. Keep it clean manually if needed.")
    print("\nEnter your answer below. Finish with an empty line:")

    lines: List[str] = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def ask_finish_or_continue(reason: str, reviewer_inbox_dir: Path) -> Tuple[bool, str]:
    banner("HUMAN CHECKPOINT")
    print(reason.strip())
    print("\nChoose:")
    print("  finish   - stop the process now")
    print("  continue - continue from the current state")
    print(f"\nreviewer_inbox: {reviewer_inbox_dir}")
    print("If you choose continue, run.py will attach everything currently present in reviewer_inbox to the NEXT reviewer request.")
    print("Inbox is not auto-cleared. Keep it clean manually if needed.")

    while True:
        choice = input("\nType finish/continue: ").strip().lower()
        if choice in {"finish", "continue"}:
            break
        print("Please type exactly: finish or continue")

    if choice == "finish":
        return True, ""

    print("\nOptional note for the next reviewer request. Finish with an empty line:")
    lines: List[str] = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    return False, "\n".join(lines).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Codex + ChatGPT orchestration loop")
    parser.add_argument("-input", "--input", "--task", dest="primary_input", required=True, help="Path to main input file")
    parser.add_argument("-instructions", "--instructions", dest="instructions_file", required=True, help="Path to reviewer instructions file")
    parser.add_argument("-config", "--config", dest="config", required=True, help="Path to config.yaml")
    parser.add_argument("--env-file", default=".env", help="Path to .env")
    args = parser.parse_args()

    load_dotenv(args.env_file)

    openai_api_key = os.getenv("OPENAI_API_KEY")
    codex_api_key = os.getenv("CODEX_API_KEY")

    if not openai_api_key:
        fail("OPENAI_API_KEY is missing in .env or environment.")

    git_path = resolve_tool_path("git")
    codex_path = resolve_tool_path("codex")

    config = load_yaml(Path(args.config))
    repo_url = config["repo_url"]
    branch = config.get("branch", "main")
    repo_dir = Path(config.get("repo_dir", "./repo")).resolve()
    artifacts_dir = Path(config.get("artifacts_dir", "./artifacts")).resolve()
    attachments_dir = Path(config.get("attachments_dir", "./attachments")).resolve()
    reviewer_inbox_dir = Path(config.get("reviewer_inbox_dir", "./reviewer_inbox")).resolve()
    reviewer_model = config.get("reviewer_model", "gpt-5.4-mini")
    max_iterations = int(config.get("max_iterations", 5))
    setup_commands = config.get("setup_commands", [])
    test_commands = config.get("all_test_commands", [])
    codex_command = config.get("codex_command", "codex exec --full-auto --json -")

    repo_retry_policy = parse_retry_policy(
        config.get("repo_retry_count", 4),
        config.get("repo_retry_sleep_sec", 5),
        "repo",
    )
    setup_retry_policy = parse_retry_policy(
        config.get("setup_retry_count", 4),
        config.get("setup_retry_sleep_sec", 5),
        "setup",
    )
    codex_retry_policy = parse_retry_policy(
        config.get("codex_retry_count", 4),
        config.get("codex_retry_sleep_sec", 5),
        "codex",
    )
    reviewer_retry_policy = parse_retry_policy(
        config.get("reviewer_retry_count", 0),
        config.get("reviewer_retry_sleep_sec", 5),
        "reviewer",
    )

    iteration_sleep_sec = int(config.get("iteration_sleep_sec", 8))
    codex_heartbeat_interval_sec = int(config.get("codex_heartbeat_interval_sec", 15))

    codex_max_runtime_sec = int(config.get("codex_max_runtime_sec", 1800))
    codex_post_turn_grace_sec = int(config.get("codex_post_turn_grace_sec", 15))
    codex_idle_timeout_sec = int(config.get("codex_idle_timeout_sec", 300))
    codex_terminate_wait_sec = int(config.get("codex_terminate_wait_sec", 5))

    primary_input_path = Path(args.primary_input).resolve()
    instructions_path = Path(args.instructions_file).resolve()

    if not primary_input_path.exists():
        fail(f"Input file not found: {primary_input_path}")
    if not instructions_path.exists():
        fail(f"Instructions file not found: {instructions_path}")

    primary_input_text = read_text(primary_input_path)
    reviewer_instructions = read_text(instructions_path)

    artifacts_dir.mkdir(parents=True, exist_ok=True)

    if not attachments_dir.exists():
        warn(f"Attachments dir does not exist. Iteration 1 will be sent without folder attachments: {attachments_dir}")
    elif not attachments_dir.is_dir():
        fail(f"attachments_dir exists but is not a directory: {attachments_dir}")

    if not reviewer_inbox_dir.exists():
        warn(f"Inbox dir does not exist. Follow-up inbox attachments will be unavailable until you create it: {reviewer_inbox_dir}")
    elif not reviewer_inbox_dir.is_dir():
        fail(f"reviewer_inbox_dir exists but is not a directory: {reviewer_inbox_dir}")

    codex_env = os.environ.copy()
    if codex_api_key:
        codex_env["CODEX_API_KEY"] = codex_api_key

    banner("START")
    info(f"Input file: {primary_input_path}")
    info(f"Instructions file: {instructions_path}")
    info(f"Config: {Path(args.config).resolve()}")
    info(f"Repo URL: {repo_url}")
    info(f"Branch: {branch}")
    info(f"Repo dir: {repo_dir}")
    info(f"Artifacts dir: {artifacts_dir}")
    info(f"Attachments dir: {attachments_dir}")
    info(f"Reviewer inbox dir: {reviewer_inbox_dir}")
    info(f"Resolved git path: {git_path}")
    info(f"Resolved codex path: {codex_path}")
    info(f"Configured codex command: {codex_command}")
    info(f"Codex heartbeat interval: {codex_heartbeat_interval_sec}s")
    info(f"Codex max runtime: {codex_max_runtime_sec}s")
    info(f"Codex post-turn grace: {codex_post_turn_grace_sec}s")
    info(f"Codex idle timeout: {codex_idle_timeout_sec}s")
    info(f"Codex terminate wait: {codex_terminate_wait_sec}s")
    info(
        f"Retry policy repo: retries={'∞' if repo_retry_policy.max_retries is None else repo_retry_policy.max_retries}, "
        f"sleep={repo_retry_policy.sleep_sec}s"
    )
    info(
        f"Retry policy setup: retries={'∞' if setup_retry_policy.max_retries is None else setup_retry_policy.max_retries}, "
        f"sleep={setup_retry_policy.sleep_sec}s"
    )
    info(
        f"Retry policy codex: retries={'∞' if codex_retry_policy.max_retries is None else codex_retry_policy.max_retries}, "
        f"sleep={codex_retry_policy.sleep_sec}s"
    )
    info(
        f"Retry policy reviewer: retries={'∞' if reviewer_retry_policy.max_retries is None else reviewer_retry_policy.max_retries}, "
        f"sleep={reviewer_retry_policy.sleep_sec}s"
    )

    ensure_repo(git_path, repo_url, branch, repo_dir, retry_policy=repo_retry_policy)
    #normalize_windows_workspace_acl(repo_dir, retry_policy=repo_retry_policy)
    run_setup_commands(repo_dir, setup_commands, retry_policy=setup_retry_policy)

    previous_response_id: Optional[str] = None
    previous_technical_channel: Optional[Dict[str, Any]] = None
    previous_codex_model_summary: Optional[Dict[str, Any]] = None
    pending_user_answer: Optional[str] = None
    pending_user_followup_attachments_text: Optional[str] = None

    iteration_seq = 0
    window_iteration = 0
    first_iteration_attachments_text: Optional[str] = None

    while True:
        if window_iteration >= max_iterations:
            should_finish, checkpoint_note = ask_finish_or_continue(
                reason=(
                    f"Reached max_iterations ({max_iterations}) without an explicit reviewer question. "
                    "Do you want to finish or continue?"
                ),
                reviewer_inbox_dir=reviewer_inbox_dir,
            )
            if should_finish:
                banner("STOP")
                info("Stopped by user at max_iterations checkpoint.")
                return 0

            window_iteration = 0
            pending_user_answer = checkpoint_note or "User chose to continue after max_iterations checkpoint."
            inbox_payload = collect_directory_attachments(
                source_dir=reviewer_inbox_dir,
                manifest_path=artifacts_dir / "checkpoint_inbox_manifest.json",
                payload_path=artifacts_dir / "checkpoint_inbox_attachments.txt",
                label_prefix="USER_INBOX_ATTACHMENT",
            )
            pending_user_followup_attachments_text = inbox_payload

            inbox_files = list_files_recursive(reviewer_inbox_dir)
            if inbox_files:
                banner("CHECKPOINT INBOX ATTACHMENTS")
                info(f"Attaching {len(inbox_files)} file(s) from reviewer_inbox to the next reviewer request:")
                for file_path in inbox_files:
                    info(f"- {file_path}")
            else:
                info("reviewer_inbox is empty. No follow-up attachments will be sent.")
            continue

        iteration_seq += 1
        window_iteration += 1
        banner(f"ITERATION {iteration_seq} (window {window_iteration}/{max_iterations})")

        art = create_iteration_artifacts(artifacts_dir, iteration_seq)

        attachments_text = ""
        if first_iteration_attachments_text is None:
            first_iteration_attachments_text = collect_directory_attachments(
                source_dir=attachments_dir,
                manifest_path=art.first_iteration_attachments_manifest_path,
                payload_path=art.first_iteration_attachments_payload_path,
                label_prefix="ATTACHMENT",
            )
            first_iteration_files = list_files_recursive(attachments_dir)
            if first_iteration_files:
                banner("FIRST ITERATION ATTACHMENTS")
                info(f"Attaching {len(first_iteration_files)} file(s) from attachments:")
                for file_path in first_iteration_files:
                    info(f"- {file_path}")
            else:
                info("attachments is empty or missing. No first-iteration folder attachments will be sent.")

        if first_iteration_attachments_text is not None and iteration_seq == 1:
            attachments_text = first_iteration_attachments_text

        reviewer_input = build_reviewer_input(
            primary_input_text=primary_input_text,
            attachments_text=attachments_text,
            iteration=iteration_seq,
            technical_channel=previous_technical_channel,
            codex_model_summary=previous_codex_model_summary,
            user_answer=pending_user_answer,
            user_followup_attachments_text=pending_user_followup_attachments_text,
        )
        write_text(art.reviewer_request_path, reviewer_input)

        print_reviewer_payload_preview(
            iteration=iteration_seq,
            reviewer_instructions=reviewer_instructions,
            primary_input_text=primary_input_text,
            attachments_text=attachments_text,
            technical_channel_text=(
                json.dumps(previous_technical_channel, ensure_ascii=False, indent=2)
                if previous_technical_channel is not None
                else None
            ),
            model_channel_text=(
                json.dumps(previous_codex_model_summary, ensure_ascii=False, indent=2)
                if previous_codex_model_summary is not None
                else None
            ),
            user_answer=pending_user_answer,
            user_followup_attachments_text=pending_user_followup_attachments_text,
            reviewer_input=reviewer_input,
        )

        banner("CHATGPT REVIEWER")
        info("Sending request to reviewer model...")
        reviewer_response = call_reviewer_api(
            api_key=openai_api_key,
            model=reviewer_model,
            reviewer_input=reviewer_input,
            reviewer_instructions=reviewer_instructions,
            previous_response_id=previous_response_id,
            retry_policy=reviewer_retry_policy,
        )
        previous_response_id = reviewer_response.get("_response_id")
        save_json(art.reviewer_response_path, reviewer_response)

        print("\n[CHATGPT SUMMARY]")
        print(reviewer_response["summary"])
        print("\n[CHATGPT NOTES]")
        print(reviewer_response["review_notes"])

        status = reviewer_response["status"]

        if status == "done":
            should_finish, checkpoint_note = ask_finish_or_continue(
                reason=(
                    "Reviewer returned DONE. "
                    "Do you want to finish the process or continue from the current state?"
                ),
                reviewer_inbox_dir=reviewer_inbox_dir,
            )
            if should_finish:
                banner("DONE")
                print(reviewer_response["summary"])
                return 0

            window_iteration = 0
            pending_user_answer = checkpoint_note or "User chose to continue after reviewer returned done."
            inbox_payload = collect_directory_attachments(
                source_dir=reviewer_inbox_dir,
                manifest_path=art.inbox_manifest_path,
                payload_path=art.inbox_attachments_payload_path,
                label_prefix="USER_INBOX_ATTACHMENT",
            )
            pending_user_followup_attachments_text = inbox_payload

            inbox_files = list_files_recursive(reviewer_inbox_dir)
            if inbox_files:
                banner("INBOX ATTACHMENTS")
                info(f"Attaching {len(inbox_files)} file(s) from reviewer_inbox to the next reviewer request:")
                for file_path in inbox_files:
                    info(f"- {file_path}")
            else:
                info("reviewer_inbox is empty. No follow-up attachments will be sent.")

            info("User chose to continue after DONE. Continuing from current state.")
            continue

        if status == "escalate":
            banner("ESCALATION")
            print(reviewer_response["summary"])
            return 2

        if status == "question":
            question = reviewer_response.get("question_for_user", "").strip()
            if not question:
                fail("Reviewer returned status='question' but question_for_user is empty.")

            answer = ask_user(question, reviewer_inbox_dir=reviewer_inbox_dir)
            write_text(art.user_answer_path, answer + "\n")
            pending_user_answer = answer
            window_iteration = 0

            inbox_payload = collect_directory_attachments(
                source_dir=reviewer_inbox_dir,
                manifest_path=art.inbox_manifest_path,
                payload_path=art.inbox_attachments_payload_path,
                label_prefix="USER_INBOX_ATTACHMENT",
            )
            pending_user_followup_attachments_text = inbox_payload

            inbox_files = list_files_recursive(reviewer_inbox_dir)
            if inbox_files:
                banner("INBOX ATTACHMENTS")
                info(f"Attaching {len(inbox_files)} file(s) from reviewer_inbox to the next reviewer request:")
                for file_path in inbox_files:
                    info(f"- {file_path}")
            else:
                info("reviewer_inbox is empty or missing. No follow-up attachments will be sent.")

            info("User answer captured. Iteration window reset. Continuing to next reviewer iteration without Codex run.")
            continue

        pending_user_answer = None
        pending_user_followup_attachments_text = None

        codex_task_md = reviewer_response["codex_task_md"]
        write_text(art.codex_prompt_path, codex_task_md)

        print("\n[CODEX TASK]")
        print(codex_task_md)

        #normalize_windows_workspace_acl(repo_dir, retry_policy=repo_retry_policy)

        codex_exit, codex_model_summary = run_codex(
            codex_executable=codex_path,
            repo_dir=repo_dir,
            codex_task_path=art.codex_prompt_path,
            codex_summary_schema_path=art.codex_summary_schema_path,
            codex_summary_json_path=art.codex_summary_json_path,
            trace_path=art.codex_trace_path,
            stderr_path=art.codex_stderr_path,
            fallback_path=art.codex_report_fallback_path,
            codex_command_template=codex_command,
            codex_env=codex_env,
            heartbeat_interval_sec=codex_heartbeat_interval_sec,
            retry_policy=codex_retry_policy,
            max_runtime_sec=codex_max_runtime_sec,
            post_turn_grace_sec=codex_post_turn_grace_sec,
            idle_timeout_sec=codex_idle_timeout_sec,
            terminate_wait_sec=codex_terminate_wait_sec,
        )

        git_diff_text = get_git_diff(git_path, repo_dir)
        git_diff_stat_text = get_git_diff_stat(git_path, repo_dir)
        changed_files_text = get_changed_files(git_path, repo_dir)

        write_text(art.git_diff_path, git_diff_text)
        write_text(art.git_diff_stat_path, git_diff_stat_text)
        write_text(art.changed_files_path, changed_files_text)

        extra_test_commands = reviewer_response.get("extra_test_commands", [])
        if reviewer_response.get("should_run_all_tests", True):
            tests_summary = run_test_commands(
                repo_dir,
                test_commands,
                extra_test_commands,
                art.test_log_path,
                art.tests_summary_path,
            )
        else:
            tests_summary = run_test_commands(
                repo_dir,
                [],
                extra_test_commands,
                art.test_log_path,
                art.tests_summary_path,
            )

        previous_technical_channel = {
            "git_diff_patch": git_diff_text,
            "git_diff_stat": git_diff_stat_text,
            "changed_files": [line.strip() for line in changed_files_text.splitlines() if line.strip()],
            "tests_summary": tests_summary,
        }
        previous_codex_model_summary = codex_model_summary

        if codex_exit == 0 and not changed_files_text.strip():
            warn("Codex completed successfully but produced no repository changes.")

        info(f"Iteration {iteration_seq} complete. Codex exit code: {codex_exit}")
        time.sleep(iteration_sleep_sec)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n[STOPPED] Interrupted by user.")
        raise SystemExit(130)
    except Exception as exc:
        print("\n[UNHANDLED ERROR]")
        print(str(exc))
        print("\n[TRACEBACK]")
        print(traceback.format_exc())
        raise SystemExit(1)
