"""LabVIEW's Boolean Array To Number and Number To Boolean Array for integer outputs.

Element 0 of the array is the least significant bit. The bits map straight onto one
fixed-width integer; there is no count and no byte per element, unlike a flattened array.
"""

from __future__ import annotations

from collections.abc import Iterable

from ._errors import BitpackError, as_bools, as_int, quote
from ._modes import SignExtension
from ._types import IntType, check_type


def _check_mode(mode: object) -> SignExtension:
    if type(mode) is not SignExtension:
        raise BitpackError(f"sign_extension must be a SignExtension, not {quote(mode)}")
    return mode


def _pad_bit(bits: list[bool], int_type: IntType, mode: SignExtension) -> int:
    """The bit that fills every position above the supplied elements."""
    if mode is SignExtension.NEVER or not bits:
        return 0
    if mode is SignExtension.IF_SIGNED and not int_type.signed:
        return 0
    return 1 if bits[-1] else 0


def bools_to_number(
    values: Iterable[bool | int],
    int_type: IntType,
    *,
    sign_extension: SignExtension = SignExtension.IF_SIGNED,
) -> int:
    """Convert a Boolean array to an integer, as LabVIEW's Boolean Array To Number does.

    Element 0 is the least significant bit. Elements beyond the width are dropped; a short
    array is padded as ``sign_extension`` says (LabVIEW's default is ``IF_SIGNED``). A signed
    type gives the two's complement value. ``values`` is any finite iterable of
    ``True``/``False``, ``0``/``1`` or NumPy booleans; a string is refused.

    >>> from lvbitpack import I8, U8, SignExtension, bools_to_number
    >>> bools_to_number([False, True], U8), bools_to_number([False, True], I8)
    (2, -2)
    >>> bools_to_number([False, False, True, False, True], U8, sign_extension=SignExtension.ALWAYS)
    244
    >>> bools_to_number([True] * 9, U8)
    255
    """
    int_type = check_type(int_type)
    mode = _check_mode(sign_extension)
    bits = as_bools(values)
    width = int_type.bits
    raw = 0
    for index, bit in enumerate(bits[:width]):
        if bit:
            raw |= 1 << index
    if len(bits) < width and _pad_bit(bits, int_type, mode):
        raw |= int_type.mask ^ ((1 << len(bits)) - 1)
    if int_type.signed and raw > int_type.max:
        raw -= 1 << width
    return raw


def number_to_bools(number: int, int_type: IntType) -> list[bool]:
    """Convert an integer to a Boolean array, as LabVIEW's Number To Boolean Array does.

    The result has one element per bit of the type (8, 16, 32 or 64); element 0 holds the
    least significant bit of the two's complement form. ``number`` must fit the type: LabVIEW
    would have coerced it to the wire's type first, so a value outside it is refused.

    >>> from lvbitpack import I8, U8, number_to_bools
    >>> number_to_bools(2, U8)
    [False, True, False, False, False, False, False, False]
    >>> number_to_bools(-2, I8) == [False] + [True] * 7
    True
    """
    int_type = check_type(int_type)
    value = as_int(number, "number")
    if not int_type.contains(value):
        raise BitpackError(
            f"{quote(value)} is out of range for {int_type.name} [{int_type.min}, {int_type.max}]"
        )
    raw = value & int_type.mask
    return [bool((raw >> index) & 1) for index in range(int_type.bits)]
