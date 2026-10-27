# 손목 Z축 비교 독립 검수

## 1차 — 실행 전 변경 범위 검수

요약 판정: **문제없음 — 사전 검수 PASS**. 실제 물리·저장 분석·산출물의 최종 PASS는 아직 판정하지 않았다. Native·analyzer·collection·plot·audit는 검수자가 실행하지 않았다.

- Critical: 없음.
- Warning: 없음.
- Suggestion: 없음.

확인 근거:

- [runner:28](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_wrist_z_support.py:28): 봉인된 Y runner와 비교하여 pulse joint만 `L_Wrist_z`로 바꾸고 ±.005rad/2~2.5초 ramp를 유지한다. 다른 차이는 설명 문자열뿐이다. [106줄](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_wrist_z_support.py:106)의 원 baseline 목표 확인과 other80 대조, fresh gate·동일 초기화 1200step/151frame 구조를 유지한다.
- [phase:32](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_wrist_z_support_phase.py:32): 변경은 새 Z 소스·계획·출력 경로와 모듈/MPLCONFIGDIR이다. 조건별 단일 subprocess, 입력 SHA·원문 사본·닫힌 로그 보존을 유지하며 자동 retry는 없다.
- [preflight_commands.json:2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/preflight_commands.json:2): root의 독립 명령 기록에서 두 조건 모두 첫484개 전체81목표/other80/모든손가락/native목표한계 통과, 첫 분기485를 확인했다. Z 목표 범위는 plus [−.4212333858013153, −.4162333905696869], minus [−.4262333810329437, −.4212333858013153]rad다.
- [analyzer:89](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_wrist_z_support.py:89): Y 대비 변경은 Z joint/field와 새 경로·계획뿐이다. 공통20초기필드/other80/첫484목표·첫2초state/trace·fresh15gate·원자료/영상 SHA 확인과 기존42검사 구조를 유지한다. [몸통 분석:9](/home/ajou/yigyu/3/stability_adapter_2/analyze_quiet_wrist_z_body_motion.py:9)는 결과 경로만 바뀌며 실제 몸통각과 held 목표를 구분한다.
- [후처리:118](/home/ajou/yigyu/3/stability_adapter_2/run_quiet_wrist_z_postprocess.py:118), [collector:23](/home/ajou/yigyu/3/stability_adapter_2/collect_quiet_wrist_z_videos.py:23): 입력·사본·invocation·닫힌 로그 SHA 보존 구조를 유지한다. 기존162개 → 새4개/총166개, VIDEO_INDEX_v16 및 update_v15 경로·제목·count가 일치한다.

새6개 Python 파일의 AST3.8 검사는 모두 PASS다. 비교한 이전 Y 6개 소스는 이전 봉인 artifact_inventory의 SHA와 모두 일치한다. 사전 검수 SHA256:

| 소스 | SHA256 |
|---|---|
| run_quiet_wrist_z_support.py | cf49d5c8b708d16ebfc25202fc812e9cd0bc538ee92848c7bd08821ecaaaf261 |
| run_quiet_wrist_z_support_phase.py | 4e22c5ef75f74fa3f536ff4ba7dc7f556df4cb09e701dfee2d2fa8b43a41e8c6 |
| analyze_quiet_wrist_z_support.py | 74a85a43ff0914bd32d77827f4acc5fd69adb1704a3669a2ca7ad1cf6bf1d114 |
| analyze_quiet_wrist_z_body_motion.py | 47f9c9265f434bca17ff3ce1193a54543713b17c7c4deed8c8c920c746f4f123 |
| run_quiet_wrist_z_postprocess.py | e5e63759fc36b7584022f0939be5ce90103b4ddda6239a705eca420ed9508c17 |
| collect_quiet_wrist_z_videos.py | 6062dd13807d5ac88803c1f9f5ddce54b2465341c21380591c8d8fe66999c273 |

## 2차 — 그림 및 Y/Z 응답 비교 실행 전 검수

요약 판정: **문제없음 — 추가 사전 검수 PASS**. 이 판정은 실제 생성된 그림·comparison.json의 최종 검수가 아니다. 검수자는 producer·wrapper·비교 계산을 실행하지 않았다.

- Critical: 없음.
- Warning: 없음.
- Suggestion: 없음.

확인 근거:

- [그림 producer:63](/home/ajou/yigyu/3/stability_adapter_2/make_quiet_wrist_z_artifacts.py:63): 42개 PASS 분석과 두1200step 조건을 요구하며 Z actual/target field·새 경로·축제목이 분석과 일치한다. Y 대비 사용하지 않는 quaternion validation을 제거했으나 그림은 world 위치·이미 계산된 회전오차를 사용한다. [wrapper:112](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/artifacts/run_producer.sh:112)는 소스·leaf·입력·닫힌 native log를 사전 SHA/사본/invocation으로 보존하고 새 산출물 덮어쓰기를 거부한다.
- [Y/Z 비교:30](/home/ajou/yigyu/3/stability_adapter_2/compare_quiet_wrist_yz.py:30): Y analysis/series와 원baseline initial을 Y 봉인 SHA에 대조하며 baseline world pose/time/error exact·두분석 PASS를 확인한다. 직접 읽는8파일과 사전 invocation의 전후 SHA, 실행 소스 사본을 기록한다.
- [Y/Z 비교:37](/home/ajou/yigyu/3/stability_adapter_2/compare_quiet_wrist_yz.py:37): desired world 회전은 log(goal×baseline⁻¹), 회전 예측은 exp(Jrot·delta)×baseline, 예측 회전 잔차는 SO(3) 상대회전의 magnitude로 계산한다. .03m/5°는 행 단위 정규화이며 성공 gate로 쓰지 않는다. ±.005rad bounded LS 결과를 미측정 합성 후보로 명시한다.
- [Y/Z 비교:40](/home/ajou/yigyu/3/stability_adapter_2/compare_quiet_wrist_yz.py:40): rank<2이면 조건수는 null, zero열이면 cosine은 null이다. 비zero rank1의 cosine ±1은 정의된 값으로 남긴다. 퇴화 자체를 실패로 숨기지 않는다. 6×2가 전체6D 제어권을 보장한다고 주장하지 않는다.

두 추가 Python 파일의 AST3.8 검사는 PASS다. 사전 검수 SHA256:

| 소스 | SHA256 |
|---|---|
| make_quiet_wrist_z_artifacts.py | 55642dd6af02082cea0f91bf9f4ded3aa89a9f0499c13520c18cddd15270e809 |
| artifacts/run_producer.sh | ce1faf98d22e554dc7b9499c1270fbba7dcafc9504d623dbe0df49f7381b32cc |
| compare_quiet_wrist_yz.py | 700d5d879f4796e7215cb946089b421efe69a0041d57735c0f96ff3cdf55397a |

## 3차 — 비교 v1 실패 정정 및 v2 사전 검수

요약 판정: **v1 참조 오류는 수정 필요였으며 v2에서 정정됨 — v2 사전 검수 PASS**. 2차 검수는 inventory 실제 key 존재 확인을 놓쳤다. 위의 v1 사전 PASS는 baseline 참조에 대해서는 잘못된 판정이며 이 기록으로 정정한다.

- [v1 비교:30](/home/ajou/yigyu/3/stability_adapter_2/compare_quiet_wrist_yz.py:30)의 원baseline 파일은 Y inventory에 없어 KeyError로 종료했다. [실패 기록:2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/comparison_failure.json:2)의 exit1·입력8개 전후 SHA·원소스700d…/사본/invocation을 보존했고 comparison.json은 생성되지 않았다. 물리·분석 재실행 없이 별도v2 경로로 정정한다.
- [v2 비교:30](/home/ajou/yigyu/3/stability_adapter_2/compare_quiet_wrist_yz_v2.py:30)는 Yanalysis/series를 Yinventory, 원baselineinitial을 baseline 자체 inventory에 대조한다. 세 entry의 실제 존재와 현재 SHA exact를 독립 확인했다. 새입력은 원baseline inventory·v2leaf·실패기록이며 새v2 source/invocation/output 경로를 사용한다. 수학·단위·물리조건 변경은 없다.
- v2 AST3.8 PASS, SHA256 `f72c6b31274ccb0a2dd25ea3bdf2c0ed6d588eabc1edbaddd6aebcd32d75e8b6` exact. 현재 v2의 Critical/Warning/Suggestion 없음.

## 4차 — 완료된 실제/저장분석/수집/그림 단계 검수

요약 판정: **문제없음 — 완료된 단계 검수 PASS**. 최종 문서와 Y/Z 비교v2 결과는 아직 이 판정에 포함하지 않는다. 검수자는 해당 실행을 재실행하지 않고 저장결과·SHA·실제 PNG를 읽었다.

- [plus report:2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/plus/report.json:2)와 [minus report:2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/native/minus/report.json:2): 각각 ONE 초기화·1200step·151frame·위반0·fresh15gate 및 report checks 전체PASS다. 두103입력 전후/current SHA와 닫힌 log SHA를 확인했다.
- [analysis:2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/analysis.json:2)의42검사와 [body_motion:2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/body_motion.json:2)의7검사가 PASS다. 두 native 분기는485이며 종료위치 baseline/plus/minus는13.819696/13.817638/13.829543mm, 회전은2.918277/2.895722/2.946758°다. 목표한계와 실제 최대한계초과 .000099949539rad, 몸통 held 목표와 실제최대변화 약.06176rad를 구분한다.
- Analysis1958입력/1957사본, collection173입력/172사본, artifact1959입력/14사본의 전후/current SHA·사본·닫힌 log를 확인했다. 각 exit0이다. [영상 update:214](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/video_collection_update_v15.json:214)의 기존162개 SHA와 새4개 복사 SHA·총166개·v16색인 SHA가 일치한다.
- [실제4panel PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/artifacts/quiet_wrist_z_support_response.png)를 열어 축·단위·범례·캡션과 곡선의 원자료 정합을 확인했다. 제목/손목축은 Z이며 범례·캡션이 표본을 가리지 않는다. 목표/actual 구분과 재사용baseline 설명이 읽힌다.
- Critical: 없음. Warning: 없음. Suggestion: 없음.

## 5차 — Y/Z 비교v2 완료, 후속feedback 계획, 미소비 감사코드

요약 판정: **비교v2와 후속계획은 문제없음 / 감사코드는 한 항목 수정 권장**. 최종 문서의 전체 PASS는 아직 판정하지 않았다.

- Critical: 없음.
- Warning: [root_final_audit_producer.py:56](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/root_final_audit_producer.py:56)의 최종 sources 목록은 이전Y `make_quiet_wrist_artifacts.py`를 포함하고 현재Z producer를 빠뜨렸다. 현재Z 원문은 artifact_source에 보존되어 있으나 source_final/current-source inventory 목록도 이번phase와 맞도록 미소비 감사코드의 해당 항목을 `make_quiet_wrist_z_artifacts.py`로 정정할 것을 권장한다.
- Suggestion: 없음.

확인 근거:

- [comparison_v2:2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/comparison_v2.json:2)의6checks/12입력 전후/current SHA exact를 확인했다. [82줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/comparison_v2.json:82)의 rank2·cos−.7281272961564396·조건수2.719646212433991, δ=[−.005,+.005]·예측13.635786789mm/2.882135324°는 미측정 동시입력의 저장 모델 계산이며 실제native 결과로 설명하지 않는다.
- [feedback 계획:7](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_YZ_FEEDBACK_PLAN.md:7): world p오차/world log회전오차, S 정규화, A=S⁻¹J와 g=Aᵀb의 차원·부호가 정합하다. A/g 단위rad⁻¹·kappa rad²/s이므로 rate는rad/s, 60Hz 적분은rad다. delta 자체의 속도/각도 제한 후 기존 최종목표 compose를 한 번 통과시키며 목표한계를 넘으면 거절한다. 임의 state/pose쓰기나 기타힘을 도입하지 않는다.
- [feedback 계획:15](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_YZ_FEEDBACK_PLAN.md:15): 저장baseline t2의 실제p/q와 확정J에서 숫자만 독립검산해 g_ref=[−.8247321000112535,.4581455826792709], kappa=.00242502989755426, rates=[−.002,.001111016735429649]를 exact 확인했다. 실제ON은 현재오차를 사용한다. 최대2native·OFF/ON각ONE·첫484/다른79/손가락/앞2초 보존 계획과 측정한계가 명시된다. 계획 SHA256 `302081ab9ecee19908839ebd07e13ec720d0073767b297e363a3c6a852dddbb9` exact.
- 감사코드 SHA256 `d349c2f9fbbacc09b475e459875047f0da00f193a4869122390cb759673c686d`·AST3.8 PASS다. v1실패원문/사전invocation/입력·v2엄격결과6검사·몸통7검사·두ONE actual·이전Y 보존목록 포함과 최종review후 봉인 순서가 정합하다. 감사코드는 검수자가 실행하지 않았다.

## 6차 — 최종 문서 및 정정 완료 확인

최종 판정: PASS

요약 판정: **문제없음**. 이번 Z 비교의 변경코드·두 실제완료기록·저장분석42/몸통7·Y/Z비교v2 6검사·영상166개·그림·최종문서의 독립 검수를 완료했다. 최종 보존감사 실행과 봉인은 이 검수 후 root가 수행하며, 검수자는 native/분석/수집/그림/감사를 실행하지 않았다.

- Critical: 없음.
- Warning: 없음 — 5차의 감사 source 목록은 [감사코드:56](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/root_final_audit_producer.py:56)에서 현재Z producer로 정정됐다. 새 감사코드 AST3.8 PASS/SHA256 `1d5501bcc55789e82ae947596e6fec110e66ac9d24a36eeddaa5907d72bb1d27`를 확인했다.
- Suggestion: 없음.

최종 근거:

- [결과 README:63](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/README.md:63)와 [누적 보고서:2140](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2140)의 v1 실패 보존 표현을 실제와 맞게 실행소스 사본·사전invocation/입력 전후 SHA·failure 기록으로 정정했다. v1원문/실패와 엄격참조 v2 완료를 구분하며 원comparison.json 부재·물리재실행0도 정확하다.
- 최종 한국어 문서는 약2µm의 작은 위치차이를 과장하지 않으며 실제 두5초/모델예측/미구현·미실행feedback을 구분한다. 공통2초는 진단용이며 전체66권한을 유지하고 자연연주/정책호환/폐루프안정성을 인증하지 않는다. 몸통held 목표와 실제관절변화, 목표한계와 actual 초과, rawlambda와 힘/forceclosure, straproute와 천mesh를 구분한다.
- [파일색인:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/CHANGED_FILES.md:1)과 결과 README의 총66개 절대경로 링크·실제줄이 유효하다. 이전 검수의 실제4panel PNG·소스/입력/닫힌log SHA·영상복사검증을 재사용했다.
- [메인 README:1301](/home/ajou/yigyu/3/stability_adapter_2/README.md:1301), [PLAN:2122](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:2122), [누적 보고서 §120:2124](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2124)의 추가 내용이 완료기록/미실행계획과 일치하며 세문서 모두 journal_before의 원prefix SHA를 보존한다.

최종 문서 SHA256:

| 파일 | SHA256 |
|---|---|
| 결과 README.md | 7008f7787dd05246fc408a16ffafe8c812030ffa0d1183ebbaee69218e9b7728 |
| CHANGED_FILES.md | 1e8b9501d0123fffac8be56dafea67dc33d3b7d6f719b74a54ce0461314b3c0d |
| VISUAL_REPORT.md | 10d36a9e747bab10011b87c23cef98884a148693bb4efa3ea7d43a876d2d31b8 |

이 기록 이후 review.md는 root의 최종 봉인을 위해 고정한다.
