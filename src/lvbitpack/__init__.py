"""LabVIEW Boolean arrays in Python: Boolean Array To Number, its inverse, and flattening.

>>> import lvbitpack
>>> lvbitpack.bools_to_number([False, True], lvbitpack.I8)
-2
"""

from ._bytes import bools_to_bytes, bytes_to_bools, bytes_to_number, number_to_bytes
from ._errors import BitpackError
from ._flatten import pack_flattened, unpack_flattened
from ._number import bools_to_number, number_to_bools
from ._pack import pack_bools, unpack_bools
from ._types import I8, I16, I32, I64, U8, U16, U32, U64, IntType, SignExtension

__version__ = "1.0.0"

# Shown as lvbitpack.<Name> in tracebacks, help() and reprs, not as a private module.
for _public in (BitpackError, IntType, SignExtension):
    _public.__module__ = __name__
del _public

__all__ = [
    "I8",
    "I16",
    "I32",
    "I64",
    "U8",
    "U16",
    "U32",
    "U64",
    "BitpackError",
    "IntType",
    "SignExtension",
    "bools_to_bytes",
    "bools_to_number",
    "bytes_to_bools",
    "bytes_to_number",
    "number_to_bools",
    "number_to_bytes",
    "pack_bools",
    "pack_flattened",
    "unpack_bools",
    "unpack_flattened",
]
