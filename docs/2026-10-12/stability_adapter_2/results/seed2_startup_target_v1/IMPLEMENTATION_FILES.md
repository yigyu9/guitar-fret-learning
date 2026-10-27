# 구현·계획 실제 줄 인덱스

같은 seed2 초기각·기타 상태·절대LA·PD에서 왼팔12 startup bias만0/.5/1로 비교했다. 기존 frozen source/raw는 보존하고 다음 파일을 추가했다.

| 파일 | 실제 줄 | 역할 |
|---|---:|---|
| [prepare_seed2_startup_trials.py](/home/ajou/yigyu/3/stability_adapter_2/prepare_seed2_startup_trials.py:17) | 17 | 저장입력 봉인·왼팔12만 바꾼3trial 생성, native0 |
| [run_seed2_startup_target.py](/home/ajou/yigyu/3/stability_adapter_2/run_seed2_startup_target.py:18) | 18 | fresh 초기검사·1200step·두뷰151frame·partial 기록 |
| [69개 유지 목표 검사](/home/ajou/yigyu/3/stability_adapter_2/run_seed2_startup_target.py:57) | 57 | 왼팔12 외 모든 목표를 초기값과 대조 |
| [analyze_seed2_startup_target.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_seed2_startup_target.py:24) | 24 | 저장 raw·실제초기81q·목표/native한계·영상·법칙 검증 |
| [실제 목표 변화 통계](/home/ajou/yigyu/3/stability_adapter_2/analyze_seed2_startup_target.py:73) | 73 | float32 합성/clipping 대조와 target−initial q 계산 |
| [양손 접촉 분리 집계](/home/ajou/yigyu/3/stability_adapter_2/analyze_seed2_startup_target.py:123) | 123 | LH/RH↔ANY 기타 body별 집계, 넥면 분류 아님 |
| [SEED2_STARTUP_TARGET_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/SEED2_STARTUP_TARGET_PLAN.md:1) | 1 | 소비된 비교 leaf계획의 원문 보존 |
| [SEED2_GUITAR_RESPONSE_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/SEED2_GUITAR_RESPONSE_PLAN.md:10) | 10 | 다음 제어권 합성과 작은G응답 probe/heldout 계획, 아직미실행 |
| [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1342) | 1342 | 완료 체크와 다음 방향 |
| [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:711) | 711 | 결과와 현재 조건 |
| [off trial](/home/ajou/yigyu/3/stability_adapter_2/trials/seed2_startup_target_v1/off.json:1) | 1 | 시작bias0 |
| [half trial](/home/ajou/yigyu/3/stability_adapter_2/trials/seed2_startup_target_v1/half.json:1) | 1 | 시작bias0.5 |
| [full trial](/home/ajou/yigyu/3/stability_adapter_2/trials/seed2_startup_target_v1/full.json:1) | 1 | 기존bias1 |

각 초기81q·PD·기타world p/xyzw q·속도·목표scale·SHA는 native/<조건>/initial_values.json에 저장했다. 실제3init/3600step과 저장자료 후처리를 구분한다. 그림producer와 누적문서의 실제 줄 인덱스는 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_startup_target_v1/CHANGED_FILES.md:1)를 따른다.
