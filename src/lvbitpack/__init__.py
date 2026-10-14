"""LabVIEW Boolean arrays in Python: Boolean Array To Number, its inverse, and flattening.

>>> import lvbitpack
>>> lvbitpack.bools_to_number([False, True], lvbitpack.I8)
-2
>>> from lvbitpack import I8, I16, I32, I64, U8, U16, U32, U64
>>> [t.name for t in (U8, U16, U32, U64, I8, I16, I32, I64)]
['u8', 'u16', 'u32', 'u64', 'i8', 'i16', 'i32', 'i64']
"""

from ._bytes import bools_to_bytes, bytes_to_bools, bytes_to_number, number_to_bytes
from ._errors import BitpackError
from ._flatten import pack_flattened, unpack_flattened
from ._modes import SignExtension
from ._number import bools_to_number, number_to_bools
from ._pack import pack_bools, unpack_bools
from ._types import I8, I16, I32, I64, U8, U16, U32, U64, IntType

__version__ = "1.0.0"

# Functions show lvbitpack as their module in help(); classes keep their real module so
# that inspect.getsource and pickles find them where they are defined.
for _public in (
    bools_to_bytes,
    bools_to_number,
    bytes_to_bools,
    bytes_to_number,
    number_to_bools,
    number_to_bytes,
    pack_bools,
    pack_flattened,
    unpack_bools,
    unpack_flattened,
):
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
