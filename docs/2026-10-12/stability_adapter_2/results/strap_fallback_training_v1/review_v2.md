# 스트랩 파일럿 native 결과 독립 검수 v2

요약 판정: **문제없음 — 이번 smoke의 실제 정책 갱신·곡 평가·안전 종료/reset 연결을 확인했다.** 스트랩 안정화와 음악 연주 성공은 확인하지 못했다. 정식 reward v4/v5 인증·후속 장기 학습 완료·마감 시각 보장을 뜻하지 않는다. 산출물 표기에는 아래 Warning이 있다.

검수자는 저장된 소스·JSON·checkpoint state·PNG와 SHA를 읽기 전용으로 대조했다. 추가 native 실행·정책 추론·최적화 없이 이 파일만 생성했다. [사전 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/review_v1.md:1)는 보존했다.

## Critical

추가 차단 오류 없음. reset probe v1의 실패는 정책 ABI에 진단 producer를 포함해 발생한 실제 `ABI mismatch before restore`다. 장면 초기화1회·물리0이며 실패 소스/보고서를 보존했다. [probe v2:22](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/run_reset_probe_v2.py:22)는 policy closure와 진단 감사 입력을 분리했고 실제 검사가 성공했다. ABI 거절을 우회하거나 기존 policy 소스를 수정하지 않았다.

## Warning

- [그림 producer:196](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/produce_artifacts.py:196): 실제 PNG에서 상단/중간 우측 범례가 마지막 평탄선 일부를 가린다. 수치와 추세는 대조 가능하지만 AGENTS의 표본 비가림 요건에는 미흡하다. 소비된 그림은 보존하고 후속 버전에서 범례를 axes 밖에 둘 것을 권장한다.
- [초기 산출물 설명:83](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/README.md:83): `input_hashes.json` 링크가 상대 경로다. 파일은 존재하며 근거는 확인했지만 다음 설명 버전에는 절대 링크를 사용할 것. 이 README는 초기 정책 비교만 다루므로 진행 중으로 적힌12-update 상태를 최종 학습 결과로 대신 읽지 않는다.
- [native3:258](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v3.py:258): 안전 임계값은60Hz 제어 끝의 actual qdot 표본이다. OFF의 종료는 물리 불안정의 실재 증거이며 상태를 안전하게 유지했다는 인증이 아니다. 최종 PD 목표 bounds/rate 통과는 실제 관절각·속도·몸통 움직임 제한과 다르다. 오디오 합성·audible 연주·완전 pad/dropout 계약·정확 SO(3) 외부 최단 거리 인증도 이번 범위 밖이다.

## 실제 초기 비교

[초기 정책 동등성](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/initial_policy_ON_OFF_equivalence_v1.json:1)을 실제 두 checkpoint와 대조했다. model/RMS16키 전체 `torch.equal`, 양쪽Adam empty·updates/transitions0다. 동일 등록820 CP에서 두 mode ABI의 별도825 CP를 만들었으며 두 CP 파일 자체는 서로 다르다. runner의 actual native t0+random33표본 검사 기록은 action/latent/value/log-prob 최대 오차0이다. native 초기 상태도 양쪽 exact이다.

[초기 비교 분석 소스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/analyze_initial_comparison_v1.py:27)와 [결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/initial_comparison_v1.json:1)를 raw controls/trace로 재계산했다. 두 초기 평가 각각982 control·3928 physics·16.366667초·42 event 정산이며 공동 성공/accepted crossing은0이다.

| 초기 정책 비교 | OFF | ON |
|---|---:|---:|
| 초기 대비 최대 actor-root 이동 | 1.142949m | 0.583618m |
| 초기 대비 최대 SO(3) 회전 | 121.203950° | 96.504222° |
| 위치 envelope 밖 endpoint 비율 | 84.012220% | 84.623218% |
| 최장 연속 밖 표본 구간 | 12.55초 | 12.60초 |
| force API 호출 | 0 | 51,064=13×3,928 |

위치·회전 최대량은 줄었지만 범위 유지와 연주 성공은 실패다. 위치는 기타 actor-root, 회전은 초기 quaternion 대비 shortest-arc다. envelope 외부 거리 proxy·몸통/기타 body 중심이나 실제 연속 구간 인증으로 바꾸어 해석하지 않는다.

actual 초기 route1.073577334m/rest length1.101846972m/slack28.269638mm이며 원본 Chest/L_Thorax11개 guide와13개 route body mapping을 확인했다. 현재 계산 장력과 직전 preintegration 명령 장력이 분리되어 있다. ON의 제어 endpoint 최대 직전 장력29.082695N은 센서 측정이나 전체240Hz extrema가 아니다.

## 실제 학습과 안전 종료/reset

[OFF 학습 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/smoke_off_v1/report.json:1)·[ON 학습 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/smoke_on_v1/report.json:1)와 각 training.jsonl을 대조했다. 양쪽12 update·3072 transitions,12개 각 update마다 실제 optimizer step1이며 `completed/inputs_unchanged=true`다. 학습용 episode는982-tick horizon에서 reset되고 마지막126-tick partial episode를 실제 종료 기록으로 남겼다. 보고서 완료는 학습 실행 완료이며 연주 성공이 아니다.

OFF의 [갱신12 평가](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/smoke_off_v1/evaluations/update_000012/native/episode_0001/report.json:1)는273 control·1092 physics·4.55초에 끝났다. actual trace의 index55=`R_Elbow_y`, q=−0.845332623rad/qdot=99.553558350rad/s와 safety 기록이 일치한다. 직전까지의 기록된 제어 endpoint 최대속도는1.397085rad/s였으므로60Hz 표본 사이의 급격한 native 실패를 기록한 것이다. 곡 완주가 아니며 MP4는 실제 마지막 step1092에서 끝난138프레임이다.

fatal 전이의 남은 horizon은709tick, raw 비용은−970.474450778359다. `−2−2Σ(k=1..709)γ^k−1`을 독립 재계산해 오차0, scaled=raw×0.1을 확인했다. 현재·미래 floor를 중복하거나 누락하지 않았고 실제 끝난 뒤 가짜 프레임/음악 event를 추가하지 않았다. ON의 갱신12 평가는982/3928의 full16.366667초로 끝났지만 음악 성공은0이다.

[실제 reset probe v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/reset_probe_v2/report.json:1)는 OFF12 정책을 deterministic 진단으로300전이 수집했다. zero-based272번에서 실제 terminal→새episode2로 reset했고 나머지27 control/108 physics를 진행했다. 두 episode raw 길이는273/274와27/28 control/trace이며 두 초기 native 상태는 reference와 exact다. model/RMS 불변·최적화 추가0·기존 counters12/3072 유지이므로 이 probe를 추가 PPO 학습으로 집계하지 않는다. GAE의 terminated bootstrap 차단은 사전 검수한 코드 계약과 맞는다.

## 원자료·산출물·보존 대조

초기/갱신1/갱신12의 여섯 평가 controls/trace·frames·영상·raw ledger를 확인했다. 최종 목표 native bound 초과0, rate 오차 최대1.04×10⁻⁷rad로 float roundoff 범위다. 첫 기준은 preload 요청이 아닌 실제 초기 제출 목표/q다. raw 성분 합 오차<5×10⁻¹⁶, scaled/raw 및 report 누적합도 일치했다. OFF force0, ON은 세 평가 모두13×physics step이며 금지 호출0·baseline 가중치 불변이다. 기존 영상12개의 기록 SHA와 실제 파일이 일치한다. full 평가492프레임/16.4초 인코딩과 실제16.366667초를 구분한다.

[초기 산출물](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/README.md:1)의 두 PNG를 실제로 열어 raw 프레임/수치와 대조했다. contact sheet는 overlay 없는 native raw RGB이며 캡션이 원본 픽셀 밖에 있다. 그래프는60Hz outside vector norm/mm,30Hz 초기 대비 SO(3) 회전,60Hz 직전 명령 장력을 구분한다. 비교 MP4는 저장된 영상을 제목 띠와 hstack으로 재인코딩한 산출물이며 새 물리 실행이 아니다. 두 비교 영상 SHA, producer30입력 전후/현재 SHA 일치와 final producer SHA를 확인했다. 세 QA 수정 전 producer/설명/입출력 보존 디렉터리도 존재한다. overlay 선은 계산 경로 표시이며 접촉·관통 검증으로 부르지 않는다.

독립 SHA 재계산에서 두 학습 attempt각1131 입력, 여섯 평가 각1131 입력, reset probe1132 입력 변경·누락0이었다. 초기 분석18입력과 producer30입력도 현재 SHA와 일치한다. 검증은 이 기록된 입력집합과 완료한 smoke/probe 범위이며 root의 프로젝트 전체 보존 감사·동적 phase 봉인은 별도다.

후속 두 mode 장기 학습은 각12-update CP의 exact ABI 복원과 새 물리 episode로 시작하는 예정 단계다. `initial_000000`은 새 실행의 초기 checkpoint label이며 payload가 updates12일 수 있다는 설명이 필요하다. 이 검수는 후속30분 반복 평가·11:40 cutoff 실제 이행·장기 품질을 소급 인증하지 않는다.
