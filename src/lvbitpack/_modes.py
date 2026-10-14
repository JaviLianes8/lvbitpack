"""The sign extension modes of Boolean Array To Number."""

from __future__ import annotations

import enum
from typing import Any

from ._errors import BitpackError, plain_str, quote


class _ModeLookup(enum.EnumMeta):
    """Looks a mode up by its exact text, and refuses anything else with ``BitpackError``.

    The standard lookup hashes the value and prints its repr before asking ``_missing_``,
    so a huge integer or a hostile object would raise its own error instead of ours.
    """

    def __call__(cls, value: Any, *args: Any, **kwargs: Any) -> Any:
        if args or kwargs:  # the functional API that builds a new enum
            return super().__call__(value, *args, **kwargs)
        if type(value) is cls:
            return value
        text = plain_str(value)
        for member in cls:  # type: ignore[var-annotated]
            if text is not None and member.value == text:
                return member
        raise BitpackError(f"no sign extension mode {quote(value)}; use never, if_signed or always")


class SignExtension(enum.Enum, metaclass=_ModeLookup):
    """How Boolean Array To Number pads an array shorter than the integer width.

    LabVIEW sets this by right-clicking the node; ``IF_SIGNED`` is LabVIEW's default.

    - ``NEVER``: pad with FALSE.
    - ``IF_SIGNED``: pad unsigned outputs with FALSE and signed outputs with the last element.
    - ``ALWAYS``: pad with the last element.

    >>> from lvbitpack import I8, SignExtension, bools_to_number
    >>> array = [False, True, False, True]
    >>> [bools_to_number(array, I8, sign_extension=mode) for mode in SignExtension]
    [10, -6, -6]
    >>> SignExtension("always")
    <SignExtension.ALWAYS: 'always'>
    """

    NEVER = "never"
    IF_SIGNED = "if_signed"
    ALWAYS = "always"
