"""Contracts found missing by an independent mutation round: the command line."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from lvbitpack._cli import main
from lvbitpack._cli_io import write

_SRC = str(Path(__file__).resolve().parents[1] / "src")


def run(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    code = main(list(args))
    out, err = capsys.readouterr()
    return code, out, err


def test_numbers_of_exactly_one_hundred_characters_are_read(
    capsys: pytest.CaptureFixture[str],
) -> None:
    hundred = "0x" + "0" * 97 + "1"
    assert run(capsys, "unpack", hundred, "-t", "u8") == (0, "10000000\n", "")
    code, out, err = run(capsys, "unpack", "0" + hundred, "-t", "u8")
    assert (code, out) == (1, "") and "101 characters; at most 100" in err


def test_unflatten_ignores_underscores_and_surrounding_space(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert run(capsys, "unflatten", "0000_0002_01_00") == (0, "10\n", "")
    assert run(capsys, "unflatten", " 0x0000000101 ") == (0, "1\n", "")


def test_an_unknown_type_is_quoted_as_typed(capsys: pytest.CaptureFixture[str]) -> None:
    for command in (("pack", "01"), ("unpack", "1")):
        code, _, err = run(capsys, *command, "-t", " x12 ")
        assert code == 2 and "unknown integer type ' x12 '" in err


@pytest.mark.parametrize("size", [301, 1000, 2999])
def test_every_long_usage_error_is_cut(capsys: pytest.CaptureFixture[str], size: int) -> None:
    code, _, err = run(capsys, "pack", "01", "-t", "u8", "-s", "x" * size)
    assert code == 2 and "x" * 300 not in err and len(err) < 700


class _GoneReader:
    """A stream whose reader went away; fileno is a real pipe so silencing can be observed."""

    def __init__(self, fd: int, *, fail_write: bool, fail_flush: bool) -> None:
        self.fd, self.fail_write, self.fail_flush = fd, fail_write, fail_flush

    def write(self, text: str) -> int:
        if self.fail_write:
            raise BrokenPipeError
        return len(text)

    def flush(self) -> None:
        if self.fail_flush:
            raise BrokenPipeError

    def fileno(self) -> int:
        return self.fd


def _was_silenced(read_end: int, write_end: int) -> bool:
    """True when write_end no longer feeds the pipe (it was pointed at the null device)."""
    os.write(write_end, b"x")
    os.close(write_end)
    try:
        return os.read(read_end, 1) == b""
    finally:
        os.close(read_end)


@pytest.mark.parametrize("args", [["--version"], ["--help"], ["pack", "--help"]])
def test_help_or_version_that_cannot_be_written_exits_one(
    monkeypatch: pytest.MonkeyPatch, args: list[str]
) -> None:
    read_end, write_end = os.pipe()
    monkeypatch.setattr(sys, "stdout", _GoneReader(write_end, fail_write=True, fail_flush=True))
    assert main(args) == 1
    assert _was_silenced(read_end, write_end)


def test_a_failed_answer_write_silences_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    read_end, write_end = os.pipe()
    monkeypatch.setattr(sys, "stdout", _GoneReader(write_end, fail_write=True, fail_flush=False))
    assert main(["pack", "01", "-t", "u8"]) == 1
    assert _was_silenced(read_end, write_end)


def test_write_reports_and_silences_a_gone_reader(monkeypatch: pytest.MonkeyPatch) -> None:
    read_end, write_end = os.pipe()
    monkeypatch.setattr(sys, "stderr", _GoneReader(write_end, fail_write=True, fail_flush=False))
    assert write("stderr", "x") is False
    assert _was_silenced(read_end, write_end)


def test_finish_silences_a_stream_whose_flush_fails(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    read_end, write_end = os.pipe()
    monkeypatch.setattr(sys, "stdout", _GoneReader(write_end, fail_write=False, fail_flush=True))
    assert main(["pack", "2", "-t", "u8"]) == 1  # a data error: stdout is only flushed
    assert _was_silenced(read_end, write_end)


def test_a_descriptor_closed_under_the_cli_ends_quietly() -> None:
    code = (
        "import os, sys; os.close(1); from lvbitpack._cli import main; "
        "raise SystemExit(main(['pack', '01', '-t', 'u8']))"
    )
    env = {**os.environ, "PYTHONPATH": _SRC, "PYTHONIOENCODING": "utf-8"}
    done = subprocess.run(
        [sys.executable, "-c", code],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    assert (done.returncode, done.stderr) == (1, "")
