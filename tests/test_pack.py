import pytest

from lvbitpack import pack_bools, unpack_bools


@pytest.mark.parametrize("length", [0, 1, 7, 8, 9, 16])
def test_round_trip_preserves_values_for_various_lengths(length: int) -> None:
    values = [index % 3 == 0 for index in range(length)]
    assert unpack_bools(pack_bools(values), length) == values


def test_first_value_lands_in_the_most_significant_bit() -> None:
    assert pack_bools([True, True, False, True, False, False, False, False]) == b"\xd0"


def test_single_true_packs_to_the_high_bit_of_one_byte() -> None:
    assert pack_bools([True]) == b"\x80"


def test_empty_input_packs_to_no_bytes() -> None:
    assert pack_bools([]) == b""


def test_nine_values_span_two_bytes_with_padded_tail() -> None:
    packed = pack_bools([True] * 9)
    assert packed == b"\xff\x80"
    assert len(packed) == 2


def test_padding_bits_of_the_final_byte_are_zero() -> None:
    assert pack_bools([True, False, False]) == b"\x80"


def test_count_truncates_the_trailing_padding_bits() -> None:
    assert unpack_bools(b"\x80", 1) == [True]
    assert unpack_bools(b"\xff", 3) == [True, True, True]


def test_negative_count_raises() -> None:
    with pytest.raises(ValueError):
        unpack_bools(b"\x00", -1)


def test_count_beyond_the_available_bits_raises() -> None:
    with pytest.raises(ValueError):
        unpack_bools(b"\x80", 9)
