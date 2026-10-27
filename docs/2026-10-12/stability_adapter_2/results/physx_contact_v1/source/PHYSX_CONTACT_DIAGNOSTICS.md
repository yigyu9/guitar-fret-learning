# PhysX 접촉·물리 step 진단 계획

2026-10-06. 직전 단위는 입력·batch 재개를 검증했다. 이번 단위는 H0의 초기 관통 후보와 0.1초 큰 기타 이탈을 실제 native 접촉 기록으로 비교한다. 새 자세·길이·제어권·gate·허용치·성공 기준을 채택하지 않는다.

## 계획과 검증

1. 기존 step의 물리 1회 부분을 `step_physics()`로 분리한다. 기존 60Hz `step()`은 동일한 240Hz 물리 4회를 호출한다. → H0의 기존 7개 기록 시점 p/q·속도·몸통 측정과 완전히 같은지 확인한다.
2. 같은 CPU PhysX·dt·contact/rest offset에서 analytic box의 분리, skin 범위, 접촉, 1mm 관통을 비교한다. 준비 후 초기 상태를 한 번 복원하고 첫 물리 step의 native contact를 기록한다. → `initial_overlap` 부호·크기·contact 발생 여부를 관찰하고 의미를 검증한 뒤 실제 기타 기록을 해석한다. `min_dist`는 유지 목표 거리이며 실제 signed gap으로 쓰지 않는다. `lambda`는 원 API 필드로 보존하며 단위 교정 없이 impulse/force로 환산하지 않는다.
3. H0 + 기존 절대 L_A를 24 physics steps 실행한다. 각 step에서 자유 기타 상태, 실제 스트랩 적용 장력, native 접촉의 env body ID·부위·normal·initial_overlap·나머지 raw 필드를 기록한다. → 고정 root·held target 유지, 기록 query의 상태 비변경, baseline 재현을 확인한다.
4. Sol이 원자료를 분석한다. → Luna가 확정된 brief로 시계열 그림·설명을 누적한다. 별도 change-reviewer가 코드·실측·문서를 검수한다.

- [ ] 단일 physics step API·baseline 동등성
- [ ] analytic box의 native 접촉 필드 대조
- [ ] H0 240Hz 상태·장력·접촉 기록 및 불변 조건
- [ ] 결과 그림·누적 설명·원자료 보존
- [ ] 별도 검수

## 해석 경계

환경 초기화는 prepare 후 상태 복원을 포함한다. 복원 직후 contact buffer는 이전 prepare의 기록일 수 있으므로 첫 step 전 buffer를 현재 초기 배치의 증거로 쓰지 않는다. 첫 완료 step의 `initial_overlap`은 API상 그 물리 step 시작의 overlap이다. 실제 source mesh와 cooked PhysX의 수치 일치·전체 전신 clearance는 별도이며 한 부위의 contact 유무로 인증하지 않는다.

접촉은 기타 지지에 필요하다. 접촉 발생과 관통을 구별하며, 접촉 시점과 기타 이탈이 함께 보여도 그것만으로 단독 원인을 확정하지 않는다. 관절 torque, 자기 충돌과 chair/ground의 영향도 미검증임을 남긴다.

몸통 PD 목표·humanoid 고정 root·양쪽 Thorax 이하66 범위를 유지한다. 기타 고정/부착/반복 pose 덮어쓰기/인위적 복원 힘은 추가하지 않는다. calibration의 고정 analytic box는 기타 실험의 고정을 뜻하지 않는다.

구현은 `stability_adapter_2/`, 원자료·로그·그림·source snapshot은 `docs/2026-10-12/stability_adapter_2/results/physx_contact_v1/`에 저장한다. 이전 batch와 source snapshot은 그대로 보존한다. source 변경 후 이전 batch의 resume 거부는 의도된 계약이며 그 결과를 새 코드로 덮어쓰지 않는다.
