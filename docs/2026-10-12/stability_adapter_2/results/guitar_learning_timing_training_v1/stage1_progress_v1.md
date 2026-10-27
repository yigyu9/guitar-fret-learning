# Stage1 학습·실제 평가 분석

검증 조건 충족: **False**. stage1 범위의 판단이며 다음 단계 승격을 뜻하지 않는다.

stage0의24회 학습 source와 새 stage1의 학습 횟수를 구분한다. 시간창은 ±0.5초이며 정책 pre-roll1초·전체5초·native 정착2초는 유지한다.

| 손 | 회차 | 단계 성공 | audible 유지율 | 최초 down 절대오차(ms) | 추가 목표 down | 반대 up | 기타 최대 이동(mm) |
|---|---:|---:|---:|---:|---:|---:|---:|

left: native 평가 자료 미완료.

right: native 평가 자료 미완료.

240Hz 비용 적분·시계·실제 crossing 깊이/속도·inactive 행동0·원 joint music·입력 SHA는 JSON에 보존했다.

[전체 수치와 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/stage1_progress_v1.json)

![KL·실제 LR·critic](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/stage1_progress_v1.png)
