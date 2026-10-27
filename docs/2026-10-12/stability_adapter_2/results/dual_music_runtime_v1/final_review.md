# 양손 음악 runtime 최종 독립 검수

## 요약 판정

**문제없음 — 이번 진단의 코드 경로·원자료·분석·최종 설명은 일치한다.** 최신 진입점은 `run_dual_music_v5.py`다. 두 동결 정책의 실제 연결은 확인됐지만 연주와 지지에는 실패했으며, 최종 공동 정책·학습 환경의 완성 판정이 아니다.

검수자는 소스를 읽고 저장 데이터를 CPU에서 재계산했다. 추가 native 물리·정책 추론·학습을 실행하지 않았으며, 이 파일만 작성했다. 전체 기존 파일 보존 감사와 최종 봉인은 root 소유다.

## Critical — 반드시 고칠 것

현재 진단 실행을 막는 미해결 오류는 발견하지 못했다. v1의 빈 프레임 cleanup·영역 판정 우회·metadata 문제는 보존된 v1을 수정하지 않고 v2에서 보완했다. v4의 Strike 입력 검증 누락도 v5에서 보완했고 실제 재실행까지 확인했다.

## Warning — 학습 전 해소할 것

- [run_dual_music_v5.py:196](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v5.py:196), [base.py:787](/home/ajou/yigyu/3/tab2body/env/base.py:787): 실제 최종 목표를 source 행동 이력으로 역변환하면 action_scale과 clip 때문에 항상 표현되지 않는다. Fret 재구성 오차는 최대 0.662462 rad, PLAY 중 0.637462 rad이고 clip 표본은 146개다. 물리548D의 직전 최종 목표는 정확하지만 source 실행 동등성이나 교사 유효성을 주장할 수 없다. 후속 학습 전에 지지 자세와 source 표현 범위를 맞추거나 이력 계약을 새 버전으로 정해야 한다.
- [run_dual_music_v5.py:143](/home/ajou/yigyu/3/stability_adapter_2/run_dual_music_v5.py:143), [README.md:65](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/README.md:65): source 관측은 native COM 선속도를 상속하고 physical548은 body-origin 속도를 사용한다. Strike의 작은 역변환 오차 8.94e-8 rad도 관측 ABI 동등성을 증명하지 않는다. 후속 단계에서 속도 좌표와 기준점을 명시적으로 닫아야 한다.
- [dual_music_clock_v1.py:56](/home/ajou/yigyu/3/stability_adapter_2/dual_music_clock_v1.py:56), [dual_music_clock_v1.py:73](/home/ajou/yigyu/3/stability_adapter_2/dual_music_clock_v1.py:73): 공동 판정은 240Hz 양 끝 sounding 값과 dwell의 보수적 bracket 및 crossing 성공 집계다. 실제 subframe 압현·접촉력·음표 유지/해제·dropout·fatal ledger를 인증하지 않는다. 현재 설명의 `training_ready=false`를 유지하고 이 계약들을 구현한 뒤 학습 준비를 판정해야 한다.
- [README.md:59](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/README.md:59): 두 pair 모두 준비 2초 뒤 PLAY 1.85초에 Fret의 기타-local 손목 X 위치 안전 경계로 끝났다. 공동 정산 4건 중 성공 0건, 오현 crossing 1건, 기타 최대 변위 403.605 mm/회전 63.992°다. 정적 preload의 위치 상자 개선을 연주 지지 성공으로 채택하면 안 되며, 현재 기타 자세의 공동 제어와 지지 호환성을 먼저 해결해야 한다.
- [PROVENANCE_NOTE_V2.md:14](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/PROVENANCE_NOTE_V2.md:14): 최초 실패한 pair artifact producer는 실행 시점 소스 snapshot/SHA 없이 같은 경로에서 정정됐다. 재구성본은 당시 봉인 원본으로 독립 인증할 수 없다. 최종 설명은 이 예외를 정확히 공개하며 성공한 v1/v2 후처리와 native 원자료의 현재 SHA는 확인된다. 후속 실패 시에도 수정 전에 원본 소스와 실행 기록을 보존해야 한다.

## Suggestion — 선택

새 반례 검증에서 crossing 직전·직후의 압현 전환과 이벤트 경계, sustain/dropout 및 실패 정산을 추가하면 음악 판정의 다음 구현 단계에 도움이 된다. 이번 12개 음악 반례와 4개 입력 검증은 실제 42개 이벤트 완주나 최종 reward 검증을 대신하지 않는다.

## 독립 대조 결과

- 정적 preload 0.5/1.0은 각각 1200 physics step·300 control·5초다. 저장 neutral 기준을 포함한 세 조건의 실제 초기 관절/기타 상태 동일성을 확인했다. 저장 trace에서 기타 변위·회전·위치 상자 초과 수치와 300개 최종 목표를 재계산해 분석값과 일치했다. 선택 1.0은 최대 변위 46.306 mm, 최대 회전 9.179°, 위치 상자 초과 0/301이며 전체 SO(3)·접촉 안정 인증은 아니다.
- pair v4의 924개 물리 표본을 `JointMusicClock`에 독립 재입력해 crossing과 이벤트 결과가 저장본과 완전히 일치했다. 231개 제어 기록에서 단일81 codec의 최종 목표·rate/bounds·physical548 직전 목표·1299 후보 관측의 유한성을 확인했다.
- 실제 terminal 원자료는 Fret done=true/Strike done=false, 손목 G-local 위치 X=0.34882652759552 m, 위반 축 X다. 관절각 한계나 곡 정상 완료로 해석하지 않았다. `report.completed=true`는 진단 기록의 정상 종료이며 음악 성공이 아니다.
- v5 입력 guard는 checkpoint 문서 digest/task, goal/grip SHA, 원본 행동 이름 순서·관측 manifest를 추론 전에 검증한다. 새 CPU 입력 반례 4개를 독립 재실행해 모두 통과했고 소비 SHA 3개가 현재 파일과 일치했다.
- v4/v5의 controls 231행, trace 232행, initial values, 음악 physics 표본 924행, crossing, 이벤트와 observation manifest가 전체 값까지 같다. v5 guard 보완은 같은 실패를 재현했으며 native 제어·판정 변화나 성능 향상을 주장하지 않는다.
- 실행 집계는 새 native 4회·4248 physics step·동결 pair 추론 총222 tick·영상8개·학습0이다. v3 Ninja import 실패는 scene 생성 전 0-step 시도이고, 이전 schema analyzer 실패도 별도 보존됐다. 기존 neutral은 재사용했다.
- preload/pair 후처리 manifest v1/v2 4개에서 전후 입력 및 현재 입력·출력 SHA가 모두 일치했다. 실제 preload 비교·곡선과 pair v2 몽타주를 열어 native 프레임·축·단위·시간·캡션을 대조했다. pair 그림은 v4의 0/2/3.85초 프레임이며 영상 117frame/30fps=3.9초와 물리 3.85초를 구분한다.
- 한국어 최종 README, CHANGED_FILES의 실제 줄 링크와 네 main 추가 기록을 대조했다. 곡 ID/42개 이벤트, 행동81/후보관측1299, 원본 정책30+30/유지21, 최종512→256 공동 정책 미구현이 구분됐다. 색인 링크25개는 파일·줄이 유효했고, 예정된 root 봉인 파일은 검수 시점에 완료된 것으로 취급하지 않았다.

검수 대상: [최종 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/README.md:1) · [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/CHANGED_FILES.md:1) · [preload 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload_analysis_v2.json:1) · [pair 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/pair_analysis_v1.json:1) · [v5 대조](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/contract_guard_v5_verification.json:1).
