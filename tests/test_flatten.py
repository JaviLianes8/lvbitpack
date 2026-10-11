import pytest

from lvbitpack import pack_flattened, unpack_flattened


@pytest.mark.parametrize("length", [0, 1, 7, 8, 9, 16])
def test_round_trip_through_the_flattened_form(length: int) -> None:
    values = [index % 2 == 0 for index in range(length)]
    assert unpack_flattened(pack_flattened(values)) == values


def test_header_is_a_big_endian_i32_element_count() -> None:
    packed = pack_flattened([True] * 9)
    assert packed[:4] == b"\x00\x00\x00\x09"
    assert packed[4:] == b"\xff\x80"


def test_empty_array_flattens_to_a_bare_count_header() -> None:
    assert pack_flattened([]) == b"\x00\x00\x00\x00"


def test_data_shorter_than_the_header_raises() -> None:
    with pytest.raises(ValueError):
        unpack_flattened(b"\x00\x00")


def test_header_count_beyond_the_payload_raises() -> None:
    with pytest.raises(ValueError):
        unpack_flattened(b"\x00\x00\x00\x09\x80")
