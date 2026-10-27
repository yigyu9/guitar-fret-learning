# seed2_guitar_feedback_v1 독립 검수

검수일: 2026-10-08. 신규 prepare/runner/analyzer, 저장 원자료, 최종 두 PNG·문서 및 다음 warmstart 계획을 검수했다.
검수 중 native 초기화·physics·producer 재실행은 0회다. 다른 코드·원자료·이전 동결 리뷰는 수정하지 않았다.

## 요약 판정
문제없음. Critical 없음, 미해소 Warning 없음, 추가 Suggestion 없음. 신규 실제 실행은 3init/3600step이며 두 과거 곡선은 저장 참조다. 상수 −.016의 오차 감소와 feedback의 종료 오차 감소는 관측이며 지속 지지·초기 복원·연주 안정성 또는 최종 채택을 인증하지 않는다.

## 코드·독립 저장 자료 대조

- `prepare_seed2_feedback_trials.py:31–50`의 last-1s backward j 출처, 유한·양의 가중 분모, 전체 δ구간의 float32/native/합성 ±.3 검사가 계획과 일치했다. 실제 연산 helper와 proxy audit는 import 이전에 봉인된 입력 closure에 포함된다.
- `run_seed2_guitar_feedback.py:115–129`의 world G6 오차, −gain·projection 부호, 60Hz 적분·속도제한·δ∈[−.016,0], palm-up 이탈 시 갱신 보류를 확인했다. 초기 q+지지 bias+residual의 unclipped 제출 목표를 대조하며 관절·기타 상태를 runtime에 덮어쓰지 않는다.
- 각 1201상태/trace/task, 1200controls/contact, 300갱신과 4step 유지 기록을 독립 대조했다. 공통 초기 81q·전체 state·PD·G·LA·solver, root/하체 body struct 불변, float32 왼팔12 제출 목표와 계산상 다른69 목표 유지가 일치했다. SDK 목표 getter를 이 단계에서 새로 조회한 것은 아니다.
- pre-step states[i]의 오차·projection·rate·δ·freeze 재계산 차이는 1e−12 미만이다. 3600구간의 이전 trace 기반 수동 cable-law scalar 오차는 0N이다. 분석 9계약과 입력 SHA 8733개를 확인했다.
- feedback은 pre-step 2.233333333초에 −.016 경계에 도달했고 180/300갱신이 경계이며 freeze는 0회였다. raw 요청 rate 최대 .105175293rad/s, 속도제한 후 요청 .008rad/s, 실제 float32 목표 변화율 .008003711700439453rad/s를 구별했다. 비활성 상수 조건의 계산상 rate는 적용되지 않았고 실제 목표 증분은 0이다.
- 최대 p/q는 상수 −.008의 25.929259mm/7.900654°, −.016의 25.280921mm/7.753357°, feedback의 26.950260mm/8.210682°로 일치했다. feedback 종료는 21.953773mm/7.096483°지만 최대 이동은 저장 기준보다 컸다. 세 조건의 초기 step0–24 Gp/Gq 25관측은 기준과 exact다.
- index3 마지막 양의 raw λ는 87/95/255, palm은 123/124/124이며 palm 마지막 전체 행의 step은 131/138/136이다. R_Hip는 각 1200개 고유 step에 양의 λ가 있었고 RH–기타 행은 없었다. ANY-body/LH/RH 집계를 독립 대조했다.

## 미디어·문서·보존

- 최종 두 PNG를 직접 확인했다. 저장 두 곡선/신규 세 곡선, 전체 0–5초 축, mm/world SO(3)도 단위와 요청/실제 float32 mrad 분리가 맞다. 손 카메라 2×3은 신규 각 run의 실제 Gym step0/1200 저장 프레임이며 source 재구성이 아니다.
- producer·21개 입력 전후/current SHA·두 출력·manifest·log가 일치한다. 성공 returncode0과 이후 metadata wrapper 경로 오류를 구별했고, 보존되지 않은 elapsed를 null/unmeasured로 기록한 것은 적절하다. 독립 검수에서 producer를 재실행하지 않았다.
- 문서 Warning 해소: VISUAL_REPORT:1428의 palm 131/138/136을 행 수가 아닌 마지막 step으로 정정했고 실제 행 수 32/38/48과 분리했다. 그림108/109, README:13의 여섯째 자리 반올림, main/dated/다음 계획의 속도제한 후 요청 rate 표현도 확인했다.
- 이전 locality 문서 두 개의 current/snapshot SHA와 보존된 오편집 사본 SHA를 직접 대조했다. 누적 VISUAL §1–76 prefix도 원 snapshot bytes와 exact다. 전체 1005파일 보존은 root 기록이며 이 좁은 복원 검수와 구별한다.
- 다음 warmstart는 미실행이다. 초기 왼쪽33 좌표만 보간·속도0으로 옮기고 같은 절대 PD 목표를 새 offset으로 재표현한다. 계획:27–28은 왼쪽33 절대 목표/그 외48 초기 목표를 구분해 손가락 초기각 변경과 기존69 guard의 충돌을 피한다. fresh source/FK/native admission·partial 보존은 향후 검증 대상이다.

## 검수한 정확한 SHA-256

- prepare: `141daeb863f7dabc6f29f638c431a5d3155f2bd43a18cb898d6db4c94b33b73e`
- runner: `fc081532bb4912b5b1cb88e6fe923f14e48220912c01419f3785cb45fe7e349c`
- analyzer: `072d36863179f058fd0e6a1cc05dc9ddaaac5fe1a6490693f84c2954aab0c0bd`
- plotter: `255da51545e975db05fb99ce91bd71b91d5695291f3ade75d04e5fad8479589c`
- analysis: `c92b8cf1d239ce4c38cbdc366b466dbd17c4c7b6418d33899cec83952c3af0bd`
- artifact manifest: `df31e32c021baab0e7a2034934aced3cf44626ba01c65c4aee06ee1a030c64ac`

## 한계·동결

상향 proxy·source hull은 해부학적 부호나 cooked 접촉 인증이 아니다. scalar DOF 편차는 whole-joint SO(3) 회전각이 아니며 named-body/λ 기록은 면별 접촉·Newton 힘·substep 연속 지지를 증명하지 않는다. 검지·palm 접촉 소실과 초기 여섯 부위 통합 접근 미달, 기타 오차가 남는다.
이 리뷰는 동결 가능하다. 최종 상태 체크·source snapshot·inventory·보존 감사는 root의 후속 작업으로 남겨 두며 여기서 완료를 인증하지 않는다.
