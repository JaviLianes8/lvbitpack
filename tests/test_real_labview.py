"""Ground truth from LabVIEW 2026 itself: every captured result is reproduced exactly.

The captures and how they were made are described in tests/fixtures/labview2026/manifest.json.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from lvbitpack import (
    U32,
    IntType,
    SignExtension,
    bools_to_number,
    number_to_bools,
    pack_flattened,
    unpack_flattened,
)

_DIR = Path(__file__).resolve().parent / "fixtures" / "labview2026"
_MANIFEST: dict[str, Any] = json.loads((_DIR / "manifest.json").read_text(encoding="utf-8"))
_BAT: list[dict[str, Any]] = json.loads(
    (_DIR / "boolean_array_to_number.json").read_text(encoding="utf-8")
)["configurations"]
_NBA: list[dict[str, Any]] = json.loads(
    (_DIR / "number_to_boolean_array.json").read_text(encoding="utf-8")
)["types"]


def _bits(text: str) -> list[bool]:
    return [char == "1" for char in text]


def test_every_fixture_matches_its_manifest() -> None:
    files = _MANIFEST["files"]
    assert sorted(files) == sorted(p.name for p in _DIR.iterdir() if p.name != "manifest.json")
    for name, entry in files.items():
        data = (_DIR / name).read_bytes()
        assert (len(data), hashlib.sha256(data).hexdigest()) == (entry["size"], entry["sha256"])


def test_the_captures_cover_every_type_and_mode() -> None:
    explicit = {(c["node_output"], c["mode"]) for c in _BAT if c["node_output"] != "default"}
    names = ["u8", "u16", "u32", "u64", "i8", "i16", "i32", "i64"]
    assert explicit == {(n, m.value) for n in names for m in SignExtension}
    assert {c["type"] for c in _NBA} == set(names)
    assert sum(len(c["rows"]) for c in _BAT) >= 2900


@pytest.mark.parametrize(
    "config", [c for c in _BAT if c["node_output"] != "default"], ids=lambda c: c["mode"]
)
def test_boolean_array_to_number_matches_labview(config: dict[str, Any]) -> None:
    int_type, mode = IntType.parse(config["node_output"]), SignExtension(config["mode"])
    for bits, number in config["rows"]:
        assert bools_to_number(_bits(bits), int_type, sign_extension=mode) == number, bits


@pytest.mark.parametrize(
    "config", [c for c in _BAT if c["node_output"] == "default"], ids=lambda c: c["mode"]
)
def test_an_unconfigured_node_outputs_u32(config: dict[str, Any]) -> None:
    # Without an explicit representation LabVIEW's node gives a U32, here read into a
    # 64-bit indicator, so the value is the U32 result unchanged.
    mode = SignExtension(config["mode"])
    for bits, number in config["rows"]:
        assert bools_to_number(_bits(bits), U32, sign_extension=mode) == number, bits


def test_labview_agrees_with_nis_table() -> None:
    lookup = {(c["node_output"], c["mode"], b): n for c in _BAT for b, n in c["rows"]}
    assert lookup[("i8", "if_signed", "01")] == -2
    assert lookup[("u8", "if_signed", "01")] == 2
    assert lookup[("i8", "always", "0101")] == -6
    assert lookup[("i8", "never", "0101")] == 10


@pytest.mark.parametrize("config", _NBA, ids=lambda c: c["type"])
def test_number_to_boolean_array_matches_labview(config: dict[str, Any]) -> None:
    int_type = IntType.parse(config["type"])
    for number, bits in config["rows"]:
        assert number_to_bools(number, int_type) == _bits(bits), number
        assert len(bits) == int_type.bits


@pytest.mark.parametrize("length", [0, 1, 8, 9, 17, 300])
def test_labviews_datalog_holds_our_flattened_array(length: int) -> None:
    inputs = json.loads(_MANIFEST["datalog_bool_len*.dat"].split("per file: ", 1)[1])
    data = (_DIR / f"datalog_bool_len{length}.dat").read_bytes()
    array = _bits(inputs[f"datalog_bool_len{length}.dat"])
    assert len(array) == length
    flat = pack_flattened(array)
    at = data.find(flat)
    assert at >= 0
    if length >= 8:
        assert data.count(flat) == 1
    assert unpack_flattened(data[at : at + 4 + length]) == array
