# 기타 바디 쪽 몸통 기울임 — 실제 5초 비교

사용자가 지정한 방향은 **정면 화면의 왼쪽 = 휴머노이드 오른쪽 = 기타 바디 쪽**이다. 이 방향으로 추가 4° 기울임을 만들고 오른팔과 기타 초기 배치를 함께 맞췄다. 상완 접촉은 생겼지만 기타 초기 회전을 유지하지 못했으므로 최종 안정 자세로 채택하지 않는다.

## 초기 상태와 제어

- 승인된 자연 오른팔 기준에서 Torso 1°·Spine 2.5°·Chest 4°의 추가 world 방향 기울임을 만들었다. 이는 각 관절 scalar 축의 각도와 다르다. 머리 초기 world 방향은 보정했다.
- 기타 초기 이동은 기준에서 world X −32.779mm, Y +10.632mm, Z +21.925mm이다. 초기 기타 회전은 원래 수평 넥/정면 앞판을 유지했다. 오른 Thorax·Shoulder·Elbow 9각을 조정하고 손목·손가락·왼팔 초기각을 유지했다.
- 두 실행의 전체 native 초기 상태가 정확히 같다. right12만 인간 관절 토크로 제어하고 다른69는 기준 목표각 PD를 사용한다. root·하체 고정, 스트랩 OFF, 왼손 지지 없음, 기타는 자유 물체다. 기타 직접 외력·손 부착·런타임 pose 덮어쓰기는 없다.
- 조건1은 기존 전완점 유지 제어다. 조건2는 같은 초기값에 상완 근위점 제어를 추가했다. 두 인간 목표점은 초기 world 위치로 유지한다. 전완 목표는 초기 surface 안쪽8mm, 상완은6mm이며 실제 침투 깊이 명령이 아니다.
- 전완 K1500/D25, 상완 K2000/D30, 각 요청힘 상한30N. 자세 토크와 중력 보상을 더하고 모델 토크 한계로 제한한다. 요청힘은 측정된 접촉력이 아니다.

## 실제 결과

| 지표 | 전완 제어 | 전완 + 상완 제어 |
|---|---:|---:|
| 5초 바디 bounding-box 중심 이동 | 48.051mm | 47.501mm |
| 5초 기타 전체 SO(3) 회전 변화 | 52.174° | 47.662° |
| 5초 넥 고도(초기 수평0°) | −15.921° | −10.019° |
| 2→5초 바디 중심 추가 이동 | 0.310mm | 0.316mm |
| 2→5초 전체 회전 변화 | 0.317° | 0.494° |
| 상완 접촉 표본 | 968/1200 | 256/1200 |
| 전완 접촉 표본 | 1191/1200 | 1149/1200 |
| 왼팔·손 / 머리 접촉 표본 | 각각0/1200 | 각각0/1200 |

접촉 표본은240Hz의 각 물리 step 후 기록이며 지지력 비중을 의미하지 않는다. 상완 누름 추가로 넥 하강은 줄었지만 상완 접촉 표본은 감소했다. 2초 뒤 거의 정지한 것은 초기 자세 유지 성공이 아니라 회전된 자세로 정착했다는 뜻이다. 원점이 넥 쪽에 있어 큰 회전 시 루트 이동373.073/345.241mm가 바디 중심 이동보다 크게 나온다. 바디 bounding-box 중심은 질량중심이 아니다.

오른허벅지 접촉은별도60Hz 제어직전 표본에서 두 조건 모두297/300이었다(양 raw lambda 표본297/296). 왼Hip는3/300, Chest는0/300이었다. 이 표본계열을1200개 endpoint 수치와 합치지 않는다.

## 자료와 검증

[그림·설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/artifacts_v1/README_V1.md:1), [5초 전신·손 영상4개](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/body_side_lean_axilla_v1/INDEX_V1.md:1), [초기 후보와81관절각](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/search_v5/right4_close_support/candidate.json:1), [두 조건 요약](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/result_summary_v1.json:1), [전완 조건 검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/analysis_v2/verification.json:1), [상완 추가 검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/analysis_v3/verification.json:1). 분석은 기록·명령식·제한된 점속도 일치 검증이며 연주·중력/Jacobian 전체 인증·반복 강건성 검증은 아니다. 두 조건 모두1200물리step/300제어/151영상frame, 물리5초·영상5.033초다. checkpoint·학습은 이번 단계에서 연결하지 않았다.

## 계획·중간 실패 보존

- source1의 몸통만4°/8° 후보는 상완 겹침으로 제외했다. source2~4는 겹침·임시 근위간격 문턱으로 제외하고 실제 실행하지 않았다.
- source5는 source4 해를 그대로 복사하고 임시 근위 접근 문턱만3→5mm로 바꿔 native 진단 후보로 수락했다. source 전체와 analytic capsule 간격이 양수여도 PhysX cooked 접촉 인증은 아니다. 정확한 오른Hip1.782mm/왼Hip.131mm source 수치는 [정정 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/source_scope_note_v1.md:1)에 있다. 소비된 계획의 ‘두Hip 약.1mm’ 문구를 수정하지 않고 정정 기록을 추가했다.
- analysis_v1은 상대 config 경로가 native의 절대경로 해시 키와 맞지 않아 실패했다. 실패 입력/로그를 보존하고 절대경로로 analysis_v2를 새로 실행했다. 현재 두 분석기의 CLI는 절대경로를 사용한다.
- 이전 넥 쪽 기울임 실험은 반대 방향 진단으로 보존한다.

## 다음 소단계

이번4° 몸통 기울임은 상완 접근에 도움이 됐다. 다음에는 초기 기타 자세는 유지하면서 오른 허벅지 받침점과 상완·전완 접촉 위치를 함께 조정해 기타의 기울어짐과 앞판 비틀림을 줄이는2개 이하의5초 비교가 적절하다. 상완 누름 크기를 키우기보다 지지점 배치를 먼저 다룬다. 현재 두 조건을 연주용 안정 초기값으로 확정하지 않는다.

[현재 비교 계획](/home/ajou/yigyu/3/stability_adapter_2/BODY_SIDE_LEAN_AXILLA_PLAN_V6.md:1), [변경 파일·실제 줄 번호](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/CHANGED_FILES_v1.md:1).
