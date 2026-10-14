"""Compact bit packing: MSB first by default, LSB first on request, count-aware unpacking."""

from __future__ import annotations

import random
from typing import Literal

import pytest

from lvbitpack import U8, bools_to_number, pack_bools, unpack_bools

Order = Literal["msb", "lsb"]
ORDERS: list[Order] = ["msb", "lsb"]


def test_msb_first_puts_element_zero_in_bit_seven() -> None:
    assert pack_bools([True]) == b"\x80"
    assert pack_bools([True, True, False, True]) == b"\xd0"
    assert pack_bools([True] * 9) == b"\xff\x80"


def test_lsb_first_puts_element_zero_in_bit_zero() -> None:
    assert pack_bools([True], bit_order="lsb") == b"\x01"
    assert pack_bools([True, True, False, True], bit_order="lsb") == b"\x0b"
    assert pack_bools([True] * 9, bit_order="lsb") == b"\xff\x01"


def test_lsb_bytes_equal_boolean_array_to_number_of_each_octet() -> None:
    rng = random.Random(7)
    array = [rng.random() < 0.5 for _ in range(203)]
    packed = pack_bools(array, bit_order="lsb")
    chunks = [array[i : i + 8] for i in range(0, len(array), 8)]
    assert list(packed) == [bools_to_number(chunk, U8) for chunk in chunks]


def test_empty_input_packs_to_no_bytes() -> None:
    assert pack_bools([]) == b""
    assert unpack_bools(b"") == []


def test_fill_bits_of_the_last_byte_are_zero() -> None:
    assert pack_bools([True, False, False]) == b"\x80"
    assert pack_bools([True, False, False], bit_order="lsb") == b"\x01"
    assert pack_bools([False] * 3) == pack_bools([False] * 3, bit_order="lsb") == b"\x00"


@pytest.mark.parametrize("bit_order", ORDERS)
def test_round_trip_for_every_length_up_to_70(bit_order: Order) -> None:
    rng = random.Random(bit_order)
    for length in range(71):
        array = [rng.random() < 0.5 for _ in range(length)]
        packed = pack_bools(array, bit_order=bit_order)
        assert len(packed) == (length + 7) // 8
        assert unpack_bools(packed, length, bit_order=bit_order) == array


def test_msb_and_lsb_are_bit_reversals_of_each_other() -> None:
    rng = random.Random(11)
    array = [rng.random() < 0.5 for _ in range(64)]
    msb, lsb = pack_bools(array), pack_bools(array, bit_order="lsb")
    assert [int(f"{b:08b}"[::-1], 2) for b in msb] == list(lsb)


def test_count_defaults_to_every_bit_and_drops_fill_bits_when_given() -> None:
    assert unpack_bools(b"\x80") == [True] + [False] * 7
    assert unpack_bools(b"\x80", 1) == [True]
    assert unpack_bools(b"\xff\xff", 9) == [True] * 9
    assert unpack_bools(b"\x01", 1, bit_order="lsb") == [True]
    assert unpack_bools(b"\x80", 0) == []


def test_fill_bits_are_not_checked() -> None:
    assert unpack_bools(b"\xff", 2) == [True, True]


@pytest.mark.parametrize(("count", "message"), [(-1, "negative"), (9, "more than the 8 bits")])
def test_counts_outside_the_data_are_refused(count: int, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        unpack_bools(b"\x80", count)


@pytest.mark.parametrize("bit_order", ["MSB", "big", "", None])
def test_an_unknown_bit_order_is_refused(bit_order: object) -> None:
    with pytest.raises(ValueError, match="bit_order must be 'msb' or 'lsb'"):
        pack_bools([True], bit_order=bit_order)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="bit_order must be 'msb' or 'lsb'"):
        unpack_bools(b"\x00", bit_order=bit_order)  # type: ignore[arg-type]
