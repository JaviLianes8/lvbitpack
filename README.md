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
padded to a byte boundary. Python's own tools do not speak this convention:
`int.to_bytes`, `struct` and the generic bit libraries (`bitarray`, `bitstring`)
have their own bit order and no notion of the LabVIEW count header, so they
cannot read a flattened boolean array or produce one a LabVIEW VI will accept.
No maintained Python package covers this LabVIEW-specific packing. lvbitpack does
exactly that and nothing else: zero dependencies, fully typed.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
