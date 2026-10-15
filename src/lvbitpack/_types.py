"""The integer representations and the sign extension modes of Boolean Array To Number."""

from __future__ import annotations

from dataclasses import dataclass

from ._errors import BitpackError, as_int, is_integer, numpy_bool, plain_str, quote, type_name

_VALID_BITS = (8, 16, 32, 64)
_PREFIXES = (("uint", False), ("int", True), ("u", False), ("i", True))


@dataclass(frozen=True)
class IntType:
    """A LabVIEW integer representation: 8, 16, 32 or 64 bits, signed or unsigned.

    ``U8`` to ``I64`` are ready-made; equal types compare and hash equal.

    >>> from lvbitpack import IntType, U16
    >>> IntType(16, False) == U16
    True
    >>> from lvbitpack import BitpackError
    >>> try:
    ...     IntType(12, False)
    ... except BitpackError as error:
    ...     print(error)
    bits must be 8, 16, 32 or 64, not 12
    """

    bits: int
    signed: bool

    def __post_init__(self) -> None:
        bits = as_int(self.bits, "bits")
        if bits not in _VALID_BITS:
            raise BitpackError(f"bits must be 8, 16, 32 or 64, not {quote(bits)}")
        object.__setattr__(self, "bits", bits)  # a NumPy or other __index__ width is stored as int
        signed = self.signed if type(self.signed) is bool else numpy_bool(self.signed)
        if signed is None:
            raise BitpackError(f"signed must be a bool, not {type_name(self.signed)}")
        object.__setattr__(self, "signed", signed)

    @property
    def name(self) -> str:
        """The short lower-case name.

        >>> from lvbitpack import I32
        >>> I32.name
        'i32'
        """
        return f"{'i' if self.signed else 'u'}{self.bits}"

    @property
    def mask(self) -> int:
        """All ones over the type's width.

        >>> from lvbitpack import U16
        >>> hex(U16.mask)
        '0xffff'
        """
        return (1 << self.bits) - 1

    @property
    def min(self) -> int:
        """The smallest value the type holds.

        >>> from lvbitpack import I8, U8
        >>> I8.min, U8.min
        (-128, 0)
        """
        return -(1 << (self.bits - 1)) if self.signed else 0

    @property
    def max(self) -> int:
        """The largest value the type holds.

        >>> from lvbitpack import I8, U8
        >>> I8.max, U8.max
        (127, 255)
        """
        return (1 << (self.bits - 1)) - 1 if self.signed else self.mask

    def contains(self, number: object) -> bool:
        """Whether ``number`` is an integer within the type's range.

        Any ``__index__`` integer counts; ``bool``, floats and other types are never contained.

        >>> from lvbitpack import I8
        >>> I8.contains(-128), I8.contains(128), I8.contains(1.0), I8.contains(True)
        (True, False, False, False)
        """
        if not is_integer(number):
            return False
        try:
            value = as_int(number, "number")
        except BitpackError:  # an __index__ that refuses, such as a NumPy array's
            return False
        return self.min <= value <= self.max

    @classmethod
    def parse(cls, text: str) -> IntType:
        """Read a name such as ``"u8"``, ``"I16"``, ``"uint32"`` or ``"int64"``.

        Case and surrounding white space are ignored.

        >>> from lvbitpack import IntType
        >>> IntType.parse("I16"), IntType.parse(" uint8 ")
        (IntType(bits=16, signed=True), IntType(bits=8, signed=False))
        """
        plain = plain_str(text)
        if plain is None:
            raise BitpackError(f"an integer type name must be str, not {type_name(text)}")
        key = plain.strip().lower()
        for prefix, signed in _PREFIXES:
            digits = key[len(prefix) :]
            if key.startswith(prefix) and digits in ("8", "16", "32", "64"):
                return cls(int(digits), signed)
        raise BitpackError(
            f"unknown integer type {quote(text)}; use u8, u16, u32, u64, i8, i16, i32 or i64"
        )


U8 = IntType(8, False)
U16 = IntType(16, False)
U32 = IntType(32, False)
U64 = IntType(64, False)
I8 = IntType(8, True)
I16 = IntType(16, True)
I32 = IntType(32, True)
I64 = IntType(64, True)


def check_type(int_type: object) -> IntType:
    """``int_type`` as a plain ``IntType``; anything else is refused.

    A subclass is rebuilt from its two fields, so overridden methods change nothing.
    """
    kind = type(int_type)
    if not issubclass(kind, IntType):
        raise BitpackError(f"int_type must be an IntType such as U8, not {type_name(int_type)}")
    try:
        bits = object.__getattribute__(int_type, "bits")
        signed = object.__getattribute__(int_type, "signed")
    except Exception:  # never initialised, or a subclass whose field lookup fails
        raise BitpackError("int_type is an IntType that was never initialised") from None
    if kind is IntType and type(bits) is int and type(signed) is bool and bits in (8, 16, 32, 64):
        return int_type  # type: ignore[return-value]
    return IntType(bits, signed)  # rebuilt, so a subclass or a tampered value is checked
