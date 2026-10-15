"""Contracts found missing by the third independent mutation round."""

from __future__ import annotations

import ctypes
import tracemalloc
from collections.abc import Callable

import pytest

from lvbitpack import (
    I8,
    U8,
    U16,
    U64,
    BitpackError,
    IntType,
    SignExtension,
    bools_to_number,
    bytes_to_number,
    number_to_bools,
    number_to_bytes,
)


class _ShyIndex:
    """An integer through its type's ``__index__``; every instance attribute lookup fails."""

    def __index__(self) -> int:
        return 5

    def __getattribute__(self, name: str) -> object:
        raise AttributeError(name)


def test_contains_asks_the_type_not_the_instance_for_index() -> None:
    assert I8.contains(_ShyIndex()) is True


class _ClaimsNumpy(type):
    @property
    def __module__(cls) -> str:  # type: ignore[override]
        return "numpy"


def test_a_metaclass_cannot_claim_to_be_numpy() -> None:
    impostor = _ClaimsNumpy("bool_", (), {"__bool__": lambda self: True})()
    with pytest.raises(BitpackError, match="element 0 must be a boolean"):
        bools_to_number([impostor], U8)


def test_a_type_with_a_non_text_module_is_not_a_numpy_boolean() -> None:
    odd = type("bool_", (), {"__module__": 5, "__bool__": lambda self: True})()
    with pytest.raises(BitpackError, match="element 0 must be a boolean"):
        bools_to_number([odd], U8)


def test_delete_characters_in_type_names_are_escaped() -> None:
    odd = type("a\x7fb", (), {})()
    with pytest.raises(BitpackError) as caught:
        bools_to_number(odd, U8)
    assert "\x7f" not in str(caught.value) and "a\\x7fb" in str(caught.value)


@pytest.mark.parametrize("kind", [bytes, bytearray])
def test_quoting_a_huge_byte_string_does_not_copy_it(kind: Callable[[bytes], object]) -> None:
    huge = kind(b"\x00" * 5_000_000)
    tracemalloc.start()
    try:
        with pytest.raises(BitpackError, match="byteorder must be"):
            number_to_bytes(1, U8, byteorder=huge)  # type: ignore[arg-type]
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert peak < 1_000_000


class _Pretender:
    """Claims to be an int through ``__class__``; its real type is not."""

    @property  # type: ignore[misc]
    def __class__(self) -> type:
        return int

    def __repr__(self) -> str:
        return "pretender"


def test_quote_goes_by_the_real_type_not_the_claimed_class() -> None:
    with pytest.raises(BitpackError) as caught:
        bools_to_number([1], U8, sign_extension=_Pretender())  # type: ignore[arg-type]
    assert str(caught.value).endswith("not pretender")


def test_a_boolean_is_quoted_as_a_boolean() -> None:
    with pytest.raises(BitpackError) as caught:
        bools_to_number([1], U8, sign_extension=True)  # type: ignore[arg-type]
    assert str(caught.value).endswith("not True")


class _ModePretender:
    @property  # type: ignore[misc]
    def __class__(self) -> type:
        return SignExtension


def test_sign_extension_lookup_does_not_trust_a_claimed_class() -> None:
    with pytest.raises(BitpackError, match="no sign extension mode"):
        SignExtension(_ModePretender())


def test_a_buffer_of_python_objects_is_refused() -> None:
    pointers = (ctypes.py_object * 1)(5)  # type: ignore[misc]
    with pytest.raises(BitpackError, match="holds Python objects, not bytes"):
        bytes_to_number(pointers, U64)


def test_a_tampered_width_of_the_wrong_type_is_refused() -> None:
    tampered = IntType(8, False)
    object.__setattr__(tampered, "bits", 8.0)
    with pytest.raises(BitpackError, match="bits must be an integer"):
        number_to_bools(1, tampered)


def test_a_numpy_signed_flag_is_stored_as_a_bool() -> None:
    numpy_true = type("bool_", (), {"__module__": "numpy", "__bool__": lambda self: True})()
    made = IntType(8, numpy_true)
    assert type(made.signed) is bool and made == I8


class _SaysLittle(str):
    def __str__(self) -> str:
        return "little"


def test_option_text_is_read_without_calling_a_subclass_str() -> None:
    assert number_to_bytes(1, U16, byteorder=_SaysLittle("big")) == b"\x00\x01"  # type: ignore[arg-type]
