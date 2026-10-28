# v3 독립 코드 검수

요약 판정: **문제없음(PASS)**. Critical/Warning/Suggestion finding 없음.

- All521 archived files have exact manifest SHA256 and byte counts. Comparing archived paths against current source shows exactly the five designated code/test files plus README.md and AGENTS.md differ; every other archived active input including fixture is unchanged.
- Surgical source diff only: WRIST_CONTROL schema/scopes, bounded position candidate, runtime actual arm12 input/diagnostic clone, evaluator extra candidate trace/scopes, relevant tests/docs. All wrist function ASTs other than bounded_wrist_target are identical to archive, preserving qpos-J v2 mathematics.
- Single raw DLS solve computes candidate=actual_arm_q+dq; proposal=base+stored_correction; existing correction_step_rad clips candidate-proposal; existing request rate and action bounds remain in original order; correction=request-base. Inactive rows mask Jacobian/error before solve, actualq before candidate, delta0, diagnostic candidate=valid proposal, preserving feedforward.
- Runtime selects actual q using controller.active[:12]; candidate is the fourth return from the same solve and cloned into last_wrist_feedback and wrist_candidate_arm_rad. Neutral requested_delta_rad remains; v3 contract/trace metadata specify pre-rate/bound candidate difference and inactive proposal fallback. No duplicate solve, physical state overwrite, reward input or observation change.
- Independent CPU four-module unittest run: test_short_finger_learning/test_wrist_position_jacobian23 tests in5.301s PASS; test_gpu_control/test_thumb_contact_probe20 tests in2.501s PASS; total43 PASS. Coverage includes overshoot reversal/settling, zero-error lag, reset NaNs, feedforward, bounds/rate, input preservation, trace values/scopes and oldv1/v2 rejection/newv3 identical-contract checkpoint load.
- Independent NumPy SVD DLS oracle96 mixed active/inactive rows, both float32 and float64, matches candidate/delta/request/correction, rate/bounds and input preservation. No Isaac Gym native module or initialized CUDA used.
- Production PD, rewards/termination, native ranges, finger codec, raw J33 policy, velocity/force Jacobians and fixed .5degree correction cap are unchanged. Documentation preserves arm-only scope, strict old-checkpoint rejection and native performance unverified status.

생산 소스·원자료·archive·봉인을 변경하지 않았다. native/GPU 실행은 없으며 실제 도달·압현·하중 개선은 아직 미검증이다. 검수 시점의 최종7파일 SHA는 code_review.json에 기록했다.
