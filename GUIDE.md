# lvbitpack guide

Every example below runs as written; the test suite executes them.

## Boolean Array To Number

`bools_to_number(values, int_type, *, sign_extension=SignExtension.IF_SIGNED)` reads the
array as the binary form of one integer. Element 0 is the least significant bit.

```pycon
>>> from lvbitpack import I8, I16, U8, SignExtension, bools_to_number
>>> bools_to_number([False, True], U8)
2
>>> bools_to_number([True] * 8 + [False, True], U8)
255
>>> bools_to_number([], I16)
0

```

Elements past the width are dropped. A shorter array is padded above its last element as
the sign extension mode (set by right-clicking the node in LabVIEW) says:

| Mode | Unsigned output pads with | Signed output pads with |
| --- | --- | --- |
| `SignExtension.NEVER` | FALSE | FALSE |
| `SignExtension.IF_SIGNED` (LabVIEW's default) | FALSE | the last element |
| `SignExtension.ALWAYS` | the last element | the last element |

```pycon
>>> from lvbitpack import I8, U8, SignExtension, bools_to_number
>>> array = [False, False, True, False, True]
>>> [bools_to_number(array, U8, sign_extension=mode) for mode in SignExtension]
[20, 20, 244]
>>> [bools_to_number(array, I8, sign_extension=mode) for mode in SignExtension]
[20, -12, -12]

```

A signed output is the two's complement value; an empty array is 0 in every mode. The test
suite replays about 2,900 results of this node and 200 of Number To Boolean Array produced
by LabVIEW 2026 (all eight types, the three modes, arrays of 0 to 65 elements; see
`tests/fixtures/labview2026`). There a node with no output representation set gave a U32
(it was inserted by editing a VI file; NI does not document the default).

## Number To Boolean Array

`number_to_bools(number, int_type)` returns one element per bit of the type, element 0 the
least significant bit of the two's complement form. A number outside the type raises
`BitpackError` (LabVIEW would have coerced it to the wire's type first).

```pycon
>>> from lvbitpack import I8, U64, number_to_bools
>>> number_to_bools(-2, I8)
[False, True, True, True, True, True, True, True]
>>> len(number_to_bools(5, U64))
64

```

## Integer types

`IntType(bits, signed)` takes 8, 16, 32 or 64 bits. `U8`, `U16`, `U32`, `U64`, `I8`, `I16`,
`I32` and `I64` are ready-made, and `IntType.parse` reads names in any case.

```pycon
>>> from lvbitpack import IntType, I32
>>> IntType.parse("int32") == I32
True
>>> I32.name, I32.min, I32.max, hex(I32.mask)
('i32', -2147483648, 2147483647, '0xffffffff')
>>> I32.contains(2**31)
False

```

## Bytes of the number

`number_to_bytes`, `bytes_to_number`, `bools_to_bytes` and `bytes_to_bools` lay the number
out in exactly `bits // 8` bytes. The default is big-endian, LabVIEW's flattened order;
pass `byteorder="little"` for the memory order of x86 and ARM machines. The element to bit
mapping never changes with byte order.

```pycon
>>> from lvbitpack import I32, U16, bools_to_bytes, bytes_to_number, number_to_bytes
>>> number_to_bytes(-19, I32).hex()
'ffffffed'
>>> bytes_to_number(bytes.fromhex("edffffff"), I32, byteorder="little")
-19
>>> bools_to_bytes([False, True], U16, byteorder="little")
b'\x02\x00'

```

## Flattened Boolean arrays

`pack_flattened` writes what LabVIEW's Flatten To String writes for a 1-D Boolean array with
its "prepend array or string size?" input left at its default (TRUE): a big-endian I32
element count, then one byte per element, 0x01 for TRUE and 0x00 for FALSE.
`unpack_flattened` reads it back; any nonzero element byte is TRUE, and the input must hold
exactly the counted elements.

```pycon
>>> from lvbitpack import pack_flattened, unpack_flattened
>>> pack_flattened([True, False, True, True]).hex()
'0000000401000101'
>>> unpack_flattened(bytes.fromhex("00000002ff00"))
[True, False]

```

## Dense bit packing

`pack_bools` stores eight elements per byte with no header, filling unused bits of the last
byte with zeros. `bit_order="msb"` (default) puts element 0 in bit 7 of byte 0; `"lsb"` puts
it in bit 0, so each byte equals Boolean Array To Number of its eight elements as a U8.
`unpack_bools(data, count=None)` reads `count` elements, or every bit when `count` is None.
Current LabVIEW stores and flattens a Boolean as a whole byte; this form is for protocols
and files that pack bits.

```pycon
>>> from lvbitpack import pack_bools, unpack_bools
>>> pack_bools([True] * 9), pack_bools([True] * 9, bit_order="lsb")
(b'\xff\x80', b'\xff\x01')
>>> unpack_bools(b"\xd0", 4)
[True, True, False, True]

```

## What counts as input

- A Boolean array is any finite iterable (list, tuple, generator, NumPy array) of `True`,
  `False`, 0, 1 (or `__index__` objects giving 0 or 1) or NumPy booleans; the hints say
  `Iterable[bool | int]`. `str`, `bytes`, `bytearray` and `memoryview` are refused: `"0101"`
  is not four Booleans. A set has no element order, so pass a sequence.
- Numbers, counts and `IntType` widths accept any `__index__` integer except `bool`
  (`number` and `count` are typed `SupportsIndex`; elsewhere a type checker wants `int(...)`
  or `bool(...)` around NumPy scalars). `IntType.contains` answers False for anything else.
- Bytes are any buffer-protocol object (`bytes`, `bytearray`, `memoryview`, `array.array`,
  NumPy arrays, ctypes objects), read as raw bytes in memory order. Text, lists and buffers
  of Python objects (a NumPy `object` array) are refused.

```pycon
>>> import array
>>> from lvbitpack import U16, bytes_to_number
>>> bytes_to_number(array.array("B", [1, 0]), U16)
256

```

## Errors

Every refusal raises `BitpackError`, a subclass of `ValueError`, including
`SignExtension(value)` for any value that is not a member or one of its three names.
Messages are printable ASCII, quote at most 40 characters of a bad value and describe
integers wider than 128 bits by their size. Checks use an object's real type, never a
`__class__` it claims. An object that cannot be iterated, indexed or read as a buffer at
all is refused; any other exception your own object raises (from `__index__`, `__iter__`,
while iterating, or from `__buffer__` on Python 3.12 and later, except a `ValueError`)
passes through unchanged, as do ordinary call mistakes such as a missing argument.

| Situation | Message starts with |
| --- | --- |
| number outside the type | `<n> is out of range for <type>` |
| element that is not a Boolean | `element <i> must be a boolean` |
| text or bytes as the array | `values must be an iterable of booleans` |
| wrong byte count for a number | `<type> needs exactly <n> bytes` |
| short flattened array | `a flattened array starts`, `the count says` |
| negative count, extra bytes | `the element count is negative`, `<n> byte(s) follow(s)` |
| bad option or `int_type` | the parameter's name |

## Command line

```
$ lvbitpack pack 01 --type u8
2
$ lvbitpack pack 01 --type i8
-2
$ lvbitpack pack 0101 --type i8 --sign-extension always
-6
$ lvbitpack pack 1 --type u16 --base hex
0x1
$ lvbitpack unpack 0x80 --type u8
00000001
$ lvbitpack flatten 1011
0000000401000101
$ lvbitpack unflatten 0000000401000101
1011
```

Bit strings list element 0 first; `1`, `t`, `T` are TRUE, `0`, `f`, `F` FALSE, and spaces,
commas and underscores are ignored. `unpack` reads decimal or `0x`, `0o`, `0b` prefixed
numbers in ASCII digits, negative ones included (`unpack -0x80 -t i8`). Data errors print
`lvbitpack: error: ...` and exit 1; usage errors, an unknown `--type` included, exit 2.

## Scope

Boolean Array To Number can also produce a fixed-point number, and Number To Boolean Array
accepts one; lvbitpack covers the eight integer types. Multi-dimensional arrays are not
flattened here.
