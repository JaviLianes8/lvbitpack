# lvbitpack 1.0.0 certification report

Progress:
- [x] Branch `release/1.0.0` created from `main` (0.2.0, 901e1eb)
- [x] Baseline gates run on 0.2.0
- [x] API review and 1.0.0 API changes (item 1)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [ ] Real LabVIEW 2026 captures (item 7)
- [ ] Contract, fuzz and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [ ] Packaging, e2e, every interpreter (items 8, 10, 13, 14)
- [ ] Independent reviewer and five QA lenses report PASS (items 16, 19)
- [ ] Gates (item 15)
- [ ] PR and trace guard CLEAN (item 17); merge and publish left to the maintainer

## Baseline on 0.2.0 (before any change)

| Command | Result |
| --- | --- |
| `ruff format --check .`, `ruff check .` | exit 0 |
| `mypy --strict src tests` | 3 errors in `tests/test_number.py` (unused ignores) |
| `pytest` | 59 passed |
| `pytest --doctest-modules src` | no doctests at all |

lvbitpack has never been published: `https://pypi.org/pypi/lvbitpack/json` answers 404, so
there is no PyPI release to upgrade from. Behaviour changes below are relative to the 0.2.0
source on `main`.

Defects of 0.2.0 found during this round (each reproduced against the 0.2.0 source):
`pack_flattened` wrote a count plus bit-packed bytes and its docstring called that LabVIEW's
Flatten To String layout, which is one byte per element (NI's Flattened Data page and real
LabVIEW captures); `bools_to_number("0101", U8)` returned 15 (each character truthy);
`IntType(8.0, "yes")` was accepted; `number_to_bools(True, U8)` was accepted;
`number_to_bytes(1.5, U8)` leaked `AttributeError`; `bools_to_number(iter([True]), U8)` leaked
`TypeError`; `number_to_bools(10**5000, U8)` failed inside its own message with Python's
integer printing limit; the CLI exited 120 on a closed pipe.
