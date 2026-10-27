# Strike current-G 전이 및 종료 후 기록 독립 검수

검수 범위는 신규 v2 runner·사전 보존 wrapper·종료 후 촬영 계획과 현재 저장 native_v1/v2 기록이다. 기존 pre_review.md는 동결 유지하며 검수자는 actor/native/분석/렌더/감사 본체를 실행하거나 다른 담당자 파일을 수정하지 않았다. 최종 문서·미디어 전체·보존 봉인은 후속 대상이다.

## 요약 판정: 수정 권장

Critical: 현재 변경 경로에서 확인된 즉시 물리 blocker 없음. 다음 Warning은 소비본을 보존한 상태에서 설명 범위를 좁히거나 별도 버전으로 보완한다.

- Warning — [run_strike_live_probe_v2.py:160](/home/ajou/yigyu/3/stability_adapter_2/run_strike_live_probe_v2.py:160): source unsafe는 terminal 시점 한 번만 검사한다. 이후 [passive loop:169](/home/ajou/yigyu/3/stability_adapter_2/run_strike_live_probe_v2.py:169)는 joint q/qd·기타 body pose/twist의 finite와 |qd|>50만 검사하며 새로운 guitar penetration/irrecoverable safety 및 전체 human body pose/twist nonfinite를 재평가하지 않는다. 후기 전체의 포괄적 unsafe 즉시 중단으로 인증하면 안 된다. 현재 실제 감시 범위를 문서에 적고, 일반 안전 감시가 필요하면 원본 source scoring/clock과 분리한 read-only monitor를 새 variant로 추가한다.
- Warning — [STRIKE_TRANSFER_RECORDING_CONTINUATION.md:7](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TRANSFER_RECORDING_CONTINUATION.md:7)의 terminalstep 표본 보존 문구와 실제 v2는 다르다. [runner:154](/home/ajou/yigyu/3/stability_adapter_2/run_strike_live_probe_v2.py:154)의 break 뒤 별도 sample이 없고 후기도 stride8로만 기록한다. 실제 v2 trace는192→200이며 종료196의 native p/q 표본이 없다. policy_end_step196/time·control info/reasons는 보존된다. v1에는196 마지막 native 표본이 있으나 이를 v2에서 실제 측정한 표본으로 표시하지 않는다. 최종 설명에서 구분하거나 차후 trace-only terminal sample을 추가하고 균일 영상 clock은 유지한다.

## 코드·실제 저장 대조

[사전 보존 wrapper](/home/ajou/yigyu/3/stability_adapter_2/strike_probe_preserved_run.py:18)는 task import/native 초기화 전에 보수적956입력 superset SHA를 기록하고 직접 패키지 py/md/xml 사본을 만든다. runner 자신의 __main__ 원문과 이전에 누락됐던 config/pose/gains/assets·BASE·FACETS 입력이 포함된다. 새 runner/wrapper/continuation 원문 사본3개는 before SHA 및 현재 파일과 exact다. 외부 source/data는 SHA 보존이며 모두 사본을 만들었다고 주장하지 않는다. inputs_after는956개 changed없음/task_error없음을 기록한다. 이전 v1 자체 attempt의 누락은 소급 수정하지 않고 새 wrapper 근거로 구분한다. 전체956 SHA의 별도 최종 봉인은 root 후속 범위다.

v2의 목표 합성·초기화·actor·원본303 관측/후처리는 v1과 같고 terminal 이후 분기만 별도다. done 뒤 actor 추론/view.step·PI update·song clock/detector scoring은 중단한다. 마지막81목표를 그대로 유지한 native simulate/fetch만 계속하며 no-reset/no-state/no-force guard와 PD/render 검사를 유지한다. source episode가 연속5초 진행된 것으로 해석하지 않는다.

실제 v1은 failure null/checks true이지만 wrong_crossing_count performance terminal로49 policy/196 physics step,0.816666667초에 멈췄고 completed_requested_5s false다. 실제 v2 초기값 전체와49 control records는 v1과 exact다. 공통 stride8 trace0..192의 모든 기존 field도 exact이며 v1의 추가196 terminal 표본은 v2에 없다. v2는 총1200physics step/49policy,policy_end196·0.816666667초,post_termination_passive_only true다. trace151개 중192시점까지 policy_active true,200부터 false이고 report의 상수 후기목표·PD·render·금지호출 판정은 true다. learning0/music_success false를 유지한다. completed_requested_5s true는 물리 촬영 경과 완료이며5초 policy 또는 연주 성공이 아니다.

사전 probe-only의 명령/한계/history 판정은0회 루프의 초기값이라는 이전 Warning을 유지한다. CPU pose 변환/actor 입력 반응만 그 결과의 완료 범위다. 이번 실제49명령은 별도 근거이며 원본 학습 actuator/범위와 자유기타 native 환경의 전체 ABI 동등성·공식 G0 자격은 인증하지 않는다.

Python3.8 AST는 새 Python2개에서 통과했다. 읽은 소스 SHA:

- run_strike_live_probe_v2.py: `03a53787aaf5cc5d1e8a00631a255bee2a9058aa3c81bd154758c06d8c1f01fb`
- strike_probe_preserved_run.py: `ef530627c36e2aa312285c585b0c1186b7d3401226ac64f6eec07f1abd4043d8`
- STRIKE_TRANSFER_RECORDING_CONTINUATION.md: `abc625521abfd46e908a096c806d314d48c63f0f754b4f9598f4ceb86c8eeccf`

현재 단계별 검수 기록이며 최종 문서·artifact/영상·원자료 해석 delta와 root 보존 감사는 아직 완료 판정하지 않는다.

## 최종 자료·문서 및 봉인 코드 검수

수정 전 검수 초안은 [review_before_final.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_live_guitar_probe_v1/review_before_final.md)에 exact 보존했고 pre_review.md의 동결 SHA도 유지했다. 최종 README·변경 색인·VISUAL §124 및 main PLAN:124/README:1429의 실제 파일·줄·MP4 embed를 대조했다. main 이전 snapshot과 현재 append prefix는 exact다. 원본 소비 leaf의 terminal 표본/unsafe 감시 불일치는 그대로 보존하고 최종 결과 설명에서 실제 범위를 좁혀 명시했다. 따라서 위 Warning2는 구현상 미인증 후속 항목으로 남지만 현재 진단의 자료·설명을 차단하는 과장이나 누락으로 남지는 않는다.

[저장 분석기](/home/ajou/yigyu/3/stability_adapter_2/analyze_strike_live_probe.py:11)를 읽고 Python3.8 AST 및 입력14 SHA를 확인했다. 실제49 controls exact 대조, history inverse 오차 `8.548069962976967e-8`, 다음 관측 history 차이 `0`을 독립 계산했다. raw151 p/q와 clock0..1200/stride8로 최대 `63.386052295 mm / 14.883320825°`, 마지막 `44.061419548 mm / 11.767637916°`를 재계산해 summary·표와 일치했다. tip 첫 post-step `351.935863495 mm`, 최소 `131.525650620 mm`, 종료 `152.024284005 mm` 및 terminal TP0/FP4/FN1/F1=0은 원본 detector 평가 범위이며 물리적 현의 진동/소리 성공으로 인증하지 않는다.

실제 최종 timeline PNG를 열어 두 축 단위·0~5초·196step 경계·passive 음영/설명이 자료를 가리지 않는지 확인했다. 196은192/200 사이 경계이며 해당 native p/q를 생성하거나 보간하지 않는다. 최종 artifact의 입력12/출력1 및 producer SHA가 현재 파일과 일치한다. 원본 실패/이전 성공 후처리 variant와 문서 정정 전 사본은 유지한다. elapsed는 미측정 null이고 그림 생성은 물리/actor 실행이 아니다. 두 MP4 SHA와 저장 ffprobe의151frames/30fps/5.033333s를 대조했으며 새 ffprobe/렌더 실행은 하지 않았다.

wrapper의956개 before SHA를 현재 원문 및 직접 패키지 사본에 대조했다. 변동은 실행 이후 승인된 main PLAN/README 두 문서뿐이며 main_before는 당시 입력 SHA와 일치한다. during-run inputs_after의 changed없음과 after-authorized-append 변동을 구분한다. 초기 실패 probe_v1/v2 로그는 gymtorch import 단계의 cache/Ninja 오류이며 native 환경 생성 전이다. 성공한 probe-only1회와 native policy2회는 구분하고 probe-only 물리0/두 실제물리196 및1200step을 연속 한episode로 합치지 않는다.

미실행 [seal_strike_live_probe.py](/home/ajou/yigyu/3/stability_adapter_2/seal_strike_live_probe.py:16)는956입력/승인된 main delta·당시 main 사본·summary 입력/판정·최종그림 manifest12입력/1출력/producer를 검증하고 직접 source_final 사본을 exact 확인한다. phase inventory 생성은 자기 inventory/final verification 생성 이전이며 재귀 SHA를 포함하지 않는다. Python3.8 AST 통과 및 보존 논리에서 현재 조건의 명백한 blocker는 없다. 검수자는 봉인 producer를 실행하지 않았고 향후 생성될 root 결과를 선인증하지 않는다.

최종 README SHA: `ce5b97805ac95f50dba9498f15e69c637f8ffae2f8a7759f023e22704e3a1b3f`.
최종 CHANGED_FILES SHA: `b0e680c103529d26941ede91a3757675ec9ab78ed8fb5dd661becad443137fc2`.
최종 timeline PNG SHA: `9f9c05e2b5dd7b60e5ee844e37f56907852a4ac262dd46b6dfc79f906457256b`.

요약 판정: 문제없음. 현재 범위는 current-G CPU 반응 및 실제49명령의 연결·실패 재현·종료 후 자유물리 촬영·그 자료와 설명의 정확성이다. 전체 source ABI/G0 자격·후기 전체 안전 감시·연주 성공은 미인증이다. 소비 소스 변경이나 추가 actor/native/분석/그림 실행 없이 검수를 완료한다. 이 기록은 최종 동결하며 root 보존 봉인만 후속으로 남는다.

최종 판정: PASS
