# 현재 기타 자세에서 팔 피드백 비교 v1

## 결과

같은 무스트랩 후보 자세에서 `fixedroot/legs/selfcollision`, 몸통 유지, 2초 준비 조건을 사용했다. 두 조건 모두 손가락 21개는 정책으로 계속 제어했고, checkpoint 가중치는 고정했다. 기준 OFF는 준비 마지막에 제출된 왼팔 9개 관절 PD 목표를 유지했고, 비교 조건 ON은 손목 위치 목표에 부드러운 방향 유지(soft orientation)를 더했다. 초기 상태는 동일하며 별도 초기 교란은 없었다. ON 왼팔 목표는 초기 관절값 ±0.3 rad 및 관절 한계 안으로 제한했고, 목표 변화율 한계는 0.8 rad/s였다. 이는 초기 각도 교란이나 초기 속도 설정이 아니다. OFF의 원래 native 상태·목표·행동·sourceinfo는 그대로 기록·보존했다.

ON은 겹치는 218개 목표 시점에서 평균 손목 위치 오차가 14.861 mm 낮았고, 마지막 겹치는 시점 오차도 OFF 192.549 mm, ON 175.035 mm였다. 같은 0–5.633초 구간으로 맞춰도 기타 최대 위치 변화는 OFF 73.190 mm, ON 267.200 mm였으며 최대 회전 변화는 각각 47.863°와 50.220°였다. ON의 기타 이동과 상자 범위 초과(171.025 mm)는 커졌다. 같은 목표·시각으로 맞춘 258개 표식의 평균 거리 차는 ON이 19.359 mm 낮았지만, 표식 거리는 압력이나 접촉을 입증하지 않는다. ON 녹화는 손가락 뒤쪽 실패로 더 일찍 종료됐다. 손목 오차와 표식 거리의 개선만으로 안정적 개선이라 판정할 수 없다.

양쪽 모두 첫 손가락 뒤쪽 실패로 끝났으며 `episode_success=false`, `goal_finished=false`였다. 종료 지표에서 물리 프레스 성공률과 안정 프레스 성공률은 모두 0이었다. ON 218개 제어 표본 중 40개는 함수 평가 예산 20회 안에 수렴 판정을 받지 못했다. 이 표본도 유한한 최선 추정값을 냈고 목표 변화율과 관절 범위 검사는 통과했다. 사전 점검 11개와 분석 점검 16개, OFF native 검사 18개, ON native 검사 17개는 모두 통과했다. 검사 통과는 연주 성공이나 안정성 향상을 뜻하지 않는다.

다음 실험 후보는 v2의 지지 관계 우선, 작은 교정이다. 이는 계획 단계이며 이 문서에는 v2 결과를 포함하지 않는다.

## native 녹화

아래 MP4는 각 조건의 전체 몸과 손 화면 native 녹화다. 프레임 기록 길이는 OFF 12.916667초(389프레임, 행동 655회), ON 5.633333초(170프레임, 행동 218회)다.

### ON

![ON native 전체 몸 녹화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/ON/data/images/whole_body.mp4)

![ON native 손 녹화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/ON/data/images/hands.mp4)

### OFF

[OFF native 전체 몸 녹화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/OFF/data/images/whole_body.mp4) · [OFF native 손 녹화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/OFF/data/images/hands.mp4)

## 같은 시점 native 그림

각 그림은 OFF와 ON의 같은 시각 native 프레임을 나란히 보여준다. 위쪽 행은 전체 몸, 아래쪽 행은 손 화면이다. 그림은 위치 차이를 살펴보는 기록이며 접촉이나 압력의 증명으로 해석하지 않는다.

### 준비 완료 시점: 2초

![2초 native 전체 몸 OFF와 ON 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/analysis_verified/whole_body_480.png)

![2초 native 손 OFF와 ON 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/analysis_verified/hands_480.png)

### 공통 구간 중간: 3초

![3초 native 전체 몸 OFF와 ON 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/analysis_verified/whole_body_720.png)

![3초 native 손 OFF와 ON 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/analysis_verified/hands_720.png)

### ON 종료 시점과 같은 시각의 OFF 프레임: 5.633초

![5.633초 native 전체 몸 OFF와 ON 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/analysis_verified/whole_body_1352.png)

![5.633초 native 손 OFF와 ON 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/analysis_verified/hands_1352.png)

## 기록과 검수 상태

- 검증 재분석 수치와 매칭 목표: [summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/analysis_verified/summary.json), [matched_goals.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/analysis_verified/matched_goals.json)
- 공통 구간 및 표식 해석: [interpretation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/interpretation.json)
- 사전 점검 및 조건별 native 보고서: [tests_pre.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/tests_pre.json), [OFF 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/OFF/data/report.json), [ON 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/ON/data/report.json)
- 종료 지표 원자료: [OFF terminal_info.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/OFF/data/terminal_info.json), [ON terminal_info.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/ON/data/terminal_info.json)
- 최초 분석은 일부 보조 분석 입력의 provenance 해시를 포함하지 않아 보존본으로 남겼다. 최종 인용은 분석 직전·직후 1,899개 입력이 같음을 확인한 검증 재분석에서 가져왔다: [분석 전후 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/analysis_verified_audit/inputs_after.json). 이 수치는 검증 분석 단계의 입력 보존 범위다. 실행 시 소비한 소스 스냅샷과 실행 후 추가된 진행 문서의 구분은 최종 감사 기록에 정리되어 있다.
- `source_first_done`은 기록 전체 구간에서 확인됐고 학습 업데이트는 0회다. 독립 검수가 완료됐다: [review_final.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/review_final.md). 보존 감사와 소비한 소스 스냅샷·실행 후 진행 갱신본의 구분은 [final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/final_verification.json)에서, 전체 파일 목록과 SHA는 [artifact_inventory.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/artifact_inventory.json)에서 확인한다. 보존된 최종 소스는 [source_final/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/source_final)에 있다.
