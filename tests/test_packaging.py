"""Packaging promises: metadata, links, changelog, file sizes and the house rules."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import pytest

import lvbitpack

_ROOT = Path(__file__).resolve().parents[1]
needs_tomllib = pytest.mark.skipif(sys.version_info < (3, 11), reason="tomllib is 3.11+")


def _project() -> dict[str, Any]:
    if sys.version_info >= (3, 11):
        import tomllib

        data = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        project: dict[str, Any] = data["project"]
        return project
    raise AssertionError("tomllib is 3.11+")


@needs_tomllib
def test_metadata_is_stable_and_dependency_free() -> None:
    project = _project()
    assert project["version"] == lvbitpack.__version__ == "1.0.0"
    assert project["dependencies"] == []
    assert project["requires-python"] == ">=3.10"
    classifiers = project["classifiers"]
    assert "Development Status :: 5 - Production/Stable" in classifiers
    minors = [
        c for c in classifiers if re.fullmatch(r"Programming Language :: Python :: 3\.\d+", c)
    ]
    assert [c.rsplit(".", 1)[1] for c in minors] == ["10", "11", "12", "13", "14"]
    assert {"Homepage", "Source", "Issues", "Changelog"} <= set(project["urls"])
    assert project["license"] == "MIT" and project["keywords"]
    assert project["scripts"] == {"lvbitpack": "lvbitpack._cli:main"}


def test_readme_links_are_absolute_and_reach_the_guide_and_changelog() -> None:
    readme = (_ROOT / "README.md").read_text(encoding="utf-8")
    links = re.findall(r"\]\(([^)]+)\)", readme)
    assert links and all(link.startswith("https://") for link in links)
    assert "https://github.com/JaviLianes8/lvbitpack/blob/main/GUIDE.md" in links
    assert "https://github.com/JaviLianes8/lvbitpack/blob/main/CHANGELOG.md" in links


def test_changelog_has_a_dated_section_for_this_version() -> None:
    changelog = (_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    pattern = rf"^## \[{re.escape(lvbitpack.__version__)}\] - \d{{4}}-\d{{2}}-\d{{2}}$"
    assert re.search(pattern, changelog, re.M)


def _tracked_text_files() -> list[Path]:
    patterns = ("*.py", "*.md", "*.toml", "*.ps1", "*.json", "*.txt")
    found = [p for pattern in patterns for p in _ROOT.rglob(pattern)]
    skip = {".venv", ".git", "build", "dist", ".mypy_cache", ".pytest_cache", ".ruff_cache"}
    return [p for p in found if not skip & set(p.relative_to(_ROOT).parts)]


def test_no_source_file_exceeds_two_hundred_lines() -> None:
    for path in [*(_ROOT / "src").rglob("*.py"), *(_ROOT / "tests").rglob("*.py")]:
        assert len(path.read_text(encoding="utf-8").splitlines()) <= 200, path


def test_no_long_dash_anywhere() -> None:
    dash = chr(0x2014)
    for path in _tracked_text_files():
        assert dash not in path.read_text(encoding="utf-8", errors="replace"), path
