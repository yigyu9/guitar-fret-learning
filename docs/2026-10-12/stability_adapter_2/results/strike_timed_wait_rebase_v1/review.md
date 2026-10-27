# 독립 최종 검수

요약 판정: 문제없음. Critical 없음 / 미해소 Warning 없음 / 미해소 Suggestion 없음. 이번 단계의 구현·저장 원자료·영상·최종 문서 검수를 완료했다.

- `run_strike_timed_wait_rebase.py:182`의 닫힌 source phase 1 명령 42개를 대조했다. 실제 R9 좌표+bounded IK 보정을 요청하고 I를 유지한다. RECOVER 61개는 이전 actuator 목표+2×보정을 유지한다. float32 제출과 기존 rate/native bounds, phase별 81항 PD readback·setter 상태 보존을 확인했다. 실제 상태·source clock·phase를 덮어쓰는 변경은 없다.
- 실제 1,200 physics steps, 300 controls, 151 camera frames와 21개 실행 계약을 확인했다. PREPARE/PLAY/HOLD는 49/178/73이다. Native 입력 1,066개와 별도 분석 입력 7개는 before/after 및 현재 SHA가 일치했다.
- 이 단계의 `compare_before_wait.py`와 `pre_wait_comparison.json`을 독립 대조했다. 이전 priority 실행 대비 2.5초 전 controls 150개(`info` 포함), 2.5초까지 전체 native trace 76개와 비교 입력 6 SHA가 exact다. 전체 1,200-step 동등성 주장은 아니다.
- 첫 event 0/string 2 DOWN의 1.35초 timely hit(+44.484798ms) 1건과 첫 scheduled recovery 2.366667초를 확인했다. Wrong 총 4회는 초기 READY 1회 및 후속 3회이며, source 종료는 3.783333초다. Physical target hit/accepted release mask는 각각 1, physical release 4, miss 6, partial F1 0.166666672다. 이후 HOLD 기록을 연주 완료로 계산하지 않는다.
- 실제 pick의 guitar-local z 최대 97.983354mm를 닫힌 창 저장 상태에서 재계산했다. 기타 위치 최대/종료 46.353646/39.772717mm, 회전 최대/종료 7.095455/5.416182°와 region 제어 283/300·policy 164/178을 대조했다. 이 위치 관측은 원인·음향·접촉력 인증이 아니다.
- 두 native 영상의 실제 SHA와 ffprobe 1280×720, 151 frames, 30fps, 5.033333초를 확인하고 종료 hands PNG를 직접 검수했다. README·CHANGED의 절대 링크와 자료 출처를 확인했다.

해소된 Warning: README:7의 후속 wrong 4회 표현을 총 4회(초기 READY 포함)로 교정했고, CHANGED_FILES:17의 prefix 미완료 표현을 완료된 비교/검수 작성 대기로 분리했다. 수정 전 두 문서는 `doc_before_final_wording/`에 보존되어 있다.

확인 SHA256: runner `c0c58a112c7b3bd09920a8bd035d14d80708ca6e5bdf578cca92eb194491840e`, preserved wrapper `dd82b0ca438ee58a3b7a37992667002478cf93408484124eccd4865d226355f4`, 분석 요약 `0e53d92f2f643e011334eb53ca718c7897c3d154dc2afc904dede265dcc9eb2f`, prefix 결과 `c37d359fa451211d81fe66aaadb2cf2151afbbd57acbe89bddda305d28b14470`.

검수는 읽기 전용 저장 자료·순수 수치 계산·SHA·ffprobe·이미지 확인 범위다. 추가 native 초기화/물리 실행은 없었다. 완성 연주·지속 지지·학습 성공은 미확인이고, root의 후속 최종 보존 감사는 이 검수의 완료 주장에 포함하지 않는다. 이 review는 동결한다.
