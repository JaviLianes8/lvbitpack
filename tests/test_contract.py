"""The public contract: the exact surface, and the whole promise of every public name."""

from __future__ import annotations

import dataclasses
import importlib.resources
import inspect
from collections.abc import Callable
from typing import Literal

import pytest

import lvbitpack
from lvbitpack import (
    I8,
    I16,
    I32,
    I64,
    U8,
    U16,
    U32,
    U64,
    BitpackError,
    IntType,
    SignExtension,
    bools_to_bytes,
    bools_to_number,
    bytes_to_bools,
    bytes_to_number,
    number_to_bools,
    number_to_bytes,
    pack_bools,
    pack_flattened,
    unpack_bools,
    unpack_flattened,
)

ORDERS: tuple[Literal["big"], Literal["little"]] = ("big", "little")
BIT_ORDERS: tuple[Literal["msb"], Literal["lsb"]] = ("msb", "lsb")

PUBLIC_API = [
    "BitpackError",
    "I8",
    "I16",
    "I32",
    "I64",
    "IntType",
    "SignExtension",
    "U8",
    "U16",
    "U32",
    "U64",
    "bools_to_bytes",
    "bools_to_number",
    "bytes_to_bools",
    "bytes_to_number",
    "number_to_bools",
    "number_to_bytes",
    "pack_bools",
    "pack_flattened",
    "unpack_bools",
    "unpack_flattened",
]


def test_all_lists_exactly_the_public_api() -> None:
    assert sorted(lvbitpack.__all__) == sorted(PUBLIC_API)
    public = {name for name in vars(lvbitpack) if not name.startswith("_")}
    modules = {name for name in public if inspect.ismodule(getattr(lvbitpack, name))}
    assert public - modules == set(PUBLIC_API)


def test_version_and_type_information() -> None:
    assert lvbitpack.__version__ == "1.0.0"
    assert importlib.resources.files("lvbitpack").joinpath("py.typed").is_file()


def test_public_classes_keep_their_real_module_for_source_lookup() -> None:
    for cls in (BitpackError, IntType, SignExtension):
        assert cls.__module__.startswith("lvbitpack._")  # its real module, for getsource
        source = inspect.getsource(cls).splitlines()
        assert any(line.startswith(f"class {cls.__name__}") for line in source[:2])


def test_signatures_are_the_stable_ones() -> None:
    def shape(function: Callable[..., object]) -> list[tuple[str, str, object]]:
        params = inspect.signature(function).parameters.values()
        return [(p.name, p.kind.name, p.default) for p in params]

    empty = inspect.Parameter.empty
    mode = SignExtension.IF_SIGNED
    assert shape(bools_to_number) == [
        ("values", "POSITIONAL_OR_KEYWORD", empty),
        ("int_type", "POSITIONAL_OR_KEYWORD", empty),
        ("sign_extension", "KEYWORD_ONLY", mode),
    ]
    assert shape(number_to_bools) == [
        ("number", "POSITIONAL_OR_KEYWORD", empty),
        ("int_type", "POSITIONAL_OR_KEYWORD", empty),
    ]
    order = ("byteorder", "KEYWORD_ONLY", "big")
    assert shape(number_to_bytes)[-1] == order and shape(bytes_to_number)[-1] == order
    assert shape(bools_to_bytes)[-2:] == [("sign_extension", "KEYWORD_ONLY", mode), order]
    assert shape(bytes_to_bools)[-1] == order
    assert shape(pack_bools) == [
        ("values", "POSITIONAL_OR_KEYWORD", empty),
        ("bit_order", "KEYWORD_ONLY", "msb"),
    ]
    assert shape(unpack_bools) == [
        ("data", "POSITIONAL_OR_KEYWORD", empty),
        ("count", "POSITIONAL_OR_KEYWORD", None),
        ("bit_order", "KEYWORD_ONLY", "msb"),
    ]
    assert shape(pack_flattened) == [("values", "POSITIONAL_OR_KEYWORD", empty)]
    assert shape(unpack_flattened) == [("data", "POSITIONAL_OR_KEYWORD", empty)]


def test_presets_are_the_eight_labview_integers() -> None:
    presets = [U8, U16, U32, U64, I8, I16, I32, I64]
    assert [(t.bits, t.signed, t.name) for t in presets] == [
        (8, False, "u8"),
        (16, False, "u16"),
        (32, False, "u32"),
        (64, False, "u64"),
        (8, True, "i8"),
        (16, True, "i16"),
        (32, True, "i32"),
        (64, True, "i64"),
    ]
    for t in presets:
        assert (t.min, t.max, t.mask) == (
            -(2 ** (t.bits - 1)) if t.signed else 0,
            2 ** (t.bits - 1) - 1 if t.signed else 2**t.bits - 1,
            2**t.bits - 1,
        )
        assert IntType.parse(t.name.upper()) == t
        assert hash(IntType(t.bits, t.signed)) == hash(t)
    assert [f.name for f in dataclasses.fields(IntType)] == ["bits", "signed"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        U8.bits = 16  # type: ignore[misc]


def test_sign_extension_has_exactly_labviews_three_modes() -> None:
    assert [(m.name, m.value) for m in SignExtension] == [
        ("NEVER", "never"),
        ("IF_SIGNED", "if_signed"),
        ("ALWAYS", "always"),
    ]


def test_the_error_type_is_a_value_error() -> None:
    assert issubclass(BitpackError, ValueError)
    with pytest.raises(BitpackError):
        number_to_bools(256, U8)


def test_every_public_function_round_trips() -> None:
    array = [True, False, True, True, False, False, True]
    for int_type in (U8, U16, U32, U64, I8, I16, I32, I64):
        for number in (int_type.min, -1 if int_type.signed else 1, 0, int_type.max):
            bits = number_to_bools(number, int_type)
            assert len(bits) == int_type.bits
            assert bools_to_number(bits, int_type) == number
            for order in ORDERS:
                data = number_to_bytes(number, int_type, byteorder=order)
                assert bytes_to_number(data, int_type, byteorder=order) == number
                assert bytes_to_bools(data, int_type, byteorder=order) == bits
                assert bools_to_bytes(bits, int_type, byteorder=order) == data
    for bit_order in BIT_ORDERS:
        packed = pack_bools(array, bit_order=bit_order)
        assert unpack_bools(packed, len(array), bit_order=bit_order) == array
    assert unpack_flattened(pack_flattened(array)) == array
