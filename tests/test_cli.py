"""The command line, run in process: every help example, every error path, exit codes."""

from __future__ import annotations

import re
import shlex

import pytest

import lvbitpack
from lvbitpack._cli import _EXAMPLES, main


def run(capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str, str]:
    code = main(list(args))
    out, err = capsys.readouterr()
    return code, out, err


def _help_examples() -> list[tuple[list[str], str]]:
    found = re.findall(r"^  lvbitpack (.+?)\s+-> (\S+)$", _EXAMPLES, re.M)
    return [(shlex.split(command), result) for command, result in found]


def test_the_help_lists_nine_examples() -> None:
    assert len(_help_examples()) == 9


@pytest.mark.parametrize(("args", "expected"), _help_examples())
def test_every_help_example_prints_what_it_claims(
    capsys: pytest.CaptureFixture[str], args: list[str], expected: str
) -> None:
    assert run(capsys, *args) == (0, expected + "\n", "")


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    assert run(capsys, "--version") == (0, f"lvbitpack {lvbitpack.__version__}\n", "")


def test_help_shows_the_examples(capsys: pytest.CaptureFixture[str]) -> None:
    code, out, _ = run(capsys, "--help")
    assert code == 0 and "examples:" in out and "Flatten To String" in out


@pytest.mark.parametrize(
    ("args", "expected"),
    [
        (["pack", "", "--type", "u8"], "0"),
        (["pack", "1,0 1_1", "-t", "U16"], "13"),
        (["pack", "tFtT", "-t", "i8", "-s", "never"], "13"),
        (["pack", "1", "-t", "u64", "-s", "always", "--base", "hex"], "0xffffffffffffffff"),
        (["pack", "0" * 63 + "1", "-t", "i64"], str(-(2**63))),
        (["unpack", "0x80", "-t", "u8"], "00000001"),
        (["unpack", "0b11", "-t", "i16"], "1100000000000000"),
        (["unpack", "-1", "-t", "i32"], "1" * 32),
        (["flatten", ""], "00000000"),
        (["unflatten", "0x00000002 ff00"], "10"),
    ],
)
def test_commands(capsys: pytest.CaptureFixture[str], args: list[str], expected: str) -> None:
    assert run(capsys, *args) == (0, expected + "\n", "")


@pytest.mark.parametrize(
    ("args", "message"),
    [
        (["pack", "012", "--type", "u8"], "character 2 is '2'"),
        (["unpack", "256", "--type", "u8"], "256 is out of range for u8 [0, 255]"),
        (["unpack", "1.5", "--type", "u8"], "not an integer: '1.5'"),
        (["unpack", "9" * 101, "--type", "u64"], "101 characters"),
        (["unflatten", "zz"], "not valid hex: 'zz'"),
        (["unflatten", "00000002 01"], "says 2 elements but only 1 byte follows"),
        (["unflatten", "ffffffff"], "count is negative"),
    ],
)
def test_data_errors_go_to_stderr_with_exit_one(
    capsys: pytest.CaptureFixture[str], args: list[str], message: str
) -> None:
    code, out, err = run(capsys, *args)
    assert (code, out) == (1, "")
    assert err.startswith("lvbitpack: error: ") and message in err


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["frobnicate"],
        ["pack", "01"],
        ["pack", "01", "--type", "u8", "-s", "sometimes"],
        ["pack", "01", "--type", "u8", "--base", "oct"],
        ["unflatten"],
        ["pack", "01", "--type", "f64"],
        ["unpack", "1", "--type", "u12"],
    ],
)
def test_usage_errors_exit_two(capsys: pytest.CaptureFixture[str], args: list[str]) -> None:
    code, out, err = run(capsys, *args)
    assert (code, out) == (2, "")
    assert "usage: lvbitpack" in err


def test_a_huge_bad_argument_is_not_echoed(capsys: pytest.CaptureFixture[str]) -> None:
    code, _, err = run(capsys, "pack", "01", "--type", "u8", "-s", "x" * 100_000)
    assert code == 2 and len(err) < 1000
    code, _, err = run(capsys, "pack", "2" * 100_000, "--type", "u8")
    assert code == 1 and len(err) < 400
    code, _, err = run(capsys, "unflatten", "z" * 100_000)
    assert code == 1 and len(err) < 400


def test_pack_and_unpack_round_trip(capsys: pytest.CaptureFixture[str]) -> None:
    for text in ("-128", "-1", "0", "1", "127"):
        code, bits, _ = run(capsys, "unpack", text, "-t", "i8")
        assert code == 0
        assert run(capsys, "pack", bits.strip(), "-t", "i8") == (0, text + "\n", "")


def test_flatten_and_unflatten_round_trip(capsys: pytest.CaptureFixture[str]) -> None:
    code, flat, _ = run(capsys, "flatten", "1101 0010 1")
    assert (code, flat) == (0, "00000009" + "010100010000010001\n")
    assert run(capsys, "unflatten", flat.strip()) == (0, "110100101\n", "")
