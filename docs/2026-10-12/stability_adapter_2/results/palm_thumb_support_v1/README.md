# Palm/thumb support 실험 결과

## 결론

선택된 source 형상 후보(`0p025`)를 적용했을 때 접촉 동시 raw solver 응답은 baseline보다 증가했다. 접촉점 추종을 켠 `candidate_on`은 동시 양수 비율이 73.6667%로 가장 높았지만, 최대 root 변위는 96.2238 mm, 최대 회전은 16.2361°였고 위치 상자 밖 표본은 144/151개였다. 초기 지지 접촉 응답이 늘어난 사실은 확인했으나, 안정화나 자연스러운 연주 자세가 성공했다고 볼 수 없다. Fret gate는 네 조건 모두 통과하지 못했다.

## 실험 설정과 조건

무스트랩, free guitar, 고정 root와 하체, self-collision 조건에서 몸통 PD 목표를 유지했다. 초기 변경 탐색 폭은 0.025, 0.1, 0.3 rad였다. 왼팔은 12개 관절 각각을 해당 폭만큼 탐색했고, 엄지 5개 관절은 동일 폭을 사용했다. 나머지 16개 손가락 관절은 `±min(width, 0.18 rad)` 범위와 각 관절의 native limit 교집합을 사용했다. 선택 후보의 최대 변화는 0.019987315 rad(약 1.145°)다. 이는 “초기 왼팔 각도 12 rad”를 뜻하지 않는다.

| 조건 | 정의 |
|---|---|
| `baseline_v4` | source 변경 전의 기준 조건 |
| `candidate_off` | 선택 source 후보를 적용하되 접촉점 제어 OFF; 초기 자세 변경 효과를 분리 |
| `candidate_on` | `candidate_off`와 같은 초기 source 자세에서 기존 왼팔 PI를 접촉점 추종 제어로 대체 |
| `posture_on_retry` | 단일 17관절 PI 재시도. 팔 목표는 초기 actual 오차 + `0.25 × task q error`, 엄지 목표는 `0.25 × task q error`; arm rate 0.8 rad/s, thumb rate 0.3 rad/s |

원래 선택 목표는 source frame G에서 palm 아래쪽(+X_G)과 엄지 뒤쪽(-Z_G)에 해당하는 면이다. 이 탐색은 source 기하의 closest surface를 이용한 진단이며, 정확히 cooked된 면의 일치, PhysX에서의 해당 면 접촉, 마찰이나 힘의 검증이 아니다. source surface gap도 정적 source 형상 거리일 뿐 실제 물리 접촉을 증명하지 않는다.

각 정식 실행은 native 물리 1200 step(240 Hz, 5초), 30 Hz 저장 151 frame(t=0 포함, MP4 길이 5.03333초), 60 Hz 제어 직전 contact 조회 300회로 구성된다. 최대 변위·회전은 30 Hz pose 표본의 최댓값이다. 동시 양수 비율은 300회의 조회에서 palm과 thumb 양쪽의 raw lambda가 동시에 양수였던 비율이다. raw lambda는 solver 응답이며 뉴턴 단위 힘이 아니고, 이를 힘·마찰·미끄럼 성공으로 환산하거나 해석하지 않는다. 위치 초과는 역사적 actor-root world 위치 상자 기준이며 pelvis 상대 전신 자세 범위가 아니다. 회전은 초기 quaternion으로부터의 최단 회전각이며 자연스러운 포즈 집합 검사도 아니다.

## 네 조건 결과

| 조건 | 최대 root 변위 (mm) | 최대 회전 (°) | 동시 양수 응답 (300회) | 위치 상자 초과 최대 (mm) | 상자 밖 frame |
|---|---:|---:|---:|---:|---:|
| `baseline_v4` | 62.9606 | 13.6314 | 0/300 (0%) | 1.1656 | 6/151 |
| `candidate_off` | 62.7971 | 13.7047 | 66/300 (22%) | 1.2528 | 6/151 |
| `candidate_on` | 96.2238 | 16.2361 | 221/300 (73.6667%) | 31.3373 | 144/151 |
| `posture_on_retry` | 63.3030 | 13.7575 | 133/300 (44.3333%) | 2.0761 | 8/151 |

source surface gap은 `baseline_v4`에서 `candidate_off`/`candidate_on`/`posture_on_retry`로 갈 때 palm 0.326351 mm에서 0.053756 mm로, 엄지 0.023697 mm에서 0.004402 mm로 줄었다. 이것은 source 형상 간 거리 변화다. 정식 네 실행은 inputs audit에서 소비 입력 불변, 각 실행 1200 step, 60 Hz contact 표본, native 검사 통과, 151 frame이 확인됐다. `fret_gate_passed`는 false다.

## 분석 그림과 대표 프레임

`analysis_final/timeline.png`는 네 조건의 native 측정 추이를 비교한다. 아래 프레임은 실제 native 실행 렌더에서 각각 t=0, 2, 5초에 저장한 hands 및 전신 시점이다. 이 그림은 source 기하 스케치가 아니라 native 실행 영상의 대표 프레임이다.

![네 조건 native 측정 timeline](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/analysis_final/timeline.png)

![손 native 프레임 t=0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/analysis_final/hands_t0.png)

![손 native 프레임 t=2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/analysis_final/hands_t2.png)

![손 native 프레임 t=5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/analysis_final/hands_t5.png)

![전신 native 프레임 t=0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/analysis_final/whole_body_t0.png)

![전신 native 프레임 t=2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/analysis_final/whole_body_t2.png)

![전신 native 프레임 t=5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/analysis_final/whole_body_t5.png)

## 네 조건 전체 실행 영상

각 조건의 hands와 whole-body 영상은 `data/images/` 아래 있다. MP4는 t=0 포함 151 frame으로 저장되어 길이가 5.03333초다.

### baseline_v4

![baseline_v4 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/baseline_v4/data/images/hands.mp4)

![baseline_v4 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/baseline_v4/data/images/whole_body.mp4)

### candidate_off

![candidate_off 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/candidate_off/data/images/hands.mp4)

![candidate_off 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/candidate_off/data/images/whole_body.mp4)

### candidate_on

![candidate_on 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/candidate_on/data/images/hands.mp4)

![candidate_on 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/candidate_on/data/images/whole_body.mp4)

### posture_on_retry

![posture_on_retry 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/posture_on_retry/data/images/hands.mp4)

![posture_on_retry 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/posture_on_retry/data/images/whole_body.mp4)

## 실행 이력과 보존 범위

총 8회의 native 시도가 있었다. 3회(`baseline`, `baseline_v2`, `posture_on`)는 카메라 단계 SIGSEGV로 부분 영상만 남았다. `posture_on` 부분 영상은 각 시점 82 frame이며 마지막 캡처는 2.7초다. journal의 완료 시각 2.716667초는 별도 기록값이다. 5회는 물리 실행을 완주했으며, 그중 `baseline_v3`는 실행 중 분석기가 수정되어 입력 SHA가 오염됐으므로 공식 비교에서 제외했다. 나머지 네 정식 실행은 위 표와 `analysis_final/summary.json`에 기록되어 있다. source 기하 탐색은 두 번 실행했고 각각 세 후보(총 여섯 후보)를 비교했다. 해당 탐색의 새 native 환경 생성·physics step은 0이다. baseline 및 baseline_v2 부분 영상은 `partial_videos/`, posture_on 부분 영상은 `partial_posture_videos/`에 보존했다. 기존 `partial_videos/manifest.json`의 `input_hashes`는 baseline_v2 프레임 범위에 대한 기록이므로 이를 posture_on 영상이나 모든 부분 영상의 포괄 SHA 검증으로 해석하지 않는다.

### posture_on 중단 부분 영상

카메라 단계 SIGSEGV로 중단된 `posture_on`의 부분 캡처다. 각 영상은 82 frame이며 마지막 캡처 시점은 2.7초다. 실행 journal의 완료 시각 2.716667초와는 구분한다.

![posture_on 손 부분 영상, 82 frame, 마지막 캡처 2.7초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/partial_posture_videos/posture_on_hands_PARTIAL.mp4)

![posture_on 전신 부분 영상, 82 frame, 마지막 캡처 2.7초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/partial_posture_videos/posture_on_whole_body_PARTIAL.mp4)

`source_before`는 해당 실행 전 보존한 입력 snapshot이고 `source_final`은 실행 후 최종 보존본을 가리킨다. 둘의 시점과 용도를 혼동하지 않는다. posture 분석기 v1/v2는 미실행 초안으로 보존하고, 접촉추종 분석기 v1과 그 세 조건 실행 결과도 보존한다. 최종 네 조건 비교는 posture 분석기 v3의 `analysis_final`이다. 이 README는 정식 결과만 요약하며 review나 보존 봉인 기록을 대신하지 않는다.

## 주요 원자료

- [analysis_final/summary.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/analysis_final/summary.json): 네 정식 실행의 수치, native 검사, Fret gate 및 해석 범위.
- [analysis_final/inputs_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/analysis_final/inputs_after.json): 정식 입력 및 완료 실행 audit.
- 각 조건 디렉터리: 입력 snapshot, 실행 로그, native 데이터 및 hands/whole-body 영상.
- [partial_videos/manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/partial_videos/manifest.json): 카메라 단계에서 중단된 실행의 부분 영상 목록.

## 검증·검수·변경 색인

- [final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/final_verification.json): 최종 수치·입력·산출물 검증 결과.
- [review_final.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/review_final.md): 독립 최종 검수 기록.
- [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/CHANGED_FILES.md): 변경 파일 색인.
