"""``python -m lvbitpack`` as a real process: output, exit codes and closed pipes."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_SRC = str(Path(__file__).resolve().parents[1] / "src")
_ENV = {**os.environ, "PYTHONPATH": _SRC, "PYTHONIOENCODING": "utf-8"}


def run(*args: str) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, "-m", "lvbitpack", *args]
    return subprocess.run(command, capture_output=True, text=True, timeout=60, env=_ENV)


def test_module_entry_point_packs_and_unpacks() -> None:
    assert run("pack", "01", "--type", "i8").stdout == "-2\n"
    assert run("unpack", "-2", "--type", "i8").stdout == "01111111\n"
    assert run("flatten", "1011").stdout == "0000000401000101\n"


def test_exit_codes() -> None:
    assert run("unpack", "256", "--type", "u8").returncode == 1
    assert run("frobnicate").returncode == 2
    assert run("--version").returncode == 0


def test_a_closed_output_pipe_exits_one_quietly() -> None:
    command = [sys.executable, "-m", "lvbitpack", "unpack", "-1", "--type", "i64"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=_ENV)
    assert process.stdout is not None and process.stderr is not None
    process.stdout.close()  # the reader goes away before the answer is written
    error = process.stderr.read()
    process.stderr.close()
    assert process.wait(timeout=60) == 1
    assert b"Traceback" not in error


def test_help_to_a_closed_pipe_does_not_crash() -> None:
    command = [sys.executable, "-m", "lvbitpack", "--help"]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=_ENV)
    assert process.stdout is not None and process.stderr is not None
    process.stdout.close()
    error = process.stderr.read()
    process.stderr.close()
    assert process.wait(timeout=60) in (0, 1)
    assert b"Traceback" not in error
