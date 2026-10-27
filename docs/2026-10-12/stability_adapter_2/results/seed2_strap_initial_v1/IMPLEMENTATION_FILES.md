# 구현·계획 실제 줄 인덱스

원seed2 초기각을 그대로 두고 절대스트랩 길이만 바꾼 실제3조건을 실행했다. 기존 frozen source와 raw는 보존한다. 이 인덱스는 이번 추가 구현과 갱신된 메인 상태를 가리킨다.

| 파일 | 실제 줄 | 역할 |
|---|---:|---|
| [prepare_seed2_strap_trials.py](/home/ajou/yigyu/3/stability_adapter_2/prepare_seed2_strap_trials.py:17) | 17 | 저장seed2 입력 봉인 및 LA3조건 trial/proposal 생성, native0 |
| [run_seed2_strap_initial.py](/home/ajou/yigyu/3/stability_adapter_2/run_seed2_strap_initial.py:18) | 18 | fresh초기감사·각1200step/두뷰151frame 실행 |
| [run_seed2_strap_initial.py strap metadata](/home/ajou/yigyu/3/stability_adapter_2/run_seed2_strap_initial.py:73) | 73 | 실제법칙계수 저장, 물리변경 없음 |
| [analyze_seed2_strap_initial.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_seed2_strap_initial.py:24) | 24 | 연속 raw·native한계·영상·input closure 검증 |
| [이전상태 기반 장력 재구성](/home/ajou/yigyu/3/stability_adapter_2/analyze_seed2_strap_initial.py:83) | 83 | trace[k−1]법칙scalar와 trace[k]기록 대조 |
| [SEED2_STRAP_INITIAL_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/SEED2_STRAP_INITIAL_PLAN.md:1) | 1 | 소비된3길이 leaf계획, 원문보존 |
| [SEED2_STARTUP_TARGET_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/SEED2_STARTUP_TARGET_PLAN.md:1) | 1 | 다음bias0/.5/1 비교계획, 아직미실행 |
| [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1314) | 1314 | 실제비교·체크리스트·다음진단 결정 |
| [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:691) | 691 | 현재조건과 결과 연결 |
| [current trial](/home/ajou/yigyu/3/stability_adapter_2/trials/seed2_strap_initial_v1/current.json:1) | 1 | 실제입력LA1.1018469719600776m |
| [taut trial](/home/ajou/yigyu/3/stability_adapter_2/trials/seed2_strap_initial_v1/taut.json:1) | 1 | 실제입력LA1.0866096862014567m |
| [preload5n trial](/home/ajou/yigyu/3/stability_adapter_2/trials/seed2_strap_initial_v1/preload5n.json:1) | 1 | 실제입력LA1.0857763528681235m |

각실행의 초기81q·PD·기타world p/xyzw q·속도·입력sha는 native/<조건>/initial_values.json에 저장한다. 그림producer·누적보고서의 줄인덱스는 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/CHANGED_FILES.md:1)로 연결한다. native3init/3600step과 저장자료후처리를 별도로 집계한다.
