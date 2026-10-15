"""The library's error type and the input checks every public function shares.

Every check looks at ``type(value)``, never at ``value.__class__``, so an object that lies
about its class (or whose attribute lookup fails) cannot slip past or raise its own error.
"""

from __future__ import annotations

import operator
from collections.abc import Iterable
from typing import Protocol

from ._text import plain_str, quote, type_name

__all__ = ["BitpackError", "Buffer", "as_bool", "as_bools", "as_buffer", "as_int"]
__all__ += ["is_integer", "numpy_bool", "plain_str", "quote", "type_name"]

_NUMPY_BOOL_NAMES = frozenset({"bool", "bool_"})
_BYTE_STRINGS = (bytes, bytearray, memoryview)


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


def is_integer(value: object) -> bool:
    """Whether ``value``'s type has ``__index__`` and is not ``bool``."""
    kind = type(value)
    try:
        return kind is not bool and hasattr(kind, "__index__")
    except Exception:  # a metaclass whose attribute lookup fails
        return False


def as_int(value: object, what: str) -> int:
    """``value`` as a plain ``int``; ``bool`` and non-integers are refused."""
    if type(value) is bool:
        raise BitpackError(f"{what} must be an integer, not bool")
    try:
        return int(operator.index(value))  # type: ignore[arg-type]
    except TypeError:
        raise BitpackError(f"{what} must be an integer, not {type_name(value)}") from None


def numpy_bool(value: object) -> bool | None:
    """The truth of a NumPy boolean scalar, or None when ``value`` is not one."""
    kind = type(value)
    try:
        module = type.__dict__["__module__"].__get__(kind, type)
    except Exception:
        return None
    if type_name(value) not in _NUMPY_BOOL_NAMES or type(module) is not str:
        return None
    if module != "numpy" and not module.startswith("numpy."):
        return None
    try:
        truth = bool(value)
    except Exception:
        return None
    return truth


def as_bool(value: object, index: int) -> bool:
    """One array element as a ``bool``: True/False, 0/1, or a NumPy boolean."""
    if type(value) is bool:
        return value
    truth = numpy_bool(value)
    if truth is not None:
        return truth
    try:
        number = int(operator.index(value))  # type: ignore[arg-type]
    except TypeError:
        number = None
    if number in (0, 1):
        return number == 1
    raise BitpackError(f"element {index} must be a boolean (True/False or 0/1), not {quote(value)}")


def as_bools(values: Iterable[object]) -> list[bool]:
    """A finite iterable of booleans as a list; text and byte strings are refused."""
    kind = type(values)
    if issubclass(kind, (str, *_BYTE_STRINGS)):
        what = "a string" if issubclass(kind, str) else "a byte string"
        raise BitpackError(
            f"values must be an iterable of booleans, not {type_name(values)}; "
            f"{what} is not a Boolean array"
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
    if not issubclass(type(data), str):
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
