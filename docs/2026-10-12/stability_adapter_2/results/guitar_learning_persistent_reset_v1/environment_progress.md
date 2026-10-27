# Persistent environment implementation

- Ownership: only new `guitar_learning/persistent_environment.py` and `guitar_learning/tests/test_persistent_environment.py`.
- Existing source files, native models, running training inputs and old results were not modified.
- `PersistentContactEnvironment` reuses the original contact/control reset: only its first entry close is suppressed; cached native sessions run `reset_episode(config, out)`. The original 105/97/8 validation, two-second finite preparation, codec and contact reset still run every episode.
- Explicit close and reset failures destroy the owned session. Failures before the original reset's inner try block (such as an existing episode directory) are also cleaned up. Changed configuration, closed sessions and missing reset APIs are rejected.
- `build_persistent_environment(config, out, **kwargs)` patches the control constructor only during original task-sampling construction and restores it afterwards. Legacy/dense/pool targets, observations, contracts and reward semantics are preserved.
- New CPU tests: 7 passed (13.132s). Existing training/dense/task-sampling regression tests: 12 passed (25.686s). These replay recorded bodies and are not native dynamics validation.
- Native validation and final artifacts remain root responsibility. Source implementation and its tests are frozen pending root integration/review.
