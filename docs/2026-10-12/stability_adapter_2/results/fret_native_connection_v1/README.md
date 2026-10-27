# Fret 네이티브 전이 결과

## 판정

Checkpoint `fret_035000.pt` (SHA-256 `a6f0c303f69686eb02ebed5f7dce743fdc223fd89c8a8fb2b40303d0abeab5ca`)를 자유 기타에 연결한 시험이다. 모델 계약은 관측 420 / 행동 30 / value 6이다. 왼쪽 어깨·팔꿈치·손목 9축과 왼손 21축이 Fret 정책을 이룬다. 오른팔 12축은 bounded hold 목표, 오른손 21축은 초기 목표로 유지했고 Strike actor는 꺼 두었다. 기타 스트랩은 비활성화했다. 준비 중 왼손 목표 변화율 상한은 0.8 rad/s, PLAY의 Fret 목표 변화율 상한은 3.2 rad/s다. 2초간 실제 물리 준비로 source 준비 60프레임을 대체한 뒤 PLAY로 이관했고, 실제 제출한 목표로 EMA 이력을 초기화했다.

Native v3 report의 runtime guard 15개와 독립 결과 검증 17개가 모두 통과했고 1,143개 추적 입력이 실행 전후 동일했다. 실행은 첫 source terminal에서 끝났다. PLAY는 2.0초에 시작했고 actor 46회, PhysX 664 step(2.7667초 기록, 30fps 84프레임)을 진행했다. `finger_back_termination`으로 종료했으며 손가락별 표시는 `[index, middle, ring, pinky] = [참, 거짓, 참, 거짓]`이다. `press_success_rate=0`, sustain 성공은 `0/2`, episode 성공은 거짓이다. 이 종료 플래그는 source 종료 조건이 발생했다는 뜻이며, 그 자체만으로 실제 접촉이나 관통을 판정하지 않는다.

기타 기준점 G는 준비 시작에서 이관 시점까지 51.094 mm / 6.495° 이동했다. 종료 시점의 시작 기준 누적 변위는 434.475 mm, 회전 변화는 68.336°여서 안정화에 성공하지 못했다. 이관 시점의 실제 관절각은 source profile 범위를 최대 0.095522 rad 벗어났다. terminal 평균 목표 거리는 0.217316 m였고, 손가락별 집계에서 index는 2.5714/34=0.075630 m, ring은 0.5424/12=0.045200 m였다. 두 손가락의 후면 종료 표식과 무 press/sustain 결과에 비춰, 다음 왼손 실험은 index/ring의 프렛 접촉 목표 거리와 후면 접근 축을 먼저 계측한 뒤 목표 위치를 조정한다. 실제 종료 trace와 terminal 상태를 함께 확인한다.

Profile은 source 정규화·정책 목표에만 적용됐다(27 joints). Native 물리 hard limit은 XML 기준이다. handoff에서 측정한 profile 범위 초과는 앞서 보고한 값 그대로 보존했으며 보정하거나 잘라내지 않았다. Checkpoint와 현재 실행 자산 사이에는 asset 2개(`chair_thin_seat.xml`, `guitar_thigh_proxy.xml`)와 implementation 10개가 달랐다. 따라서 이 기록은 원본 학습 환경 재현이 아니라, 해당 checkpoint를 변경 이력이 기록된 자유 기타 native 환경에 옮긴 진단이다. PhysX는 CPU에서 실행됐다.

## 시도 이력

1. v1 정적 preflight는 의자 asset 차이에서 중단되어 native 실행에 도달하지 못했다.
2. v2는 보존된 사전 검수에서 preflight 이력의 `moving_guitar_observation` 판정이 action cache 변화와 기타 이동을 함께 비교한 혼동 가능성을 확인했다. 수정 검증 v3는 cache baseline 이후 기타 이동만 비교했고 10개 검사가 통과했다. 이어진 v2 native 시도는 누락된 `chair_thin_seat.xml`의 SHA를 mismatch 기록 중 읽으려다 PREPARE 0 physics step에서 종료했다.
3. v3는 누락 파일을 차이 목록에 기록하도록 고친 runner로 수행했다. 15개 runtime guard가 모두 통과했고 위 결과를 남겼다. 이 preflight 수정은 누락 asset을 복원하거나 native 환경을 원본과 동등하게 만들지 않는다.

## 기록 영상

**전신 보기 — native v3, 84프레임, 2.8초.**

![전신 native 재생](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/images/whole_body.mp4)

**양손 보기 — 같은 native v3 프레임.**

![양손 native 재생](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/images/hands.mp4)

## 시작·이관·종료 프레임

### 시작 — t=0.000초, physics step 0

![시작 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/images/frames/whole_body/00000.png)
![시작 양손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/images/frames/hands/00000.png)

시작 장면에서 기타 넥은 수평에 가깝고 왼손은 초기 grip 자세다.

### PLAY 이관 — t=2.000초, physics step 480

![이관 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/images/frames/whole_body/00060.png)
![이관 양손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/images/frames/hands/00060.png)

이 장면은 PLAY 진입 직전의 source-profile 목표 준비 자세다. G는 시작 기준 51.094 mm / 6.495° 이동했다. 이 이미지만으로 손가락 접촉 여부를 판정하지 않는다.

### source terminal — t=2.767초, physics step 664

![종료 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/images/frames/whole_body/00083.png)
![종료 양손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/images/frames/hands/00083.png)

종료 때 왼손과 기타가 서로 멀어졌고 G 회전 변화는 시작 기준 68.336°다. source `finger_back` 실패 조건으로 종료됐다.

## 원시 기록

native v3의 실행 설정·guard·terminal 값·제어 이력·초기 상태·프레임 지문·입력 불변 기록은 다음 원시 파일에 보존했다.

- [report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/report.json:1), [terminal_info.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/terminal_info.json:1), [trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/trace.json:1), [controls.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/controls.json:1)
- [initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/initial_values.json:1), [initial_audit.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/initial_audit.json:1), [capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/data/images/capture.json:1)
- 입력과 소스 보존: [inputs_before.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/inputs_before.json:1), [inputs_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/native_v3/inputs_after.json:1), [source_preservation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/source_preservation.json:1)
- 독립 기록 감사(23 checks): [recording_audit.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/recording_audit.json:1)

`native_v2/data/report.json`은 chair asset 누락으로 물리 전진 전에 끝난 시도를 보존한다. 시도별 코드 snapshot과 로그도 각 native 폴더에 있다.
