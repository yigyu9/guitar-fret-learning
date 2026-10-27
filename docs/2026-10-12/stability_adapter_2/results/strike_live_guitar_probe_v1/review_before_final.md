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
