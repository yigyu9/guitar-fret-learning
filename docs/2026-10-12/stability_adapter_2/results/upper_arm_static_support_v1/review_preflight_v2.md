# 상완 초기 지지 사전 독립 검수 v2

요약 판정: **문제없음 — 정정된 4조건의 native 사전 준비 범위.** v1의 시간 정규화 Critical은 해결되었으며 추가 미결 Critical은 없습니다. 실제 5초 지지·접촉·안정성은 아직 검증하지 않았습니다.

- [prepare_upper_arm_static_v2.py:15](/home/ajou/yigyu/3/stability_adapter_2/prepare_upper_arm_static_v2.py:15)의 새 config4개는 모두 prep2/horizon5로 관측 분모가3입니다. [runner:54](/home/ajou/yigyu/3/stability_adapter_2/run_upper_arm_static_v1.py:54)는 관측의 PREP/PLAY 태그와 관계없이 전5초 동일 초기 q_ref를 제출하므로 음악 제어를 시작하지 않습니다. 원 검색/config와 [v1 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/review_preflight_v1.md:1)는 보존되었습니다.
- [새 선택:11](/home/ajou/yigyu/3/stability_adapter_2/prepare_upper_arm_static_v2.py:11)은 source 검사 통과 후보 중 실제 예측 gap이2mm 이내인 후보를 고릅니다. [선택 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/configs_v2/selected.json:1)의 지지 후보0°/3°/5° 실제 예측 gap은 각각1.329166/0.503593/0.503503mm로 모두 양수입니다. 요청 라벨 `gap500`과 실제 값을 구분하여 기록했습니다. 기준 후보는 지지 간격 제한의 대상이 아닙니다.
- [runner:39](/home/ajou/yigyu/3/stability_adapter_2/run_upper_arm_static_v1.py:39)의 기타 초기 위치·회전 및 40행의 DOF/기타 초기속도0 검사를 확인했습니다. 이전 미실행 준비본은 [revision 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/preflight_source_revision_v1.json:1)의 snapshot SHA와 일치하고, 현재 runner 변경은 이 초기 검사 추가입니다.
- [source_before_native_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/source_before_native_v2.json:1)의7파일 현재 SHA, 선택 JSON의 기존 입력 SHA 및4config의 후보 SHA를 직접 대조했습니다. 봉인 JSON SHA256은 `e1f74bafa8a3609b54044056355834703dcfb1962d6544b976e676a3964edc83`입니다. 새 준비 소스 SHA는 `e5e93a3f27416bbeb272141bddc1b4d0f59e96f218ab8833c3492ebbf9379376`, 현재 runner SHA는 `11b5417b71850fc585efc7a7d2617842ce2984225797cc92ab8b773b702337c6`입니다.

## Warning

[prepare_upper_arm_static_v2.py:17](/home/ajou/yigyu/3/stability_adapter_2/prepare_upper_arm_static_v2.py:17)의 설명처럼 source 양의 gap은 native cooked 접촉·힘·안정 지지의 증거가 아닙니다. 실제 native contact와 전체/후기 기타 위치·회전을 따로 확인해야 합니다. 현재 선택에서는 v1의2.1213mm 후보가 제외되어 간격 경고가 해소됐으나 요청 gap을 실제 측정값으로 표현하면 안 됩니다.

기존 CPU3 통과와 읽기 전용 코드 검토 범위만 확인했습니다. 실제 native 초기화·5초 물리·영상 결과 및 학습 성공은 이 사전 기록의 인증 대상이 아닙니다. 검수자는 이 새 파일만 작성했으며 기존 파일 수정·추가 물리 실행·학습은 하지 않았습니다.
