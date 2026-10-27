# 준비 자세에서 Strike 전달 진단 — rate와 RH arm gain 비교

같은 prepared candidate의 5초 native 실행에서 오른팔 정책 목표 변화율과 초기 RH arm stiffness 배율을 비교했다. 모든 최종 조건은 1200 physics steps와 15개 contract check를 통과했고, closure 입력은 실행 전후 변경되지 않았다. 세션은 진단 비교이며 완전한 곡 재생이나 연주 성공을 뜻하지 않는다.

## 세 최종 실행

| 조건 | RH 정책 목표 rate 상한 | RH arm PD stiffness 배율 | 정책 표본 | 사용자 기타 범위 참 표본 | 최소 준비점 거리 (mm) | 기타 위치 변화 max / 끝 (mm) | 기타 회전 변화 max / 끝 (°) |
|---|---:|---:|---:|---:|---:|---:|---:|
| base_v2 | 0.8 rad/s | 1× | 180 | 67/180 | 11.230 | 59.445 / 28.340 | 46.688 / 46.688 |
| rate | 3.2 rad/s | 1× | 180 | 20/180 | 6.891 | 59.445 / 42.693 | 45.509 / 43.070 |
| gain_v2 | 3.2 rad/s | 4× | 174 (시작 2.1초) | 7/174 | 10.848 | 60.411 / 26.893 | 42.705 / 39.827 |

오른손 rate만 올린 조건에서 source motor phase 0과 1이 모두 관측되어 brief상 APPROACH 단계 진입은 확인됐다. 그러나 세 조건 모두 source target hit, physical target hit, accepted release는 0이다. 각 정책 구간은 전체 episode를 마치지 않았으며, 표의 기타 범위 표본도 정책 중 모니터링 결과이지 경계 복귀나 연주 성공의 증거가 아니다. stiffness 4× 조건은 채택되지 않았다.

원본 READY의 10 mm/6연속 표본 조건과 source detector는 변경하지 않았다. 초기 root·하체는 고정, 기타는 strap 없이 자유 운동했고, 학습 업데이트는 없다. gain_v2에서는 환경 생성 뒤 첫 physics step 전에 오른팔 12축 stiffness만 4배 설정했다. native implicit-PD와 rate 제한 동작은 source checkpoint의 명시적 actuator 구현과 같다고 가정하지 않는다.

세 실행은 이번 비교의 base_v2를 공통 기준으로 직접 비교한다. 과거 prepared baseline과는 float64 rate-cap 계산에 미세한 차이가 있어 byte-exact라고 주장하지 않는다. 시도 이력은 아래와 같이 구분해 보존했다. `base`는 Ninja 부재로 import가 실패해 physics 0회였고 최종 base_v2로 대체했다. 첫 `gain` 실행은 5초 물리는 기록했지만 helper log field 변경으로 closure 검증이 실패해 보존 상태로 남겼고, 최종 비교에는 gain_v2 재실행을 사용했다.

## 실제 native 카메라 이미지와 영상

각 실행은 151 frames, 30 fps로 전신·손 카메라를 저장했으며 ffprobe stream duration은 5.033333초다. 아래 프레임 index는 00000=0초, 00060=2초, 00150=5초다. hands 카메라는 왼손 근접 시점이다.

### base_v2 — 0.8 rad/s, stiffness 1×

![base_v2 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base_v2/data/images/frames/whole_body/00000.png)

![base_v2 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base_v2/data/images/frames/whole_body/00060.png)

![base_v2 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base_v2/data/images/frames/whole_body/00150.png)

손 카메라 같은 시점: [0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base_v2/data/images/frames/hands/00000.png) · [2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base_v2/data/images/frames/hands/00060.png) · [5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base_v2/data/images/frames/hands/00150.png)

![base_v2 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base_v2/data/images/whole_body.mp4)

![base_v2 손 근접 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base_v2/data/images/hands.mp4)

### rate — 3.2 rad/s, stiffness 1×

![rate 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/rate/data/images/frames/whole_body/00000.png)

![rate 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/rate/data/images/frames/whole_body/00060.png)

![rate 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/rate/data/images/frames/whole_body/00150.png)

손 카메라 같은 시점: [0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/rate/data/images/frames/hands/00000.png) · [2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/rate/data/images/frames/hands/00060.png) · [5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/rate/data/images/frames/hands/00150.png)

![rate 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/rate/data/images/whole_body.mp4)

![rate 손 근접 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/rate/data/images/hands.mp4)

### gain_v2 — 3.2 rad/s, RH arm stiffness 4×

![gain_v2 전신 0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain_v2/data/images/frames/whole_body/00000.png)

![gain_v2 전신 2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain_v2/data/images/frames/whole_body/00060.png)

![gain_v2 전신 5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain_v2/data/images/frames/whole_body/00150.png)

손 카메라 같은 시점: [0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain_v2/data/images/frames/hands/00000.png) · [2초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain_v2/data/images/frames/hands/00060.png) · [5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain_v2/data/images/frames/hands/00150.png)

![gain_v2 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain_v2/data/images/whole_body.mp4)

![gain_v2 손 근접 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain_v2/data/images/hands.mp4)

## 자료와 실행 이력

- [최종 3조건 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/analysis_final/summary.json) · [최종 분석 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/analysis_final.log)
- 각 최종 실행의 [base_v2 report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base_v2/data/report.json) · [rate report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/rate/data/report.json) · [gain_v2 report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain_v2/data/report.json)
- [base import 실패 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/base.log) · [첫 gain closure 실패 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/analysis_gain_first.log) · [최종 gain_v2 실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_transfer_iteration_v1/gain_v2.log)
- [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TRANSFER_ITERATION_PLAN.md:1) · [메인 결과 계획](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:188) · [메인 README 결과](/home/ajou/yigyu/3/stability_adapter_2/README.md:1493)
