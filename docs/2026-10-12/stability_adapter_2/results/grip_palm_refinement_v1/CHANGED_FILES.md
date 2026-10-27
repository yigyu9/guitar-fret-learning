# 파일 인덱스 — grip_palm_refinement_v1 산출물

## 이번 산출물

- [저장자료 plot producer와 입력 목록](/home/ajou/yigyu/3/stability_adapter_2/make_grip_palm_refinement_artifacts.py:50), [preseal·검사](/home/ajou/yigyu/3/stability_adapter_2/make_grip_palm_refinement_artifacts.py:72), [151-frame camera coverage](/home/ajou/yigyu/3/stability_adapter_2/make_grip_palm_refinement_artifacts.py:116), [post-read rehash·manifest](/home/ajou/yigyu/3/stability_adapter_2/make_grip_palm_refinement_artifacts.py:161)
- [결과 안내와 수치표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/README.md)
- [5초 기타 오차 곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/artifacts_v4/grip_palm_refinement_curves.png)
- [t=0/t=5초 손 카메라 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/artifacts_v4/grip_palm_refinement_hands_camera.png)
- [canonical v4 input/output SHA manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/artifacts_v4/artifact_manifest.json)
- [canonical v4 실행 명령·환경·exit 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/artifact_execution_v4.json) 및 [console log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/artifact_execution_v4.log)

## 원자료 및 이전 참고자료

- [검증 분석 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/analysis.json), [artifact brief](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/artifact_brief.json)
- 새 실행 `w1_a0p5`: [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/native/w1_a0p5/initial_values.json), [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/native/w1_a0p5/report.json), [camera capture metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/native/w1_a0p5/capture.json)
- 새 실행 `w1_a0p25`: [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/native/w1_a0p25/initial_values.json), [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/native/w1_a0p25/report.json), [camera capture metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/grip_palm_refinement_v1/native/w1_a0p25/capture.json)
- 이전 실행인 기준 seed 2: [initial values](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/native/seed_2/initial_values.json), [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/native/seed_2/report.json), [camera capture metadata](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/native/seed_2/capture.json)
- [실험 계획](/home/ajou/yigyu/3/stability_adapter_2/SEED2_STRAP_INITIAL_PLAN.md)

이번 산출물 생성 작업은 저장 분석과 이미 녹화된 PNG의 후처리이며 추가 native 실행은 없었다. 물리 실험 단계에서는 새2init/2400step을 수행했다. 이전 출력/producer 버전은 `artifacts_attempt_v1`(기본 글꼴 한글 누락), `artifacts_v2`(NanumGothic 적용), `artifacts_v3`(시트 간격 조정)로 보존했고, canonical 출력은 `artifacts_v4`다. v1–v4의 보존 producer 사본은 각 manifest의 producer SHA와 일치한다; v1–v3는 이전 초안 경로로 보존했다.
