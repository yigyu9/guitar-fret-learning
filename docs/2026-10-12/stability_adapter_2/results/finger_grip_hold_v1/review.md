# Finger grip hold 독립 검수

검수일: 2026-10-07.

범위: 이번 finger 초기 FK/seed, arm preload 적합, finger 및 palm/guitar feedback, runner·native camera recorder·검증 코드와 저장 원자료·그림·영상·결과 문서. 검수자는 추가 native 초기화·simulation·source query를 실행하지 않았으며 이 파일만 작성했다.

## 요약 판정

**문제없음. 남은 Critical / Warning / Suggestion 없음.** 현재 0.15 palm cap 조합은 다음 진단 기준이며 안정화·연주 성공 판정이 아니다.

## 검증 근거

- 기존 환경·PD·자산·고정 하체·자유 기타·고정 절대 LA를 유지하는 target-only 합성을 확인했다. 24 arm PI/preload/palm 보정과 LH finger 12 보정을 하나의 주요 66관절 목표로 전달하며 나머지 목표 유지와 실제 자세 고정을 구분한다.
- 초기 FK의 world left rotation tangent, feedback 방향 및 0.08 m/rad scaling이 정합적이다. 저장된 12×24 matrix·24열·finite/read-state 계약과 source-clear seed 연결을 확인했다. 초기 미분은 runtime 안정성 인증이 아니다.
- 1초 baseline/feedback-v2/cap-0.30 세 조건의 각 60 update를 저장 state로 독립 재계산했다. PI·DLS task·적분·component cap/rate·최종 합성 clipping과 rollback이 일치했고 float32 전달 목표 최대 차이는 6.61e−8 rad로 2e−7 rad 허용 범위 안이다. 실제 자료의 PI component 최대값도 0.15 rad 이내다.
- 저장 native 기타 위치·정규화 quaternion에서 위치오차와 회전오차 cosine을 재계산했다. 위치 차이는 3.47e−18 m 이하, cosine 차이는 4.45e−16 이하였으며 문서의 최대/종료값 및 native contact 시점과 일치했다.
- 세 1초 조건의 root/하체 8 body 전체 struct state가 모든 step에서 exact다. baseline의 이전 self-collision ON 4배열 재현, 선택 headless/camera 실행의 raw 5파일 byte-exact, 0..240 step의 61회 paired capture와 원본 PNG SHA를 확인했다.
- runtime provenance 1,800항목의 실제 current/보존 사본 SHA가 일치했다. Canonical render의 137입력/65출력 및 plot의 29입력/1출력 SHA도 일치했다. 실제 MP4는 H.264/yuv420p, 2560×720, 12 fps, 61 frame, 5.083333초다. 영상에서 시뮬레이션 0/0.5/1초 frame과 비교 그래프를 직접 확인했다.
- verification의 22개 계약 통과, 누적 79초기화/1,872 step 기록, controls metadata 정규화 및 최초 검증 실패·수정 전 producer 보존 경계를 확인했다. 정규화는 없는 zero bias/empty palm field만 보완하며 기존 raw를 변경하지 않는다. 촬영 당시 recorder 사본도 실제 입력 SHA와 일치한다.

## 지적 및 해소

- 네 Warning 모두 해소: source-clear seed 검증 연결, 실패 시 부분 raw/failure 보존, 최종 합성 제한을 반영한 palm 적분 rollback, recorder 생성자 첫 capture 실패 시 native cleanup. 각 수정 전 producer/결과는 보존됐다. 최종 rollback은 다음 update의 적분 상태에 적용되고 이미 산출한 현재 target은 유지하는 순서다.
- 두 문서 Suggestion도 해소: [README:7](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_grip_hold_v1/README.md:7)의 near2µm 생성 이동 및 유지 목표 명시, [VISUAL_REPORT:1018](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1018)의 source contact 표현을 native raw contact로 정정했다. palm 위치 측정은 native 링크 원점이며 해부학적 법선 인증이 아니다.

## 최종 판정

1초 최대 기타 오차는 baseline 20.341143 mm / 5.282789°에서 v2 16.170221 mm / 2.517144°로 감소했다. 초기 seed·preload·feedback을 함께 바꾼 조합 비교이며 finger 단독 효과가 아니다. 양의 LH raw lambda는 step 130까지, contact 행은 131까지이고 이후 소실한다. 10 mm / 2° 및 마지막 0.1초 지지 참고 목표를 충족하지 못했다. Cap 0.30은 미채택이며 0.15를 진단 기준으로 유지한다. 실제 camera 영상도 cooked collider·접촉력·지속 지지 인증으로 확대하지 않는다. 남은 지적사항 없이 이번 검수 기록을 동결한다.
