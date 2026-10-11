"""Real end-to-end tests: install the package and drive the installed console script.

These build a throwaway virtual environment, pip-install lvbitpack into it, and run
the real `lvbitpack` executable as a subprocess, asserting its actual stdout and exit
code. This proves the console script and [project.scripts] entry point work for real.
"""

import subprocess
import sys
import venv
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def cli(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a venv, install lvbitpack editable, return the console script path."""
    env_dir = tmp_path_factory.mktemp("lvbitpack_e2e_env")
    venv.create(env_dir, with_pip=True)
    scripts = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = scripts / ("python.exe" if sys.platform == "win32" else "python")
    subprocess.run(
        [str(python), "-m", "pip", "install", "-q", "-e", str(_PROJECT_ROOT)],
        check=True,
        capture_output=True,
    )
    executable = scripts / ("lvbitpack.exe" if sys.platform == "win32" else "lvbitpack")
    assert executable.is_file(), f"console script not installed at {executable}"
    return executable


def _run(cli: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(cli), *args], capture_output=True, text=True)


def test_version_reports_the_package_version(cli: Path) -> None:
    result = _run(cli, "--version")
    assert result.returncode == 0
    assert result.stdout.strip() == "lvbitpack 0.2.0"


def test_pack_reports_the_documented_number(cli: Path) -> None:
    result = _run(cli, "pack", "01", "--type", "u8")
    assert result.returncode == 0
    assert result.stdout.strip() == "2"


def test_pack_signed_always_mode_matches_the_vector(cli: Path) -> None:
    result = _run(cli, "pack", "0101", "--type", "i8", "--sign-extension", "always")
    assert result.returncode == 0
    assert result.stdout.strip() == "-6"


def test_pack_hex_output(cli: Path) -> None:
    result = _run(cli, "pack", "0101", "--type", "u8", "--base", "hex")
    assert result.returncode == 0
    assert result.stdout.strip() == "0xa"


def test_unpack_prints_lsb_first_bits(cli: Path) -> None:
    result = _run(cli, "unpack", "2", "--type", "u8")
    assert result.returncode == 0
    assert result.stdout.strip() == "01000000"


def test_unpack_signed_twos_complement(cli: Path) -> None:
    result = _run(cli, "unpack", "-2", "--type", "i8")
    assert result.returncode == 0
    assert result.stdout.strip() == "01111111"


def test_pack_then_unpack_round_trips_through_the_cli(cli: Path) -> None:
    packed = _run(cli, "pack", "01000000", "--type", "u8")
    assert packed.stdout.strip() == "2"
    unpacked = _run(cli, "unpack", packed.stdout.strip(), "--type", "u8")
    assert unpacked.stdout.strip() == "01000000"


def test_out_of_range_number_errors_to_stderr_with_exit_1(cli: Path) -> None:
    result = _run(cli, "unpack", "256", "--type", "u8")
    assert result.returncode == 1
    assert result.stdout == ""
    assert "out of range" in result.stderr


def test_unknown_type_errors_to_stderr_with_exit_1(cli: Path) -> None:
    result = _run(cli, "pack", "01", "--type", "f64")
    assert result.returncode == 1
    assert "unknown integer type" in result.stderr
