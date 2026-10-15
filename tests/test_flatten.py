"""LabVIEW's flattened 1-D Boolean array: I32 big-endian count, one byte per element."""

from __future__ import annotations

import random

import pytest

from lvbitpack import pack_flattened, unpack_flattened


def test_nis_documented_example() -> None:
    # NI's Flattened Data page: {T, F, T, T} flattens to 0000 0004 0100 0101.
    # https://www.ni.com/docs/en-US/bundle/labview/page/flattened-data.html (fetched 2026-10-14)
    assert pack_flattened([True, False, True, True]) == bytes.fromhex("0000000401000101")
    assert unpack_flattened(bytes.fromhex("0000000401000101")) == [True, False, True, True]


def test_an_empty_array_is_a_bare_zero_count() -> None:
    assert pack_flattened([]) == b"\x00\x00\x00\x00"
    assert unpack_flattened(b"\x00\x00\x00\x00") == []


def test_the_count_is_big_endian_and_each_element_is_one_byte() -> None:
    flat = pack_flattened([True] * 300)
    assert flat[:4] == (300).to_bytes(4, "big")
    assert flat[4:] == b"\x01" * 300
    assert pack_flattened([False, True]) == b"\x00\x00\x00\x02\x00\x01"


def test_any_nonzero_byte_reads_as_true() -> None:
    assert unpack_flattened(b"\x00\x00\x00\x03\x02\xff\x00") == [True, True, False]


def test_seeded_round_trips() -> None:
    rng = random.Random(3)
    for length in range(0, 200, 7):
        array = [rng.random() < 0.5 for _ in range(length)]
        flat = pack_flattened(array)
        assert len(flat) == 4 + length
        assert unpack_flattened(flat) == array


@pytest.mark.parametrize(
    ("data", "message"),
    [
        (b"", "4-byte count; got 0 bytes"),
        (b"\x00\x00\x00", "4-byte count; got 3 bytes"),
        (b"\xff\xff\xff\xff", r"count is negative \(-1\)"),
        (b"\x80\x00\x00\x00", r"negative \(-2147483648\)"),
        (b"\x00\x00\x00\x02\x01", "says 2 elements but only 1 byte follows"),
        (b"\x7f\xff\xff\xff", "says 2147483647 elements but only 0 bytes follow"),
        (b"\x00\x00\x00\x01\x01\x00", "1 byte follows the last of the 1 elements"),
    ],
)
def test_malformed_input_is_refused(data: bytes, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        unpack_flattened(data)


def test_buffers_are_accepted() -> None:
    flat = pack_flattened([True, False])
    assert unpack_flattened(bytearray(flat)) == [True, False]
    assert unpack_flattened(memoryview(flat)) == [True, False]
