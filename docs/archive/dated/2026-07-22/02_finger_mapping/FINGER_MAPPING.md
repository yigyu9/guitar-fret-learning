# Tablature → finger mapping

> **상태: 2026-07-22 MEETING SNAPSHOT.** 현재 계약은 [`master_plan/02_tablature_to_finger_mapping.md`](../../../master_plan/02_tablature_to_finger_mapping.md)를 따른다.

## 역할

Finger mapping은 각 note에 fret과 왼손 손가락을 배정하고, 재타현과 유지 구간을 합쳐 press event를 만든다. 학습 환경은 이 결과를 물리적으로 수행한다.

## 결과 형식

- `notes`: 각 음의 시작·종료, 줄, fret, MIDI, finger
- `presses`: 실제로 눌러야 하는 `(finger, string, fret, t_press, t_release)`
- `hand`: 시간에 따른 손 위치와 grip 추정
- `diagnostics`, `violations`: 교차·스팬·배정 문제 기록

손가락 표기는 `1=검지, 2=중지, 3=약지, 4=소지`다. 현재 단계에서는 바레를 허용하지 않는다.

## 대표 결과

| 항목 | 값 |
|---|---:|
| 입력 note | 68 |
| 압현 event | 51 |
| fret 범위 | 4~16 |
| 검지 배정 | 28 |
| 중지 배정 | 10 |
| 약지 배정 | 15 |
| 소지 배정 | 15 |
| 바레 | 0 |
| 진단·위반 | 0 |

전체 데이터는 [fingering.json](04_Jazz2-187-F%23_solo_mic.fingering.json), 시각화는 [fingering.png](04_Jazz2-187-F%23_solo_mic.fingering.png)에 있다.

![운지 타임라인](04_Jazz2-187-F%23_solo_mic.fingering.png)

## 제어 goal로의 변환

운지 event는 60Hz frame으로 변환된다. 각 줄은 매 frame 다음 중 하나가 된다.

- `PRESS`: 지정 손가락으로 지정 fret을 누름
- `NO_PRESS`: 누르면 안 됨
- `DONT_CARE`: 음향 판정에는 영향 없음

같은 위치의 재타현은 하나의 PRESS 구간으로 유지한다. 다른 fret으로 이동하기 전 빈 구간은 NO_PRESS, 마지막 event 뒤는 DONT_CARE로 처리한다.
