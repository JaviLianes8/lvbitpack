"""Compact bit packing of Boolean arrays: eight elements per byte, no header.

LabVIEW itself stores a Boolean as one byte; this is the dense form for wire protocols,
register maps and files that want one bit per element.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

from ._errors import BitpackError, Buffer, as_bools, as_buffer, as_int, quote

BitOrder = Literal["msb", "lsb"]


def _check_order(bit_order: object) -> bool:
    """True for least-significant-bit first."""
    if isinstance(bit_order, str) and bit_order in ("msb", "lsb"):
        return bit_order == "lsb"
    raise BitpackError(f"bit_order must be 'msb' or 'lsb', not {quote(bit_order)}")


def pack_bools(values: Iterable[bool], *, bit_order: BitOrder = "msb") -> bytes:
    """Pack Booleans eight to a byte, zero-filling the unused bits of the last byte.

    With ``bit_order="msb"`` (default) element 0 is bit 7 (0x80) of byte 0. With ``"lsb"``
    element 0 is bit 0 of byte 0, so each byte equals Boolean Array To Number of its eight
    elements as a U8.

    >>> from lvbitpack import pack_bools
    >>> array = [True, True, False, True]
    >>> pack_bools(array), pack_bools(array, bit_order="lsb")
    (b'\\xd0', b'\\x0b')
    """
    lsb = _check_order(bit_order)
    bits = as_bools(values)
    out = bytearray((len(bits) + 7) // 8)
    for index, bit in enumerate(bits):
        if bit:
            shift = index % 8 if lsb else 7 - index % 8
            out[index // 8] |= 1 << shift
    return bytes(out)


def unpack_bools(
    data: Buffer, count: int | None = None, *, bit_order: BitOrder = "msb"
) -> list[bool]:
    """Unpack ``count`` Booleans (default: every bit) from bytes written by ``pack_bools``.

    ``count`` drops the fill bits of the last byte; it must be between 0 and ``8 * len(data)``.
    The fill bits are not checked.

    >>> from lvbitpack import unpack_bools
    >>> unpack_bools(b"\\xd0", 4)
    [True, True, False, True]
    >>> unpack_bools(b"\\x0b", 4, bit_order="lsb")
    [True, True, False, True]
    """
    lsb = _check_order(bit_order)
    raw = as_buffer(data)
    total = len(raw) * 8
    wanted = total if count is None else as_int(count, "count")
    if wanted < 0:
        raise BitpackError(f"count must not be negative, got {quote(wanted)}")
    if wanted > total:
        raise BitpackError(f"count {quote(wanted)} asks for more than the {total} bits in data")
    return [
        bool(raw[index // 8] >> (index % 8 if lsb else 7 - index % 8) & 1)
        for index in range(wanted)
    ]
