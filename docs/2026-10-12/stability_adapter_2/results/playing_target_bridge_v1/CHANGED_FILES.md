# 변경 파일과 산출물

| 파일 | 역할 |
|---|---|
| [make_playing_bridge_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_playing_bridge_artifacts.py:1) | sealed saved-data 입력에서 Fret F1 및 여섯 관절 profile 최소 보정폭 그림 생성. |
| [playing_bridge_summary.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/artifacts/playing_bridge_summary.png) | 저장된 Fret full-song `f1_l` 두 값과 실제 PD target/초기 q mismatch grouped bars. |
| [artifact_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/artifacts/artifact_manifest.json:1) · [producer_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/artifacts/producer_execution.json:1) · [producer.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/artifacts/producer.log:1) | source/input 전후 SHA, 출력 SHA, 정확한 producer 명령, exit code 0과 실행 집계. |
| [source_snapshot.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/artifacts/source_snapshot.json:1) 및 `artifacts/source_snapshot/` | producer, checker wrapper, bridge/checker source, leaf plan의 첫 실행 전 원문 복사본과 SHA. |
| [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/README.md:1) | 수치 해석, CPU/native 범위 구분, 이전 실제 이미지·영상 설명과 후속 방향. |

그림의 계약 입력은 변경하지 않았다. 원본 결과 파일인 [contract.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/contract.json:1), [execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/execution.json:1), [execution.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_target_bridge_v1/execution.log:1)와 이전 −2 mm native 캡처는 읽기 참조만 했다.
