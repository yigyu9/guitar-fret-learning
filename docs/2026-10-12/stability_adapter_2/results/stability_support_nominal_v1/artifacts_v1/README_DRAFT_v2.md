# Q v1 초기 평가 비교 초안

> 임시 초안입니다. Q v2 평가가 끝나기 전의 비교 자료이며, 성능 개선이나 안정성·자연스러움 성공 판정이 아닙니다.

## 비교 범위

P 초기 평가와 Q v1 `support_guard` 초기 평가는 각각 한 번의 neutral 상태 평가입니다. root 비교 자료는 두 native 초기 상태가 같고 입력이 변경되지 않았음을 기록합니다. 두 실행 모두 평가 전체 구간 16.3667초, 492프레임을 완료했으며 음악 성공 이벤트는 0입니다.

범위 밖 비율은 P 85.4379%, Q v1 55.1935%였고, 최대 위치 범위 밖 norm은 각각 0.4650m와 0.3382m였습니다. 최대 root 이동량은 0.5694m와 0.4488m, 초기 자세 대비 최대 SO(3) 회전은 94.02°와 91.24°였습니다. 이는 단일 초기 평가의 관측값이며 안정성 또는 자연스러움 인증을 뜻하지 않습니다.

![P 초기와 Q v1 초기의 전신 native frame: 0초, 2초, 종료 직전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/artifacts_v1/qp_initial_whole_body_frames_draft_v1.png)

![P 초기와 Q v1 초기의 손 native frame: 0초, 2초, 종료 직전](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/artifacts_v1/qp_initial_hands_frames_draft_v1.png)

![두 평가의 시간에 따른 위치 범위 밖 거리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/artifacts_v1/qp_initial_outside_over_time_draft_v1.png)

## 영상

**P 초기 평가 · 전신**

![P 초기 평가 native 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/smoke_on_v1/evaluations/initial_000000/native/episode_0001/media/whole_body.mp4)

**P 초기 평가 · 손**

![P 초기 평가 native 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_update_correction_v1/smoke_on_v1/evaluations/initial_000000/native/episode_0001/media/hands.mp4)

**Q v1 초기 평가 · 전신**

![Q v1 초기 평가 native 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/smoke_on_v1/evaluations/initial_000000/native/episode_0001/media/whole_body.mp4)

**Q v1 초기 평가 · 손**

![Q v1 초기 평가 native 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/smoke_on_v1/evaluations/initial_000000/native/episode_0001/media/hands.mp4)

## Q v1 적용 조건과 한계

Q v1은 팔 24개 teacher action을 nominal preload 기준 ±0.15rad, 왼손 엄지 5개를 ±0.10rad로 후처리 제한했습니다. 이는 실제 관절 q를 고정하는 설정이 아니며 teacher 원본 action을 그대로 재현하지 않습니다. 기존 adapter의 body/head/arm/finger residual cap은 각각 0.03/0.10/0.30/0.20rad입니다.

## Q v1 학습 시도

초기 평가가 끝난 뒤 학습 준비 상태(profile readiness) 검사에서 불일치가 발생해 실행이 종료되었습니다(exit 1). 학습 업데이트 0회, 전이 0개이므로 Q v1 학습 결과는 없습니다. 이번 자료는 초기 평가끼리의 비교만 보여주며 Q v2는 아직 반영하지 않았습니다.

## 재현 및 출처

비교 수치의 기준 자료는 [root 초기 비교 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/initial_comparison_v1.json)입니다. 이 초안의 그림 생성기는 [비교 producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/artifacts_v1/build_qp_initial_comparison_draft_v1.py)이며 입력 전후 SHA와 미디어 SHA는 [v2 문서 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/artifacts_v1/README_DRAFT_v2_provenance.json)에 기록했습니다.
