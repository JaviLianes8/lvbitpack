"""Contracts from the fourth adversarial round: NumPy booleans as numbers, field names."""

from __future__ import annotations

import ctypes

import pytest

from lvbitpack import U8, U16, BitpackError, IntType, bytes_to_number, number_to_bools, unpack_bools


def _fake_numpy_true() -> object:
    # Stands in for numpy.True_ on NumPy releases where it still has __index__.
    kind = type(
        "bool_", (), {"__module__": "numpy", "__bool__": lambda s: True, "__index__": lambda s: 1}
    )
    return kind()


def test_a_numpy_boolean_is_never_a_number() -> None:
    true = _fake_numpy_true()
    with pytest.raises(BitpackError, match="number must be an integer, not bool"):
        number_to_bools(true, U8)  # type: ignore[arg-type]
    with pytest.raises(BitpackError, match="count must be an integer, not bool"):
        unpack_bools(b"\xff", true)  # type: ignore[arg-type]
    assert not U8.contains(true)


def test_struct_field_names_with_an_o_are_still_bytes() -> None:
    class Header(ctypes.Structure):
        _fields_ = [("Ok", ctypes.c_uint16)]

    assert bytes_to_number(Header(0x0102), U16) in (0x0102, 0x0201)
    numpy = pytest.importorskip("numpy")
    record = numpy.zeros(1, dtype=[("Offset", "<u2")])
    assert bytes_to_number(record, U16) == 0
    with pytest.raises(BitpackError, match="holds Python objects"):
        bytes_to_number((ctypes.py_object * 1)(), U16)


def test_a_tampered_int_type_is_checked_again() -> None:
    tampered = IntType(8, False)
    object.__setattr__(tampered, "bits", 7)
    with pytest.raises(BitpackError, match="bits must be 8, 16, 32 or 64"):
        number_to_bools(1, tampered)


def test_a_subclass_whose_fields_raise_is_refused() -> None:
    class Broken(IntType):
        def __getattribute__(self, name: str) -> object:
            raise RuntimeError("hostile")

    broken = object.__new__(Broken)
    with pytest.raises(BitpackError, match="never initialised"):
        number_to_bools(1, broken)


def test_a_shadowed_method_on_an_int_type_changes_nothing() -> None:
    import copy

    shadowed = copy.copy(U8)
    shadowed.__dict__["contains"] = lambda value: True
    with pytest.raises(BitpackError, match="out of range for u8"):
        number_to_bools(300, shadowed)
