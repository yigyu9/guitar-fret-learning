# 고정 길이 스트랩 + 왼팔 준비 목표 유지·Fret 손가락 사전 검수

요약 판정: **문제없음 — 사전 코드 검수 PASS**.

Critical: 없음. Warning: 없음. Suggestion: 없음.

## 확인 근거

- [underneck_strap_environment.py:12](/home/ajou/yigyu/3/stability_adapter_2/underneck_strap_environment.py:12): 생성 경로의 `GraphicsGym→NoStrapGym→native Gym`을 확인한 뒤 raw `apply_body_force_at_pos`만 전용 strap callback으로 보관한다. 일반 force/effort API와 시작 이후 state 쓰기는 기존 NoStrapGym guard를 계속 거친다. 호출 우회 범위가 passive cable 제출에 한정된다.
- [underneck_strap_environment.py:24](/home/ajou/yigyu/3/stability_adapter_2/underneck_strap_environment.py:24): 매 물리 step 직전 현재13점 route·속도로 기존 tension-only law를 평가한다. 기타 목표 pose/목표오차 입력을 사용하지 않고 길이/길이율·고정 rest length·기존 k/d/cap만 사용한다. 힘·경로 유한성, 경로힘 합0, 장력 범위, rest length 불변을 검증하고13점 힘을 환경 좌표로 제출한다.
- [underneck_strap_environment.py:39](/home/ajou/yigyu/3/stability_adapter_2/underneck_strap_environment.py:39): 두 guitar button과11 human guide의 기존 route_handles에 cable힘을 적용하고 단일 simulate/fetch 후 step을1 증가시킨다. 기타 고정·손 부착·강제pose 유지 또는 별도 물리적분을 추가하지 않았다. 로컬 Isaac Gym API 문서의 `apply_body_force_at_pos` 반환형은None이며 힘의 단위는N, ENV_SPACE는 force/point 좌표계다.
- [run_fret_fingers_strap.py:45](/home/ajou/yigyu/3/stability_adapter_2/run_fret_fingers_strap.py:45): native t=0 상태를 no-strap baseline과 exact 비교한다. 제어권 Fret21/준비L9/hold15/초기36,2초 인계, 원본 평가·최초 done 종료, 학습0·Strike OFF 경로는 이전 arm-hold runner와 같다. 스트랩으로 이후 준비 물리가 달라질 수 있으므로 t>0 PREP 상태 동등성을 주장하지 않는다.
- [run_fret_fingers_strap.py:161](/home/ajou/yigyu/3/stability_adapter_2/run_fret_fingers_strap.py:161):240Hz strap 기록을 보존하고 step 수와 일치하는지 검사한다. 최종 rest length는 기존 BASE 절대값1.1018469719600776m와 비교한다. 현재 route 길이로 rest length를 재설정하는 변경은 없다.
- [strap_trial_recording.py:55](/home/ajou/yigyu/3/stability_adapter_2/strap_trial_recording.py:55): native raw camera와 같은 상태의13점 실제 route를 기록하고 view/projection/depth로 overlay를 그린다. 시각화 후 native 상태 동일성을 확인한다. Overlay는 실제 cable 경로 표시이며 물리 천의 두께·처짐·추가 충돌이 아니다.
- [fret_fingers_strap_preserved_run.py:34](/home/ajou/yigyu/3/stability_adapter_2/fret_fingers_strap_preserved_run.py:34): baseline initial값과 overlay font 입력을 기존 conservative SHA closure에 추가하며 새 A 파일 snapshot과 실행 후 입력 불변 감시를 유지한다.

## 검증과 한계

관련 새/참조 Python6개 AST 문법 검사 PASS. ownership_preflight9개 검사PASS: 예상 초기13점route1.073576470664m, inherited rest1.1018469719600776m, 초기 slack 장력/힘0, taut 및 routed 장력 범위·힘 합0을 확인했다. 실제 force API 효과·native 초기route·스트랩 이후 물리 경과·영상·운지 결과는 아직 실행 전이다. CPU PhysX 실험 후 확인해야 하며 사전PASS를 안정화/음악 성공으로 판단하지 않는다.

[analyze_fret_strap.py:34](/home/ajou/yigyu/3/stability_adapter_2/analyze_fret_strap.py:34): 분석은 PREP 이후 exact 비교를 요구하지 않고 native t=0만 baseline과 대조한다. 고정 rest·240Hz step 시퀀스·기록 passive law 재계산·raw/overlay PNG SHA·source 최초 done·제어권·영상 terminal까지26개 검사를 구성한다. 두 실행의 공통 저장 physical step을 비교하며 초기 t=0 대비 위치/회전과 전체 실행 결과를 분리한다. 실행/분석 이후 main 진행 문서를 갱신하는 순서를 유지해야 입력 closure 현재 SHA 검사가 정확하다.

## 검수 시 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/underneck_strap_environment.py`: `e60fe4d4f792254d5b95bd4c1fb689a1c11293c67663dcf67e2f12a0427dc88e`
- `/home/ajou/yigyu/3/stability_adapter_2/run_fret_fingers_strap.py`: `a6533a1a7a8151eac1105ef75308cd737f927454c6beeea2a2c04f811d4c9064`
- `/home/ajou/yigyu/3/stability_adapter_2/fret_fingers_strap_preserved_run.py`: `efc4680541d6a5ad9d80503c7065311b10b0857b553c0a1c4a1dd624d3025dc0`
- `/home/ajou/yigyu/3/stability_adapter_2/FRET_FINGERS_STRAP_PLAN.md`: `7f95a5bcba348920787309d15cbdb4249563b0a5ade4f212bd24f0a70bf0017f`
- `/home/ajou/yigyu/3/stability_adapter_2/strap_trial_recording.py`: `a52a33eecdb943d0acbc7faffa51816ab47447c7a9c48d4036e8dd70fb7353f3`
- `/home/ajou/yigyu/3/stability_adapter_2/strap.py`: `2dd34bc52286878569ee83a1c02e15daeb35b8fe14a275d64d8a1be1969d3361`
- `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_strap_v1/ownership_preflight.json`: `e8c578f13799f97ede550cc3c49f9d53e3a5281e3bd8b807792ccb25df17ffa3`
- `/home/ajou/yigyu/3/stability_adapter_2/analyze_fret_strap.py`: `c60dd5537c9dbc0204ca37e28ab5f30dbba7fec6eb49a406125a0ed1a522a60e`
