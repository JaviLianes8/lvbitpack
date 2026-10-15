# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-14

First stable release, and the first one published on PyPI. The public API is the 21 names
in `lvbitpack.__all__`; their names, signatures, defaults and error type are now stable.

### Changed (from 0.2.0)

- `pack_flattened` and `unpack_flattened` now read and write LabVIEW's real flattened
  Boolean array: a big-endian I32 count, then one byte per element (0x01 / 0x00). In 0.2.0
  they wrote the count followed by bit-packed bytes, which LabVIEW cannot unflatten.
  `unpack_flattened` reads any nonzero byte as TRUE and refuses a negative count, missing
  elements and bytes left over after the last element.
- The byte functions (`number_to_bytes`, `bytes_to_number`, `bools_to_bytes`,
  `bytes_to_bools`) default to big-endian, LabVIEW's flattened order; 0.2.0 defaulted to
  little-endian.
- Every refusal raises the new `BitpackError` (a `ValueError`). In 0.2.0 some bad input
  leaked `TypeError` or `AttributeError` from inside, and some was silently accepted.
- Boolean arrays are checked: a `str` or bytes object is refused (0.2.0 read each
  character's truthiness, so `"0101"` gave 15), and elements must be booleans or 0/1.
- Arrays may be any finite iterable; 0.2.0 needed indexing, so generators failed, and
  `bools_to_number` refused NumPy arrays ("truth value of an array is ambiguous").
- `IntType` refuses a non-`int` or `bool` width and a non-`bool` `signed`; 0.2.0 accepted
  `IntType(8.0, "yes")`. `IntType.parse` accepts only the eight names (with `u`, `uint`, `i`,
  `int` prefixes); 0.2.0 accepted forms such as `"u08"`. A NumPy or other `__index__`
  width is accepted and stored as `int`, and a NumPy boolean `signed` is stored as `bool`. `IntType.contains` answers False for `bool` and
  floats (0.2.0 said True for `contains(1.0)` and `contains(True)`) and True for in-range
  `__index__` integers such as NumPy's.
- Byte arguments accept any buffer-protocol object and read its raw bytes, so a buffer
  of wide items (an `array.array("H")`, a NumPy `uint16` array) is measured in bytes; 0.2.0
  measured it in items. Lists of integers, which 0.2.0 read as bytes, are refused, and so
  are buffers of Python objects (a NumPy `object` array), which 0.2.0 read as pointer bytes.
- `number` and `count` are typed `SupportsIndex`, so NumPy integers pass a type checker.
- `SignExtension(...)` with anything but a member or one of its three names raises
  `BitpackError` (still a `ValueError`). `sign_extension=` takes only a `SignExtension`
  member: 0.2.0 silently treated a string such as `"never"` as `IF_SIGNED`.
- `IntType` and `SignExtension` are defined in private modules other than 0.2.0's
  (`lvbitpack._types`, `lvbitpack._modes`); pickles made by 0.2.0 still load.
- Numbers are checked: `bool` and non-integers are refused, `__index__` integers (NumPy)
  accepted, and messages never print a huge integer (0.2.0 failed inside its own message
  for integers beyond Python's 4300-digit printing limit).
- The command line prefixes errors with `lvbitpack: error:`, bounds every message, exits 1
  quietly when its output pipe closes, and runs as `python -m lvbitpack`. An unknown
  `--type` is a usage error (exit 2, was 1). Bit strings also ignore `_`; `unpack` refuses
  numbers longer than 100 characters or written with non-ASCII digits, and reads negative
  prefixed numbers such as `-0x2` on every supported Python.
- Public functions report `lvbitpack` as their module in `help()`; the classes keep the
  module they are defined in, so source lookup and pickles find them.

### Added

- `BitpackError`.
- `bit_order="msb" | "lsb"` on `pack_bools` and `unpack_bools`; `unpack_bools`'s `count` is
  now optional (every bit by default).
- `flatten` and `unflatten` commands.
- `GUIDE.md` with executed examples.

## [0.2.0]

- `bools_to_number` and `number_to_bools`: LabVIEW Boolean Array To Number and
  Number To Boolean Array, element 0 the least significant bit, U8/U16/U32/U64 and
  signed I8/I16/I32/I64 two's complement, extra elements dropped, and the three
  documented sign-extension modes for short arrays.
- `SignExtension` enum and the typed `IntType` value object with the `U8` to `I64`
  presets, bounds, mask, and a `parse` helper.
- `number_to_bytes`, `bytes_to_number`, `bools_to_bytes`, and `bytes_to_bools`.
- `lvbitpack` command line interface: `pack` and `unpack`.

## [0.1.0]

- `pack_bools` and `unpack_bools`: MSB-first bit packing with zero padding of the
  final byte and count-aware unpacking.
- `pack_flattened` and `unpack_flattened`: a four-byte big-endian element count
  followed by the packed bits.
