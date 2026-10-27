# Timing 학습 시작 후 보존 감사

**통과했습니다.**

현재 양손 stage0 학습이 진행 중인 시점의 읽기 전용 감사입니다. 새 학습의 성공률·완료 여부를 판정하지 않았고, 계속 변하는 transition·resource·status·update 결과는 불변 파일 검사에서 제외했습니다.

| 검사 | SHA 확인 수 | 결과 |
|---|---:|---|
| previous seal manifest anchors | 6 | 일치 |
| previous consumed inputs | 1658 | 일치 |
| previous exact original sources and living documents | 125 | 일치 |
| previous source snapshot copies | 125 | 일치 |
| previous immutable artifact inventory | 348 | 일치 |
| previous archived bytes | 112 | 일치 |
| previous native lifecycle bytes | 12 | 일치 |
| current left run consumed inputs | 1634 | 일치 |
| current right run consumed inputs | 1634 | 일치 |
| current learning and native Python sources | 1477 | 일치 |

서로 다른 파일 2130개를 읽었습니다. 파일 내용은 1MiB 단위로 해시했고, 읽는 동안 변한 감사 대상은 0개입니다.

현재 양손 실행 입력은 각각 1634/1634개, 합집합 1636개이며 충돌은 0개입니다. 기존 준비 상태·모델 XML·선언 mesh 폐쇄 110개가 양쪽 실행에 포함됐고 SHA가 일치했습니다. 과거 baseline 경로는 보관 디렉토리로 향하는 심볼릭 링크이므로 실행 pin과 동일하게 resolve한 실제 경로를 비교했습니다.

## BC 초기화 모델과 입력 관측

| 항목 | 왼손 | 오른손 |
|---|---:|---:|
| 관측 차원 | 536 | 536 |
| 네트워크 규모 | medium | medium |
| 전체 모델 parameter | 2944336 | 2944336 |
| 활성 손 actor 가중치 | 986401 | 979462 |
| 활성 actor 좌표 수(std 활성분 포함) | 986434 | 979468 |
| 공유 value/critic parameter | 978434 | 978434 |
| BC와 현재 initial.pt의 활성 actor/std | 일치 | 일치 |

전체 parameter 수에는 양손 actor·공유 reward/cost value·39개 log_std가 들어가며, partner_initialized의 boolean 두 원소는 제외했습니다. 한 실행에서는 선택한 손 actor와 해당 std 좌표만 정책 학습에 사용하고, 중앙 value/critic은 별도로 학습합니다. optimizer에는 log_std Parameter 전체 39원소가 들어가지만 활성 좌표는 왼손 33개·오른손 6개입니다.

각 BC 모델 SHA는 이전 최종 seal·현재 inputs_before·초기화 진단에서 모두 일치합니다. 새 학습의 initial.pt에 선택된 actor 가중치와 std가 실제로 동일하게 들어간 것도 CPU tensor 비교로 확인했습니다. 시뮬레이터 생성·정책 실행·학습·CUDA 모델 생성은 수행하지 않았습니다.

이번 감사에서 활성 문서나 기존 source·결과·checkpoint를 수정하지 않았습니다. 학습과 모델 평가가 끝난 뒤 최종 source·artifact 검증은 다시 수행해야 합니다.

[상세 감사 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/preservation_preflight_v1.json)
