"""Boolean Array To Number and Number To Boolean Array against NI's table and an oracle."""

from __future__ import annotations

import itertools
import random

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
    number_to_bools,
)

ALL = [U8, U16, U32, U64, I8, I16, I32, I64]
F, T = False, True
NEVER, IF_SIGNED, ALWAYS = SignExtension.NEVER, SignExtension.IF_SIGNED, SignExtension.ALWAYS

# Every row of the table on NI's Boolean Array To Number page, fetched 2026-10-14:
# https://www.ni.com/docs/en-US/bundle/labview-api-ref/page/functions/boolean-array-to-number.html
NI_TABLE = [
    ([F, T], I8, IF_SIGNED, "11111110", -2),
    ([F, T], U8, IF_SIGNED, "00000010", 2),
    ([F, T, F, T], I8, ALWAYS, "11111010", -6),
    ([F, T, F, T], I8, NEVER, "00001010", 10),
    ([F, F, T, F, T], U8, IF_SIGNED, "00010100", 20),
    ([F, F, T, F, T], U8, ALWAYS, "11110100", 244),
]


def oracle(values: list[bool], int_type: IntType, mode: SignExtension) -> int:
    """An independent model: build the binary text MSB first, then read it."""
    bits = values[: int_type.bits]
    last = values[-1] if values else False
    pad = mode is ALWAYS or (mode is IF_SIGNED and int_type.signed)
    fill = "1" if pad and last else "0"
    text = fill * (int_type.bits - len(bits)) + "".join("1" if b else "0" for b in reversed(bits))
    value = int(text, 2)
    if int_type.signed and text[0] == "1":
        value -= 2**int_type.bits
    return value


@pytest.mark.parametrize(("values", "int_type", "mode", "binary", "number"), NI_TABLE)
def test_every_row_of_nis_table(
    values: list[bool], int_type: IntType, mode: SignExtension, binary: str, number: int
) -> None:
    assert bools_to_number(values, int_type, sign_extension=mode) == number
    assert format(number & 0xFF, "08b") == binary
    assert oracle(values, int_type, mode) == number


def test_the_default_mode_is_if_signed() -> None:
    assert bools_to_number([F, T], I8) == -2
    assert bools_to_number([F, T], U8) == 2


@pytest.mark.parametrize("int_type", [U8, I8])
@pytest.mark.parametrize("mode", list(SignExtension))
def test_every_array_up_to_ten_elements_matches_the_oracle(
    int_type: IntType, mode: SignExtension
) -> None:
    for length in range(11):
        for values in itertools.product([F, T], repeat=length):
            array = list(values)
            assert bools_to_number(array, int_type, sign_extension=mode) == oracle(
                array, int_type, mode
            )


@pytest.mark.parametrize("int_type", ALL)
@pytest.mark.parametrize("mode", list(SignExtension))
def test_seeded_arrays_of_every_length_match_the_oracle(
    int_type: IntType, mode: SignExtension
) -> None:
    rng = random.Random(f"{int_type.name}-{mode.value}")
    for length in range(int_type.bits + 3):
        for _ in range(12):
            array = [rng.random() < 0.5 for _ in range(length)]
            result = bools_to_number(array, int_type, sign_extension=mode)
            assert result == oracle(array, int_type, mode)
            assert int_type.min <= result <= int_type.max


@pytest.mark.parametrize("int_type", ALL)
def test_an_empty_array_is_zero_in_every_mode(int_type: IntType) -> None:
    for mode in SignExtension:
        assert bools_to_number([], int_type, sign_extension=mode) == 0


def test_elements_beyond_the_width_are_dropped() -> None:
    assert bools_to_number([T] * 8 + [F, T], U8) == 255
    assert bools_to_number([F] * 8 + [T] * 30, I8, sign_extension=ALWAYS) == 0
    assert bools_to_number([T] * 64 + [F], I64) == -1


def test_a_full_array_ignores_the_mode() -> None:
    array = [F] * 7 + [T]
    assert {bools_to_number(array, I8, sign_extension=m) for m in SignExtension} == {-128}
    assert {bools_to_number(array, U8, sign_extension=m) for m in SignExtension} == {128}


def test_unsigned_if_signed_never_extends() -> None:
    assert bools_to_number([T], U16) == 1
    assert bools_to_number([T], U16, sign_extension=ALWAYS) == 0xFFFF


def test_signed_extension_copies_the_last_element_not_the_first() -> None:
    assert bools_to_number([T, F], I8) == 1
    assert bools_to_number([F, F, T], I16) == -4
    assert bools_to_number([T, T, F], I16, sign_extension=ALWAYS) == 3


@pytest.mark.parametrize("int_type", ALL)
def test_number_to_bools_gives_one_element_per_bit_lsb_first(int_type: IntType) -> None:
    rng = random.Random(int_type.name)
    edges = [int_type.min, int_type.max, 0, 1, -1 if int_type.signed else 2]
    for number in edges + [rng.randint(int_type.min, int_type.max) for _ in range(300)]:
        bits = number_to_bools(number, int_type)
        assert len(bits) == int_type.bits
        expected = format(number & int_type.mask, f"0{int_type.bits}b")[::-1]
        assert "".join("1" if b else "0" for b in bits) == expected
        assert bools_to_number(bits, int_type, sign_extension=NEVER) == number


def test_number_to_bools_documented_examples() -> None:
    assert number_to_bools(2, U8) == [F, T, F, F, F, F, F, F]
    assert number_to_bools(-2, I8) == [F] + [T] * 7
    assert number_to_bools(-1, I64) == [T] * 64
    assert number_to_bools(1 << 63, U64) == [F] * 63 + [T]


@pytest.mark.parametrize("int_type", ALL)
def test_values_outside_the_type_are_refused(int_type: IntType) -> None:
    for number in (int_type.min - 1, int_type.max + 1):
        with pytest.raises(ValueError, match="out of range"):
            number_to_bools(number, int_type)
