# 현재 기타 기준 왼팔 보정 v1 결과 검수

**요약 판정: 문제없음.** 보존 범위 누락은 새 분석 경로에서 해소됐으며 결과 수치·정렬·제어·영상에서 Critical 오류는 확인하지 못했다. 실험은 OFF/ON 모두 원본 실패로 끝났으며 기타 안정화·압현·곡 완주 성공을 뜻하지 않는다.

- Critical: 없음.
- Warning: 원 분석의 입력 봉인 누락을 발견했으나 `analysis_verified_audit`로 보완 완료. 아래에 발견 근거와 해소 범위를 남긴다.
- Suggestion: 없음.

구현·기존 raw/analysis·A 문서·v2 자료는 수정하지 않았다. 이 검수 문서만 추가했으며 native trial은 실행하지 않았다.

## 결과와 제어 대조

- [run_fret_current_guitar_arm.py:153](/home/ajou/yigyu/3/stability_adapter_2/run_fret_current_guitar_arm.py:153): 두 run 모두 이전 PLAY 행의 source_done은 모두 false, 마지막 행만 true다. 마지막 control 뒤 정확히4 physics step에서 terminal state를 보존하며 terminal_info는 마지막 source_info와 exact 같다. OFF는12.9166667초/655 actor step, ON은5.6333333초/218 actor step에서 원본 finger_back 실패로 끝난다. ON의 termination_by_finger는 index만 true다.
- [OFF/data/controls.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/OFF/data/controls.json): 기존 fret_fingers_arm_hold_v1과 전체 time·submitted targets·actor action·observation·executed history·source info·done 및 native trace를 대조해 exact 일치했다. OFF/ON의 native 초기 상태와2초 준비 trace, mode metadata를 제외한 준비 control도 exact 같다.
- [ON/data/controls.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/ON/data/controls.json): 모든 finger21 요청은 source 요청의 해당 slot과 exact 같고 목표 속도·native bounds를 대조했다. 다음 observation의 O_history는 직전 executed_history와 exact 같다. trace가 존재하는 control timestamp에서 actual wrist와 현재 기타→world 목표는 같은 시점의 raw state와 일치한다. root/하체 고정도 raw trace에서 확인했다.
- ON의 최대 FK/native 위치 오차2.659e-7m·회전 오차6.264e-7rad는 사전 허용치보다 작다.40/218회 fit은 제한된 평가 횟수에서 수렴하지 않았으나 이는 summary에 노출돼 있고 유한·bounded 명령만 제출됐다. 최적화 수렴이나 실제 추종 성공으로 설명하지 않는다.

## 분석 수치와 시점

- [analyze_fret_current_guitar_arm.py:60](/home/ajou/yigyu/3/stability_adapter_2/analyze_fret_current_guitar_arm.py:60): timestamp뿐 아니라 source_frame_before까지 일치하는218개 pre-integration control을 비교한다.2.0000000~5.6166667초의 독립 재계산 평균 wrist ON−OFF는−14.861428844114894mm로 저장 summary와 일치한다. control observation의 wrist vector norm, arm 기록 및 해당 timestamp native wrist가 정렬됨을 확인했다. 마지막 control 오차와5.6333333초 terminal pose는 서로 다른 시점이다.
- [analyze_fret_current_guitar_arm.py:37](/home/ajou/yigyu/3/stability_adapter_2/analyze_fret_current_guitar_arm.py:37): 기타 최대 root 이동은 실제 trace에서 계산되며 OFF73.190mm·ON267.200mm다. OFF도 ON 종료까지의 같은 관찰 구간 최대가73.190mm였다. 위치box 최대 초과는 OFF15.005mm·ON171.025mm다. 손목 오차 감소를 기타 안정화 개선으로 해석할 수 없다.
- [analysis_verified/summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/analysis_verified/summary.json): 기존 분석과 OFF/ON 수치·matched_goals·검사·제약 설명이 exact 같다. matched_goals JSON 및 생성 PNG7개도 byte exact다. timeline과 native 비교 패널을 열어 실제 raw 시각·표시·축 범위를 확인했다. 곡 목표가 변하는 곡선과 같은 goal/time 비교의 구분, 서로 다른 전체 episode 길이의 한계가 명시돼 있다.

## raw 영상과 보존

전신·손 raw PNG 전체 SHA, MP4 SHA 및 독립 ffprobe 결과를 대조했다. capture와 trace의 physics step 목록은 exact 같다. OFF는t0~12.9166667초389 frame이며 마지막3100 step은30fps 격자 밖의 추가 최종 frame이다. ON은t0~5.6333333초170 frame이다. MP4 길이는 각각12.966667초/5.666667초로 물리 경과와 구별된다. 두 view는1280×720·30fps이며 source 첫 done까지 영상이 존재한다. 성공 영상이나 전체곡 완주로 표시하지 않는다.

### 발견한 Warning과 해소

[analyze_fret_current_guitar_arm.py:47](/home/ajou/yigyu/3/stability_adapter_2/analyze_fret_current_guitar_arm.py:47)의 원 `input_sha256`는 run raw 일부 및 선택 PNG만 기록한다. 실제 소비한 BASE·기존 baseline controls/trace·producer/helper·420D ABI·font가 누락돼, 같은 파일의 `analysis_inputs_unchanged`만으로 전체 소비 입력의 보존을 판정할 수 없었다. [EXPERIMENT_WORKFLOW.md:100](/home/ajou/yigyu/3/stability_adapter_2/EXPERIMENT_WORKFLOW.md:100)의 “직접 읽는 원자료뿐 아니라 재사용 helper와 … inventory도 실행 시작 전에 입력 SHA 목록에 포함한다”는 지침에 맞게, 원 자료를 보존하고 새 경로에서 입력 전후 SHA와 producer 원문을 봉인하는 보완을 권고했다.

[fret_arm_analysis_preserved.py:22](/home/ajou/yigyu/3/stability_adapter_2/fret_arm_analysis_preserved.py:22)의 새 wrapper는 analyzer import 전에 A 소스·raw JSON/PNG·BASE·baseline controls/trace·ABI·font를 봉인한다. [analysis_verified_audit/inputs_before.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_current_guitar_arm_v1/analysis_verified_audit/inputs_before.json)에1899개 입력이 기록됐으며 after·현재 SHA와 source snapshot이 일치한다. verified analyzer는 원 계산에서 출력 경로만 인자로 변경했고 수치·이미지 결과가 exact 같다. 따라서 새 분석 실행의 보존 공백은 해소됐다. 새 봉인이 과거 원 analyzer의 미기록 소비 SHA를 소급 증명한다는 뜻은 아니다.

이 검수는 `analysis_verified`를 최종 분석 근거로 사용한다. 원 analysis와 native 실패 기록은 그대로 보존한다.

후속 진행 기록 갱신으로 현재 A/PLAN.md·A/README.md 작업본은 감사 당시 소비본과 달라졌다. 위1899개 전후 동일성 판정은 분석 실행 시점의 판정이며, 당시 두 문서 원문은 source_before에 보존돼 있다. 이후 작업본 갱신을 과거 소비 소스가 변경된 것으로 합치거나, 현재 작업본 전체가 당시1899개 SHA와 동일하다고 설명하지 않는다.

## 결과 문서 검수

수정된 README/FILE_INDEX의 정책·제어 용어와 원자료 인용을 확인했다. checkpoint 가중치 고정과 계속 동작하는 finger21 정책, OFF의 준비 마지막 PD 목표 유지, 초기 ±0.3rad 목표 envelope·0.8rad/s 목표 변화율,40개 미수렴 control과 평가 예산20회, overlay가 없는 native 나란히 비교가 정확하게 구분됐다. 색인의 verified analyzer·입력 보존 wrapper·COLOR-only 녹화기 및 실제 줄 번호도 확인했다.

interpretation.json의 같은 goal/time/finger258개 표식 거리 차이를 독립 계산해−19.358995000289166mm를 확인했다. 같은0~5.6333333초 구간의 OFF/ON 최대 이동·회전도 raw trace와 일치했다. terminal의 physical_press_rate·stable_press_success_rate는 두 조건 모두0이며 문서는 이를 종료 지표로 설명한다. 성공이나 압력·접촉 증명으로 과장하지 않는다. 실제 파일 링크를 확인했고, root 최종 봉인 산출물은 작성 예정으로 명시돼 있다.
