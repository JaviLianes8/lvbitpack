# Improvements round: LabVIEW Boolean Array To Number and Number To Boolean Array

This round adds a faithful, additive implementation of LabVIEW's **Boolean Array To
Number** and **Number To Boolean Array** primitives, with configurable integer width,
signed two's complement, the three documented sign-extension modes, byte serialization,
honest errors, typed results, and a command line interface. Nothing existing is removed
or changed; every new name is purely additive.

## Ground truth (NI documented semantics)

Source: NI LabVIEW API reference, "Boolean Array To Number" and "Number To Boolean
Array". Each claim below was reproduced in a plain Python session before it was coded.

- **Element index 0 is the least significant bit (LSB).** `{FALSE, TRUE}` reads as the
  number 2 for an unsigned 8-bit output.
- **Bit order is independent of byte endianness.** The array to bit mapping is fixed
  (index 0 is the LSB); byte order only matters when the resulting number is serialized
  to bytes.
- **Extra elements are dropped.** If the array is longer than the integer width, the
  elements beyond the width are ignored.
- **Short arrays are padded per the Sign Extension Mode** (set by right-clicking the
  node in LabVIEW):
  - `NEVER`: padding bits are always FALSE (zero padding).
  - `IF_SIGNED` (LabVIEW default): unsigned outputs pad with FALSE, signed outputs pad
    with the array's last element (sign extension).
  - `ALWAYS`: padding bits are always the array's last element.
- **Signed outputs use two's complement.** Documented vectors, all reproduced:
  `{FALSE, TRUE}` as I8 (default mode) is -2 (0b11111110);
  `{FALSE, TRUE, FALSE, TRUE}` as I8 is 10 under NEVER and -6 under ALWAYS.
- **Number To Boolean Array** returns an 8, 16, 32, or 64 element array for an integer
  input, with element 0 holding the LSB of the two's complement representation.

## Honest distinction from a flattened boolean array

This packing is **not** the same as LabVIEW's *Flatten To String* form of a boolean
**array**. A flattened boolean array prefixes a 32-bit big-endian element count and then
stores **one byte per element** (0x00 or 0x01), not bit-packed. Boolean Array To Number
instead maps the array's bits directly onto the bits of a single fixed-width integer.
The two are different wire formats and must not be confused; this is documented in the
README and the module docstrings. The existing `pack_flattened` helper is a separate,
pre-existing concern and is left untouched.

## Ranked improvements

1. **`bools_to_number` (Boolean Array To Number).** Core primitive. LSB-first, any of
   U8/U16/U32/U64/I8/I16/I32/I64, all three sign-extension modes, extra elements
   dropped, signed two's complement. Highest value: it is the headline function and the
   one most error prone to hand roll.

2. **`number_to_bools` (Number To Boolean Array).** The inverse. Returns a width-length
   boolean list, element 0 the LSB of the two's complement form. Range-checked against
   the target type with an honest error.

3. **Typed `IntType` value object plus the eight presets (`U8`..`I64`).** A frozen,
   hashable descriptor carrying bit width and signedness, exposing `name`, `min`, `max`,
   `mask`, `contains`, and a `parse` classmethod. Makes every call self-documenting and
   removes stringly-typed width arguments.

4. **`SignExtension` enum.** Names the three documented modes explicitly instead of a
   bare boolean, with `IF_SIGNED` as the LabVIEW-matching default.

5. **Byte serialization: `number_to_bytes`, `bytes_to_number`, `bools_to_bytes`,
   `bytes_to_bools`.** Round trip to and from raw little or big endian bytes. Proves and
   documents that the array bit order is independent of byte endianness.

6. **Honest errors.** Out-of-range numbers, bad bit widths, wrong byte lengths, and
   unknown type names all raise `ValueError` with a specific message, never a silent
   wrap or truncation (truncation of a too-long array is the one documented, intentional
   behavior and is kept).

7. **Command line interface (`lvbitpack`).** `pack` (bits to number) and `unpack`
   (number to bits) subcommands, `--type`, `--sign-extension`, `--base`, `--version`,
   and a `--help` with runnable examples. Errors go to stderr with exit code 1.

8. **Contract test and real end-to-end test.** A contract test pins the complete
   documented promise (the vectors above). A real e2e test pip-installs the package
   editable and drives the installed `lvbitpack` console script through a subprocess,
   asserting real stdout and exit codes.

## Deliberately out of scope

- No change to `pack_bools`, `unpack_bools`, `pack_flattened`, `unpack_flattened`.
- No floating point or fixed-point representations (LabVIEW fixed-point word lengths of
  1 to 63 bits are noted in docs but left for a future round).
- No third-party dependencies; the library stays zero-dependency and fully typed.
