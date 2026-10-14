"""Real end to end: build a wheel, install it into a throwaway venv, run its ``lvbitpack``.

No imports of the command module and no mocks: every test shells out to the console script
pip generated inside a fresh virtual environment that shares nothing with the test runner.
Set ``LVBITPACK_WHEEL`` to test an already built wheel instead of building one.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import venv
import zipfile
from pathlib import Path

import pytest

import lvbitpack

_ROOT = Path(__file__).resolve().parents[1]
_LEAKY = ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "PYTHONSTARTUP")
_ENV = {key: value for key, value in os.environ.items() if key.upper() not in _LEAKY}


def _wheel(tmp_path_factory: pytest.TempPathFactory) -> Path:
    given = os.environ.get("LVBITPACK_WHEEL")
    if given:
        return Path(given)
    if not (_ROOT / "src" / "lvbitpack" / "__init__.py").is_file():
        pytest.skip("no source tree to build from; set LVBITPACK_WHEEL to a built wheel")
    wheels = tmp_path_factory.mktemp("wheels")
    build = [sys.executable, "-m", "pip", "wheel", "--quiet", "--no-deps"]
    if importlib.util.find_spec("hatchling") is not None:
        build.append("--no-build-isolation")
    subprocess.run([*build, "-w", str(wheels), str(_ROOT)], check=True, timeout=600, env=_ENV)
    (wheel,) = wheels.glob("lvbitpack-*.whl")
    return wheel


@pytest.fixture(scope="module")
def env(tmp_path_factory: pytest.TempPathFactory) -> tuple[str, str]:
    wheel = _wheel(tmp_path_factory)
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
    assert "lvbitpack/__init__.py" in names and "lvbitpack/py.typed" in names
    env_dir = tmp_path_factory.mktemp("venv")
    venv.EnvBuilder(with_pip=True).create(env_dir)
    scripts = env_dir / ("Scripts" if os.name == "nt" else "bin")
    python = str(scripts / "python")
    install = [python, "-m", "pip", "install", "--quiet", "--no-index", "--no-deps"]
    subprocess.run([*install, str(wheel)], check=True, timeout=600, env=_ENV)
    where = [python, "-c", "import lvbitpack; print(lvbitpack.__file__)"]
    location = subprocess.run(
        where, check=True, capture_output=True, text=True, cwd=env_dir, env=_ENV
    )
    assert Path(location.stdout.strip()).resolve().is_relative_to(env_dir.resolve())
    found = shutil.which("lvbitpack", path=str(scripts))
    assert found is not None, "pip did not install the lvbitpack console script"
    return found, python


def _run(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=60, env=_ENV, cwd=cwd)


def test_version_comes_from_the_installed_package(env: tuple[str, str]) -> None:
    result = _run([env[0], "--version"])
    assert (result.returncode, result.stdout.strip()) == (0, f"lvbitpack {lvbitpack.__version__}")


def test_the_executable_reproduces_nis_table(env: tuple[str, str]) -> None:
    rows = [
        (["01", "-t", "i8"], "-2"),
        (["01", "-t", "u8"], "2"),
        (["0101", "-t", "i8", "-s", "always"], "-6"),
        (["0101", "-t", "i8", "-s", "never"], "10"),
        (["00101", "-t", "u8"], "20"),
        (["00101", "-t", "u8", "-s", "always"], "244"),
    ]
    for args, expected in rows:
        result = _run([env[0], "pack", *args])
        assert (result.returncode, result.stdout.strip()) == (0, expected)


def test_unpack_flatten_and_unflatten(env: tuple[str, str]) -> None:
    assert _run([env[0], "unpack", "-2", "-t", "i8"]).stdout == "01111111\n"
    assert _run([env[0], "flatten", "1011"]).stdout == "0000000401000101\n"
    assert _run([env[0], "unflatten", "0000000401000101"]).stdout == "1011\n"


def test_errors_exit_one_on_stderr_and_bad_usage_exits_two(env: tuple[str, str]) -> None:
    bad = _run([env[0], "unpack", "256", "-t", "u8"])
    assert (bad.returncode, bad.stdout) == (1, "")
    assert bad.stderr.startswith("lvbitpack: error: ")
    assert _run([env[0], "frobnicate"]).returncode == 2


def test_an_outside_consumer_uses_the_api(env: tuple[str, str], tmp_path: Path) -> None:
    code = (
        "from lvbitpack import I8, BitpackError, bools_to_number, pack_flattened\n"
        "assert bools_to_number([False, True], I8) == -2\n"
        "assert pack_flattened([True]).hex() == '0000000101'\n"
        "try:\n    bools_to_number('01', I8)\nexcept BitpackError:\n    print('ok')\n"
    )
    result = _run([env[1], "-c", code], cwd=tmp_path)
    assert (result.returncode, result.stdout.strip()) == (0, "ok")
    module = _run([env[1], "-m", "lvbitpack", "pack", "1", "-t", "i8"], cwd=tmp_path)
    assert module.stdout.strip() == "-1"
