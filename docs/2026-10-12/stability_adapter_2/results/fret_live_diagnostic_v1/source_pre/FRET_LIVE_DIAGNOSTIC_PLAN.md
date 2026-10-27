# 현재 기타 기준 Fret 실시간 진단 — v1

## 목적·범위

사용자 승인에 따라 실제 Fret 실행에서 기타 이동과 손 접근 실패를 분리한다. 기존 무스트랩 `fret_fingers_arm_hold_v1`의 candidate_1·PD·준비 2초·팔 목표 유지·손가락21 정책을 그대로 재사용한다. 이번 단계는 관측/표시이며 새 보정 제어·학습을 추가하지 않는다. 기존 원본 runner와 보존 wrapper는 수정하지 않고 실행 시 recorder와 view 생성의 두 연결만 임시 교체한다.

root·하체는 기존 별도 고정 자산을 유지하고 몸통 목표도 유지한다. 기타는 자유 물리 상태다. 기타 고정·강제 손 부착·상태 덮어쓰기·인위적 기타 지지 힘은 사용하지 않는다. 스트랩 OFF를 명시한다.

## 기록 정의

- 바디 중심: 질량중심이 아닌 표시 기준점 local `[0,-0.4,-0.0217] m`; 현재 native p/q로 world 및 Pelvis 오른쪽/앞/위(RFU) 변환.
- 사용자 위치: 기존 world actor-root `[−.50,−.15,.65]`~`[−.15,.15,초기 Chest z] m`. 현재 q의 offset을 더한 조건부 바디 중심 box로 표시한다. 초기 Chest 상한을 고정하고 회전 자체로 경계를 바꾸지 않는다.
- 위치 이탈량: 각 world 축의 box 초과 거리 및 그 벡터의 길이. 회전: 초기 대비 최단 회전각·넥 world 고도·기타 앞면과 Pelvis 전방의 각도. 전체 Euler 허용집합 판정/거리 계산은 이번 단계에 포함하지 않는다.
- Fret: 카메라 시점에 native 상태를 view에 새로 복사하고 평가 전 현재 goal frame/弦·품·지정 손가락·현재 기타 기반 target_world를 기록한다. t0는 view 생성 전이므로 목표 미초기화로 표시한다. 손끝 body 원점→목표의 유클리드 거리와 source의 one-sided pad 접근거리를 구분한다. 후자는 실제 압착/성공 판정이 아니다.
- 손목: 실제 L_Wrist를 기타 local로 변환하고 goal wrist가 있으면 현재 기타로 옮겨 오차를 측정한다. 손목의 기타 상대 변화와 목표 frame 전환을 함께 본다.
- 접촉: native PhysX pair/raw 필드를 그대로 저장하고 실제 기타 body/neck와 왼손 접촉을 집계한다. pluck_range proxy는 별도로 제외한다. 표시는 접촉 body의 원점이며 정확한 표면 접촉점 또는 관통 깊이 인증이 아니다. raw lambda를 힘(N)으로 변환하지 않는다.
- source observe 인터페이스는 tracker를 갱신하지 않는다. 호출 전후 goal frame·progress·준비 clock·PD/history·goal/reward tensor 불변과 native 상태/제출 목표 불변을 검사한다. state/contact 복사 버퍼 갱신은 허용하며 제어 명령은 추가하지 않는다.

## 실행·검증 체크리스트

1. 계획 → 구현 → 사전검토: 좌표/경계/목표 할당 테스트와 독립 검수. root 소유: 새 source·wrapper·분석·main PLAN; 검수자: 지정 review.md만.
2. 실행: Isaac Gym native 전신/양손 raw PNG와 진단 PNG·전체 MP4를 t0~첫 원본 done까지 저장. 240 Hz physics / 30 fps; 최소 준비2초, 5초 임의 중단 없음. 입력 snapshot은 native import 이전, 입력 변경 시 실패. 보존 wrapper가 실행 중 A를 hash하므로 이 기간에는 A 문서도 수정하지 않는다.
3. 분석: 이전 baseline과 초기상태/제출 목표/trace를 비교해 관측이 기존 제어를 바꾸었는지 확인한다. 동일 target frame 구간에서 실제 거리·접촉·기타 상대 손목 이동을 해석하고 source 실패를 숨기지 않는다.
4. 검토·정리: 새 phase에 결과/이미지/영상/초기값/검증·파일 색인을 기록하고 과거 산출물 보존을 대조한다. 전체 회전영역/안전 형상/음악 성공은 이번 검사로 인증하지 않는다. 다음 제어 변경은 별도 v2 계획으로 진행한다.

결과 경로: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_live_diagnostic_v1/`.

- [ ] 구현·단위 검증·사전검수
- [ ] 실제 실행·전체 녹화·원본 제어 비교
- [ ] 분석·이미지 설명·독립 결과 검토·최종 보존

이 leaf 계획은 실행 소비 후 수정하지 않는다. 진행 완료 기록은 main PLAN에 추가한다.
