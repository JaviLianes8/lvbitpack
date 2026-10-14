"""The library's error type and the input checks every public function shares."""

from __future__ import annotations

import operator
import reprlib
from collections.abc import Iterable
from typing import Protocol

# Values quoted in messages are cut to this many characters, so huge input is never echoed.
_QUOTE_LIMIT = 40
_NUMPY_BOOL_NAMES = frozenset({"bool", "bool_"})
_REPR = reprlib.Repr()
_REPR.maxstring = _REPR.maxother = _QUOTE_LIMIT + 10
_REPR.maxlist = _REPR.maxtuple = _REPR.maxdict = _REPR.maxset = 4


class Buffer(Protocol):
    """Any object with the buffer protocol: bytes, bytearray, memoryview, array, NumPy."""

    def __buffer__(self, flags: int, /) -> memoryview: ...


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
    """A short, safe, ASCII description of ``value`` for an error message."""
    try:
        if isinstance(value, int) and not isinstance(value, bool):
            size = int.bit_length(value)  # the int method: a subclass cannot override it
            if size > 128:
                return f"an integer of {size} bits"
            return int.__repr__(value)
        text = _REPR.repr(value)
    except Exception:  # a hostile object must not replace our error with its own
        return f"<{type_name(value)} object>"
    text = text.encode("ascii", "backslashreplace").decode("ascii")
    return text if len(text) <= _QUOTE_LIMIT else text[:_QUOTE_LIMIT] + "..."


def type_name(value: object) -> str:
    """The type name of ``value``, cut for messages; a metaclass cannot change it."""
    try:
        name = type.__dict__["__name__"].__get__(type(value), type)
        name = name.encode("ascii", "backslashreplace").decode("ascii")
    except Exception:
        name = "object"
    return str(name)[:_QUOTE_LIMIT]


def plain_str(value: object) -> str | None:
    """``value`` as an exact ``str`` without calling a subclass's methods, else None."""
    return str.__str__(value) if issubclass(type(value), str) else None


def is_integer(value: object) -> bool:
    """Whether ``value`` is an ``__index__`` integer other than ``bool``."""
    return not isinstance(value, bool) and hasattr(type(value), "__index__")


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
    if type(value) is bool:
        return value
    kind = type(value)
    try:
        module = getattr(kind, "__module__", None)
    except Exception:  # a metaclass may make even this lookup fail
        module = None
    if (
        type_name(value) in _NUMPY_BOOL_NAMES
        and isinstance(module, str)
        and module.startswith("numpy")
    ):
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
        kind = "a string" if isinstance(values, str) else "a byte string"
        raise BitpackError(
            f"values must be an iterable of booleans, not {type_name(values)}; "
            f"{kind} is not a Boolean array"
        )
    try:
        items = iter(values)
    except TypeError:
        raise BitpackError(
            f"values must be an iterable of booleans, not {type_name(values)}"
        ) from None
    return [as_bool(item, index) for index, item in enumerate(items)]


def as_buffer(data: object, what: str = "data") -> bytes:
    """The raw bytes of any buffer-protocol object; text and everything else is refused."""
    if not isinstance(data, str):
        try:
            with memoryview(data) as view:  # type: ignore[arg-type]
                if "O" in view.format:  # object pointers are not data
                    raise BitpackError(f"{what} holds Python objects, not bytes")
                return view.tobytes()  # raw bytes in memory order, any item format
        except TypeError:
            pass
        except BitpackError:
            raise
        except ValueError:  # a released view, or a buffer of a kind Python cannot export
            raise BitpackError(f"{what} cannot be read as bytes ({type_name(data)})") from None
    raise BitpackError(f"{what} must be a bytes-like object, not {type_name(data)}")
