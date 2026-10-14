"""Contracts from the second adversarial round: mocks, metaclasses, enum lookups, argv."""

from __future__ import annotations

import pickle
from collections.abc import Iterator
from typing import Any
from unittest import mock

import pytest

from lvbitpack import (
    I8,
    U8,
    BitpackError,
    IntType,
    SignExtension,
    bools_to_number,
    bytes_to_number,
    number_to_bools,
    number_to_bytes,
    pack_bools,
    pack_flattened,
)
from lvbitpack._cli import main


class Hostile:
    def __repr__(self) -> str:
        raise RuntimeError("hostile")

    def __hash__(self) -> int:
        raise RuntimeError("hostile")


@pytest.mark.parametrize(
    "value", [10**5000, Hostile(), None, "ALWAYS", [1], b"never"], ids=lambda v: type(v).__name__
)
def test_any_unknown_sign_extension_value_is_a_bitpack_error(value: object) -> None:
    with pytest.raises(BitpackError, match="no sign extension mode"):
        SignExtension(value)


def test_sign_extension_lookups_that_work() -> None:
    class Text(str):
        def __eq__(self, other: object) -> bool:
            raise RuntimeError("hostile")

        __hash__ = str.__hash__

    assert SignExtension(Text("never")) is SignExtension.NEVER
    assert SignExtension(SignExtension.ALWAYS) is SignExtension.ALWAYS
    for mode in SignExtension:
        assert pickle.loads(pickle.dumps(mode)) is mode


def test_mocks_with_a_spec_are_refused_cleanly() -> None:
    with pytest.raises(BitpackError, match="byteorder must be"):
        number_to_bytes(1, U8, byteorder=mock.Mock(spec=str))
    with pytest.raises(BitpackError, match="bit_order must be"):
        pack_bools([True], bit_order=mock.Mock(spec=str))
    with pytest.raises(BitpackError, match="must be str"):
        IntType.parse(mock.Mock(spec=str))
    for call in (
        lambda: number_to_bytes(1, mock.Mock(spec=IntType)),
        lambda: bools_to_number([True], mock.Mock(spec=IntType)),
        lambda: bytes_to_number(b"\x01", mock.Mock(spec=IntType)),
        lambda: number_to_bools(1, mock.Mock(spec=IntType)),
    ):
        with pytest.raises(BitpackError, match="int_type must be an IntType"):
            call()
    for array_call in (pack_flattened, pack_bools, lambda v: bools_to_number(v, U8)):
        with pytest.raises(BitpackError, match="element 0 must be a boolean"):
            array_call([mock.Mock(spec=bool)])


def test_an_int_type_subclass_cannot_change_the_rules() -> None:
    class Lenient(IntType):
        def contains(self, number: object) -> bool:
            return True

    lenient = Lenient(8, False)
    with pytest.raises(BitpackError, match="out of range for u8"):
        number_to_bytes(10**30, lenient)
    assert bools_to_number([True] * 8, lenient) == 255


def test_contains_never_raises() -> None:
    numpy = pytest.importorskip("numpy")
    assert not I8.contains(numpy.array([1, 2]))
    assert not I8.contains(numpy.array(1.5))
    assert not I8.contains(Hostile())


def test_object_buffers_and_odd_formats_are_refused_with_a_clear_message() -> None:
    numpy = pytest.importorskip("numpy")
    with pytest.raises(BitpackError, match="holds Python objects"):
        bytes_to_number(numpy.array([object()], dtype=object), U8)
    dates = numpy.array(["2020-01-01"], dtype="datetime64[D]")
    with pytest.raises(BitpackError, match=r"cannot be read as bytes \(ndarray\)"):
        bytes_to_number(dates, U8)


class _Meta(type):
    @property
    def __name__(cls) -> str:  # type: ignore[override]
        raise RuntimeError("hostile")


def test_a_metaclass_cannot_break_the_messages() -> None:
    odd = _Meta("Odd", (), {})()
    with pytest.raises(BitpackError, match="element 0 must be a boolean"):
        bools_to_number([odd], U8)
    with pytest.raises(BitpackError, match="must be a bytes-like object, not Odd"):
        bytes_to_number(odd, U8)


def test_a_type_error_while_iterating_passes_through() -> None:
    def broken() -> Iterator[bool]:
        yield True
        raise TypeError("from the caller")

    with pytest.raises(TypeError, match="from the caller"):
        bools_to_number(broken(), U8)


def test_byte_counts_read_naturally() -> None:
    with pytest.raises(BitpackError, match="u8 needs exactly 1 byte, got 2"):
        bytes_to_number(b"\x00\x00", U8)
    with pytest.raises(BitpackError, match="a byte string is not a Boolean array"):
        bools_to_number(b"\x01", U8)


def test_usage_errors_never_echo_control_characters(capsys: pytest.CaptureFixture[Any]) -> None:
    assert main(["pack", "01", "-t", "u8", "-s", "\x1b]0;title\x07é"]) == 2
    err = capsys.readouterr().err
    assert "\x1b" not in err and "\x07" not in err and err.isascii()
    assert "\\x1b" in err
