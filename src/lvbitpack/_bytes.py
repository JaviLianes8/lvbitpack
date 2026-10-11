"""Byte serialization for Boolean Array To Number results.

The array bit order (element 0 is the LSB) is fixed and independent of byte order.
Byte order only chooses how the resulting integer is laid out across its bytes.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from ._number import IntType, SignExtension, bools_to_number, number_to_bools

ByteOrder = Literal["little", "big"]


def number_to_bytes(number: int, int_type: IntType, *, byteorder: ByteOrder = "little") -> bytes:
    """Serialize a number to its fixed-width bytes, little or big endian."""
    if not int_type.contains(number):
        raise ValueError(
            f"{number} is out of range for {int_type.name} [{int_type.min}, {int_type.max}]"
        )
    return number.to_bytes(int_type.bits // 8, byteorder, signed=int_type.signed)


def bytes_to_number(data: bytes, int_type: IntType, *, byteorder: ByteOrder = "little") -> int:
    """Read a number from exactly the type's width in bytes."""
    width = int_type.bits // 8
    if len(data) != width:
        raise ValueError(f"{int_type.name} needs exactly {width} bytes, got {len(data)}")
    return int.from_bytes(data, byteorder, signed=int_type.signed)


def bools_to_bytes(
    values: Sequence[bool],
    int_type: IntType,
    *,
    sign_extension: SignExtension = SignExtension.IF_SIGNED,
    byteorder: ByteOrder = "little",
) -> bytes:
    """Convert a boolean array to a number and then to its bytes."""
    number = bools_to_number(values, int_type, sign_extension=sign_extension)
    return number_to_bytes(number, int_type, byteorder=byteorder)


def bytes_to_bools(
    data: bytes, int_type: IntType, *, byteorder: ByteOrder = "little"
) -> list[bool]:
    """Read bytes into a number and then into a boolean array, element 0 the LSB."""
    number = bytes_to_number(data, int_type, byteorder=byteorder)
    return number_to_bools(number, int_type)
