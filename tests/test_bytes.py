"""Byte forms of the numbers: big-endian by default, little on request, exact widths."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from lvbitpack import (
    I8,
    I16,
    I32,
    I64,
    U8,
    U16,
    U32,
    U64,
    IntType,
    SignExtension,
    bools_to_bytes,
    bytes_to_bools,
    bytes_to_number,
    number_to_bytes,
)

ALL = [U8, U16, U32, U64, I8, I16, I32, I64]


def test_big_endian_is_the_default_like_labviews_flatten() -> None:
    # NI's Flattened Data page: a 32-bit integer of -19 flattens to FFFF FFED.
    # https://www.ni.com/docs/en-US/bundle/labview/page/flattened-data.html (fetched 2026-10-14)
    assert number_to_bytes(-19, I32) == bytes.fromhex("ffffffed")
    assert bytes_to_number(bytes.fromhex("ffffffed"), I32) == -19


def test_little_endian_on_request() -> None:
    assert number_to_bytes(-19, I32, byteorder="little") == bytes.fromhex("edffffff")
    assert bytes_to_number(bytes.fromhex("edffffff"), I32, byteorder="little") == -19


@pytest.mark.parametrize("int_type", ALL)
def test_width_is_bits_over_eight(int_type: IntType) -> None:
    assert len(number_to_bytes(int_type.max, int_type)) == int_type.bits // 8
    assert number_to_bytes(int_type.min, int_type) == int_type.min.to_bytes(
        int_type.bits // 8, "big", signed=int_type.signed
    )


def test_the_same_bytes_read_signed_and_unsigned() -> None:
    assert bytes_to_number(b"\xff\xfe", I16) == -2
    assert bytes_to_number(b"\xff\xfe", U16) == 65534
    assert bytes_to_number(b"\x80" + b"\x00" * 7, I64) == -(2**63)
    assert bytes_to_number(b"\x80", I8) == -128 and bytes_to_number(b"\x80", U8) == 128


def test_bit_order_does_not_depend_on_byte_order() -> None:
    assert bools_to_bytes([False, True], U16) == b"\x00\x02"
    assert bools_to_bytes([False, True], U16, byteorder="little") == b"\x02\x00"
    little = bytes_to_bools(b"\x02\x00", U16, byteorder="little")
    assert little == bytes_to_bools(b"\x00\x02", U16)
    assert little[:2] == [False, True]


def test_bools_to_bytes_passes_the_sign_extension_through() -> None:
    always = SignExtension.ALWAYS
    assert bools_to_bytes([True], U16) == b"\x00\x01"
    assert bools_to_bytes([True], U16, sign_extension=always) == b"\xff\xff"
    assert bools_to_bytes([False, True], I8) == b"\xfe"


def test_buffers_of_every_kind_are_read_as_raw_bytes() -> None:
    assert bytes_to_number(bytearray(b"\x01\x00"), U16) == 256
    assert bytes_to_number(memoryview(b"\x01\x00"), U16) == 256
    wide = memoryview(bytes(4)).cast("I")  # one 4-byte item, still 4 raw bytes
    assert bytes_to_number(wide, U32) == 0


@pytest.mark.parametrize("data", [b"", b"\x00", b"\x00\x00\x00"])
def test_the_wrong_number_of_bytes_is_refused(data: bytes) -> None:
    with pytest.raises(ValueError, match="needs exactly 2 bytes"):
        bytes_to_number(data, U16)
    with pytest.raises(ValueError, match="needs exactly 2 bytes"):
        bytes_to_bools(data, I16)


@pytest.mark.parametrize("order", ["middle", "BIG", "", None, b"big"])
def test_an_unknown_byte_order_is_refused(order: object) -> None:
    calls: list[Callable[[], object]] = [
        lambda: number_to_bytes(1, U16, byteorder=order),  # type: ignore[arg-type]
        lambda: bytes_to_number(b"\x00\x01", U16, byteorder=order),  # type: ignore[arg-type]
        lambda: bools_to_bytes([True], U16, byteorder=order),  # type: ignore[arg-type]
        lambda: bytes_to_bools(b"\x00\x01", U16, byteorder=order),  # type: ignore[arg-type]
    ]
    for call in calls:
        with pytest.raises(ValueError, match="byteorder must be 'big' or 'little'"):
            call()


@pytest.mark.parametrize("int_type", ALL)
def test_out_of_range_numbers_are_refused(int_type: IntType) -> None:
    with pytest.raises(ValueError, match=f"out of range for {int_type.name}"):
        number_to_bytes(int_type.max + 1, int_type)
    with pytest.raises(ValueError, match=f"out of range for {int_type.name}"):
        number_to_bytes(int_type.min - 1, int_type)
