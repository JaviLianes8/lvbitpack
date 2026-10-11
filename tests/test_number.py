"""Contract tests for the LabVIEW Boolean Array To Number semantics.

Every assertion here is a documented NI promise, reproduced as a fixed vector.
"""

import pytest

from lvbitpack import (
    I8,
    I16,
    U8,
    U16,
    U32,
    IntType,
    SignExtension,
    bools_to_bytes,
    bools_to_number,
    bytes_to_bools,
    bytes_to_number,
    number_to_bools,
    number_to_bytes,
)

F, T = False, True


def test_element_zero_is_the_least_significant_bit() -> None:
    assert bools_to_number([F, T], U8) == 2


def test_extra_elements_beyond_the_width_are_dropped() -> None:
    assert bools_to_number([T] * 9, U8) == 255


def test_short_unsigned_array_pads_with_false() -> None:
    assert bools_to_number([T], U8) == 1
    assert bools_to_number([F, T], U16) == 2


def test_signed_default_mode_sign_extends_from_the_last_element() -> None:
    # {FALSE, TRUE} as I8 is 0b11111110 == -2 under the LabVIEW default mode.
    assert bools_to_number([F, T], I8) == -2


def test_sign_extension_never_zero_pads_even_for_signed() -> None:
    assert bools_to_number([F, T, F, T], I8, sign_extension=SignExtension.NEVER) == 10


def test_sign_extension_always_pads_with_last_element() -> None:
    assert bools_to_number([F, T, F, T], I8, sign_extension=SignExtension.ALWAYS) == -6


def test_sign_extension_if_signed_matches_always_for_signed_types() -> None:
    assert bools_to_number([F, T, F, T], I8, sign_extension=SignExtension.IF_SIGNED) == -6


def test_sign_extension_if_signed_zero_pads_for_unsigned_types() -> None:
    assert bools_to_number([F, T, F, T], U8, sign_extension=SignExtension.IF_SIGNED) == 10


def test_empty_array_is_zero() -> None:
    assert bools_to_number([], U8) == 0
    assert bools_to_number([], I8, sign_extension=SignExtension.ALWAYS) == 0


def test_number_to_bools_puts_the_lsb_first() -> None:
    assert number_to_bools(2, U8) == [F, T, F, F, F, F, F, F]


def test_number_to_bools_uses_twos_complement_for_signed() -> None:
    assert number_to_bools(-2, I8) == [F, T, T, T, T, T, T, T]


def test_number_to_bools_length_matches_the_width() -> None:
    assert len(number_to_bools(0, U16)) == 16


@pytest.mark.parametrize("int_type", [U8, U16, U32, I8, I16])
def test_round_trip_number_to_bools_and_back(int_type: IntType) -> None:
    for number in (int_type.min, 0, int_type.max, int_type.max // 3):
        assert bools_to_number(number_to_bools(number, int_type), int_type) == number


def test_number_out_of_range_raises() -> None:
    with pytest.raises(ValueError):
        number_to_bools(256, U8)
    with pytest.raises(ValueError):
        number_to_bools(128, I8)
    with pytest.raises(ValueError):
        number_to_bools(-1, U8)


def test_bit_order_is_independent_of_byte_order() -> None:
    # The same booleans produce the same number; only the byte layout differs.
    assert bools_to_bytes([F, T], U16, byteorder="big") == b"\x00\x02"
    assert bools_to_bytes([F, T], U16, byteorder="little") == b"\x02\x00"


def test_byte_round_trip_little_and_big() -> None:
    for order in ("little", "big"):
        data = number_to_bytes(-6, I16, byteorder=order)  # type: ignore[arg-type]
        assert bytes_to_number(data, I16, byteorder=order) == -6  # type: ignore[arg-type]
        assert bytes_to_bools(data, I16, byteorder=order) == number_to_bools(  # type: ignore[arg-type]
            -6, I16
        )


def test_bytes_to_number_rejects_wrong_length() -> None:
    with pytest.raises(ValueError):
        bytes_to_number(b"\x00", U16)


def test_int_type_parse_and_properties() -> None:
    assert IntType.parse("u8") == U8
    assert IntType.parse("I16") == I16
    assert IntType.parse("int32").name == "i32"
    assert U8.max == 255 and U8.min == 0
    assert I8.max == 127 and I8.min == -128
    with pytest.raises(ValueError):
        IntType.parse("f64")
    with pytest.raises(ValueError):
        IntType(7, False)
