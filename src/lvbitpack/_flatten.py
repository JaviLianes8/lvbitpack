"""LabVIEW's flattened form of a 1-D Boolean array: an I32 count, then one byte per element.

This is what Flatten To String writes for a Boolean array (and what front-panel datalogs
hold): the count is big-endian, TRUE is written as 0x01 and FALSE as 0x00, and on reading
any nonzero byte is TRUE.
"""

from __future__ import annotations

from collections.abc import Iterable

from ._errors import BitpackError, Buffer, as_bools, as_buffer

_HEADER = 4
_MAX_COUNT = 0x7FFFFFFF


def pack_flattened(values: Iterable[bool]) -> bytes:
    """Flatten a 1-D Boolean array the way LabVIEW's Flatten To String does.

    >>> from lvbitpack import pack_flattened
    >>> pack_flattened([True, False, True, True]).hex()
    '0000000401000101'
    """
    bits = as_bools(values)
    if len(bits) > _MAX_COUNT:
        raise BitpackError(f"a LabVIEW array holds at most {_MAX_COUNT} elements")
    return len(bits).to_bytes(_HEADER, "big") + bytes(bits)


def unpack_flattened(data: Buffer) -> list[bool]:
    """Read a flattened 1-D Boolean array: the I32 count, then exactly that many bytes.

    Any nonzero element byte is TRUE. A negative count, missing bytes or bytes left over
    after the last element raise ``BitpackError``.

    >>> from lvbitpack import unpack_flattened
    >>> unpack_flattened(bytes.fromhex("0000000401000101"))
    [True, False, True, True]
    """
    raw = as_buffer(data)
    if len(raw) < _HEADER:
        raise BitpackError(f"a flattened array starts with a 4-byte count; got {len(raw)} bytes")
    count = int.from_bytes(raw[:_HEADER], "big", signed=True)
    if count < 0:
        raise BitpackError(f"the element count is negative ({count})")
    body = len(raw) - _HEADER
    if body < count:
        raise BitpackError(f"the count says {count} elements but only {body} bytes follow")
    if body > count:
        raise BitpackError(f"{body - count} bytes follow the last of the {count} elements")
    return [byte != 0 for byte in raw[_HEADER:]]
