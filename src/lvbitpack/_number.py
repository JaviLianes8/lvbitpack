"""LabVIEW Boolean Array To Number and Number To Boolean Array semantics.

Element index 0 is the least significant bit (LSB), matching LabVIEW. The array's
bits map directly onto a single fixed-width integer, so this is distinct from a
flattened boolean array (which prefixes a count and stores one byte per element).
"""

from __future__ import annotations

import enum
from collections.abc import Sequence
from dataclasses import dataclass

_VALID_BITS = (8, 16, 32, 64)


class SignExtension(enum.Enum):
    """How a boolean array shorter than the integer width is padded.

    These mirror LabVIEW's right-click "Sign Extension Mode" on Boolean Array To
    Number. The padding bit fills every position above the supplied elements.
    """

    NEVER = "never"
    IF_SIGNED = "if_signed"
    ALWAYS = "always"


@dataclass(frozen=True)
class IntType:
    """A fixed-width integer representation: bit width plus signedness."""

    bits: int
    signed: bool

    def __post_init__(self) -> None:
        if self.bits not in _VALID_BITS:
            raise ValueError(f"bits must be one of {_VALID_BITS}, got {self.bits}")

    @property
    def name(self) -> str:
        """The short name, for example "u8" or "i32"."""
        return f"{'i' if self.signed else 'u'}{self.bits}"

    @property
    def mask(self) -> int:
        """The all-ones mask covering the type's bit width."""
        return (1 << self.bits) - 1

    @property
    def min(self) -> int:
        """The smallest value the type can hold."""
        return -(1 << (self.bits - 1)) if self.signed else 0

    @property
    def max(self) -> int:
        """The largest value the type can hold."""
        return (1 << (self.bits - 1)) - 1 if self.signed else self.mask

    def contains(self, number: int) -> bool:
        """Whether number fits in this type without overflow."""
        return self.min <= number <= self.max

    @classmethod
    def parse(cls, text: str) -> IntType:
        """Parse a name such as "u8", "I16", or "int32" into an IntType."""
        key = text.strip().lower()
        prefixes = {"u": False, "uint": False, "i": True, "int": True}
        for prefix, signed in prefixes.items():
            if key.startswith(prefix):
                digits = key[len(prefix) :]
                if digits.isdigit():
                    return cls(bits=int(digits), signed=signed)
        raise ValueError(f"unknown integer type {text!r}; use u8/u16/u32/u64 or i8/i16/i32/i64")


U8 = IntType(8, False)
U16 = IntType(16, False)
U32 = IntType(32, False)
U64 = IntType(64, False)
I8 = IntType(8, True)
I16 = IntType(16, True)
I32 = IntType(32, True)
I64 = IntType(64, True)


def _pad_bit(values: Sequence[bool], int_type: IntType, mode: SignExtension) -> int:
    """The value (0 or 1) used to fill positions above the supplied elements."""
    if mode is SignExtension.NEVER:
        return 0
    last_is_true = bool(values) and bool(values[-1])
    if mode is SignExtension.ALWAYS:
        return 1 if last_is_true else 0
    return 1 if (int_type.signed and last_is_true) else 0


def bools_to_number(
    values: Sequence[bool],
    int_type: IntType,
    *,
    sign_extension: SignExtension = SignExtension.IF_SIGNED,
) -> int:
    """Convert a boolean array to a number, LabVIEW Boolean Array To Number.

    Element 0 is the least significant bit. Elements beyond the integer width are
    dropped. A short array is padded per sign_extension. Signed types return a
    two's complement value. The default sign_extension matches LabVIEW's default.
    """
    pad = _pad_bit(values, int_type, sign_extension)
    raw = 0
    for index in range(int_type.bits):
        bit = (1 if values[index] else 0) if index < len(values) else pad
        raw |= bit << index
    if int_type.signed and raw > int_type.max:
        raw -= 1 << int_type.bits
    return raw


def number_to_bools(number: int, int_type: IntType) -> list[bool]:
    """Convert a number to a boolean array, LabVIEW Number To Boolean Array.

    The result has one element per bit of the type, element 0 holding the least
    significant bit of the two's complement representation. Raises ValueError when
    number does not fit the type.
    """
    if not int_type.contains(number):
        raise ValueError(
            f"{number} is out of range for {int_type.name} [{int_type.min}, {int_type.max}]"
        )
    raw = number & int_type.mask
    return [bool((raw >> index) & 1) for index in range(int_type.bits)]
