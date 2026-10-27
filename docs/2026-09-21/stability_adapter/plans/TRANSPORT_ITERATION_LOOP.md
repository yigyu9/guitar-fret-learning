# TRANSPORT unattended iteration loop

상태: Iteration 8까지 실행, 다음 개선점 확정

리뷰 보정: force-only acquisition support fallback dwell을 strict functional-grip의
8프레임 값과 분리해 30프레임으로 고정했다. 두 경계는 OR 조건이며 rollout
명칭은 teacher-guided learned arm으로 정정했다.

## 현재 기준선

- curriculum: 1 mm
- learned rollout: success=false, grip lost
- final error: 3.58 mm (tolerance 0.20 mm)
- final hand load: 58.86 N, overload=true
- failure boundary: simultaneous active-digit overpressure

## 반복 절차

1. 종료 trace와 접촉력을 분석한다.
2. 한 번에 하나의 원인군만 수정하고 단위 테스트를 추가한다.
3. 1 mm teacher smoke에서 안전/그립/오차를 검증한다.
4. teacher 성공 시 MOVE-only 20,000 update 학습과 learned rollout을 렌더한다.
5. learned 성공 시 2 mm, 이후 5 mm로 승격한다.
6. 실패 시 수치와 원인을 기록하고 다음 수정으로 반복한다.

## Iteration 1 — force-consistent retention + thumb reacquisition

- [x] MOVE thumb/finger 유지 판정을 실제 distal-link force 기준으로 통일
- [x] 저압 엄지에만 rear-face 경로 reference를 bounded slew로 재개입
- [x] 경계 테스트 및 전체 stability adapter 테스트
- [x] 1 mm teacher smoke
- [ ] 성공 시 20,000 update 학습
- [ ] learned rollout 렌더 및 분석
- [x] 실패 분석: 682 MOVE samples, overload=false, grip lost,
  final error=25.71 mm, thumb distal force=0.475 N

## Iteration 2 — closed-loop direction A/B

- [x] 기타 위치 오차에 대한 palm velocity 부호 반전
- [x] 1 mm teacher smoke에서 error 추세 비교
- [x] 실패: 540 MOVE samples, final error=29.46 mm로 정방향보다 악화

## Iteration 3 — grip-frame impedance

- [x] TRANSPORT 시작 palm-guitar 상대 오프셋 저장
- [x] object error + relative-offset restoration 결합
- [x] 1 mm teacher smoke
- [x] 실패: final error=5.93 mm로 개선됐으나 101 samples에서 thumb loss

## Iteration 4 — orientation-aware 6-DoF grip frame

- [x] palm offset을 guitar-local 좌표로 저장
- [x] 현재 guitar quaternion으로 world offset 복원
- [x] 1 mm teacher smoke
- [x] 실패: Iteration 3과 동일하게 101 MOVE samples, final error=5.93 mm
  및 thumb loss. 초기 실패 구간에서는 회전 보상이 병목이 아님.

## Iteration 5 — TRANSPORT 전용 thumb path recovery

- [x] trace 분석: thumb LOAD 고착, surface gap=-4.5~-4.9 mm,
  alignment=0.734~0.737, normal force≈0 N
- [x] 최초 구현 실패: 전역 LOAD rollback이 정상 GRIP acquisition까지 차단
- [x] 복구 적용 범위를 TRANSPORT 이후로 제한
- [x] 획득 trace: thumb/index/middle/ring distal force는
  3.63/1.62/2.56/2.37 N이나 angular speed=0.536 rad/s 및 palm force=0 N로
  정적 functional gate가 계속 실패
- [x] TRANSPORT 진입을 30-frame distal support gate로 분리하고 정착 검사는
  기존 SECURE 단계에 유지
- [x] deep/tangential 접촉 10프레임 지속 시 CLEAR부터 재접근
- [x] 단계 trace: frame 3420에 TRANSPORT 진입, SECURE 초반 최대 11/20 valid
  이후 재경로가 조기 발동해 thumb force=0 N 및 SECURE 0/20으로 붕괴
- [x] thumb 재경로 발동 범위를 MOVE 단계로 추가 제한
- [x] 재접근 중 thumb reference 이동 한도와 thumb loss 유예 확대
- [x] 1 mm teacher smoke: MOVE 260 samples, overload=false,
  final error=5.30 mm, thumb loss
- [x] teacher 실패로 해당 버전의 본 학습은 건너뜀

## Iteration 6 — local thumb TOUCH recovery

- [x] Iteration 5 MOVE 260 samples, overload=false, final error=5.30 mm
- [x] 실패 분석: full CLEAR는 엄지 가동범위에서 10 mm 이격에 도달하지
  못하고 최종 thumb distal force=0 N으로 종료
- [x] 현재 접촉 위치를 기준으로 TOUCH를 재시작하도록 변경
- [x] TRANSPORT TOUCH에서는 alignment>=0.78 전까지 LOAD 전이를 금지하고
  orientation IK weight를 0.80으로 상향
- [x] 1 mm teacher smoke: MOVE 162 samples, overload=true,
  final error=9.15 mm, total load=66.46 N
- [x] 과압으로 해당 버전의 본 학습은 건너뜀

## Iteration 7 — low-impulse local recovery

- [x] Iteration 6 실패: MOVE 162 samples, final error=9.15 mm,
  thumb distal=29.69 N, total load=66.46 N, overload=true
- [x] thumb recovery slew 0.002→0.00025, reference cap 0.20→0.05
- [x] TRANSPORT TOUCH orientation weight 0.80→0.30
- [x] 느린 복구를 위해 thumb-only loss dwell 240→600 frames
- [x] 1 mm teacher smoke: MOVE 1,177 samples, overload=false,
  final error=27.84 mm, thumb loss
- [x] 20,000 update 학습: final BC loss=3.7772e-6
- [x] learned rollout 렌더: final error=6.70 mm, overload=false,
  opposing finger loss 10 frames
- [x] 다음 개선점: guitar-local per-finger distal contact servo를 arm과 분리해 검증

## Iteration 8 — opposing-finger arm tracking during thumb recovery

- [x] Iteration 7: MOVE 1,177 samples, overload=false, final error=27.84 mm,
  thumb=0 N, opposing fingers=3.40/3.93/3.88 N
- [x] 원인: thumb TOUCH 동안 arm 완전 동결로 guitar-hand frame drift 누적
- [x] thumb recovery 중 안전한 opposing distal contact 2개 이상이면
  저속 arm tracking 허용
- [x] 1 mm teacher smoke: MOVE 235 samples, final error=21.57 mm,
  overload=false이나 유지시간 급감
- [x] Iteration 8 폐기, 안전 유지시간이 가장 긴 Iteration 7로 복귀
- [x] Iteration 7 데이터로 20,000 update 학습
- [x] learned rollout 렌더 및 실패 상태 명시

## Iteration 9 — review-corrected acquisition contract

- [x] 리뷰에서 문서 30-frame dwell과 실제 8-frame GRIP dwell 재사용 불일치 발견
- [x] `TRANSPORT_ACQUISITION_SUPPORT_DWELL=30` 분리 및 29/30 경계 테스트 추가
- [x] controller 표기를 `teacher_guided_learned_arm`으로 정정
- [x] 20,000 update 재학습: MOVE 632 samples, BC loss=2.1803e-7
- [x] teacher: final error=10.93 mm, load=48.64 N, overload=true
- [x] learned-arm rollout: final error=3.58 mm, rotation error=0.535 deg,
  load=58.86 N, thumb distal=28.87 N, overload=true
- [x] 다음 개선점: TRANSPORT 진입 직후 저장된 PD 압축 해소와 digit별
  force redistribution을 arm 이동 전에 검증
