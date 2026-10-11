# lvbitpack

Pack and unpack LabVIEW boolean arrays to and from their MSB-first bit-packed binary form.

## Install

```
pip install lvbitpack
```

## Usage

```python
from lvbitpack import pack_bools, unpack_bools, pack_flattened, unpack_flattened

# Raw packed bits, MSB-first, no header.
packed = pack_bools([True, True, False, True])
assert packed == b"\xd0"                       # bits fill from 0x80 downward
assert unpack_bools(packed, 4) == [True, True, False, True]

# The count drops the zero padding of the final byte.
assert unpack_bools(b"\x80", 1) == [True]

# LabVIEW "Flatten To String" form: a four-byte big-endian count, then the bits.
blob = pack_flattened([True] * 9)
assert blob == b"\x00\x00\x00\x09\xff\x80"
assert unpack_flattened(blob) == [True] * 9
```

The first boolean occupies the most significant bit (0x80) of the first byte, the
next goes to the next bit down, and so on. When the number of booleans is not a
multiple of eight, the remaining low bits of the final byte are zero padding.
`unpack_bools` takes the element count so it can discard that padding; the
flattened helpers read and write the count for you.

## Why

LabVIEW stores a flattened boolean array as packed bits, one bit per boolean,
MSB-first within each byte, prefixed by a 32-bit big-endian element count and
padded to a byte boundary. The MSB-first packing itself, the only non-trivial
piece, is not special: `bitarray` supports MSB-first (big-endian) bit order and
`bitstring` numbers bits MSB0 by default, so either already does that part. What
they do not add is the LabVIEW-specific 32-bit big-endian count header that wraps
the bits, so on their own they neither read a flattened boolean array nor produce
one a LabVIEW VI will accept. `lvbitpack` is a thin convenience over that exact
form, the MSB-first bits plus the count header and the final-byte padding, and
nothing else: zero dependencies, fully typed, and no extra package to install for
a one-field decode.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
