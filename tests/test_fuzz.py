"""Seeded fuzzing and scaling: no crash, no hang, no foreign exception, linear time."""

from __future__ import annotations

import contextlib
import random
import time
from collections.abc import Callable

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
    BitpackError,
    IntType,
    SignExtension,
    bools_to_number,
    bytes_to_bools,
    number_to_bools,
    pack_bools,
    pack_flattened,
    unpack_bools,
    unpack_flattened,
)

ALL = [U8, U16, U32, U64, I8, I16, I32, I64]


def test_random_bytes_never_crash_the_readers() -> None:
    rng = random.Random(2026)
    for _ in range(20_000):
        data = rng.randbytes(rng.choice([0, 1, 2, 3, 4, 5, 8, 9, 40]))
        if rng.random() < 0.5 and len(data) >= 4:
            body = len(data) - 4 + rng.choice([-1, 0, 0, 1])
            data = max(body, 0).to_bytes(4, "big") + data[4:]
        try:
            values = unpack_flattened(data)
        except BitpackError:
            continue
        assert pack_flattened(values) == bytes(data[:4] + bytes(1 if b else 0 for b in data[4:]))


def test_random_arrays_respect_the_bounds_and_round_trip() -> None:
    rng = random.Random(14)
    for _ in range(20_000):
        int_type = rng.choice(ALL)
        mode = rng.choice(list(SignExtension))
        array = [rng.random() < 0.5 for _ in range(rng.randrange(0, 80))]
        number = bools_to_number(array, int_type, sign_extension=mode)
        assert int_type.min <= number <= int_type.max
        bits = number_to_bools(number, int_type)
        assert bits[: len(array)] == array[: int_type.bits]
        width = int_type.bits // 8
        assert (
            bytes_to_bools(number.to_bytes(width, "big", signed=int_type.signed), int_type) == bits
        )


def test_random_garbage_only_raises_bitpack_error() -> None:
    rng = random.Random(99)
    pool: list[object] = [None, 0, 1, 2, -1, 1.5, "1", b"\x01", [], [True], object(), True, 2**70]
    calls: list[Callable[[object, object], object]] = [
        lambda a, b: bools_to_number(a, b),  # type: ignore[arg-type]
        lambda a, b: number_to_bools(a, b),  # type: ignore[arg-type]
        lambda a, b: unpack_bools(a, b),  # type: ignore[arg-type]
        lambda a, b: IntType(a, b),  # type: ignore[arg-type]
        lambda a, _: pack_bools(a),  # type: ignore[arg-type]
        lambda a, _: unpack_flattened(a),  # type: ignore[arg-type]
    ]
    for _ in range(5_000):
        first, second = rng.choice(pool + ALL), rng.choice(pool + ALL)
        with contextlib.suppress(BitpackError):
            rng.choice(calls)(first, second)


def _seconds(function: Callable[[], object]) -> float:
    best = float("inf")
    for _ in range(3):
        start = time.perf_counter()
        function()
        best = min(best, time.perf_counter() - start)
    return best


@pytest.mark.parametrize(
    "make",
    [
        lambda n: lambda: pack_bools([True] * n),
        lambda n: lambda: unpack_bools(b"\xaa" * (n // 8)),
        lambda n: lambda: pack_flattened([False] * n),
        lambda n: lambda: unpack_flattened(n.to_bytes(4, "big") + b"\x01" * n),
        lambda n: lambda: bools_to_number([True] * n, U64),
    ],
)
def test_work_grows_linearly(make: Callable[[int], Callable[[], object]]) -> None:
    small, large = _seconds(make(20_000)), _seconds(make(400_000))
    assert large < max(small, 1e-4) * 20 * 4  # 20 times the input, generous slack


def test_a_huge_declared_count_is_refused_without_allocating() -> None:
    start = time.perf_counter()
    with pytest.raises(BitpackError):
        unpack_flattened(b"\x7f\xff\xff\xff\x01")
    with pytest.raises(BitpackError):
        unpack_bools(b"\x01", 2**62)
    assert time.perf_counter() - start < 1.0
