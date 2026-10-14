"""Fixed-width bytes for the numbers Boolean Array To Number produces.

The element to bit mapping (element 0 is the least significant bit) never depends on byte
order; byte order only lays the finished integer out across its bytes. The default is
big-endian, the order of LabVIEW's Flatten To String and Type Cast.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

from ._errors import BitpackError, Buffer, as_buffer, as_int, plain_str, quote
from ._number import bools_to_number, number_to_bools
from ._types import IntType, SignExtension, check_type

ByteOrder = Literal["big", "little"]


def _check_order(byteorder: object) -> Literal["big", "little"]:
    text = plain_str(byteorder)
    if text == "big":
        return "big"
    if text == "little":
        return "little"
    raise BitpackError(f"byteorder must be 'big' or 'little', not {quote(byteorder)}")


def number_to_bytes(number: int, int_type: IntType, *, byteorder: ByteOrder = "big") -> bytes:
    """The ``int_type.bits // 8`` bytes of ``number``, big-endian unless told otherwise.

    >>> from lvbitpack import I16, number_to_bytes
    >>> number_to_bytes(-2, I16), number_to_bytes(-2, I16, byteorder="little")
    (b'\\xff\\xfe', b'\\xfe\\xff')
    """
    int_type = check_type(int_type)
    order = _check_order(byteorder)
    value = as_int(number, "number")
    if not int_type.contains(value):
        raise BitpackError(
            f"{quote(value)} is out of range for {int_type.name} [{int_type.min}, {int_type.max}]"
        )
    return value.to_bytes(int_type.bits // 8, order, signed=int_type.signed)


def bytes_to_number(data: Buffer, int_type: IntType, *, byteorder: ByteOrder = "big") -> int:
    """Read a number from exactly ``int_type.bits // 8`` bytes.

    ``data`` is any buffer-protocol object (``bytes``, ``bytearray``, ``memoryview``,
    ``array.array``, NumPy arrays), read as its raw bytes in memory order.

    >>> from lvbitpack import I16, U16, bytes_to_number
    >>> bytes_to_number(b"\\xff\\xfe", I16), bytes_to_number(b"\\xff\\xfe", U16)
    (-2, 65534)
    """
    int_type = check_type(int_type)
    order = _check_order(byteorder)
    raw = as_buffer(data)
    width = int_type.bits // 8
    if len(raw) != width:
        raise BitpackError(f"{int_type.name} needs exactly {width} bytes, got {len(raw)}")
    return int.from_bytes(raw, order, signed=int_type.signed)


def bools_to_bytes(
    values: Iterable[bool | int],
    int_type: IntType,
    *,
    sign_extension: SignExtension = SignExtension.IF_SIGNED,
    byteorder: ByteOrder = "big",
) -> bytes:
    """``bools_to_number`` followed by ``number_to_bytes``.

    >>> from lvbitpack import U16, bools_to_bytes
    >>> bools_to_bytes([False, True], U16), bools_to_bytes([False, True], U16, byteorder="little")
    (b'\\x00\\x02', b'\\x02\\x00')
    """
    int_type = check_type(int_type)
    order = _check_order(byteorder)
    number = bools_to_number(values, int_type, sign_extension=sign_extension)
    return number_to_bytes(number, int_type, byteorder=order)


def bytes_to_bools(data: Buffer, int_type: IntType, *, byteorder: ByteOrder = "big") -> list[bool]:
    """``bytes_to_number`` followed by ``number_to_bools``; element 0 is the low bit.

    >>> from lvbitpack import U16, bytes_to_bools
    >>> bytes_to_bools(b"\\x00\\x02", U16)[:3]
    [False, True, False]
    """
    number = bytes_to_number(data, int_type, byteorder=byteorder)
    return number_to_bools(number, int_type)
