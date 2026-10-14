"""Command line interface: Boolean arrays to numbers and flattened bytes, and back."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from . import __version__
from ._cli_io import MESSAGE_LIMIT, Parser, finish, write
from ._errors import BitpackError, quote
from ._flatten import pack_flattened, unpack_flattened
from ._number import bools_to_number, number_to_bools
from ._types import IntType, SignExtension

_TRUE, _FALSE, _SKIP = frozenset("1tT"), frozenset("0fF"), frozenset(" ,_")
_NUMBER_LIMIT = 100  # characters; a 64-bit value never needs more

_EXAMPLES = """\
examples:
  lvbitpack pack 01 --type u8                    -> 2
  lvbitpack pack 01 --type i8                    -> -2
  lvbitpack pack 0101 --type i8 -s never         -> 10
  lvbitpack pack 0101 --type i8 -s always        -> -6
  lvbitpack pack 01 --type i8 --base hex         -> 0xfe
  lvbitpack unpack 2 --type u8                   -> 01000000
  lvbitpack unpack -2 --type i8                  -> 01111111
  lvbitpack flatten 1011                         -> 0000000401000101
  lvbitpack unflatten 0000000401000101           -> 1011

Bit strings list element 0 first; element 0 is the least significant bit of the number.
1/t/T is TRUE, 0/f/F is FALSE; spaces, commas and underscores are ignored. flatten prints
LabVIEW's Flatten To String bytes of the Boolean array as hex. Data errors print to stderr
and exit 1; usage errors exit 2.
"""


def _bits(text: str) -> list[bool]:
    bits: list[bool] = []
    for position, char in enumerate(text):
        if char in _SKIP:
            continue
        if char in _TRUE or char in _FALSE:
            bits.append(char in _TRUE)
        else:
            raise BitpackError(f"character {position} is {quote(char)}; use 0/1, f/t or F/T")
    return bits


def _number(text: str) -> int:
    if len(text) > _NUMBER_LIMIT:
        raise BitpackError(f"the number has {len(text)} characters; at most 100 are read")
    try:
        return int(text, 0)
    except ValueError:
        raise BitpackError(f"not an integer: {quote(text)}") from None


def _hex(text: str) -> bytes:
    cleaned = text.strip().removeprefix("0x").removeprefix("0X").replace("_", "")
    try:
        return bytes.fromhex(cleaned)
    except ValueError:
        raise BitpackError(f"not valid hex: {quote(text)}") from None


def _show(bits: list[bool]) -> str:
    return "".join("1" if bit else "0" for bit in bits)


def _build_parser() -> argparse.ArgumentParser:
    parser = Parser(
        prog="lvbitpack",
        description="LabVIEW Boolean Array To Number, Number To Boolean Array and flattening.",
        epilog=_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"lvbitpack {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    types = "u8, u16, u32, u64, i8, i16, i32 or i64"

    pack = sub.add_parser("pack", help="Boolean array to number")
    pack.add_argument("bits", help="bit string, element 0 (the LSB) first, e.g. 01 or 0,1")
    pack.add_argument("--type", "-t", required=True, help=f"integer type: {types}")
    pack.add_argument(
        "--sign-extension",
        "-s",
        choices=[mode.value for mode in SignExtension],
        default=SignExtension.IF_SIGNED.value,
        help="padding of a short array (default: if_signed, LabVIEW's default)",
    )
    pack.add_argument("--base", choices=["dec", "hex"], default="dec", help="output base")

    unpack = sub.add_parser("unpack", help="number to Boolean array")
    unpack.add_argument("number", help="integer: decimal, or 0x/0o/0b prefixed")
    unpack.add_argument("--type", "-t", required=True, help=f"integer type: {types}")

    flatten = sub.add_parser("flatten", help="Boolean array to LabVIEW flattened bytes (hex)")
    flatten.add_argument("bits", help="bit string, element 0 first")
    unflatten = sub.add_parser("unflatten", help="LabVIEW flattened bytes (hex) to bit string")
    unflatten.add_argument("hex", help="the flattened bytes as hex")
    return parser


def _run(args: argparse.Namespace) -> str:
    if args.command == "pack":
        int_type = IntType.parse(args.type)
        mode = SignExtension(args.sign_extension)
        number = bools_to_number(_bits(args.bits), int_type, sign_extension=mode)
        return f"0x{number & int_type.mask:x}" if args.base == "hex" else str(number)
    if args.command == "unpack":
        int_type = IntType.parse(args.type)
        return _show(number_to_bools(_number(args.number), int_type))
    if args.command == "flatten":
        return pack_flattened(_bits(args.bits)).hex()
    return _show(unpack_flattened(_hex(args.hex)))


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the ``lvbitpack`` console command.

    Exit codes: 0 done, 1 bad data (or the reader of the output went away), 2 bad usage.

    >>> from lvbitpack._cli import main
    >>> main(["pack", "01", "--type", "i8"])
    -2
    0
    """
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as stop:
        return stop.code if isinstance(stop.code, int) else 2
    try:
        output = _run(args)
    except BitpackError as error:
        write("stderr", f"lvbitpack: error: {str(error)[:MESSAGE_LIMIT]}\n")
        return finish(1)
    return finish(0 if write("stdout", output + "\n") else 1)


if __name__ == "__main__":
    raise SystemExit(main())
