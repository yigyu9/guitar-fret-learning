# 초기 middle3 정렬: 같은 최종 목표의 실제 비교

이번 비교는 초기 middle3 각도만 공통 유지 목표인 52.089980°에 맞춘 조건과 기존 시작 각도를 유지한 조건을 비교한다. 새 조건의 middle3 offset은 0이고, 기존 held-only 조건의 실제 middle3 offset은 −0.14060189723968505 rad다. 기존 joint18 baseline에서 최종 held goal까지의 누적 변화 −0.15 rad와 actual offset은 구분한다. 최종 81개 절대 목표 명령과 명령 시계는 두 조건에서 동일하다. 다른 80개 초기 관절각, 기타 위치·자세, LA 1.1018469719600776 m와 손목 파형도 같다. 새 조건에서 초기 middle3 오차는 8.055894°에서 0°가 되었지만 기타의 초기 기준 최대 위치오차와 후기 1초 변동은 커졌다. 그러므로 이 후보를 기타 안정성 개선으로 해석하지 않는다.

![초기 middle3 정렬과 기타 초기·후기 오차 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/artifacts/initial_middle3_alignment_summary.png)

| 측정값 | 기존 시작각 유지 | 초기각 정렬 |
|---|---:|---:|
| 초기 middle3 실제각 → 공통 유지목표 | 60.145874° → 52.089980° | 52.089980° → 52.089980° |
| 초기 목표 오차 | 8.055894° | 0° |
| 5초 middle3 실제각 | 52.090865° | 52.090366° |
| 0–0.5초 기타 최대 위치오차 / 회전오차 | 13.665403 mm / 2.787520° | 14.522575 mm / 2.744799° |
| 0–0.5초 최대 선속도 / 각속도 | 0.129085 m/s / 0.527685 rad/s | 0.137609 m/s / 0.557034 rad/s |
| 최대 초기자세 기준 기타 위치 / 회전 오차 | 14.077232 mm / 2.922581° | 14.608483 mm / 2.918412° |
| 후기 완전 1초 창 최대 위치변화 / 회전변화 | 0.437387 mm / 0.080289° | 0.648625 mm / 0.115306° |
| 이전 방식의 2초 자세 기준 2–5초 변동 | 0.246108 mm / 0.047665° | 0.877649 mm / 0.148793° |
| 후기 1초 창 임시 한계 통과 | 121/121 | 121/121 |

원 trace는 240 Hz이며 후기 1초 창의 시작은 60 Hz 간격이다. 각 창은 시작점 2.000–4.000초인 121개 창이고, 창마다 241개 표본을 포함한다. 그림의 초기 기준 오차 곡선과 표의 이전 방식인 2초 기준 2–5초 변동은 서로 다른 측정이다. 임시 30 mm/5° 초기 구역 표본 초과는 두 조건 모두 0개이고, 후기 창도 둘 다 5 mm/1° 한계 안에 있다. 이 한계는 자연스러운 자세, 연주 성공 또는 지지 인증이 아니다.

아래는 이번에 저장한 **초기 정렬 조건**의 실제 native 손 프레임이다. 00150 프레임의 시뮬레이션 시각은 5.000초다. 두 영상은 151프레임을 30 fps로 담아 표시 재생시간이 5.033333초다. 실행은 CPU PhysX였고 CUDA 및 visual geometry 경고를 native 로그에 보존했다. 이 산출물 생성에서는 native 실행이나 프레임 수정을 하지 않았다.

![초기 정렬 조건의 실제 손 프레임, t=0초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/frames/hands/00000.png)

![초기 정렬 조건의 실제 손 프레임, t=5.000초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/frames/hands/00150.png)

![초기 정렬 조건 실제 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/hands.mp4)

![초기 정렬 조건 실제 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/whole_body.mp4)

기존 시작각 조건의 프레임과 영상은 [fixed-strap middle-relax v2 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_middle_relax_v2/README.md:1)에 기록된 실제 실행 자료를 재사용한다. 이를 이번에 새로 실행한 영상이나 새 조건의 렌더로 보지 않는다.

양의 raw λ 표본은 index3 1,158→1,156 step, middle3 50→91, ring3 19→38, thumb3 124→587이다. 이는 접촉 solver의 raw λ 기록으로 뉴턴 단위 힘이나 연속 지지 품질을 뜻하지 않는다. 새 조건의 middle3와 ring3 관측은 초기 구간에만 나타났다. Palm 양의 λ는 없고 사람 self-contact 기록은 0이며 palm-up proxy는 통과했다. Native bound excess 9.99495×10⁻⁵ rad는 남아 있다. 초기 source 검사와 이 기록은 동적 cooked 형상의 관통이 없다는 증명도 아니다. proxy나 raw contact 기록을 자연스러움의 증거로 확대하지 않는다.

입력의 초기 상태는 [initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/initial_values.json:1), 새 trial 정의는 [middle3_initial_at_goal.json](/home/ajou/yigyu/3/stability_adapter_2/trials/initial_middle3_alignment_v1/middle3_initial_at_goal.json:1)에 있다.

### 판단과 다음 단계

초기각 정렬은 시작 오차를 없앴지만 기타 초기 최대 위치오차, 속도, 후기 변동이 늘었다. 두 조건 모두 임시 창 한계를 통과했으므로 기존 quiet 기준과 새 시작자세 후보를 함께 보존한다. 현재 고정 LA에서 fret·strike source 범위와 초기 후보의 호환성을 다시 조사하는 다음 단계는 아직 실행하지 않았다. 사용자 환경의 LA 출처, 실제 연주 기능과 학습도 미완료다. 전체 판단은 [초기 middle3 정렬 결정](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_MIDDLE3_ALIGNMENT_DECISION.md:1), 실행 범위는 [계획](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_MIDDLE3_ALIGNMENT_PLAN.md:1), root의 산출물 검증은 [검증 노트](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/ROOT_VERIFICATION_NOTES.md:1)를 참조한다.

그림은 [재현 가능한 Python 3.8 producer](/home/ajou/yigyu/3/stability_adapter_2/make_initial_middle3_alignment_artifacts.py:1)로 한 번 생성했다. 실행은 성공했고, 산출물 단계의 추가 native 초기화·물리 step·actor 추론·학습 업데이트는 모두 0이다. 입력 전후 SHA-256이 일치하며 세부 기록은 [실행 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/artifacts/producer_execution.json:1)와 [산출물 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/artifacts/artifact_manifest.json:1)에 있다.
