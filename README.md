# lvbitpack

Pack and unpack LabVIEW boolean arrays: compact bit-packed bytes and the
**Boolean Array To Number** / **Number To Boolean Array** conversion. Zero
dependencies, fully typed.

## Install

```
pip install lvbitpack
```

## Boolean Array To Number

LabVIEW's Boolean Array To Number maps a boolean array onto a single fixed-width
integer. Element index 0 is the least significant bit (LSB).

```python
from lvbitpack import bools_to_number, number_to_bools, U8, I8, SignExtension

# Element 0 is the LSB, so {FALSE, TRUE} is the number 2.
assert bools_to_number([False, True], U8) == 2

# Elements beyond the width are dropped.
assert bools_to_number([True] * 9, U8) == 255

# A signed type uses two's complement. Under LabVIEW's default sign-extension
# mode a short signed array pads with its last element, so {FALSE, TRUE} is -2.
assert bools_to_number([False, True], I8) == -2
assert bools_to_number([False, True, False, True], I8, sign_extension=SignExtension.NEVER) == 10
assert bools_to_number([False, True, False, True], I8, sign_extension=SignExtension.ALWAYS) == -6

# The inverse: element 0 holds the LSB of the two's complement form.
assert number_to_bools(2, U8) == [False, True, False, False, False, False, False, False]
assert number_to_bools(-2, I8) == [False, True, True, True, True, True, True, True]
```

### Sign-extension modes

When the array is shorter than the integer width, the padding bit is chosen by the
mode, matching LabVIEW's right-click "Sign Extension Mode":

- `SignExtension.NEVER`: padding is always FALSE (zero padding).
- `SignExtension.IF_SIGNED` (default): unsigned types pad with FALSE, signed types
  pad with the array's last element.
- `SignExtension.ALWAYS`: padding is always the array's last element.

### Types and bytes

`U8`, `U16`, `U32`, `U64`, `I8`, `I16`, `I32`, `I64` are ready-made `IntType`
values; build others with `IntType(bits, signed)` or `IntType.parse("u16")`.

The array bit order is fixed and independent of byte endianness. Byte order only
decides how the resulting number is laid out in memory:

```python
from lvbitpack import bools_to_bytes, bytes_to_bools, U16

assert bools_to_bytes([False, True], U16, byteorder="big") == b"\x00\x02"
assert bools_to_bytes([False, True], U16, byteorder="little") == b"\x02\x00"
assert bytes_to_bools(b"\x02\x00", U16, byteorder="little") == number_to_bools(2, U16)
```

## Command line

```
lvbitpack pack 01 --type u8                 # element 0 is the LSB, prints 2
lvbitpack pack 0101 --type i8 -s always     # prints -6
lvbitpack unpack 2 --type u8                # prints 01000000
lvbitpack unpack -2 --type i8               # prints 01111111
lvbitpack --version
```

Bit strings read element 0 first. Errors go to stderr with exit code 1.

## Raw bit packing

The original helpers pack booleans as bits without any number interpretation,
MSB-first within each byte, and add the LabVIEW count header on request.

```python
from lvbitpack import pack_bools, unpack_bools, pack_flattened, unpack_flattened

# Raw packed bits, MSB-first, no header. The first boolean fills 0x80.
packed = pack_bools([True, True, False, True])
assert packed == b"\xd0"
assert unpack_bools(packed, 4) == [True, True, False, True]

# A four-byte big-endian element count followed by the packed bits.
blob = pack_flattened([True] * 9)
assert blob == b"\x00\x00\x00\x09\xff\x80"
assert unpack_flattened(blob) == [True] * 9
```

## How the three formats differ

These are three distinct wire formats. Pick by what you are reading or writing:

- **Boolean Array To Number** (`bools_to_number`): the array's bits become one
  fixed-width integer, element 0 the LSB. No header, no per-element bytes.
- **Raw bit packing** (`pack_bools`): one bit per boolean, MSB-first, padded to a
  byte boundary, with no header and no number interpretation.
- **Flattened boolean array**: LabVIEW's Flatten To String of a boolean *array*
  writes a 32-bit big-endian element count and then **one byte per element**
  (0x00 or 0x01), not bit-packed. `pack_flattened` here instead writes the count
  followed by the compact bit-packed form, so it is a compact variant and not the
  byte-per-element layout a LabVIEW Unflatten of a boolean array expects. Use it
  only when both ends agree on this compact form.

## License

MIT. See [LICENSE](LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
