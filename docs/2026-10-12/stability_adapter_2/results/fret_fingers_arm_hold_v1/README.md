# 준비 팔 목표 유지 + 손가락 Fret 제어 결과

## 판정

2초 준비 이후 왼쪽 어깨·팔꿈치·손목 9축의 **제출 목표**를 유지하고 왼손 손가락 21축에만 Fret 목표를 적용했다. 팔과 기타의 물리 상태를 고정하지 않았으며, native 실행은 원본 `finger_back` 조건에서 끝났다. 공통 비교시점인 2.766667초에서 기타 기준점 G의 이동은 기존 434.475472 mm에서 72.742681 mm로, 회전 변화는 68.335935°에서 9.854978°로 줄었다. 그러나 이번 실행도 기타 안정성·운지·음악 성공에는 도달하지 않았다.

| 지표 | 기존 Fret native v3 | 팔 목표 유지 시험 |
|---|---:|---:|
| 비교 가능한 종료시각 | 2.766667 s | 2.766667 s |
| 공통 종료 시각의 G 이동 | 434.475472 mm | 72.742681 mm |
| 공통 구간 최대 G 이동 | 434.475472 mm | 73.190237 mm |
| 해당 시각까지 최대 G 회전 변화 | 68.335935° | 13.164685° |
| 종료 시각 | 2.766667 s | 12.916667 s (물리 기록) |
| 전체 실행 최대 G 이동 | 434.475472 mm | 73.190237 mm |
| 전체 실행 최대 G 회전 변화 | 68.335935° | 50.248030° |
| 최종 G 이동 / 회전 변화 | 434.475472 mm / 68.335935° | 48.096796 mm / 50.248030° |
| source 운지 종료 | 검지·약지 `finger_back` | 검지 `finger_back` |
| press 성공률 | 0% | 0% |
| sustain 성공 | 0/2 | 0/27 |

같은 시각까지는 두 G 지표가 개선됐다. 이번 기록 전체에서는 위치 변화가 73.190237 mm 이내였지만, 회전은 다시 50.248030°까지 커졌고 원본 실패 종료가 발생했다. 기록상 5·8·10초 회전 변화는 각각 46.303°·46.166°·46.407°, G 이동은 14.957·14.277·15.536 mm였다. 즉 기타는 비교적 작은 위치 변화 주변에 머물면서도 회전된 상태에 도달했다. 결과는 **초기 기타 위치 유지의 개선**이며 안정화 또는 연주 성공이 아니다. 두 실행의 종료시각과 sustain 분모가 다르므로 전체 종료값이나 sustain 개수를 같은 길이의 성공률 비교로 해석하지 않는다. source 손가락별 종료 표식과 contact 지표는 시뮬레이터의 실제 접촉·관통을 단독으로 입증하지 않는다.

## 실행 조건과 범위

Fret 체크포인트 `fret_035000.pt` (SHA-256 `a6f0c303f69686eb02ebed5f7dce743fdc223fd89c8a8fb2b40303d0abeab5ca`)의 관측/행동/value 계약은 420/30/6이다. 기존 Fret native v3와 같은 초기자세·체크포인트·2초 준비 및 물리 설정을 사용했다. 왼쪽 어깨·팔꿈치·손목 9축은 준비 종료 때 마지막으로 제출한 목표를 PLAY 동안 유지했고, source actor가 요청한 해당 9축 값은 기록만 했다. LH 손가락 21축 source 요청은 목표 합성에 사용한 뒤 3.2 rad/s 변화율 및 native XML 한계를 거쳐 제출했다. LThorax 3축과 오른팔 12축은 제한된 hold, 나머지 36축은 초기 목표 유지였다. 준비 구간의 120 제어 목표와 61개 저장 상태, 그리고 t=2초 handoff 카메라 bytes는 기존 실행과 일치했다.

Root와 하체는 고정했고 기타는 자유 상태였다. Strap은 껐고 Strike actor 및 학습 갱신도 없었다. 기타 pose를 덮어쓰거나 외력을 가하지 않았다. Source profile은 정책·목표 정규화의 27개 관절에만 적용됐으며 native 관절 hard limit은 작성된 XML을 따랐다. 체크포인트 자산은 `assets/chair_thin_seat.xml`, `assets/guitar_thigh_proxy.xml` 두 파일, 구현은 `env/base.py`, `env/rewards/fret.py`, `env/tasks/__init__.py`, `env/tasks/task_fret.py`, `learning/__init__.py`, `learning/checkpoint_contract.py`, `learning/curriculum.py`, `learning/ppo.py`, `train.py`, `train_fret.py` 열 파일이 현재 native 환경과 달랐다. 그러므로 이는 원본 체크포인트 학습환경 재현이 아니라 변경 차이를 기록한 CPU PhysX 진단이다. 화면은 Isaac Gym native camera/lavapipe 캡처다. MuJoCo는 내부 FK 검증에만 사용됐으며 렌더러나 동등 물리엔진이 아니다.

Native 기록은 물리 3,100 step, source actor 655회, 총 12.916667초, 389 camera frame이다. 실행은 정상적으로 첫 source terminal에서 끝났다. 판정은 `finger_back`이며 손가락별 source 표식은 `[index, middle, ring, pinky] = [참, 거짓, 거짓, 거짓]`; 목표 완료는 false, press 성공률은 0, sustain은 0/27이다. 기타의 최대 회전 변화는 전체 기록 중 50.248030°였고, terminal G 위치 변화는 48.096796 mm였다.

## 기록 영상

전신 native 영상, 389 프레임이다.

![전신 native 재생](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/images/whole_body.mp4)

양손 native 영상, 전신 영상과 같은 389 프레임이다.

![양손 native 재생](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/images/hands.mp4)

## 시작·handoff·종료 프레임

### 시작 — t=0.000초, physics step 0

![시작 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/images/frames/whole_body/00000.png)
![시작 양손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/images/frames/hands/00000.png)

실제 native 초기 장면이다. 렌더 캡처는 저장 상태를 바꾸지 않는 것으로 확인했다.

### PLAY handoff — t=2.000초, physics step 480

![handoff 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/images/frames/whole_body/00060.png)
![handoff 양손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/images/frames/hands/00060.png)

준비 구간과 기존 native v3의 동일 시점이다. 여기서 제출한 왼팔 9축 목표는 이어지는 PLAY 구간 동안 유지된다. 실제 팔 관절각이나 기타 자세를 이 프레임에 고정하지 않았다.

### 원본 source terminal — t=12.916667초, physics step 3100

![terminal 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/images/frames/whole_body/00388.png)
![terminal 양손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/images/frames/hands/00388.png)

검지의 `finger_back` 원본 종료 표식에서 기록이 끝났다. 프레임은 기타의 최종 이동 48.096796 mm와 회전 변화 50.248030°를 보여주며, 이미지 단독으로 접촉 성공을 판단하지 않는다.

## 원자료와 검증

- Native 실행 설정 및 runtime checks: [report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/report.json:1), [terminal_info.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/terminal_info.json:1).
- Native 상태·제어·handoff 자료: [trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/trace.json:1), [controls.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/controls.json:1), [handoff_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/handoff_values.json:1), [initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/initial_values.json:1).
- 입력 closure와 사후 비교: [native inputs before](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/inputs_before.json:1), [native inputs after](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/inputs_after.json:1), [analysis summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/analysis/summary.json:1), [analysis input hashes](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/analysis/inputs.json:1). 분석 검사는 23개 통과했고, 추적 입력 1,148개의 실행 전후 SHA가 동일하다.
- [초기 상태 audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/initial_audit.json:1), [camera capture manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/native/data/images/capture.json:1), [native recording audit (31 checks)](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/recording_audit.json:1), [source preservation audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/source_preservation.json:1).
- [기존 Fret native v3 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_native_connection_v1/README.md:1)는 보존했다. 이번 수치의 공통시각 비교와 전체 실행 비교는 [analysis summary](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_fingers_arm_hold_v1/analysis/summary.json:1)에 기록되어 있다.
- 두 native 원본에서 복사한 영상과 SHA-256은 [video index](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_fret_arm_hold.md:1) 및 [collection manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_COLLECTION_fret_arm_hold.json:1)에 있다.

다음 후보는 현재 기타 기준 왼손 손목·운지 목표의 오차를 측정하고, 손가락 21축 목표를 덮어쓰지 않는 작은 왼팔 9축 보정을 평가하는 것이다. 손바닥 접촉을 강제하지 않고 기존 완주·운지·source 종료 기준을 유지한다. 학습 구조 변경은 이번 결과로 결정하지 않았다.
