# 병렬 수집 CP316→CP320 cutoff 요약

## 실행 검증과 범위

완료 검증은 passed=true, 14/14 checks, process exit code 0, archive errors 0을 기록했습니다. N4T256으로 네 production update와 4,096 transition을 확인해 CP316에서 CP320(전체 84,992 transitions)까지 진행했습니다. 첫 production collection 1,024 transition은 23.1704초(44.1943 transition/s), 네 update의 평균 combined throughput은 36.5024 transition/s였습니다. 과거 참고값 14.8839는 CP와 data batch가 달라 controlled benchmark가 아니므로 처리량 향상 주장에 사용하지 않습니다.

## native 평가 비교

표의 initial은 CP316, cutoff는 CP320의 각각 별도 단일 환경 결정론 평가입니다. 두 평가 모두 같은 설정의 strap·baseline을 사용했고 전체 물리 구간을 마쳤지만, 병렬 네 환경 동시 화면이 아닙니다.

| 체크포인트 | 상자 밖 시간 | 최대 actor-root 상자 이탈 | 평균 actor-root 상자 이탈 | 초기 기타 orientation 대비 최대 SO(3) | 음악 성공 |
|---|---:|---:|---:|---:|---:|
| CP316 initial | 59.78% | 30.45 cm | 5.82 cm | 93.93° | 0/42 |
| CP320 cutoff | 55.19% | 33.99 cm | 8.49 cm | 91.21° | 0/42 |

각 영상 평가는 16.3667 physics seconds, 3,928 physics step, 982 control step, 492 frame이며 MP4 재생 시간은 16.4초입니다. 각 평가에서 strap은 51,064회 호출됐고 51,064 = 13×3,928이며 금지 API 호출은 0회였습니다. Baseline은 고정됐습니다. 이 지표들은 서로 엇갈렸고 음악 성공은 없으므로 성능 성공으로 판정하지 않습니다. 위치 이탈은 actor-root world 위치의 상자 진단이고, SO(3)는 초기 기타 orientation quaternion 대비 회전 거리입니다.

![CP316 initial과 CP320 cutoff의 전신·손 native 프레임 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/artifacts_v2/cp316_cp320_native_frames_v2.png)

## 보관 영상

영상은 이미 SHA 검증되어 저장된 V1 보관본을 그대로 링크합니다. 이 문서는 기존 영상 또는 매니페스트를 다시 복사하거나 기록하지 않았습니다.

![CP316 initial 전신](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_long_v1/initial_000000/whole_body.mp4)

![CP316 initial 손](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_long_v1/initial_000000/hands.mp4)

![CP320 cutoff 전신](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_long_v1/cutoff_000320/whole_body.mp4)

![CP320 cutoff 손](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_long_v1/cutoff_000320/hands.mp4)

## 실행 종료 및 판정 범위

이번 실행은 11:40 KST wall-clock cutoff를 기록하고 종료했습니다. 이는 설정된 cutoff까지의 유한 생산 prefix입니다. 장기 목표 완료, 재개 성공 또는 음악 성능을 의미하지 않습니다. 이 범위의 native 초기·cutoff 평가는 둘 다 끝났으나, 미래 평가 결과는 포함하지 않습니다.

## 근거와 provenance

- [CP316→CP320 completion 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/completion_verification_v1.json)
- [production 수집·속도 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/production_analysis_v1.json)
- [새 프레임 전용 producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/artifacts_v2/build_cp320_panels_v2.py)
- [입력 및 출력 해시 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/artifacts_v2/provenance_v2.json)


정정: 기존 README.md 원본은 보존합니다. strap 물리 호출은 0회가 아니라 51,064회입니다.
