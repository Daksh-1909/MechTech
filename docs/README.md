# MechTech Documentation

Phase 1 requirements live in
[`../MechTech_Phase_1_Requirements.md`](../MechTech_Phase_1_Requirements.md).
The Phase 2 backend design and milestones live in
[`../MechTech_Phase_2_Backend_Architecture.md`](../MechTech_Phase_2_Backend_Architecture.md).

## Phase 2 deliverables

1. Detailed system architecture diagram
2. Frontend and backend module breakdown
3. Database ER diagram with keys and relationships
4. Sensor-data contract and simulator/backend flow
5. ML pipeline diagram, feature definitions and evaluation plan
6. 3D motor component hierarchy and sensor-to-component mapping
7. Knowledge graph node/edge schema
8. API endpoint list with request/response examples
9. Authentication and authorization design
10. Final project folder structure
11. Staged implementation plan with test checkpoints

## Implemented documentation

- [`api-contract.md`](./api-contract.md): Phase 2 endpoint, authentication,
  role, idempotency, error and schema contract.
- [`performance-baseline.md`](./performance-baseline.md): measured local
  p50/p95/p99 baseline, environment and limitations.
- [`benchmark-baseline.json`](./benchmark-baseline.json): raw benchmark report.
- [`../backend/README.md`](../backend/README.md): local setup, domain APIs,
  ML scripts, simulator, backup/restore and operational notes.

The architecture, data-model, ML-pipeline and knowledge-graph design content is
currently maintained in the Phase 2 backend architecture document.
