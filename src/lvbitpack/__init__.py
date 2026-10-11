"""Pack and unpack LabVIEW boolean arrays: bit-packed bytes and Boolean Array To Number."""

from __future__ import annotations

from ._bytes import bools_to_bytes, bytes_to_bools, bytes_to_number, number_to_bytes
from ._flatten import pack_flattened, unpack_flattened
from ._number import (
    I8,
    I16,
    I32,
    I64,
    U8,
    U16,
    U32,
    U64,
    IntType,
    SignExtension,
    bools_to_number,
    number_to_bools,
)
from ._pack import pack_bools, unpack_bools

__version__ = "0.2.0"

__all__ = [
    "I8",
    "I16",
    "I32",
    "I64",
    "U8",
    "U16",
    "U32",
    "U64",
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
