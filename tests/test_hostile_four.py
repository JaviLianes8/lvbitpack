"""Contracts from the third adversarial round: lying classes, argv numbers, printable text."""

from __future__ import annotations

from collections.abc import Callable
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
    pack_flattened,
    unpack_bools,
)
from lvbitpack._cli import main


class LyingClass:
    @property  # type: ignore[misc]
    def __class__(self) -> type:
        raise ZeroDivisionError("hostile")


class IndexMeta(type):
    def __getattribute__(cls, name: str) -> Any:
        if name == "__index__":
            raise RuntimeError("hostile")
        return super().__getattribute__(name)


def test_an_object_lying_about_its_class_is_refused_cleanly() -> None:
    liar = LyingClass()
    calls: list[Callable[[], object]] = [
        lambda: number_to_bools(liar, U8),  # type: ignore[arg-type]
        lambda: number_to_bytes(liar, U8),  # type: ignore[arg-type]
        lambda: unpack_bools(b"\x00", liar),  # type: ignore[arg-type]
        lambda: bools_to_number(liar, U8),  # type: ignore[arg-type]
        lambda: pack_flattened(liar),  # type: ignore[arg-type]
        lambda: bytes_to_number(liar, U8),  # type: ignore[arg-type]
        lambda: bools_to_number([True], U8, sign_extension=liar),  # type: ignore[arg-type]
        lambda: IntType(8, liar),  # type: ignore[arg-type]
    ]
    for call in calls:
        with pytest.raises(BitpackError):
            call()
    assert not U8.contains(liar)


def test_contains_survives_a_hostile_metaclass() -> None:
    assert not U8.contains(IndexMeta("Odd", (), {})())


def test_an_uninitialised_int_type_is_refused() -> None:
    for kind in (IntType, type("Sub", (IntType,), {})):
        with pytest.raises(BitpackError, match="never initialised"):
            number_to_bools(1, object.__new__(kind))


def test_sign_extension_takes_exactly_one_value() -> None:
    with pytest.raises(BitpackError, match="exactly one value"):
        SignExtension(10**10000, None)  # type: ignore[call-arg]


def test_signed_must_really_be_a_bool() -> None:
    with pytest.raises(BitpackError, match="signed must be a bool"):
        IntType(8, mock.Mock(spec=bool))
    numpy = pytest.importorskip("numpy")
    made = IntType(8, numpy.bool_(True))
    assert made == I8 and type(made.signed) is bool


def test_a_fake_numpy_boolean_is_not_one() -> None:
    fake = type("bool_", (), {"__module__": "numpyx", "__bool__": lambda self: True})()
    with pytest.raises(BitpackError, match="element 0 must be a boolean"):
        bools_to_number([fake], U8)
    broken = type("bool_", (), {"__module__": "numpy", "__bool__": lambda self: 2})()
    with pytest.raises(BitpackError, match="element 0 must be a boolean"):
        bools_to_number([broken], U8)


def test_messages_are_printable_even_for_hostile_names_and_reprs() -> None:
    odd = type("E\x1b[31m\n", (), {"__repr__": lambda self: "\x07bell\x1b"})()
    calls: list[Callable[[], object]] = [
        lambda: bools_to_number([odd], U8),
        lambda: bytes_to_number(odd, U8),
    ]
    for call in calls:
        with pytest.raises(BitpackError) as caught:
            call()
        assert str(caught.value).isprintable() and str(caught.value).isascii()


def test_a_huge_byte_string_element_is_quoted_cheaply() -> None:
    with pytest.raises(BitpackError) as caught:
        bools_to_number([b"x" * 20_000_000], U8)  # type: ignore[list-item]
    assert len(str(caught.value)) < 120


@pytest.mark.parametrize(
    ("text", "bits"),
    [("-0x2", "01111111"), ("-0b1", "11111111"), ("-1_0", "01101111"), ("-0o7", "10011111")],
)
def test_negative_prefixed_numbers_work_on_every_python(
    capsys: pytest.CaptureFixture[str], text: str, bits: str
) -> None:
    assert main(["unpack", text, "-t", "i8"]) == 0
    assert capsys.readouterr().out == bits + "\n"


def test_only_ascii_digits_are_numbers(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["unpack", "٣", "-t", "u8"]) == 1
    assert "not an integer" in capsys.readouterr().err
