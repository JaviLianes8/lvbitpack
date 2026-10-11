"""LabVIEW Flatten To String form: an I32 big-endian count, then the packed bits."""

from __future__ import annotations

from collections.abc import Sequence

from ._pack import pack_bools, unpack_bools

_HEADER = 4
_MAX_COUNT = 0x7FFFFFFF


def pack_flattened(values: Sequence[bool]) -> bytes:
    """Pack booleans the way LabVIEW flattens a boolean array to a string.

    The result is a four-byte big-endian element count followed by the MSB-first
    packed bits. This is the layout LabVIEW's Flatten To String node produces.
    """
    count = len(values)
    if count > _MAX_COUNT:
        raise ValueError("boolean array is too large for a 32-bit count")
    return count.to_bytes(_HEADER, "big") + pack_bools(values)


def unpack_flattened(data: bytes) -> list[bool]:
    """Read a LabVIEW flattened boolean array: the I32 count, then its bits."""
    if len(data) < _HEADER:
        raise ValueError("data is too short to hold a 32-bit count header")
    count = int.from_bytes(data[:_HEADER], "big")
    return unpack_bools(data[_HEADER:], count)
