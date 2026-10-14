# lvbitpack

LabVIEW Boolean arrays in pure Python: **Boolean Array To Number** with its three sign
extension modes, **Number To Boolean Array**, the flattened form LabVIEW writes for a Boolean
array, and compact bit packing. No dependencies, fully typed, Python 3.10 or newer.

The full reference is the [guide](https://github.com/JaviLianes8/lvbitpack/blob/main/GUIDE.md);
every release is described in the
[changelog](https://github.com/JaviLianes8/lvbitpack/blob/main/CHANGELOG.md).

## Install

```
pip install lvbitpack
```

## The problem

A LabVIEW program that reads digital lines, status registers or flag words often turns a
Boolean array into one integer with Boolean Array To Number, and back with Number To Boolean
Array. Element 0 is the least significant bit, elements past the width are dropped, and a
short array is padded by a per-node setting (Sign Extension Mode) that most people never
look at, yet it decides whether `{FALSE, TRUE}` as an I8 is 2 or -2. Getting the same
numbers in Python means reproducing those rules exactly.

## Quick start

```python
from lvbitpack import I8, U8, U16, SignExtension, bools_to_number, number_to_bools

# Element 0 is the least significant bit.
assert bools_to_number([False, True], U8) == 2

# LabVIEW's default mode pads a signed output with the last element: {F, T} as I8 is -2.
assert bools_to_number([False, True], I8) == -2
assert bools_to_number([False, True, False, True], I8, sign_extension=SignExtension.NEVER) == 10
assert bools_to_number([False, True, False, True], I8, sign_extension=SignExtension.ALWAYS) == -6

# Elements beyond the width are dropped.
assert bools_to_number([True] * 9, U8) == 255

# The inverse returns one element per bit of the type.
assert number_to_bools(-2, I8) == [False, True, True, True, True, True, True, True]
assert len(number_to_bools(1, U16)) == 16
```

Bytes, LabVIEW's flattened array and dense bit packing:

```python
from lvbitpack import U16, bools_to_bytes, pack_bools, pack_flattened, unpack_flattened

# The number's bytes, big-endian by default like LabVIEW's Flatten To String.
assert bools_to_bytes([False, True], U16) == b"\x00\x02"
assert bools_to_bytes([False, True], U16, byteorder="little") == b"\x02\x00"

# Flatten To String of a Boolean array: an I32 count, then one byte per element.
assert pack_flattened([True, False, True, True]).hex() == "0000000401000101"
assert unpack_flattened(bytes.fromhex("0000000401000101")) == [True, False, True, True]

# Eight elements per byte, first element in the high bit (or the low bit with "lsb").
assert pack_bools([True, True, False, True]) == b"\xd0"
assert pack_bools([True, True, False, True], bit_order="lsb") == b"\x0b"
```

Anything refused (a value out of range, a string where a Boolean array belongs, a truncated
flattened array) raises `lvbitpack.BitpackError`, a `ValueError`.

## Command line

```
$ lvbitpack pack 01 --type i8
-2
$ lvbitpack pack 0101 --type i8 --sign-extension never
10
$ lvbitpack unpack -2 --type i8
01111111
$ lvbitpack flatten 1011
0000000401000101
```

Bit strings list element 0 first. `python -m lvbitpack` works too.

## Why this library

- It follows LabVIEW's own rules: the three Sign Extension Mode settings, truncation of long
  arrays, the 8, 16, 32 and 64-bit signed and unsigned outputs, and the flattened Boolean
  array layout, checked against NI's documentation and against output of LabVIEW 2026.
- NumPy's `packbits` packs 0/1 arrays into `uint8` bytes (high or low bit first) but has no
  notion of LabVIEW's integer widths or sign extension, and needs NumPy. `bitarray` (a C
  extension) and `bitstring` (which depends on `tibs`) are general bit containers; neither
  reproduces Boolean Array To Number. lvbitpack is small, pure Python and dependency free.

What it does not cover: Boolean Array To Number with a fixed-point output (see the guide).

## License

MIT. See [LICENSE](https://github.com/JaviLianes8/lvbitpack/blob/main/LICENSE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
