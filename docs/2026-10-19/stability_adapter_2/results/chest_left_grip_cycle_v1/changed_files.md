# 변경 파일·실제 줄 번호

이번 진단에 필요한 별도 파일과 main 문서의 결과 추가 부분이다. 기존 실험·자산·stability_adapter/·독립 fresh 학습 파일은 수정하지 않았다.

|파일 절대 경로|진입 줄|
|---|---:|
|[CHEST_LEFT_GRIP_CYCLE_PLAN_V1.md](/home/ajou/yigyu/3/stability_adapter_2/CHEST_LEFT_GRIP_CYCLE_PLAN_V1.md:1)|1|
|[chest_left_grip_cycle_v1.py](/home/ajou/yigyu/3/stability_adapter_2/chest_left_grip_cycle_v1.py:27)|27|
|[run_chest_left_grip_cycle_v1.py](/home/ajou/yigyu/3/stability_adapter_2/run_chest_left_grip_cycle_v1.py:8)|8|
|[analyze_chest_left_grip_cycle_v1.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_chest_left_grip_cycle_v1.py:17)|17|
|[CHEST_LEFT_GRIP_CYCLE_COMPLETION_V1.md](/home/ajou/yigyu/3/stability_adapter_2/CHEST_LEFT_GRIP_CYCLE_COMPLETION_V1.md:1)|1|
|[README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:2446)|2446|
|[PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1358)|1358|

직접 입력은 이 결과 폴더의 config_v1.json이다. 원시 상태/접촉/목표/토크/영상은 native_v1에, 분석은 analysis_v1.json에 보존했다. main 문서의 추가 전 원문은 main_before 및 main_before_results에 있다.

[프로젝트 지침의 문서 연결 규칙](/home/ajou/yigyu/3/stability_adapter_2/AGENTS.md:31)을 추가했다. 설명 정정 후 영상 색인이 과거 요약으로 돌아가는 반복 오류를 방지한다.

같은 지침에 native 쿼터니언 정규화와 파생 자료 전체 표본 대조 규칙도 추가했다. 원본 물리 실행·접촉 판정은 수정하지 않았다.
