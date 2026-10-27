# 엄지 뒷면 접촉의 실제 GPU 진단

2026-10-26. 합의한035/v14 초기 상태, 자유 기타·중력ON·스트랩OFF와 생산 `GpuScene`/`BatchedController`를 유지했다. 전체39행동 채널 중 엄지5축의 요청만 바꾸고 나머지34채널은0으로 두었다. 기존 유한 하체·가슴·오른팔 지지와 발 IK는 계속 동작했다. 물리240Hz·제어60Hz·native 카메라30fps이며 정책 추론·학습은 없다. 상태 주입은 에피소드 경계의 준비 복원뿐이다.

## 실행과 실패를 구분한 결과

| 실행 | 관측 결과 | 판단 |
|---|---|---|
| `native_thumb_hold` | 15초간 thumb3 결과력0N·접촉 후보0%, 마지막 선택점 gap0.209mm | 아주 가까운 표면과 실제 하중을 구분한 기준 |
| `native_thumb_contact` | 양수 gap0.1mm 목표 도달, 15초간 결과력0N·후보0% | 실제 접촉 도달 실패 |
| `native_thumb_contact_zero_gap` | 3.833초 뒤 첫 목표 유지 진입, 첫1.517초·최종1.5초 유지 후보100% | 접촉 후보·해제·재접촉 반응 확인. 원래 동적 선택점 해제 기준은 실패 그대로 보존 |
| `native_thumb_contact_fixed_witness` | 처음 선택점63을 고정해 작은 음수 gap까지 접근했지만 결과력0N·후보0% | 특정 source 샘플의 거리만으로 native 접촉을 보장할 수 없음 |
| `native_thumb_smooth_tape` | 앞 실행에서 반응이 확인된 엄지 목표를3초씩 부드럽게 연결. 첫2초·마지막2초 유지 후보100%, 해제 유지1초는0N·후보0% | 실제 목표 요청만으로 접촉 후보 유지→해제→재접촉 가능함을 확인 |

모든 실행은 원자료와 원래 `report.json`을 보존했다. 정상 실행 완료와 접촉 목표 달성은 각각 별도다. 실패 실행을 최종 성공으로 소급 재분류하지 않았다.

## 최종 명령 테이프의 측정

초기1초 → 접촉 목표 이동3초 → 유지2초 → 해제 목표 이동3초 → 해제 유지1초 → 재접근3초 → 유지2초의 총15초·900제어tick·3,600물리표본이다. 기존 `hand_contact_probe --tape`가 bounded action39만 제출했다. 테이프의 `target` 행은 비교 자료이며 native 상태나 목표를 직접 덮어쓰지 않았다.

| 구간 | 결과 |
|---|---|
| 첫 접촉 유지4–6초 | 후보100%, rear-normal 결과력 평균2.171N, 선택점 마지막 gap0.0282mm |
| 해제 유지9–10초 | 후보0%, 결과력0N |
| 최종 접촉 유지13–15초 | 후보100%, rear-normal 결과력 평균1.698N |
| 연속 후보 구간 | 3.400–6.775초, 12.4958–15.000초의240Hz 표본 |
| 기타 최대 변위/회전 | 초기 대비2.203mm / 0.005882rad(약0.337도) |

해제 직전6초의 선택점42번을 고정해 사후 측정하면 같은 표면점의 gap은0.0282mm에서 해제 유지 끝6.039mm로 증가했다. 반면 전체128점에서 보상에 유리한 점을 다시 고르는 production 선택점은 그동안 바뀌며 해제 끝의 gap이0.438mm였다. **어떤 표면점이 움직였는지와 그 순간 선택된 점의 거리는 서로 다른 측정이다.** 원래 동적 선택점의2mm 해제 기준을 같은 점의 해제로 바꿔 과거 실패를 성공 처리하지 않았다.

최종 사후 측정은 [smooth_tape_measurements.npz](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_hand_contact_v22/support/thumb_native_protocol/smooth_tape_measurements.npz)와 [JSON](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_hand_contact_v22/support/thumb_native_protocol/smooth_tape_measurements.json)에 있다. `time_s`, `thumb_signed_gap`, `thumb_normal_load`, `thumb_contact_candidate`, `thumb_sample_index`, `control_witness_gap`, `control_witness_index`, `stage`를 포함하며 원본 native 기록은 수정하지 않았다.

## 순간 하중과 해석 한계

- 처음 Jacobian 진단의 접촉 진입에는24.85N의 단일240Hz 피크가 있었다. 100ms마다 확인하는2N 조건은 다음 목표 조절을 중단하는 가드이며 물리적인 힘 상한이 아니다.
- 최종 매끄러운 테이프에서도 첫 진입13.32N·재진입18.84N의 순간 하중이 남았다. 5N 초과와10N 초과는 각각 전체2표본·8.33ms다. 유지 하중과 진입 순간 하중을 섞어 설명하지 않는다.
- **최종 테이프에는2N 가드가 없다.** 기존 도구의 기타 변위0.08m·회전0.35rad·관절속도50rad/s 중단 검사와 매 물리tick 유한 지지 검사를 사용했다. 이번 결과는 부하가2N 이하이거나 충격이 없는 접촉을 증명하지 않는다.
- v22 후보는 같은 source 패드점의 영역·방향·gap과 thumb3 native rear-normal 결과력의 조합이다. native 결과력은 몸체쌍별 접촉력·보정된 현 압력·음향 인증이 아니다. source 메시와 PhysX가 실제 사용하는 cooked 충돌 형상의 차이가 있으므로 source 거리만으로 접촉을 판정할 수 없다.
- native Jacobian의 COM→표면점 보정 예측속도와 실제 몸체 속도의 RMS 차이는 초기 유지2.65e−6m/s, zero-gap 진단2.67e−6m/s였다. 이 작은 오차는 좌표·부호·단위 확인이며 접촉쌍 인증이 아니다.

## 이웃 손가락과 영상

실제5.992/9.992/14.992초의106몸체 자세를 물리 적분 없이 source 모델에 옮겨 검사했다. 위치 오차0, 회전 오차 약5.1e−16rad 이하이며 각90개의 서로 다른 손가락 마디 쌍에서 source convex 교차는0이었다. [감사 결과](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_hand_contact_v22/support/thumb_native_protocol/source_overlap_audit.json). 이는 세 시점의 source convex 기하 검사이고, 연속 구간의 cooked 무관통이나 관통 깊이 인증은 아니다.

[실제 native 영상](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_hand_contact_v22/native_thumb_smooth_tape/native_oblique.mp4)은 직접 Isaac Gym 카메라 픽셀이다. 사선 카메라에서는 엄지 일부가 넥과 다른 손가락에 가려진다. 영상만으로 접촉쌍을 특정하지 않으며240Hz 측정과 함께 해석한다. [5초 native 화면](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_hand_contact_v22/support/thumb_native_protocol/native_contact_5s.png).

이번 진단은 한 환경의 도달 가능성과 측정의 구분을 확인했다. 학습한 정책의 엄지 접촉 성능·압현 개선·기타 지지의 인과 효과는 별도 학습·평가로 확인해야 한다. 생산 물리·PD·가동범위·움직임 비용은 이번 진단으로 바꾸지 않았다.
