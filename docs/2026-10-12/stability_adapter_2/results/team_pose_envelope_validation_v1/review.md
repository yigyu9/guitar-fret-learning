# 현재 환경 자세 전이 진단 독립 검수

검수 대상은 새 `validate_team_pose_envelope.py`, 분석 producer, 실행 shell, `TEAM_POSE_ENVELOPE_VALIDATION_PLAN.md`와 이 소단계 원자료·설명이다. 검수자는 코드·계획·물리 설정을 수정하지 않았다. 아래 사전 지적과 그 해소를 보존하며 최종 판정은 **문제없음**이다. 전체 범위나 원 팀원 실험의 재현 성공을 인증하지 않는다.

## 사전 판정

**수정 권장(사후 실제 상태 대조로 해소 가능). Critical 없음.** 재구성 수학, source 교집합 gate, 3조건 범위, 기존 무스트랩 arm PI 재사용과 실행 shell에는 실행을 차단할 문제를 발견하지 않았다. 실행 전후 입력 SHA 보존과 별도 native readback 검증을 조건으로 결과 검수를 진행한다.

- **Warning — [validate_team_pose_envelope.py:100](/home/ajou/yigyu/3/stability_adapter_2/validate_team_pose_envelope.py:100):** `initial_q_matches` 및 다음 줄의 관절 한계 검사가 입력 캐시 `env.initial_q`를 읽는다. 저장된 `actual_initial_state.human_dof_states[].pos`로 후보각·실제 PD 한계를 독립 대조하여 실제 초기 상태 검증을 보완한다.
- **Warning — [validate_team_pose_envelope.py:104](/home/ajou/yigyu/3/stability_adapter_2/validate_team_pose_envelope.py:104):** RFU 실제값 계산이 BASE의 Pelvis p/q를 사용한다. fresh native Pelvis가 BASE와 일치함을 별도로 확인하고, 실제 Pelvis 기준 RFU를 재계산하여 대조한다.

보고 기준 첫 실행이 이 피드백 전달 전에 runner를 소비했다. 입력/소비 source를 변경하거나 이 사유만으로 다시 물리를 실행하지 않고, 세 실행 모두 저장 원자료로 같은 보완 검증을 적용했다.

## 확인 근거

- [재구성:22](/home/ajou/yigyu/3/stability_adapter_2/validate_team_pose_envelope.py:22): Pelvis anatomical basis, 넥 고도, 바디 중심 pivot, proper rotation과 local Y roll 부호가 계획의 새 가정에 부합한다. quaternion 부호 불변성도 기록된 사전 수학 검사 범위에 포함된다.
- [교집합:38](/home/ajou/yigyu/3/stability_adapter_2/validate_team_pose_envelope.py:38), [동적 gate:126](/home/ajou/yigyu/3/stability_adapter_2/validate_team_pose_envelope.py:126): 실제 native body 배치에 source convex 형상을 놓고 의자 box를 포함한다. 양의 공통 내부 반지름이 있는 배치는 동적 진행을 하지 않는다. 공통 반지름을 PhysX cooked 관통 깊이로 주장하지 않는다.
- [제어/상태 기록:127](/home/ajou/yigyu/3/stability_adapter_2/validate_team_pose_envelope.py:127), [controls 저장:157](/home/ajou/yigyu/3/stability_adapter_2/validate_team_pose_envelope.py:157): 기존 arm PI를 사용하며 매 physics step 고정 하체·finite state를 점검하고 raw contact, native sample, 제출 제어를 저장한다. 새로운 policy나 학습이 없다.
- [계획:3](/home/ajou/yigyu/3/stability_adapter_2/TEAM_POSE_ENVELOPE_VALIDATION_PLAN.md:3), [가정:12](/home/ajou/yigyu/3/stability_adapter_2/TEAM_POSE_ENVELOPE_VALIDATION_PLAN.md:12): 원 팀원 초기 입력/회전 convention/체크포인트 run 미확인을 명시하고 현재 환경의 세 배치 진단으로 범위를 제한한다.
- [shell:3](/home/ajou/yigyu/3/stability_adapter_2/run_team_pose_envelope_validation.sh:3): 프로젝트 경로와 고정 rl38 runtime을 사용하며 기존 환경 변수와 인자 `"$@"`를 보존한다. 이 shell도 실행 입력 SHA에 포함된다.
- [preflight_checks.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/preflight_checks.json): 문법 및 5개 재구성 수학 검사 pass 기록을 확인했다.

## 첫 원자료 대조

검수자가 보고 기준 `initial_values.json` 및 `attempt.json`을 독립 대조했다. native 실제 관절각의 후보 대비 최대 절대 오차는 **5.34695474563307e−8 rad**이고, native 초기 Pelvis state는 BASE와 **exact 동일**하다. 이 실행에서는 위 경고가 실제 초기 배치 불일치로 이어지지 않았다. 실제 관절 한계 및 나머지 두 실행의 같은 대조도 아래 결과 검수에서 확인했다.

## 결과 검수

**코드·수치·이미지·최종 설명 판정: 문제없음. 사전 Warning 두 건 해소.** 검수자는 새 physics 실행이나 source 수정 없이 저장 native 원자료를 대조했다. root의 최종 검증과 문서 footer도 확인했으며 artifact inventory의 최종 생성·봉인은 root 담당이다.

- [사후 audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/analysis/native_readback_audit.json)와 [후처리:41](/home/ajou/yigyu/3/stability_adapter_2/analyze_team_pose_validation.py:41): 세 조건의 실제 q가 후보와 최대 5.34695474563307e−8 rad 차이이며 실제 native PD limits 안에 있다. 실제 초기 Pelvis는 BASE와 exact 동일하고 실제 Pelvis 기준 RFU 재계산이 저장 기록과 일치한다. 초기 캐시/BASE 기준 사용 경고가 이번 결과에서 불일치로 이어지지 않았음을 확인했다.
- 각 trace의 step은 정확히 0..1200을 8step 간격으로 포함하는 151표본이며, 시뮬레이션 마지막 시점은 5초다. 접촉 원자료는 각각 step 1..1200을 포함한다. native 초기화 3회/physics 3,600step, 새 policy·학습 0이다. 6개 영상의 SHA와 저장 ffprobe 151frame을 대조했다. t0 포함으로 영상 길이는 5.033333초이며 물리 경과 5초와 구분한다.
- 독립 재계산한 초기 actor-root 대비 최대 이동/최단 회전 차이는 현재 수평 대조 **62.4376mm/15.5396°**, 보고 기준 재구성 **1,381.1780mm/122.9846°**, 보고 중앙 재구성 **1,306.7908mm/154.3569°**다. 이는 저장 30Hz 표본 최대이며 physics step 전체의 최대값 인증이 아니다. [요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/analysis/summary.json) 및 [재계산:54](/home/ajou/yigyu/3/stability_adapter_2/analyze_team_pose_validation.py:54)와 일치한다.
- 보고 기준/중앙의 첫 ground contact는 각각 **0.883333초/0.5875초**이며 해당 최초 raw 쌍은 실제 `guitar/G:body`–`ground`이다. 두 조건의 `human/LH:` 접촉 step은 0/1200, 대조는 1200/1200이다. 이후 raw 목록에 기존 `G:pluck_range`–ground 접촉도 존재하므로 cooked 형상·proxy 한계를 보존하며 lambda를 힘이나 관통 깊이로 해석하지 않는다. 손 접촉 step 수는 연주 성공 또는 충분한 지지력의 인증이 아니다.
- [native 비교 이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/analysis/native_comparison.png)와 [변화 그래프](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/analysis/pose_changes.png)를 검수자가 실제 열람했다. 조건별 0/5초 구분, 원본 재현 아님, 낙하/고정 카메라 crop, actor-root 이동 단위와 최단 회전 차이 표기가 명확하며 캡션/범례 잘림을 발견하지 않았다. 보고 후보의 2초 이후 정지는 바닥에 내려앉은 결과와 함께 해석해야 한다.
- 분석 before/after SHA **952파일**의 동일성과 현존 파일 SHA를 독립 대조했다. 이전 시각화 phase 보호 **27파일**이 그대로이며 source_final의 runner/후처리/shell/세부계획 **4파일**이 현재 소비 원문과 exact 일치한다. frozen runner를 결과 이후 수정하지 않았다.

현재 humanoid 초기각/무스트랩/기존 팔 PI에서 보고 후보를 직접 옮기면 손 지지 없이 낙하한다는 국소 결론은 근거에 부합한다. 원팀 실험 실패, 전체 허용범위 불가, 자연스러움 판정, 연주 성공 또는 최적 자세를 주장할 근거는 없다. 다음 단계는 원 팀 입력 확보 또는 새 기타 배치에 맞는 관절 지지 자세를 별도로 설계하는 범위다.

## 설명 본문·진행 기록 검수

최종 [README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/README.md:1)와 [FILE_INDEX](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/FILE_INDEX.md:1)의 수치, 초기값, 6개 native 영상, 재구성 가정과 해석 한계가 원자료에 부합한다. 두 문서의 절대경로 링크·실제 줄 **45개**를 확인했다. 영상 생성과 문서 후처리의 작업 범위, source/cooked 차이, 기존 visual/articulation 경고, proxy–ground와 lambda 한계를 숨기지 않는다.

PLAN·결과 README·VISUAL_REPORT의 새 진행 구역도 확인했다. before 사본의 기존 PLAN 616줄·결과 README 552줄·VISUAL_REPORT 2276줄 전체가 새 문서의 exact prefix로 보존되었다. 이번 새 append는 현재 세 배치의 결과를 설명하며 원본 연구 계획이나 원팀의 판정을 대체하지 않는다. 현재 허용범위와 최종 연주 목표를 유지한다.

첫 문장은 native 실행과 저장 자료 후처리를 명확히 구분하도록 보완됐고, 표 아래에도 151개 30Hz 표본 최대와 raw 접촉 횟수의 한계를 명시했다. [최종 root 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/team_pose_envelope_validation_v1/final_verification.json:1)은 실제 존재하며 status=pass, 3초기화/3,600step/6영상/보호27파일/새학습0이 확인한 원자료와 일치한다. PLAN:622 완료 기록, 새 파일 색인의 실제 줄, README 및 FILE_INDEX의 검수/최종 검증 footer가 정합하다. inventory는 경로만 안내하며 현시점 생성 완료로 주장하지 않는다.

**최종 검수 완료. 미해결 Critical·Warning 없음.** 코드/물리 재실행을 요구하는 항목은 없으며 이 review의 추가 변경 없이 root가 최종 inventory·봉인을 진행할 수 있다.
