"""Contracts found missing by an independent mutation round: library functions."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

import lvbitpack._flatten as flatten_module
from lvbitpack import (
    I8,
    U8,
    U16,
    BitpackError,
    IntType,
    bools_to_bytes,
    bools_to_number,
    bytes_to_bools,
    bytes_to_number,
    number_to_bools,
    number_to_bytes,
    pack_bools,
    pack_flattened,
    unpack_bools,
)


class _EqualsEverything:
    """Compares equal to anything, like a hostile or careless str stand-in."""

    def __eq__(self, other: object) -> bool:
        return True

    __hash__ = object.__hash__


def test_contains_refuses_booleans() -> None:
    assert not U8.contains(True) and not U8.contains(False)
    assert not I8.contains(True) and not I8.contains(False)


@pytest.mark.parametrize("bits", [0, 1, 4, 7, 9, 12, 24, 48, 63, 65, 96, 128, 256, -8])
def test_only_the_four_labview_widths_exist(bits: int) -> None:
    with pytest.raises(BitpackError, match="bits must be 8, 16, 32 or 64"):
        IntType(bits, False)


def test_integers_up_to_128_bits_are_quoted_and_longer_ones_described() -> None:
    edge = (1 << 128) - 1
    with pytest.raises(BitpackError) as caught:
        number_to_bools(edge, U8)
    assert str(caught.value).startswith(f"{edge} is out of range")
    with pytest.raises(BitpackError) as caught:
        number_to_bools(1 << 128, U8)
    assert str(caught.value).startswith("an integer of 129 bits is out of range")


def test_a_quoted_value_is_cut_only_beyond_forty_characters() -> None:
    fits = "a" * 38  # repr is exactly 40 characters
    with pytest.raises(BitpackError) as caught:
        bools_to_number([fits], U8)  # type: ignore[list-item]
    assert str(caught.value).endswith(f"not {fits!r}")
    longer = "a" * 39  # repr is 41 characters
    with pytest.raises(BitpackError) as caught:
        bools_to_number([longer], U8)  # type: ignore[list-item]
    assert str(caught.value).endswith(f"not {repr(longer)[:40]}...")


def _fake_bool(module: str, truth: bool) -> object:
    kind = type("bool_", (), {"__module__": module, "__bool__": lambda self: truth})
    return kind()


def test_numpy_booleans_are_recognised_without_numpy_installed() -> None:
    array = [_fake_bool("numpy", True), _fake_bool("numpy", False), _fake_bool("numpy", True)]
    assert bools_to_number(array, U8) == 0b101  # type: ignore[arg-type]


def test_a_class_named_bool_outside_numpy_is_not_a_boolean() -> None:
    with pytest.raises(BitpackError, match="element 0 must be a boolean"):
        bools_to_number([_fake_bool("elsewhere", True)], U8)  # type: ignore[list-item]


def test_a_non_contiguous_memoryview_is_read_as_its_bytes() -> None:
    strided = memoryview(b"\x01\xee\x02\xee")[::2]
    assert bytes_to_number(strided, U16) == 0x0102
    assert bytes_to_bools(strided, U16)[:2] == [False, True]
    assert unpack_bools(strided, 16) == unpack_bools(b"\x01\x02", 16)


def test_byteorder_must_really_be_a_string() -> None:
    for call in (
        lambda: number_to_bytes(1, U8, byteorder=_EqualsEverything()),  # type: ignore[arg-type]
        lambda: bytes_to_number(b"\x01", U8, byteorder=_EqualsEverything()),  # type: ignore[arg-type]
    ):
        with pytest.raises(BitpackError, match="byteorder must be 'big' or 'little'"):
            call()


def test_bit_order_must_really_be_a_string() -> None:
    with pytest.raises(BitpackError, match="bit_order must be 'msb' or 'lsb'"):
        pack_bools([True], bit_order=_EqualsEverything())  # type: ignore[arg-type]
    with pytest.raises(BitpackError, match="bit_order must be 'msb' or 'lsb'"):
        unpack_bools(b"\x01", bit_order=_EqualsEverything())  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", ["u8", 8, None, 8.0])
def test_bytes_functions_refuse_a_non_inttype(bad: object) -> None:
    with pytest.raises(BitpackError, match="int_type must be an IntType"):
        bytes_to_number(b"\x00", bad)  # type: ignore[arg-type]
    with pytest.raises(BitpackError, match="int_type must be an IntType"):
        bytes_to_bools(b"\x00", bad)  # type: ignore[arg-type]


def _exploding() -> Iterator[bool]:
    raise AssertionError("the array was read before the arguments were checked")
    yield True  # pragma: no cover


def test_bools_to_bytes_checks_its_arguments_before_reading_the_array() -> None:
    with pytest.raises(BitpackError, match="byteorder must be"):
        bools_to_bytes(_exploding(), U8, byteorder="middle")  # type: ignore[arg-type]
    with pytest.raises(BitpackError, match="int_type must be"):
        bools_to_bytes(_exploding(), "u8")  # type: ignore[arg-type]


class _Sized:
    """Stands in for a Boolean list of a given length without allocating it."""

    def __init__(self, length: int) -> None:
        self.length = length

    def __len__(self) -> int:
        return self.length

    def __bytes__(self) -> bytes:
        return b""


def test_flatten_count_limit_is_the_i32_maximum(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(flatten_module, "as_bools", lambda values: _Sized(0x7FFFFFFF))
    assert pack_flattened([]) == b"\x7f\xff\xff\xff"
    monkeypatch.setattr(flatten_module, "as_bools", lambda values: _Sized(0x80000000))
    with pytest.raises(BitpackError, match="at most 2147483647 elements"):
        pack_flattened([])
