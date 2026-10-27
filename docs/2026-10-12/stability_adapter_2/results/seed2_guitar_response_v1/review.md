# Seed 2 기타 응답 독립 검수

2026-10-08. 이번 prepare/runner/probe 분석/heldout 선택·분석 및 최종 그림·문서만 검수했다. 리뷰어는 native 초기화·physics·producer를 실행하지 않았고 이 파일 외에는 수정하지 않았다.

## 요약 판정

문제없음. 현재 실제 7probe+1heldout 경로에 남은 Critical/Warning/Suggestion은 없다. 실제 새 실행은 8init/9600step이며 그림 생성은 저장자료 후처리다. 손바닥 지속 지지·기타 안정화 성공이나 새 기준 채택은 확인되지 않았다.

## 코드·저장 원자료 확인

- 8×1201 states/trace와 8×1200 controls/contacts를 독립 읽어 전체 초기 state·81q/PD/Ggoal/LA/solver 동일, float32 제출목표/native box, 상수 목표와 4step 갱신을 확인했다. baseline의 5개 원자료 배열 전체5초는 이전 startup/full과 byte exact다.
- 이전 trace의 route 위치·속도로 9600구간 cable law를 별도 계산해 다음 trace의 last-applied 값과 비교했다. 최대 차이는 0N이다. 이 scalar는 native force sensor 측정값이 아니다.
- 저장 guitar quaternion에서 world `Log(R_current R_goal^-1)`를 재계산해 .1/1/5초 및 step960..1200 포함 평균의 6×6 응답을 대조했다. J 최대 차이 1.39e−13, 예측 벡터 최대 차이 7.26e−16이다.
- .1초 응답 rank0, 마지막1초 잠정 rotation lever .1m 가중 rank6/조건수56647.086640을 확인했다. 마지막1초 heldout 예측 잔차 .789332733mm/.155462984°는 실제 기준 대비 벡터 변화 .152794069mm/.028115669°보다 크다. 회전 잔차는 world 오차벡터 차의 norm이며 두 자세의 geodesic 거리와 구분한다.
- 요청 보정 각 ±.001rad와 실제 float32 목표 차를 구분했다. 실제 일부 값 −.001000046730rad/−.001000002027rad는 반올림 결과다. heldout palm 37행/양λ16행, 마지막 양λ117/전체행135 및 RH–guitar 0행은 직접 집계와 일치했다.
- 사전 검수의 선언 residual–trial 연결 및 helper import 전 봉인 경고는 해소됐다. 일반 runner의 probe_axes set 검사는 중복을 포함한 임의 CLI 입력까지 배제하지 않는다(run_seed2_guitar_response.py:39). 이번 정확한 6개 입력과 ordered analyzer guard·selector로 닫힌 실제 경로와 구분하며 frozen runner 재실행을 요구하지 않는다.

## 최종 미디어·문서 확인

- canonical PNG2를 직접 보았다. 8곡선의 mm/도 단위·0~5초 전체 축·heldout 점선과 base/wrist_z/heldout 실제 Gym 손카메라 step0/1200 배열이 맞다. 카메라 재생성·물리 추가 실행은 없다.
- manifest 31입력의 생성 전후 및 현재 SHA, producer·PNG2 출력 SHA, execution returncode0/명령·환경·log/manifest 연결을 확인했다. 실행시간은 근거 없는 수치 대신 null로 정정됐다. 리뷰어는 재렌더 CLI를 실행하지 않았다.
- phase README/CHANGED/IMPLEMENTATION, main README:732·PLAN:1374, dated README:470·VISUAL §75:1369 및 미실행 locality 계획을 대조했다. 요청/float32 차·rank 출처·몸통9 native 좌표 편차·151frame/30fps/5.033333초·새8trial와 후처리 범위·실제 링크의 문구 보완은 해소됐다.

## 확인한 SHA

- prepare_seed2_response_trials.py: `85318657ce5c0dfcc59e08d2e9a43c174582450728d1fea4715953ac05ce8416`
- run_seed2_guitar_response.py: `d8c08f7046f60c3961b0ce4734e679730d7ad6f098d3e23cdfe1df8b8d6d22f5`
- analyze_seed2_guitar_response.py: `d64c49152180bff28d6ab636b65b3c0c3e8a222ada86119152dfaba58c6794cf`
- prepare_seed2_response_heldout.py: `e7b4c3627e78c3727679f07c7308f31e9da7440f4a42751f37a5333bce07b58c`
- analyze_seed2_response_heldout.py: `03d714f7fee604aa26a95000716bc1b5e4eb3dba0722eb820cda0b958f01b08d`
- make_seed2_guitar_response_artifacts.py: `6c141f489b751d24b013ce202d7fea7f3520b6a5412d2e9f6175537f6512fcad`
- probe/selector/heldout의 명시 입력 6505/6508/6827개 현재 SHA가 모두 일치했다. 원래 phase의 입력·결과를 변경하지 않았다.

## 판정의 한계·동결

heldout 최대p/q26.774777mm/8.124454°는 기준26.772807mm/8.323296° 대비 위치 미세 악화·회전 소폭 개선이다. 초기 여섯 source 접근 통합조건은 미달이며 named-body/rawλ 기록은 면별·연속 지지나 cooked clearance를 인증하지 않는다. 제출목표 검사는 저장 Python 제출값 범위이고 native 목표 getter를 별도로 조회한 것은 아니다. 몸통 PD 목표 held와 실제 좌표 고정은 다르다. 이 식별은 runtime 기타 feedback·학습·중력/drive 원인 증명이 아니며 다음 음의 두 축/half-heldout 3조건은 아직 미실행이다.

현재 검수 완료. 이 리뷰를 동결하며 이후 상태 표시와 source/inventory 보존은 root가 수행한다.
