# Guitar contact diagnostic

## Goal

Add a reproducible StabilityAdapter tool that reports which humanoid collision
links contact the guitar during acquisition and TRANSPORT.

## Contract

- Report rigid-body link names and their owning DOFs; joints themselves do not
  have collision geometry.
- Aggregate contact frames, first/last frame, longest dwell, maximum/mean net
  force, and phase counts.
- Audit the installed humanoid/guitar collision filters for every reported
  link.
- Write machine-readable JSON and CSV artifacts.
- State the attribution limitation explicitly: Isaac Gym's rigid-contact pair
  API is unavailable after GPU-pipeline simulation starts, so runtime evidence
  is net body force qualified by collision topology, not a pair-contact tensor.
- Do not change the StabilityAdapter controller or training environment.

## Checklist

- [x] Add Isaac-independent contact aggregation helpers.
- [x] Add the GPU transport-teacher diagnostic CLI.
- [x] Add unit tests for threshold, dwell, phase, sorting, and collision logic.
- [x] Run the tool on the current 50 mm / 15 degree teacher.
- [x] Verify JSON/CSV outputs and document the current result.
- [x] Run focused regression tests and independent change review.

## Current run

```bash
python -m stability_adapter.tools.diagnose_guitar_contacts \
  --frames 5600 --distance-m 0.05 --rotation-deg 15 \
  --threshold-n 0.1 --scope upper \
  --output docs/2026-09-21/stability_adapter/diagnostics/guitar_contacts_transport_v2.json
```

The deterministic run entered TRANSPORT at frame 3429 and ended at frame 5228
with `transport_timeout=true`, no overload, and no grip loss. The default
`upper` scope reported 13 links. Notable results are:

- `RH:thumb3`: 5,094 total frames and all 1,800 TRANSPORT frames, maximum net
  force 27.933 N.
- `R_Wrist`: 25 TRANSPORT frames, maximum net force 13.622 N.
- `R_Elbow`: 5,150 frames, maximum net force 18.975 N. Its filter also permits
  chair contact, and ground contact cannot be filtered out, so this row remains
  explicitly ambiguous.
- Left distal links `LH:index3`, `LH:middle3`, `LH:ring3`, and `LH:thumb3` were
  the primary neck-contact candidates. Their installed filters disable guitar
  non-neck meshes and chair contact.

The first `v1` artifact used the `all` body scope and is retained as diagnostic
history. It includes locked lower-body ground/chair forces and must not be used
as the default guitar-contact report. `v2` is the current artifact.

Validation: all 6 focused diagnostic tests and Python compilation passed. The
regenerated JSON and CSV each contain the same 13 rows and 15 contact fields,
including `shape_count`. Independent review found no Critical or Warning items.
