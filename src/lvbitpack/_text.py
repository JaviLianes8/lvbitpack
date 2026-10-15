"""Safe text for error messages: short and printable ASCII, whatever the object does."""

from __future__ import annotations

import reprlib

# Values quoted in messages are cut to this many characters, so huge input is never echoed.
_QUOTE_LIMIT = 40


class _ShortRepr(reprlib.Repr):
    """``reprlib`` with byte strings cut before their repr is built."""

    def repr_bytes(self, value: bytes, level: int) -> str:
        return repr(bytes(value[: self.maxstring]))

    def repr_bytearray(self, value: bytearray, level: int) -> str:
        return repr(bytearray(value[: self.maxstring]))


_REPR = _ShortRepr()
_REPR.maxstring = _REPR.maxother = _QUOTE_LIMIT + 10
_REPR.maxlist = _REPR.maxtuple = _REPR.maxdict = _REPR.maxset = 4


def printable(text: str) -> str:
    """``text`` with control characters and non-ASCII escaped, so it cannot drive a terminal."""
    return "".join(
        char if " " <= char <= "~" else char.encode("unicode_escape").decode("ascii")
        for char in text
    )


def _cut(text: str) -> str:
    text = printable(text)
    return text if len(text) <= _QUOTE_LIMIT else text[:_QUOTE_LIMIT] + "..."


def type_name(value: object) -> str:
    """The type name of ``value``, cut for messages; a metaclass cannot change it."""
    try:
        name = type.__dict__["__name__"].__get__(type(value), type)
        return _cut(str.__str__(name))
    except Exception:
        return "object"


def quote(value: object) -> str:
    """A short, safe, printable description of ``value`` for an error message."""
    try:
        if issubclass(type(value), int) and type(value) is not bool:
            size = int.bit_length(value)  # type: ignore[arg-type]  # a subclass cannot lie
            if size > 128:
                return f"an integer of {size} bits"
            return int.__repr__(value)
        return _cut(str.__str__(_REPR.repr(value)))
    except Exception:  # a hostile object must not replace our error with its own
        return f"<{type_name(value)} object>"


def plain_str(value: object) -> str | None:
    """``value`` as an exact ``str`` without calling a subclass's methods, else None."""
    return str.__str__(value) if issubclass(type(value), str) else None
