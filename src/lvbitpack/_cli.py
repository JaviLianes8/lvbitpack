"""Command line interface for lvbitpack.

pack converts a boolean array to a number (Boolean Array To Number); unpack
converts a number to a boolean array (Number To Boolean Array). Element 0 is the
least significant bit in both directions.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from . import __version__
from ._number import IntType, SignExtension, bools_to_number, number_to_bools

_TRUE_CHARS = frozenset("1tT")
_FALSE_CHARS = frozenset("0fF")

_EXAMPLES = """\
examples:
  lvbitpack pack 01 --type u8                 element 0 is the LSB, so 01 is 2
  lvbitpack pack 0101 --type i8 --sign-extension always   -> -6
  lvbitpack unpack 2 --type u8                -> 01000000
  lvbitpack unpack -2 --type i8               -> 01111111
  lvbitpack pack 01000000 --type u8 --base hex   -> 0x2
"""


def _parse_bits(text: str) -> list[bool]:
    """Parse a bit string into booleans. 1/t/T is True, 0/f/F is False; spaces and
    commas are ignored. Element 0 is the first character (the LSB)."""
    bits: list[bool] = []
    for char in text:
        if char in " ,":
            continue
        if char in _TRUE_CHARS:
            bits.append(True)
        elif char in _FALSE_CHARS:
            bits.append(False)
        else:
            raise ValueError(f"invalid bit character {char!r}; use 0/1, f/t, or F/T")
    return bits


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lvbitpack",
        description="LabVIEW Boolean Array To Number and Number To Boolean Array on the CLI.",
        epilog=_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--version", action="version", version=f"lvbitpack {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    pack = sub.add_parser("pack", help="boolean array to number")
    pack.add_argument("bits", help="bit string, element 0 first (the LSB), e.g. 01 or 0,1")
    pack.add_argument("--type", "-t", required=True, help="integer type: u8/u16/u32/u64 or i8..i64")
    pack.add_argument(
        "--sign-extension",
        "-s",
        choices=[mode.value for mode in SignExtension],
        default=SignExtension.IF_SIGNED.value,
        help="padding for a short array (default: if_signed, matching LabVIEW)",
    )
    pack.add_argument("--base", choices=["dec", "hex"], default="dec", help="output base")

    unpack = sub.add_parser("unpack", help="number to boolean array")
    unpack.add_argument("number", help="integer value, decimal or 0x-prefixed hex")
    unpack.add_argument(
        "--type", "-t", required=True, help="integer type: u8/u16/u32/u64 or i8..i64"
    )
    return parser


def _run_pack(args: argparse.Namespace) -> str:
    int_type = IntType.parse(args.type)
    bits = _parse_bits(args.bits)
    number = bools_to_number(bits, int_type, sign_extension=SignExtension(args.sign_extension))
    return f"0x{number & int_type.mask:x}" if args.base == "hex" else str(number)


def _run_unpack(args: argparse.Namespace) -> str:
    int_type = IntType.parse(args.type)
    number = int(args.number, 0)
    return "".join("1" if bit else "0" for bit in number_to_bools(number, int_type))


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for the lvbitpack console script. Returns the exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        output = _run_pack(args) if args.command == "pack" else _run_unpack(args)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
