"""The documentation is executable: docstrings, README and GUIDE examples all run."""

from __future__ import annotations

import doctest
import importlib
import inspect
import pkgutil
import re
import shlex
import typing
from pathlib import Path

import pytest

import lvbitpack
from lvbitpack._cli import main

_ROOT = Path(__file__).resolve().parents[1]
_README = (_ROOT / "README.md").read_text(encoding="utf-8")
_GUIDE = (_ROOT / "GUIDE.md").read_text(encoding="utf-8")
_MODULES = ["lvbitpack"] + [
    f"lvbitpack.{m.name}" for m in pkgutil.iter_modules(lvbitpack.__path__) if m.name != "__main__"
]
_CALLABLES = [n for n in lvbitpack.__all__ if callable(getattr(lvbitpack, n))]


@pytest.mark.parametrize("name", _MODULES)
def test_module_doctests_pass(name: str) -> None:
    assert doctest.testmod(importlib.import_module(name)).failed == 0


@pytest.mark.parametrize("name", _CALLABLES)
def test_every_public_callable_has_an_example(name: str) -> None:
    assert ">>>" in (getattr(lvbitpack, name).__doc__ or ""), name


@pytest.mark.parametrize(
    "name", [n for n, _ in inspect.getmembers(lvbitpack.IntType) if not n.startswith("_")]
)
def test_every_public_member_of_int_type_has_an_example(name: str) -> None:
    member = inspect.getattr_static(lvbitpack.IntType, name)
    if isinstance(member, (property, classmethod)) or inspect.isfunction(member):
        function = member.fget if isinstance(member, property) else member
        assert ">>>" in (getattr(function, "__doc__", None) or ""), name


def test_the_doctests_mention_every_public_name() -> None:
    finder = doctest.DocTestFinder()
    examples = "".join(
        example.source
        for module in _MODULES
        for test in finder.find(importlib.import_module(module))
        for example in test.examples
    )
    for name in lvbitpack.__all__:
        assert re.search(rf"\b{name}\b", examples), name


@pytest.mark.parametrize("name", _CALLABLES)
def test_type_hints_resolve_at_run_time(name: str) -> None:
    target = getattr(lvbitpack, name)
    if inspect.isclass(target):
        for member in vars(target).values():
            function = member.fget if isinstance(member, property) else member
            if isinstance(function, classmethod):
                function = function.__func__
            if inspect.isfunction(function):
                typing.get_type_hints(function)
    else:
        typing.get_type_hints(target)


@pytest.mark.parametrize("block", re.findall(r"```python\n(.*?)```", _README, re.S))
def test_readme_examples_run(block: str) -> None:
    exec(compile(block, "README.md", "exec"), {})


def test_guide_examples_run_and_print_what_they_show() -> None:
    blocks = re.findall(r"```pycon\n(.*?)```", _GUIDE, re.S)
    assert len(blocks) >= 7
    parser, runner = doctest.DocTestParser(), doctest.DocTestRunner()
    for number, block in enumerate(blocks):
        runner.run(parser.get_doctest(block, {}, f"GUIDE.md[{number}]", "GUIDE.md", 0))
    assert runner.summarize(verbose=False).failed == 0


def _transcript(text: str) -> list[tuple[list[str], list[str]]]:
    shell = re.search(r"## Command line\n.*?```\n(.*?)```", text, re.S)
    assert shell is not None
    runs: list[tuple[list[str], list[str]]] = []
    for line in shell.group(1).splitlines():
        if line.startswith("$ lvbitpack "):
            runs.append((shlex.split(line)[2:], []))
        else:
            runs[-1][1].append(line)
    return runs


@pytest.mark.parametrize(("args", "expected"), _transcript(_README) + _transcript(_GUIDE))
def test_command_line_transcripts_match(
    capsys: pytest.CaptureFixture[str], args: list[str], expected: list[str]
) -> None:
    assert main(args) == 0
    assert capsys.readouterr().out.splitlines() == expected
