# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

- First release.
- `pack_bools` and `unpack_bools`: MSB-first bit packing with zero padding of the
  final byte and count-aware unpacking.
- `pack_flattened` and `unpack_flattened`: the LabVIEW Flatten To String form, a
  four-byte big-endian element count followed by the packed bits.
