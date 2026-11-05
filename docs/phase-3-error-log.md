# Phase 3 Error Log

Track implementation and verification errors here so failures can be reproduced and resolved quickly. Record only actionable errors; expected validation failures in tests do not need an entry.

| ID | Date | Milestone | Symptom / command | Root cause | Fix | Verification |
| --- | --- | --- | --- | --- | --- | --- |
| P3-001 | 2026-11-05 | 1 | `ruff format --check simulator backend/tests/test_simulator.py` reported two files as unformatted. | New simulator dataset code and its test did not match Ruff's configured formatting. | Applied Ruff formatting to both files. | Re-ran the focused simulator tests and Ruff checks after formatting; results recorded with Milestone 1. |
| P3-002 | 2026-11-05 | 2 | `ruff format --check backend simulator` reported `backend/app/schemas/sensor.py` as unformatted. | The multiline `Literal` union did not match the configured Ruff layout. | Applied Ruff formatting to the schema. | Re-run of the full formatting check is part of Milestone 2 verification. |
| P3-003 | 2026-11-05 | 2 | `ruff check backend simulator` flagged an unsorted import in `backend/tests/test_simulator.py`. | The new contract validation test import was below the simulator imports. | Applied Ruff's import fix. | Ruff check and format check both pass across `backend` and `simulator`. |
| P3-004 | 2026-11-05 | 3 | `ruff check backend simulator` reported missing explicit `zip(strict=...)` values and long lines in feature extraction/tests. | New statistical feature code had not yet been run through the repository's complete lint/format rules. | Added explicit zip behavior and wrapped the reported expressions. | Full backend suite: 83 passed; Ruff check passed and 134 files passed format check. |

## Entry template

```text
ID:
Date/time:
Milestone:
Command or action:
Observed error:
Root cause:
Fix:
Verification command/result:
Related files/commit:
```

No Phase 3 implementation errors have been recorded yet.
