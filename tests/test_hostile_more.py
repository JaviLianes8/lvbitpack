"""Contracts from the first QA round: buffers, hostile subclasses, mocks, NumPy integers."""

from __future__ import annotations

import array
import io
import sys
from unittest import mock

import pytest

from lvbitpack import (
    I8,
    U8,
    U16,
    BitpackError,
    IntType,
    SignExtension,
    bools_to_number,
    bytes_to_number,
    number_to_bytes,
    pack_bools,
    unpack_bools,
    unpack_flattened,
)
from lvbitpack._cli import main


class BadInt(int):
    def bit_length(self) -> int:
        raise RuntimeError("hostile")

    def __repr__(self) -> str:
        raise RuntimeError("hostile")


class BadStr(str):
    def __eq__(self, other: object) -> bool:
        raise RuntimeError("hostile")

    __hash__ = str.__hash__

    def strip(self, chars: str | None = None) -> str:
        raise RuntimeError("hostile")


class BadBytes(bytes):
    def __bytes__(self) -> bytes:
        raise RuntimeError("hostile")


def test_any_buffer_protocol_object_is_read_as_raw_bytes() -> None:
    assert bytes_to_number(array.array("B", [0, 1]), U16) == 1
    assert unpack_bools(array.array("B", [0xD0]), 4) == [True, True, False, True]
    flat = array.array("B", [0, 0, 0, 1, 1])
    assert unpack_flattened(flat) == [True]
    assert bytes_to_number(BadBytes(b"\x01"), U8) == 1


def test_numpy_buffers_are_bytes_too() -> None:
    numpy = pytest.importorskip("numpy")
    assert bytes_to_number(numpy.array([0, 1], dtype=numpy.uint8), U16) == 1
    assert IntType(numpy.int64(8), False) == U8
    assert type(IntType(numpy.int64(8), False).bits) is int
    assert U8.contains(numpy.int64(5)) and not U8.contains(numpy.int64(256))


@pytest.mark.parametrize("data", [[0, 1], "01", 5, None])
def test_lists_text_and_numbers_are_not_buffers(data: object) -> None:
    with pytest.raises(BitpackError, match="must be a bytes-like object"):
        bytes_to_number(data, U16)  # type: ignore[arg-type]


def test_a_released_memoryview_is_refused() -> None:
    view = memoryview(b"\x00\x01")
    view.release()
    with pytest.raises(BitpackError, match=r"cannot be read as bytes \(memoryview\)"):
        bytes_to_number(view, U16)


def test_hostile_int_subclasses_and_mocks_only_raise_bitpack_error() -> None:
    for element in (BadInt(5), mock.Mock(spec=int), mock.Mock()):
        with pytest.raises(BitpackError, match="element 0 must be a boolean"):
            bools_to_number([element], U8)
    for bad in (mock.Mock(spec=int), BadInt(3)):
        with pytest.raises(BitpackError, match="sign_extension must be"):
            bools_to_number([True], U8, sign_extension=bad)  # type: ignore[arg-type]
        with pytest.raises(BitpackError, match="byteorder must be"):
            number_to_bytes(1, U8, byteorder=bad)  # type: ignore[arg-type]
        with pytest.raises(BitpackError, match="bit_order must be"):
            pack_bools([True], bit_order=bad)  # type: ignore[arg-type]
    assert not U8.contains(mock.Mock(spec=int))


def test_hostile_str_subclasses_are_read_as_their_text() -> None:
    assert number_to_bytes(1, U16, byteorder=BadStr("little")) == b"\x01\x00"  # type: ignore[arg-type]
    assert pack_bools([True], bit_order=BadStr("lsb")) == b"\x01"  # type: ignore[arg-type]
    assert IntType.parse(BadStr(" u8 ")) == U8


def test_an_array_of_byte_orders_is_refused_cleanly() -> None:
    numpy = pytest.importorskip("numpy")
    with pytest.raises(BitpackError, match="byteorder must be"):
        number_to_bytes(1, U8, byteorder=numpy.array(["big", "big"]))


def test_an_unknown_sign_extension_name_is_a_bitpack_error() -> None:
    for value in ("NEVER", "", None, "x" * 1000):
        with pytest.raises(BitpackError, match="no sign extension mode") as caught:
            SignExtension(value)
        assert len(str(caught.value)) < 120


def test_messages_are_ascii_and_cut() -> None:
    with pytest.raises(BitpackError) as caught:
        bools_to_number(["中" * 100], I8)  # type: ignore[list-item]
    assert str(caught.value).isascii() and len(str(caught.value)) < 120
    with pytest.raises(BitpackError, match=r"count is 9, more than the 8 bits"):
        unpack_bools(b"\x00", 9)


def test_an_ascii_only_stderr_still_gets_the_message(monkeypatch: pytest.MonkeyPatch) -> None:
    buffer = io.BytesIO()
    stream = io.TextIOWrapper(buffer, encoding="ascii", errors="strict")
    monkeypatch.setattr(sys, "stderr", stream)
    assert main(["pack", "0中1", "-t", "u8"]) == 1
    stream.flush()
    assert buffer.getvalue().startswith(b"lvbitpack: error: character 1 is ")
