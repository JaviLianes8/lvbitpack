# lvbitpack 1.0.0 certification report

Progress:
- [x] Branch `release/1.0.0` created from `main` (0.2.0, 901e1eb)
- [x] Baseline gates run on 0.2.0
- [x] API review and 1.0.0 API changes (item 1)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [x] Real LabVIEW 2026 captures (item 7)
- [x] Contract, fuzz and author mutation round (items 6, 9, 18)
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

## Author mutation round (item 18)

Each mutation was applied alone to a fresh clone of the branch on the build laptop, every
`__pycache__` purged and no bytecode written, the suite (all but the wheel end to end
module, which the CLI tests cover in process) run with `-x` and a 600-second limit, and the
file restored; the suite was green before the first and after the last mutation. The first
run at 54050af left three survivors: M17 (a `uint` name parsed as signed) was closed by
`tests/test_contract_edges.py` in 24b1cf0, and M07 and M09 are equivalent, each proved by
a contract in the same file. The table is the rerun at 24b1cf0: 46 mutations, 44 killed,
2 equivalent.

| Id | Mutation | File | Result | Caught by |
| --- | --- | --- | --- | --- |
| M01 | bit order reversed (MSB first) | `_number.py` | killed | `tests/test_bytes.py::test_bit_order_does_not_depend_on_byte_order` |
| M02 | last in-width element dropped | `_number.py` | killed | `tests/test_cli.py::test_commands[args4--9223372036854775808]` |
| M03 | long arrays not truncated | `_number.py` | killed | `tests/test_contract_edges.py::test_unsigned_results_never_exceed_the_maximum` |
| M04 | NEVER mode extends | `_number.py` | killed | `tests/test_cli.py::test_every_help_example_prints_what_it_claims[args2-10]` |
| M05 | IF_SIGNED condition inverted | `_number.py` | killed | `tests/test_bytes.py::test_bit_order_does_not_depend_on_byte_order` |
| M06 | pads with the first element | `_number.py` | killed | `tests/test_bytes.py::test_bools_to_bytes_passes_the_sign_extension_through` |
| M07 | padding check off by one | `_number.py` | equivalent | equivalent: at the full width the padding mask is empty (`test_contract_edges::test_an_array_exactly_as_wide_as_the_type_is_never_padded`) |
| M08 | pad mask wrong | `_number.py` | killed | `tests/test_bytes.py::test_bools_to_bytes_passes_the_sign_extension_through` |
| M09 | unsigned read as two's complement | `_number.py` | equivalent | equivalent: an unsigned maximum is its mask, so the step never applies (`test_contract_edges::test_unsigned_results_never_exceed_the_maximum`) |
| M10 | two's complement offset wrong | `_number.py` | killed | `tests/test_bytes.py::test_bools_to_bytes_passes_the_sign_extension_through` |
| M11 | negative numbers lose their sign | `_number.py` | killed | `tests/test_cli.py::test_every_help_example_prints_what_it_claims[args6-01111111]` |
| M12 | one element short | `_number.py` | killed | `tests/test_cli.py::test_every_help_example_prints_what_it_claims[args5-01000000]` |
| M13 | range check dropped | `_number.py` | killed | `tests/test_cli.py::test_data_errors_go_to_stderr_with_exit_one[args2-256` |
| M14 | min off by one | `_types.py` | killed | `tests/test_cli.py::test_pack_and_unpack_round_trip` |
| M15 | max off by one | `_types.py` | killed | `tests/test_bytes.py::test_width_is_bits_over_eight[int_type4]` |
| M16 | contains excludes max | `_types.py` | killed | `tests/test_bytes.py::test_width_is_bits_over_eight[int_type0]` |
| M17 | uint parsed as signed | `_types.py` | killed after a new contract | `tests/test_contract_edges.py::test_parse_reads_every_prefix_with_its_signedness[int_type0]` |
| M18 | float width accepted | `_types.py` | killed | `tests/test_hostile.py::test_int_type_validates_its_fields[8.0-False-bits` |
| M19 | non-bool signed accepted | `_types.py` | killed | `tests/test_hostile.py::test_int_type_validates_its_fields[8-1-signed` |
| M20 | default byte order little | `_bytes.py` | killed | `tests/test_bytes.py::test_big_endian_is_the_default_like_labviews_flatten` |
| M21 | signed bytes read unsigned | `_bytes.py` | killed | `tests/test_bytes.py::test_big_endian_is_the_default_like_labviews_flatten` |
| M22 | extra bytes accepted | `_bytes.py` | killed | `tests/test_bytes.py::test_the_wrong_number_of_bytes_is_refused[\x00\x00\x00]` |
| M23 | little order ignored | `_bytes.py` | killed | `tests/test_bytes.py::test_little_endian_on_request` |
| M24 | sign extension not passed through | `_bytes.py` | killed | `tests/test_bytes.py::test_bools_to_bytes_passes_the_sign_extension_through` |
| M25 | bit orders swapped in pack | `_pack.py` | killed | `tests/test_contract.py::test_every_public_function_round_trips` |
| M26 | extra byte for full octets | `_pack.py` | killed | `tests/test_pack.py::test_empty_input_packs_to_no_bytes` |
| M27 | count beyond data accepted | `_pack.py` | killed | `tests/test_pack.py::test_counts_outside_the_data_are_refused[9-more` |
| M28 | default count zero | `_pack.py` | killed | `tests/test_pack.py::test_count_defaults_to_every_bit_and_drops_fill_bits_when_given` |
| M29 | unpack ignores lsb | `_pack.py` | killed | `tests/test_contract.py::test_every_public_function_round_trips` |
| M30 | count little-endian | `_flatten.py` | killed | `tests/test_cli.py::test_every_help_example_prints_what_it_claims[args7-0000000401000101]` |
| M31 | only 0x01 read as TRUE | `_flatten.py` | killed | `tests/test_cli.py::test_commands[args9-10]` |
| M32 | trailing bytes accepted | `_flatten.py` | killed | `tests/test_flatten.py::test_malformed_input_is_refused[\x00\x00\x00\x01\x01\x00-1` |
| M33 | count read unsigned | `_flatten.py` | killed | `tests/test_cli.py::test_data_errors_go_to_stderr_with_exit_one[args7-count` |
| M34 | count -1 accepted | `_flatten.py` | killed | `tests/test_cli.py::test_data_errors_go_to_stderr_with_exit_one[args7-count` |
| M35 | bytes accepted as an array | `_errors.py` | killed | `tests/test_hostile.py::test_strings_and_bytes_are_not_boolean_arrays[\x01-<lambda>0]` |
| M36 | element 2 accepted | `_errors.py` | killed | `tests/test_hostile.py::test_elements_must_be_booleans[2-<lambda>0]` |
| M37 | bool accepted as a number | `_errors.py` | killed | `tests/test_hostile.py::test_numbers_must_be_integers[True]` |
| M38 | huge integers printed | `_errors.py` | killed | `tests/test_hostile.py::test_messages_never_echo_huge_input` |
| M39 | messages unbounded | `_errors.py` | killed | `tests/test_hostile.py::test_messages_never_echo_huge_input` |
| M40 | error type not a ValueError | `_errors.py` | killed | `tests/test_bytes.py::test_the_wrong_number_of_bytes_is_refused[]` |
| M41 | hex output not masked | `_cli.py` | killed | `tests/test_cli.py::test_every_help_example_prints_what_it_claims[args4-0xfe]` |
| M42 | CLI bit string reversed | `_cli.py` | killed | `tests/test_cli.py::test_every_help_example_prints_what_it_claims[args0-2]` |
| M43 | data error exits 2 | `_cli.py` | killed | `tests/test_cli.py::test_data_errors_go_to_stderr_with_exit_one[args0-character` |
| M44 | number length not limited | `_cli.py` | killed | `tests/test_cli.py::test_data_errors_go_to_stderr_with_exit_one[args4-101` |
| M45 | prefixed numbers refused | `_cli.py` | killed | `tests/test_cli.py::test_commands[args5-00000001]` |
| M46 | closed pipe not silenced | `_cli_io.py` | killed | `tests/test_cli_process.py::test_a_closed_output_pipe_exits_one_quietly` |

## Independent QA lenses (item 19)

Each lens was a fresh reviewer that read the certification rules and CERT-1.0.md first,
worked in its own clone and on the build machines under its own turn, ran things rather
than reading, and reported back privately.

| Lens | Round | Head | Verdict | Findings and outcome |
| --- | --- | --- | --- | --- |
| a. API and docs | 1 | 6cc718d | FAIL (1 high, 1 medium, 6 low, info) | 112 probes, 48 doctests, 26 GUIDE and 2 README examples, 35 CLI checks, 63 behaviour expressions against 0.2.0, strict consumers. README claimed a LabVIEW 2026 check before the captures existed; byte inputs narrowed versus 0.2.0; `IntType` refused NumPy widths and `contains` changed silently; hints stricter than the 0/1 runtime; private module names in `help()`; CLI changes and one cause missing or wrong in the CHANGELOG; parameter naming reviewed and kept deliberately. Fixed in 5cb3cd3 (the LabVIEW claim waits for the captures) |
| c. Adversarial and robustness | 1 | 6cc718d | FAIL (2 medium, 5 low, info) | 400,000 seeded API calls on 8 seeds, 100,000 oracle round trips, 60,000 in-process and 450 subprocess CLI runs, 16 threads with 480,000 calls, 19 scaling shapes all linear. Mocks and hostile int subclasses leaked their own errors through message quoting; option checks compared before type checks; a bytes subclass's `__bytes__` and a released view leaked; `parse` called str-subclass methods; unknown `SignExtension` names gave a plain enum error; an ASCII-only stderr was treated as a gone reader. Fixed in 5cb3cd3 |
| e. Contract strength | 1 | 6cc718d | FAIL until its contracts were added | 115 blind mutations: 84 killed, 8 proven equivalent (differential digests over up to 1.7 million cases each), 23 survivors; its 23 contracts added in 6a28a86 (`tests/test_contract_strength.py`, `tests/test_contract_strength_cli.py`) |
| e. Contract strength | 2 | 45ae1b0 | FAIL until its contracts were added | 140 mutations (115 re-anchored plus 25 on the new code): 122 killed, 7 proven equivalent, 11 survivors in the new code; its 9 contracts added in 3713fdd (`tests/test_contract_strength_two.py`) |
| a. API and docs | 2 | 45ae1b0 | PASS (3 low, info) | 147 consumer checks with and without NumPy, 22 NumPy checks, strict consumers for 3.10, 3.12 and 3.14, the suite against the installed wheel; all round 1 findings fixed but the LabVIEW claim. New: renaming the classes' module broke `inspect.getsource`; `help()` still named a private module on 3.14; three byte-input lines inexact. Fixed in 3713fdd (classes keep their real module; functions only are renamed) |
| c. Adversarial and robustness | 2 | 6a28a86 | FAIL (4 medium, 5 low) | 320,781 seeded calls, 39,402 in-process CLI runs, about 100,000 calls on 8 threads with the GIL off (3.14.2t), about 130 hostile probes on 3.10 to 3.14, scaling linear to 4 million. `SignExtension(...)` leaked the enum's own errors for huge, released or hostile values; `Mock(spec=str)` and `Mock(spec=IntType)` leaked; an `IntType` subclass could relax the range check; `contains` raised for NumPy arrays; odd buffers misreported; usage errors echoed control characters; a metaclass `__name__` leaked; singular wording. Fixed in f341592 (`tests/test_hostile_three.py`) |

## Ground truth (item 7)

`tests/fixtures/labview2026/` holds results produced by LabVIEW 2026 Community 26.3.1f1 on
this PC on 2026-10-14; `manifest.json` records the method, every file's size and SHA-256 and
the hashes of the raw capture records. VI Scripting is not reachable over ActiveX, so the test
VIs were made from a copy of the shipped example `examples/Booleans/Boolean Functions.vi` by
editing its block diagram heap with pylabview (one node replaced by the primitive, its output
representation and Sign Extension Mode set); LabVIEW loaded, compiled and ran each VI, and
inputs and outputs went through its ActiveX server. `tests/test_real_labview.py` replays:

- Boolean Array To Number: 2,940 distinct results over 30 configurations (U8 to I64 under
  the three modes, and a node with no output representation chosen), arrays of 0 to 65
  elements. All agree with lvbitpack and with NI's table. A node without an explicit
  representation outputs U32, which the guide now states.
- Number To Boolean Array: 194 results over the eight integer types, minimum, maximum and
  seeded values.
- Six front-panel datalog files (Boolean arrays of 0, 1, 8, 9, 17 and 300 elements) copied
  unchanged: each holds exactly the bytes `pack_flattened` writes.

Not captured: how LabVIEW's Unflatten reads an element byte other than 0x00 and 0x01 (the
"any nonzero is TRUE" rule comes from NI's Flattened Data page).
| b. Correctness and ground truth | 1 | 5618d69 | PASS (2 low, 3 info) | NI pages fetched again, every doc claim checked; own string and `struct` oracle over 1,293,926 seeded checks with 125,000 in-process and 300 subprocess CLI runs, 0 failures; all 3,134 LabVIEW rows and 6 datalogs decoded independently (own `DTLG` record parser), U32 the only type that fits the unconfigured-node rows. Notes: the U32 default was stated as if for a palette-placed node; the manifest omitted lengths 4 and 5; raw capture records not fetchable; "never packs" too absolute; the flatten count depends on the prepend-size input. Wording fixed in 40947af; the raw records stay on the capture machine (their hashes are in the manifest) |
| d. Packaging and real e2e | 1 | 40947af | PASS (1 low, 3 info) | sdist and wheel built, `twine check --strict` and `check-wheel-contents` clean, a wheel rebuilt from the sdist identical; the suite from the sdist with `src` removed against the installed wheel on 3.10.19 (527 passed, 1 skipped), 3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2t with the GIL off (528 passed each), plus sdist installs; 3.8 and 3.9 refused by `requires-python`; five sabotaged wheels all caught; 0.2.0 upgraded in place with every difference in the CHANGELOG; no PyPI release (404). Notes: two CHANGELOG details, the metadata contract skipped on 3.10. Fixed in 28b8117 (installed metadata now checked on every Python) |
| c. Adversarial and robustness | 3 | 2c2ec55 | FAIL (2 medium, 6 low, 3 info) | 800,000 seeded API calls on 3.10, 3.13 and 3.14t (GIL off), 160,000 oracle round trips, 160,000 in-process CLI runs, 400 subprocess runs, threads, scaling linear to 4 million; every round 2 fix held. New: an object whose `__class__` raises leaked through `isinstance`; `-0x2` refused before Python 3.14 (argparse took it for an option); a hostile metaclass through `contains`; an uninitialised `IntType`; extra `SignExtension(...)` arguments skipped the lookup; control characters from hostile reprs in messages; `signed` accepted a mock; a fake NumPy boolean; huge byte strings fully repr'd; Unicode digits read. Fixed in 25e6307 (`tests/test_hostile_four.py`) |
| c. Adversarial and robustness | 4 | 5861687 | FAIL (2 low, info) | 900,000 seeded calls on 3.10 (NumPy 2.2), 3.13 and 3.14t with the GIL off, 75,000 oracle round trips and 75,000 in-process CLI runs, 1,047 subprocess cases, 16 threads, scaling linear to 3.2 million; all ten round 3 fixes held on every Python. New: NumPy booleans older than NumPy 2.3 read as integers; a struct field name containing `O` taken for an object buffer. Both fixed, with the cheap hardening it suggested (a tampered `IntType` checked again, a 0/1 fast path), in the next commit (`tests/test_hostile_five.py`) |
| c. Adversarial and robustness | 5 | f1b7bc2 | PASS (info only) | 37 round 4 checks on each of 3.10.19 with NumPy 2.2.6, 3.13.2 and 3.14.2t (GIL off); 900,000 seeded library calls (seeds 501, 502) with hostile objects of every kind, 120,000 in-process and 900 subprocess CLI runs (seed 551), 8 threads against a mutating input, scaling linear to 2 million; longest message 108 characters. Notes: a method shadowed on an `IntType` instance got past the fast path (fixed with its suggested check and a contract in the next commit); GUIDE wording on `SignExtension` call mistakes and pointer buffers tightened; fake NumPy booleans, `__index__` returning `True` and swallowed `__release_buffer__` errors accepted as Python's own behaviour |
