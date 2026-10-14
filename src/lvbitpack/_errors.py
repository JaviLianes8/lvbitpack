"""The library's error type and the input checks every public function shares."""

from __future__ import annotations

import operator
from collections.abc import Iterable

# Values quoted in messages are cut to this many characters, so huge input is never echoed.
_QUOTE_LIMIT = 40
_NUMPY_BOOL_NAMES = frozenset({"bool", "bool_"})

Buffer = bytes | bytearray | memoryview


class BitpackError(ValueError):
    """Raised for any input lvbitpack refuses: a bad value, a bad type or a bad size.

    It subclasses ``ValueError``, so ``except ValueError`` keeps working.

    >>> from lvbitpack import BitpackError, U8, number_to_bools
    >>> try:
    ...     number_to_bools(256, U8)
    ... except BitpackError as error:
    ...     print(error)
    256 is out of range for u8 [0, 255]
    """


def quote(value: object) -> str:
    """A short, safe description of ``value`` for an error message."""
    if isinstance(value, int) and not isinstance(value, bool):
        if value.bit_length() > 128:
            return f"an integer of {value.bit_length()} bits"
        return str(int(value))
    try:
        text = repr(value)
    except Exception:  # a hostile __repr__ must not replace our error with its own
        text = f"<{type(value).__name__[:_QUOTE_LIMIT]} object>"
    return text if len(text) <= _QUOTE_LIMIT else text[:_QUOTE_LIMIT] + "..."


def type_name(value: object) -> str:
    """The type name of ``value``, cut for messages."""
    return type(value).__name__[:_QUOTE_LIMIT]


def as_int(value: object, what: str) -> int:
    """``value`` as a plain ``int``; ``bool`` and non-integers are refused."""
    if isinstance(value, bool):
        raise BitpackError(f"{what} must be an integer, not bool")
    try:
        return int(operator.index(value))  # type: ignore[arg-type]
    except TypeError:
        raise BitpackError(f"{what} must be an integer, not {type_name(value)}") from None


def as_bool(value: object, index: int) -> bool:
    """One array element as a ``bool``: True/False, 0/1, or a NumPy boolean."""
    if isinstance(value, bool):
        return value
    kind = type(value)
    if kind.__name__ in _NUMPY_BOOL_NAMES and kind.__module__.startswith("numpy"):
        return bool(value)
    try:
        number = int(operator.index(value))  # type: ignore[arg-type]
    except TypeError:
        number = None
    if number in (0, 1):
        return number == 1
    raise BitpackError(f"element {index} must be a boolean (True/False or 0/1), not {quote(value)}")


def as_bools(values: Iterable[object]) -> list[bool]:
    """A finite iterable of booleans as a list; text and byte strings are refused."""
    if isinstance(values, (str, bytes, bytearray, memoryview)):
        raise BitpackError(
            f"values must be an iterable of booleans, not {type_name(values)}; "
            "a string is not a boolean array"
        )
    try:
        items = iter(values)
    except TypeError:
        raise BitpackError(
            f"values must be an iterable of booleans, not {type_name(values)}"
        ) from None
    return [as_bool(item, index) for index, item in enumerate(items)]


def as_buffer(data: object, what: str = "data") -> bytes:
    """``bytes``, ``bytearray`` or ``memoryview`` as ``bytes``; anything else is refused."""
    if isinstance(data, (bytes, bytearray)):
        return bytes(data)
    if isinstance(data, memoryview):
        return data.tobytes()  # raw bytes whatever the item format
    raise BitpackError(f"{what} must be bytes, bytearray or memoryview, not {type_name(data)}")
