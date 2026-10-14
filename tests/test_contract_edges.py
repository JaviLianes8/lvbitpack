"""Contracts added by the mutation rounds, and checks proving two mutants equivalent."""

from __future__ import annotations

import itertools

import pytest

from lvbitpack import (
    I8,
    I16,
    I32,
    I64,
    U8,
    U16,
    U32,
    U64,
    IntType,
    SignExtension,
    bools_to_number,
)

ALL = [U8, U16, U32, U64, I8, I16, I32, I64]


@pytest.mark.parametrize("int_type", ALL)
def test_parse_reads_every_prefix_with_its_signedness(int_type: IntType) -> None:
    short = "i" if int_type.signed else "u"
    long = "int" if int_type.signed else "uint"
    for name in (short, long, short.upper(), long.upper(), f" {long.title()}"):
        assert IntType.parse(f"{name}{int_type.bits}") == int_type


@pytest.mark.parametrize("int_type", ALL)
def test_an_array_exactly_as_wide_as_the_type_is_never_padded(int_type: IntType) -> None:
    # Padding a full array touches no bit: the padding mask is empty at that length.
    full = [False] * (int_type.bits - 1) + [True]
    for mode in SignExtension:
        expected = int_type.min if int_type.signed else 1 << (int_type.bits - 1)
        assert bools_to_number(full, int_type, sign_extension=mode) == expected


def test_unsigned_results_never_exceed_the_maximum() -> None:
    # The two's complement step never applies to an unsigned type: its maximum is its mask.
    for values in itertools.product([False, True], repeat=9):
        for mode in SignExtension:
            assert 0 <= bools_to_number(list(values), U8, sign_extension=mode) <= 255
