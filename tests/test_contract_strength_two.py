"""Contracts found missing by the second independent mutation round."""

from __future__ import annotations

import inspect
import io
import sys
import time
import types

import pytest

import lvbitpack
from lvbitpack import I8, U8, BitpackError, IntType, SignExtension, bools_to_number
from lvbitpack._cli import main


class _Index:
    """An integer only through ``__index__``: no comparisons, no arithmetic."""

    def __init__(self, value: int) -> None:
        self.value = value

    def __index__(self) -> int:
        return self.value


def test_an_index_width_is_stored_as_a_plain_int() -> None:
    made = IntType(_Index(8), False)  # type: ignore[arg-type]
    assert type(made.bits) is int
    assert made == U8 and hash(made) == hash(U8) and made.mask == 0xFF


def test_contains_reads_index_integers_through_index() -> None:
    assert I8.contains(_Index(5)) and not I8.contains(_Index(200))


def test_an_instance_level_index_attribute_is_not_an_integer() -> None:
    fake = types.SimpleNamespace(__index__=lambda: 5)
    assert I8.contains(fake) is False


class _Liar(int):
    """An int subclass whose own methods lie about it."""

    def bit_length(self) -> int:
        return 1

    def __repr__(self) -> str:
        return "é" * 1000


def test_quoting_an_int_subclass_uses_the_int_methods() -> None:
    with pytest.raises(BitpackError) as caught:
        bools_to_number([1], U8, sign_extension=_Liar(1 << 200))  # type: ignore[arg-type]
    assert str(caught.value).endswith("not an integer of 201 bits")
    with pytest.raises(BitpackError) as caught:
        SignExtension(_Liar(5))
    assert "mode 5;" in str(caught.value) and str(caught.value).isascii()


def test_type_names_in_messages_are_ascii() -> None:
    odd = type("Ñandú", (), {})()
    for call in (lambda: IntType(odd, False), lambda: bools_to_number(odd, U8)):
        with pytest.raises(BitpackError) as caught:
            call()
        assert str(caught.value).isascii() and "\\xd1and\\xfa" in str(caught.value)


def test_quoting_a_wide_nested_value_stays_cheap() -> None:
    nested: object = [0] * 12
    for _ in range(6):
        nested = [nested] * 12
    start = time.perf_counter()
    with pytest.raises(BitpackError, match="sign_extension must be a SignExtension"):
        bools_to_number([1], U8, sign_extension=nested)  # type: ignore[arg-type]
    assert time.perf_counter() - start < 1.0


class _NoModule(type):
    @property
    def __module__(cls) -> str:  # type: ignore[override]
        raise AttributeError("no module here")


def test_an_element_whose_type_has_no_module_is_refused_cleanly() -> None:
    element = _NoModule("thing", (), {})()
    with pytest.raises(BitpackError, match="element 0 must be a boolean"):
        bools_to_number([element], U8)


def test_a_stream_that_cannot_encode_gets_escaped_text(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = io.BytesIO()
    strict = io.TextIOWrapper(raw, encoding="ascii", errors="strict", write_through=True)
    monkeypatch.setattr(sys, "stderr", strict)
    assert main(["pack", "01", "-t", "u8", "-s", "é"]) == 2
    text = raw.getvalue().decode("ascii")
    assert "invalid choice" in text and "\\xe9" in text


@pytest.mark.parametrize("name", lvbitpack.__all__)
def test_every_public_name_reports_the_package_as_its_module(name: str) -> None:
    value = getattr(lvbitpack, name)
    if inspect.isfunction(value):
        assert value.__module__ == "lvbitpack", name
