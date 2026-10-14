"""Hostile and wrongly typed input: always BitpackError, with short messages."""

from __future__ import annotations

from collections.abc import Callable, Iterator

import pytest

from lvbitpack import (
    I8,
    U8,
    U16,
    BitpackError,
    IntType,
    SignExtension,
    bools_to_bytes,
    bools_to_number,
    bytes_to_bools,
    bytes_to_number,
    number_to_bools,
    number_to_bytes,
    pack_bools,
    pack_flattened,
    unpack_bools,
    unpack_flattened,
)

ARRAY_FUNCTIONS: list[Callable[[object], object]] = [
    lambda v: bools_to_number(v, U8),  # type: ignore[arg-type]
    lambda v: bools_to_bytes(v, U8),  # type: ignore[arg-type]
    lambda v: pack_bools(v),  # type: ignore[arg-type]
    lambda v: pack_flattened(v),  # type: ignore[arg-type]
]
BUFFER_FUNCTIONS: list[Callable[[object], object]] = [
    lambda d: bytes_to_number(d, U8),  # type: ignore[arg-type]
    lambda d: bytes_to_bools(d, U8),  # type: ignore[arg-type]
    lambda d: unpack_bools(d),  # type: ignore[arg-type]
    lambda d: unpack_flattened(d),  # type: ignore[arg-type]
]


class Index:
    def __init__(self, value: int) -> None:
        self.value = value

    def __index__(self) -> int:
        return self.value


class Hostile:
    def __repr__(self) -> str:
        raise RuntimeError("repr is broken")


@pytest.mark.parametrize("function", ARRAY_FUNCTIONS)
@pytest.mark.parametrize("values", ["0101", b"\x01", bytearray(b"\x01"), memoryview(b"\x01")])
def test_strings_and_bytes_are_not_boolean_arrays(
    function: Callable[[object], object], values: object
) -> None:
    with pytest.raises(BitpackError, match="iterable of booleans"):
        function(values)


@pytest.mark.parametrize("function", ARRAY_FUNCTIONS)
@pytest.mark.parametrize("values", [None, 5, 1.5, object()])
def test_non_iterables_are_refused(function: Callable[[object], object], values: object) -> None:
    with pytest.raises(BitpackError, match="iterable of booleans"):
        function(values)


@pytest.mark.parametrize("function", ARRAY_FUNCTIONS)
@pytest.mark.parametrize("element", [2, -1, 0.0, 1.0, "1", None, b"\x01", Hostile()])
def test_elements_must_be_booleans(function: Callable[[object], object], element: object) -> None:
    with pytest.raises(BitpackError, match="element 1 must be a boolean"):
        function([True, element])


def test_zero_one_integers_and_index_objects_are_booleans() -> None:
    assert bools_to_number([0, 1], U8) == 2
    assert bools_to_number([Index(0), Index(1)], U8) == 2  # type: ignore[list-item]
    assert pack_flattened([1, 0]) == b"\x00\x00\x00\x02\x01\x00"


def test_any_finite_iterable_is_accepted() -> None:
    def gen() -> Iterator[bool]:
        yield False
        yield True

    assert bools_to_number(gen(), I8) == -2
    assert bools_to_number((False, True), I8) == -2
    assert pack_bools(iter([True])) == b"\x80"


def test_numpy_booleans_and_integers_are_accepted() -> None:
    numpy = pytest.importorskip("numpy")
    assert bools_to_number(numpy.array([False, True]), I8) == -2
    assert number_to_bools(numpy.int16(-2), I8)[:2] == [False, True]
    assert pack_flattened(numpy.array([True, False])) == b"\x00\x00\x00\x02\x01\x00"


@pytest.mark.parametrize("function", BUFFER_FUNCTIONS)
@pytest.mark.parametrize("data", ["00", [0], None, 0])
def test_buffers_must_be_bytes_like(function: Callable[[object], object], data: object) -> None:
    with pytest.raises(BitpackError, match="must be a bytes-like object"):
        function(data)


@pytest.mark.parametrize("number", [True, 1.0, "1", None, 1j])
def test_numbers_must_be_integers(number: object) -> None:
    with pytest.raises(BitpackError, match="number must be an integer"):
        number_to_bools(number, U8)  # type: ignore[arg-type]
    with pytest.raises(BitpackError, match="number must be an integer"):
        number_to_bytes(number, U8)  # type: ignore[arg-type]


def test_index_objects_are_integers() -> None:
    assert number_to_bytes(Index(-2), I8) == b"\xfe"  # type: ignore[arg-type]
    assert unpack_bools(b"\x80", Index(1)) == [True]  # type: ignore[arg-type]


@pytest.mark.parametrize("int_type", ["u8", 8, None, (8, False)])
def test_int_type_must_be_an_int_type(int_type: object) -> None:
    with pytest.raises(BitpackError, match="int_type must be an IntType"):
        bools_to_number([True], int_type)  # type: ignore[arg-type]
    with pytest.raises(BitpackError, match="int_type must be an IntType"):
        number_to_bools(1, int_type)  # type: ignore[arg-type]


@pytest.mark.parametrize("mode", ["never", None, 0, "IF_SIGNED"])
def test_sign_extension_must_be_the_enum(mode: object) -> None:
    with pytest.raises(BitpackError, match="sign_extension must be a SignExtension"):
        bools_to_number([True], U8, sign_extension=mode)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("bits", "signed", "message"),
    [
        (12, False, "8, 16, 32 or 64, not 12"),
        (8.0, False, "bits must be an integer, not float"),
        (True, False, "bits must be an integer, not bool"),
        (8, 1, "signed must be a bool, not int"),
        (8, None, "signed must be a bool"),
    ],
)
def test_int_type_validates_its_fields(bits: object, signed: object, message: str) -> None:
    with pytest.raises(BitpackError, match=message):
        IntType(bits, signed)  # type: ignore[arg-type]


@pytest.mark.parametrize("text", ["f64", "u12", "u08", "uint", "", "i 8", "u8x"])
def test_unknown_type_names_are_refused(text: str) -> None:
    with pytest.raises(BitpackError, match="unknown integer type"):
        IntType.parse(text)


def test_parse_refuses_non_text() -> None:
    with pytest.raises(BitpackError, match="must be str"):
        IntType.parse(8)  # type: ignore[arg-type]


def test_messages_never_echo_huge_input() -> None:
    huge = 10**5000
    for call in (lambda: number_to_bools(huge, U16), lambda: number_to_bytes(-huge, U16)):
        with pytest.raises(BitpackError) as caught:
            call()
        assert len(str(caught.value)) < 120 and "16610 bits" in str(caught.value)
    with pytest.raises(BitpackError) as caught:
        IntType.parse("u" * 10_000)
    assert len(str(caught.value)) < 120
    with pytest.raises(BitpackError) as caught:
        unpack_bools(b"", 10**5000)
    assert len(str(caught.value)) < 120


def test_a_broken_repr_does_not_replace_the_error() -> None:
    with pytest.raises(
        BitpackError,
        match=r"element 0 must be a boolean \(True/False or 0/1\), not <Hostile (object|instance)",
    ):
        bools_to_number([Hostile()], U8)  # type: ignore[list-item]


def test_sign_extension_values_round_trip_by_name() -> None:
    assert SignExtension("if_signed") is SignExtension.IF_SIGNED
    with pytest.raises(ValueError):
        SignExtension("sometimes")
