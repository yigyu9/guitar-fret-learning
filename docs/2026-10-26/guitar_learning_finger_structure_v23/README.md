# 손가락 구조 v23 비교 결과

위치 제어 옵션과 모드별 진단·설정/저장 계약을 구현하고 비교했다. **압현 성과 회귀로 position 기본 채택은 보류했으며 기본은 incremental이다. 손가락 문제 전체가 해결된 것은 아니다.**

large/128환경/H32/seed7의 동일 초기 정책으로 각각100회 학습한 고정 전곡 평가에서 평균 달성음은 누적5.6875/67, 위치0.078125/67이었다. 안전 완주는114→124/128, 목표한계 체류는51.2%→0%였지만 B복귀는 네 손가락 모두0%이고 위치 정책의 목표 변화가 대부분1도 미만이었다.

[결과·검증·남은 구조 작업](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_finger_structure_v23/RESULTS.md) · [비교 수치](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_finger_structure_v23/comparison.json).

기본 실행은 기존 누적 제어를 유지한다. 명시적 위치 실험은 아래와 같으며 이전 모델의 행동 의미를 바꾸어 재개하지 않는다.

```bash
python -m guitar_learning.train --hand left --physics gpu --device cuda:0 \
  --size large --num-envs 128 --horizon 32 --updates 100 \
  --finger-action-mode position \
  --out docs/2026-10-26/new_left_position_experiment
```

위치 옵션은 준비 참조각을0, native양끝을±1로 쓰고4rad/s로 목표에 접근한다. 전체 가동범위·PD/힘·손가락 움직임비용0을 유지하며 B 자동복귀는 없다. 기본/실험 두 모드와 진단v3를 포함한 전체 계약이 같은 checkpoint끼리만 strict resume한다.

과거v22 원문473Python은 archive/20261026_before_finger_structure_v23/, 기본 채택 판단 전 후보 원문474Python은 archive/20261026_before_position_default_rejection_v23/에 보존했다. source_manifest.json은 실험 당시 소스이며 최종 기본 선택 후 소스는 final_source_manifest.json과 구분한다.
