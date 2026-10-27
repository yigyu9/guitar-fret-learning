# Tensor effort API 실행·산출물 독립 검수

- 검수일: 2026-10-07
- 범위: 승인된 단일 hinge CPU 6조건 원자료, 실행 메타데이터, 비교 수치, 최종 그림·manifest·설명 문서.
- 검수 방식: 저장 JSON 재계산·SHA 대조·그림 직접 확인. Native 초기화·시뮬레이션은 추가 실행하지 않았다.

요약 판정: **문제없음. 남은 Critical/Warning 없음. 이 fixture의 API 응답 관측은 확인했으며 전신·GPU·기타 안정화 검증은 아니다.**

## 원자료 및 수학

- 6fresh ×24step=144step, 실제 실행 exit0. 각 run의 9계약 검사, 25상태·24제출·24개 빈 접촉 목록, step/time 연속성, finite q/velocity 및 API accepted를 독립 확인했다.
- EFFORT의 0 Nm 대비 최종 Δq는 +1 Nm에서 +0.0019764197059 rad, −1 Nm에서 −0.0019764194731 rad였다. 최종 Δvelocity도 각각 양·음이며 비교 JSON의 최종/최대 차이를 재계산해 일치했다.
- POS의 ±1 Nm는 각 25개 q/velocity가 같은 mode의 0 Nm 기준과 exact 일치했다. 제출 성공과 측정된 운동 응답을 구분한다.
- CPU pipeline/PhysX GPU=false, 중력0 및 PD/solver readback이 일치한다. CUDA 시작 탐색 오류 6회가 로그에 있지만 각 CPU 실행은 완료됐고 전체 returncode는0이다.
- 5입력 current SHA, 실행 producer와 `source_preflight_v2` 사본의 byte 일치, fixture SHA를 확인했다. 원본 모델·메인 구동·controller 변경은 없다.

## 한계 및 지적 해소

- Native readback은 두 mode 모두 `hasLimits=false`, lower=upper=0이다. `initial_within_limits`는 해당 숫자에 초기0을 비교한 계약이다. Source authored ±90°와 초기·저장 q의 별도 범위 대조를 native 제한 활성화/안전성 인증으로 해석하지 않는 README:24 및 VISUAL_REPORT:920 설명을 확인했다.
- **표시 Warning 해소:** 하단 설명 및 이후 두 줄 제목 잘림을 수정했다. 현재 `plot_tensor_effort_api.py:64`의 `bbox_inches="tight"`와 `artifacts_final_v2` 그림에서 전체 제목·범례·축·설명을 직접 확인했다. 이전 producer/그림은 보존됐다.
- q의 degree 환산과 velocity의 rad/s 단위, 6조건 표, POS 겹침 표현 및 CPU 단일축 한계가 원자료와 맞다. 구간 Δq/Δt와 SDK 완료-step velocity 차이는 원인·감쇠 설계를 확정하는 근거로 쓰지 않는다.

## 최종 산출물

지원 plot CLI를 별도 `/tmp/tensor_effort_reviewer_plot_jhywwt6s`에서 실행해 수정 전 레이아웃의 byte/RGBA exact 재현을 확인했다. 이후 저장 경계만 수정한 최종 `artifacts_final_v2`는 5 upstream·7 직접 입력·producer·출력 SHA 및 실제 실행 v4 기록을 확인했고, 2059×835 그림을 직접 검수했다. README/CHANGED_FILES의 절대 경로·실제 줄 및 VISUAL_REPORT §48:912가 유효하다.

문제없음. API 차이는 이 단일 hinge CPU 조건의 관측으로 제한한다. 실제 전신 구동 변경이나 기타 안정화 성공을 승인·인증하지 않는다.

이 runtime 검수 기록을 동결한다. 다른 코드·원자료·기존 동결 검수 파일은 수정하지 않았다.
