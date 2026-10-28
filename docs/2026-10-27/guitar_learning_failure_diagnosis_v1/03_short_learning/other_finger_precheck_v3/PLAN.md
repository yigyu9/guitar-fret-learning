# 검지·약지·소지 고정 손목 후보 사전검사

## 목적과 범위

기존 `OTHER_FINGER_EVIDENCE.md`의 검지row1·약지row16·소지row23 후보를 CPU에서 재현하고, 현재 단음 CLI의 작은 native 대조를 준비한다. 후보 JSON은 **아직 현재 arm-only 손목 teacher/onset-local3초 조건에서 검증되지 않았다.** 원래 pad+wrist teacher의 정적 접촉과 원곡 음 창 성과를 새 조건의 성공으로 상속하지 않는다.

새 파일은 이 디렉터리에만 둔다. 기존 활성 소스·동결 입력·중지 teacher/reference·원자료는 보존한다. root의 seed17 GPU 실행과 겹쳐 실행하지 않으며 이번 준비에서는 GPU를 사용하지 않는다.

## 원자료에서 고정한 선정

`02_contact_reward/teacher_fixed_B_export/teacher_trace60.npz`의 실제 `observed_time_s≥5초`, 4연속60Hz candidate·wrong0·active, 누적 wrist shadow failure 없음, 손목 excess≤20mm를 만족하는 끝점 중 distal resultant가 최소인 표본을 그대로 사용한다. `time_s`는 다음 명령시각이므로 source 관측시각으로 쓰지 않는다.

| 손가락 | source row | 원곡 target | source 관측시각 | 정적 resultant |
| --- | ---: | --- | ---: | ---: |
| 검지 | 1 | event-000004/string-3/note-4 | 5.9167초 | 1.713N |
| 약지 | 16 | event-000053/string-3/note-54 | 5.0500초 | 11.851N |
| 소지 | 23 | event-000021/string-3/note-21 | 6.2333초 | 7.768N |

팔 feedforward12와 reference4는 해당 관측시각의 `actual_target105_rad`를 사용하며 `current_target39_rad`와 일치하는지 확인한다. 실제 q, 원래 기하 source goal, contact controller target을 따로 기록한다. reference가 source goal 또는 actual q라고 설명하지 않는다.

손목 pose는 준비 상태로 보정한 FK에 **실제 q105**를 넣어 재구성한다. 대표6행×14시점의84개 native 손목 pose와 검산한다. 검지row1은 선택시각의 native 손목·기타 pose 직접 기록도 있다. 약지·소지는 해당 행 body pose가 저장되지 않아 FK 재구성값이며 native 직접 readback이 아니다. 기타 좌표 변환은 기존 중지와 같은 준비된 고정 기타 pose를 쓰고, source report의 기타 미세변위 한계와 검지 직접 대조 오차를 기록한다.

## 작은 실제 사전검사 계획

각 손가락은 같은 teacher/reference·seed7·incremental·std0.1711710544767014·large·4환경·H32 조건으로 검사한다. 기존 CLI의 train1업데이트는 **initial.pt 생성용 bootstrap**이다. 평가에는 PPO 전 initial.pt만 쓰고 final.pt 학습 결과는 사용하지 않는다. 새 장기 RL·actor 이전·B 비용 head 변경·A gamma 변경·접촉 제어 개입을 합치지 않는다.

손가락별 bootstrap1단계 후 그 initial.pt의 reference/zero/random 각4시도를 순서대로 실행한다(총12단계). reference는 선택4 contact target으로2초 유한 ramp, 팔12는 동일 고정 손목 pose teacher, audible onset은3초다. 원곡의 press/onset/end 차이·음 길이·561관측·9보상·native 전체범위/속도/PD·엄지035·다른 손가락 B·기존 실패 종료를 유지한다. 물리 실패 시도도4분모에 포함한다.

확인할 것은 reference의 원래 음 창 candidate/clean/달성, zero/random 대조, wrong·손목/물리 실패, 실제/목표각 및 tracking 오차, 손목 pose 오차, 접촉 합력이다. 새 성공 기준이나 힘 상한은 도입하지 않는다. env0 trace는60Hz 한 시도이며 전체4환경·240Hz 극값이나 실제 현 압력으로 확대하지 않는다. 결과가 부족하면 후보가 미검증/실패인 상태로 보존하고 범위를 줄이거나 teacher를 조용히 바꾸지 않는다.

## 실행과 검증

- [x] `build_candidates.py` CPU 실행: 선정·FK/native 검산·실제 controller 범위·현재 teacher/spec/reference reader 확인.
- [x] 현재 CLI12단계 dry-run과 Python3.8 구문 확인.
- [ ] 독립 검수 후 준비 seal 작성.
- [ ] root의 GPU 직렬 인계 후에만 native 검사 실행.
- [ ] 전체12단계의 완료·입력핀·scene 종료와 원래 시도분모 확인 후 별도 결과 기록.

기본 명령은 dry-run이다. root가 GPU 점유 종료와 준비 seal을 확인한 뒤에만 `--execute`를 쓴다.

```bash
python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/03_short_learning/other_finger_precheck_v3/run_prechecks.py
python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/03_short_learning/other_finger_precheck_v3/run_prechecks.py --execute
```

source 조건의 positive는 유한 기하·body-load 후보이며 자유 기타·연주 음향·정책 능력·자연스러움의 검증이 아니다.
