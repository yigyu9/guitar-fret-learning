# 왼팔 PD 유지 응답의 분리 비교

## 근거와 이번 변경

관절 유지 관측의 두 실행은 이전 states/trace/tasks/contacts/controls와 정확히 같다.
native 질량과 PD 설정을 읽었으며 총 DOF force도 완료된 24 step에서 관측했다.
총 힘은 drive-only torque가 아니므로 힘 부족이나 포화를 판정하지 않는다.
전체 작은 결합 보정에서도 종료 손 추적점 오차 9.113mm, source normal gap 9.048mm가
남고 양의 palm raw lambda는 step2 한 행뿐이다. 같은 목표에 대한 물리 응답이
PD 변경에 따라 어떻게 달라지는지 먼저 분리해 측정한다.

초기 관절각과 constant startup target은 palm_coupled_correction_v1/full 그대로다.
절대 strap LA는 1.1018469719600776m, 기타 초기 p/q와 solver도 유지한다.
왼팔 Thorax/Shoulder/Elbow/Wrist 12관절의 stiffness와 damping만 각각
1.0/1.5/2.0배로 비교한다. 3init × 24step = 72step(각 0.1초)의 짧은 진단이다.
이는 stiffness/damping의 기존 수치 비를 유지하며 실제 감쇠비 인증을 뜻하지 않는다.

| 관절군 | 기준 kp/kd | 1.5배 | 2배 | effort property 유지 |
| --- | --- | --- | --- | --- |
| Thorax·Shoulder | 200/50 | 300/75 | 400/100 | 150 |
| Elbow_x | 150/37.5 | 225/56.25 | 300/75 | 100 |
| Elbow_y·z | 60/15 | 90/22.5 | 120/30 | 100 |
| Wrist | 50/12.5 | 75/18.75 | 100/25 | 60 |

이번 runtime 실험은 기본 gain 생성기의 Wrist stiffness cap 60을 의도적으로
넘지만 native effort property는 그대로 둔다. 공용 모델·기본 gain 생성기는 수정하지
않고 별도 wrapper에서 해당 actor의 왼팔 PD property만 설정한다. 결과가 좋더라도
이 짧은 비교만으로 장기 설정이나 안정화 성공을 선언하지 않는다.

## 계획과 검증

- [ ] 별도 trial JSON과 runner를 추가하고 직접 소비하는 입력/helper를 import 전에 봉인한다.
- [ ] setter 전후 state와 Python 제출 target이 같고 readback이 지정 PD와 정확히 같은지 검사한다.
  다른 관절과 effort/driveMode/limit 등의 property는 기준과 정확히 같아야 한다.
- [ ] 세 조건을 각각 처음부터 실행해 콘솔 로그와 terminal exit code를 남긴다.
  1.0배는 기존 full의 원자료 5배열 exact 재현을 별도로 검사한다.
- [ ] 기타 최대/종료 p/q 오차, 손 추적점·법선 gap, 접촉 step/raw lambda,
  실제 몸통 움직임과 관절 좌표 오차를 함께 비교한다. 서로 다른 실행을 연결하지 않는다.
- [ ] raw 분석으로 다음 방향을 정하고 Luna 산출물 및 독립 검수를 완료한다.

root·하체는 물리적으로 고정한다. 몸통9 목표, 오른팔·양손가락 목표/PD, 66관절
합성 경로, self-collision ON은 유지한다. 기타는 free/gravity/passive strap이다.
기타 고정·강제 손 부착·반복 상태 덮어쓰기·인위적 기타 goal force는 사용하지 않는다.
평행성은 부드러운 선호이며 source palm-up proxy의 위쪽 반구 검사도 유지한다.
native 목표 getter나 whole-joint SO3 오차를 이 좌표 성분 검사와 혼동하지 않는다.

계획·구현·trial은 stability_adapter_2, 결과는
docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v1에 저장한다.
완료 체크는 봉인된 이 문서 대신 메인 PLAN.md와 run 결과에 남긴다.
