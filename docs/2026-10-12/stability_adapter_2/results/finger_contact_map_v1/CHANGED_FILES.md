# 변경 파일

- 저장 snapshot 4개를 그리는 Python 3.8 producer: [make_finger_contact_map_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_finger_contact_map_artifacts.py:1). G-local body-origin chains와 snapshot별 current positive SDK feature를 표시하며 native/actor/training을 실행하지 않는다.
- 사전 보존된 artifact 실행 wrapper: [run_finger_contact_map_artifacts.sh](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/artifacts/run_finger_contact_map_artifacts.sh:1).
- 네 snapshot의 3D contact guide/chain/data 그림: [finger_contact_map_snapshots.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/artifacts/finger_contact_map_snapshots.png).
- producer/wrapper/helper/plan/input source copy와 pre-run SHA 목록: [source_snapshot.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/artifacts/source_snapshot.json:1), [source_snapshot 디렉터리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/artifacts/source_snapshot).
- artifact input/output 및 zero-call SHA 기록: [artifact_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/artifacts/artifact_manifest.json:1).
- 실행 wrapper command/environment/exit/log SHA: [producer_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/artifacts/producer_execution.json:1), [producer.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/artifacts/producer.log:1).
- 한국어 결과 설명, native 원본 프레임, 좌표·구성 확인 제한: [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/README.md:1).
- feature 분류 및 좌표 변환 확인을 수행한 analyzer: [analyze_finger_contact_map.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_finger_contact_map.py:1), [분석 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/analysis.json:1), [1198 raw SDK feature rows](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/features.jsonl:1).
- superseded substep finding: [configuration_clarification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_contact_map_v1/configuration_clarification.json:1). Source에서 configured substeps 1은 확인했지만 native SimParams runtime readback은 하지 않았다.
- 접촉 영역 guide 설계: [FINGER_CONTACT_MAP_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/FINGER_CONTACT_MAP_PLAN.md:13), 현재 데이터로 관찰한 제한과 다음 미실행 방향: [FINGER_CONTACT_MAP_DECISION.md](/home/ajou/yigyu/3/stability_adapter_2/FINGER_CONTACT_MAP_DECISION.md:1).
- 메인 실험 기록: [stability_adapter_2/README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:1033), [stability_adapter_2/PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1831), [누적 시각 보고서 §104](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1915).

## 확인

- Python 3.8 `py_compile`, 실행 wrapper `bash -n` 통과.
- PNG 생성 전 producer/wrapper와 helper/plan/source 19개를 SHA 확인 후 root-relative snapshot으로 복사했다. Before/after input SHA가 일치한다.
- 네 패널 step 0/32/56/1200 feature 점 개수는 각각 0/2/0/1이며 Step 56에는 점을 표시하지 않았다.
- PNG 실제 열람에서 동일 G-local 축 범위, 다섯 손가락 chain, `*_top` 빈 삼각형, finite reference guides, 외부 legend와 단위를 확인했다.
- Artifact producer의 native/physics/actor/training 호출 수는 모두 0이다.
