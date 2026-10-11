"""Pack and unpack LabVIEW boolean arrays to and from their MSB-first bit-packed binary form."""

from __future__ import annotations

from ._flatten import pack_flattened, unpack_flattened
from ._pack import pack_bools, unpack_bools

__version__ = "0.1.0"

__all__ = ["pack_bools", "pack_flattened", "unpack_bools", "unpack_flattened"]
