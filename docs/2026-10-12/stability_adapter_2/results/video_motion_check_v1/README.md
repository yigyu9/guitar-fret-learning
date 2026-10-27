# 스트랩 영상에서 정지해 보이는 구간 확인

영상 중간에 환경이 종료된 것은 아니다. 실제 물리 계산은0~5초/1200step을 완료했고, camera는step0,8,…,1200의151프레임을 저장했다. 종료 조건은5초이며 마지막 프레임 뒤 환경을 닫았다.

약2초 이후 기타 pose가 매우 작게 변하는 상태다. 마지막4~5초의 시작점 대비 최대 위치 차이는0.001078251mm(약1.08µm), 회전 차이는0.000200038°였다. 따라서 화면에서 정지한 것처럼 보일 수 있다. 모든 raw 손 프레임 SHA는 서로 달랐다.

| 구간 (초) | 구간 시작점 대비 최대 이동 (mm) | 최대 회전 (°) |
|---|---:|---:|
| 0~1 | 13.854211829 | 2.884285786 |
| 1~2 | 0.323786954 | 0.059505700 |
| 2~3 | 0.001248234 | 0.001119253 |
| 3~4 | 0.001522692 | 0.000233578 |
| 4~5 | 0.001078251 | 0.000200038 |

엄밀한 정적 평형 인증은 아니다. 종료 native 선속도 field는3.851451mm/s, 각속도 field는0.523228°/s이고, 인체 관절의 최대 속도 field는0.053619rad/s다. 이 속도 값이 기록 pose의 미세한 step 변화와 일치하는지는 이번 분석에서 인증하지 않았다. 속도를 시간에 곱해 실제 이동량으로 추정하지 않는다. 힘·토크 잔차, 장시간 유지와 작은 외란에 대한 복원성도 이번에 검사하지 않았다.

또한 종료 기타는 초기 목표에서14.050564mm/2.856298° 떨어져 있고 palm 실제 접촉0인 기존 시험이므로, 거의 정지해 보이는 것을 목표 자세 유지·그립 성공으로 설명하지 않는다. 추가 물리 실행은0이다.

원자료: [states.jsonl](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/native/states.jsonl:1201), [capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/native/capture.json:1), [report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/native/report.json:1).

![분석한 기존 실제 Isaac Gym 스트랩 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/torso_hold_native_collision_v1/native/hands.mp4)
