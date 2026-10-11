"""MSB-first bit packing for LabVIEW boolean arrays, without a length header."""

from __future__ import annotations

from collections.abc import Sequence

_BYTE = 8
_HIGH_BIT = 0x80


def pack_bools(values: Sequence[bool]) -> bytes:
    """Pack booleans into bytes MSB-first, zero-padding the final byte.

    The first value occupies the most significant bit (0x80) of the first byte.
    When the count is not a multiple of eight, the remaining low bits of the
    last byte stay at zero, matching LabVIEW's packed boolean-array layout.
    """
    out = bytearray((len(values) + _BYTE - 1) // _BYTE)
    for index, value in enumerate(values):
        if value:
            out[index // _BYTE] |= _HIGH_BIT >> (index % _BYTE)
    return bytes(out)


def unpack_bools(data: bytes, count: int) -> list[bool]:
    """Unpack the first count booleans from MSB-first packed bytes.

    count drops the trailing padding bits of the final byte, so it must sit
    between zero and the number of bits the data can hold.
    """
    if count < 0:
        raise ValueError("count must not be negative")
    if count > len(data) * _BYTE:
        raise ValueError("data holds fewer bits than count requests")
    return [bool(data[index // _BYTE] & (_HIGH_BIT >> (index % _BYTE))) for index in range(count)]
