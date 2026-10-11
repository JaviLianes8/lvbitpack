# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0]

- `bools_to_number` and `number_to_bools`: LabVIEW Boolean Array To Number and
  Number To Boolean Array, element 0 the least significant bit, U8/U16/U32/U64 and
  signed I8/I16/I32/I64 two's complement, extra elements dropped, and the three
  documented sign-extension modes for short arrays.
- `SignExtension` enum and the typed `IntType` value object with the `U8` to `I64`
  presets, bounds, mask, and a `parse` helper.
- `number_to_bytes`, `bytes_to_number`, `bools_to_bytes`, and `bytes_to_bools`:
  little or big endian serialization, with the array bit order independent of byte
  order.
- `lvbitpack` command line interface: `pack` (bits to number) and `unpack` (number
  to bits) with `--type`, `--sign-extension`, `--base`, and `--version`.

## [0.1.0]

- First release.
- `pack_bools` and `unpack_bools`: MSB-first bit packing with zero padding of the
  final byte and count-aware unpacking.
- `pack_flattened` and `unpack_flattened`: the LabVIEW Flatten To String form, a
  four-byte big-endian element count followed by the packed bits.
