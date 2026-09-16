# 단계별 합격 기준

> **상태: HISTORICAL NUMERIC PROPOSAL.** 아래 수치는 아직 calibration되지 않았으며 현재
> checkpoint 승급 기준으로 봉인하지 않았다. 지표 구조와 AND gate는
> [`master_plan/09_curriculum_and_evaluation.md`](../../master_plan/09_curriculum_and_evaluation.md)를 따른다.

> 상태: **초기 제안 — G0 실측 뒤 수치 확정**

## 공통 gate

- 5 seeds와 3개 연속 evaluation window
- Fret/Strike 핵심 지표 G0 대비 95% 이상 유지
- 절대 하락 2%p 이하
- Premature strike/crossing 악화 1%p 이하
- Penetration/over-force/nonfinite hard failure 0
- Strap 중심선의 humanoid·guitar collision proxy 관통 0
- Strap tension/extension 안전 상한 통과
- Residual cap saturation 5% 미만
- Action rate/jerk 허용 범위 통과

## G1 강한 보조 통과

- Nominal 500 rollout drop 0
- Guitar pose 잠정 RMS 1.5 cm/4° 이하
- Guitar pose 잠정 p95 3 cm/8° 이하
- Strike 후 settling p95 잠정 0.5초 이하
- 한 단계 낮은 tether probe에서도 공통 gate 통과

## G1 약한 보조에서 G2로 승급

- Exact-zero-tether probe 성공률 잠정 90% 이상
- Tether assistance fraction p95 잠정 10~15% 미만
- Zero-tether에서 음악 보존·pose·support gate 동시 통과
- 평균 assist return만 높은 checkpoint는 승급 금지

## G2 완료

- 정상 step의 artificial tether/root wrench가 정확히 0이라는 assertion 통과
- `support_hardware=strapped-v1`이고 tension-only 가상 strap force가 정상적으로 활성화됨
- Nominal 500 rollout drop 0
- Randomized drop 1% 미만
- 전곡과 held-out song/tempo/physics 통과
- G0/S2/G1 regression suite도 계속 통과

이 수치는 checkpoint 선택 기준의 초안이다. 실제 G0 분포, 기타 크기, 허용 pose envelope를 측정한 뒤 확정한다. 상세 절차는 [`CURRICULUM.md`](CURRICULUM.md)를 참조한다.
