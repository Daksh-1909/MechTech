# Phase 3 Error Log

Track implementation and verification errors here so failures can be reproduced and resolved quickly. Record only actionable errors; expected validation failures in tests do not need an entry.

| ID | Date | Milestone | Symptom / command | Root cause | Fix | Verification |
| --- | --- | --- | --- | --- | --- | --- |
| P3-001 | 2026-11-05 | 1 | `ruff format --check simulator backend/tests/test_simulator.py` reported two files as unformatted. | New simulator dataset code and its test did not match Ruff's configured formatting. | Applied Ruff formatting to both files. | Re-ran the focused simulator tests and Ruff checks after formatting; results recorded with Milestone 1. |
| P3-002 | 2026-11-05 | 2 | `ruff format --check backend simulator` reported `backend/app/schemas/sensor.py` as unformatted. | The multiline `Literal` union did not match the configured Ruff layout. | Applied Ruff formatting to the schema. | Re-run of the full formatting check is part of Milestone 2 verification. |
| P3-003 | 2026-11-05 | 2 | `ruff check backend simulator` flagged an unsorted import in `backend/tests/test_simulator.py`. | The new contract validation test import was below the simulator imports. | Applied Ruff's import fix. | Ruff check and format check both pass across `backend` and `simulator`. |
| P3-004 | 2026-11-05 | 3 | `ruff check backend simulator` reported missing explicit `zip(strict=...)` values and long lines in feature extraction/tests. | New statistical feature code had not yet been run through the repository's complete lint/format rules. | Added explicit zip behavior and wrapped the reported expressions. | Full backend suite: 83 passed; Ruff check passed and 134 files passed format check. |
| P3-005 | 2026-11-05 | 4 | Initial Ruff check reported long expressions, unordered imports and formatting in the baseline service, training script, and tests. | New baseline files had not yet gone through the complete repository lint rules. | Wrapped expressions, marked the intentional project-root bootstrap imports, and simplified test fixture construction. | Full Ruff check and format pass; isolated migration plus baseline training produced a JSON report with 7 normal windows, 0/7 normal flags and all abnormal scenarios flagged in 7/7 windows (synthetic data only). |
| P3-006 | 2026-11-05 | 5 | Existing dataset test expected four classes with five `normal` rows; initial Ruff checks also reported import ordering and line wrapping in new anomaly files. | Phase 3 expands classification to five balanced labels; the test still encoded the Phase 2 dataset, and new files needed repository style fixes. | Updated the balanced-class assertion to all five labels and applied Ruff's import/format fixes. | 7 anomaly, dataset and migration tests passed; Ruff check passed and 143 files passed format check. |
| P3-007 | 2026-11-05 | 6 | Initial Ruff check found import order, long `AppError` calls, unused imports and simple test dictionary comprehensions in the new classifier/evaluator. | New Random Forest inference and CLI files had not yet been linted against project rules. | Reordered imports, wrapped errors, removed unused imports, and applied the safe test simplifications. | 14 classifier/training/evaluation/anomaly/Phase 2 inference tests passed; Ruff check passed and 146 files passed format check. |
| P3-008 | 2026-11-05 | 7 | Initial Ruff check reported line lengths in the prediction provenance migration and unified evidence responses. | New end-to-end service and migration were first drafted before the configured formatter/linter was run. | Wrapped migration operations, error messages and explanation strings. | Full backend suite: 95 passed; Ruff check passed and 148 files passed format check. |
| P3-009 | 2026-11-05 | 8 | Initial `ruff check` / `ruff format --check` reported long lines and import order in the training-job migration, API schema/router, worker and simulator. | New hardening code had not yet gone through the full configured style checks. | Applied Ruff import fixes and formatting, then added a training-job security and single-flight regression test. | Full backend suite: 96 passed; final milestone lint/format and bounded benchmark recorded in Phase 3 completion report. |

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

Entries P3-001 through P3-009 capture the actionable lint/format failures encountered and their fixes.
