# 변경 파일과 근거

이번 phase에서 추가한 것은 prepare, runner, probe analyzer, heldout selector, heldout analyzer, 그림 producer, 8개 trial 입력, 두 leaf 계획 및 결과 문서다. 기준·기존 원자료를 수정하지 않았다. 그림 단계는 저장 분석과 이미 저장된 카메라 프레임만 읽는다.

- [그림 producer](/home/ajou/yigyu/3/stability_adapter_2/make_seed2_guitar_response_artifacts.py:85)
- [그림 producer 입력·SHA 목록](/home/ajou/yigyu/3/stability_adapter_2/make_seed2_guitar_response_artifacts.py:66)
- [새 phase 결과 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/README.md:1)
- [기타 위치·회전 곡선 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/artifacts/seed2_guitar_response_curves.png)
- [실제 Gym 손 카메라 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/artifacts/seed2_guitar_response_hands_camera.png)
- [분석 결과 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/artifacts/artifact_manifest.json)
- [실행 명령·환경·출력 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/artifact_execution.json)

실험·분석 경로:

- [6개 단일축 입력 준비](/home/ajou/yigyu/3/stability_adapter_2/prepare_seed2_response_trials.py:17), [입력 정의](/home/ajou/yigyu/3/stability_adapter_2/trials/seed2_guitar_response_v1)
- [7회 native runner](/home/ajou/yigyu/3/stability_adapter_2/run_seed2_guitar_response.py:18)
- [7회 분석기](/home/ajou/yigyu/3/stability_adapter_2/analyze_seed2_guitar_response.py:24)
- [heldout 입력 선택](/home/ajou/yigyu/3/stability_adapter_2/prepare_seed2_response_heldout.py:16), [heldout 입력](/home/ajou/yigyu/3/stability_adapter_2/trials/seed2_guitar_response_v1/heldout.json)
- [heldout 선택 계획](/home/ajou/yigyu/3/stability_adapter_2/SEED2_HELDOUT_SELECTION_PLAN.md:1)
- [heldout 1회 native runner](/home/ajou/yigyu/3/stability_adapter_2/run_seed2_guitar_response.py:18), [heldout 분석기](/home/ajou/yigyu/3/stability_adapter_2/analyze_seed2_response_heldout.py:20)
- [결과 해석과 미실행 다음 계획](/home/ajou/yigyu/3/stability_adapter_2/SEED2_RESPONSE_LOCALITY_PLAN.md:1), [작업 체크리스트](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1374), [프로젝트 단계 인계](/home/ajou/yigyu/3/stability_adapter_2/README.md:732)

새 8개 실행의 원자료는 [phase native 경로](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1/native>)에 보존되어 있다. 이 producer는 native 환경이나 physics를 호출하지 않는다.
