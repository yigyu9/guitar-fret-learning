# 다른 손가락의 고정 손목 teacher 후보 근거

2026-10-27. 기존 원자료를 CPU로만 확인했다. 아래는 후보 추출 가능성의 기록이며 새 teacher JSON·실험 결과가 아니다. 활성 소스와 기존 결과는 변경하지 않았다.

## 후보와 정적 source 표본

`02_contact_reward/teacher_fixed_B_export/teacher_trace60.npz`에서 중지와 같은 조건(실제 관측시각 ≥5초, candidate 4연속 60Hz, wrong 0, 누적 wrist shadow failure 없음, 손목 excess ≤20mm)을 적용했다. 각 행의 5.0~6.4833초 90/90표본이 조건을 만족했고, 4연속 끝점 후보 87개 중 distal body resultant가 최소인 표본은 다음과 같다.

| 손가락·source row | 원곡 target ID | 실제 관측시각 | 정적 표본 resultant |
| --- | --- | ---: | ---: |
| 검지 1 | event-000004/string-3/note-4 | 5.9167초 | 1.713N |
| 약지 16 | event-000053/string-3/note-54 | 5.0500초 | 11.851N |
| 소지 23 | event-000021/string-3/note-21 | 6.2333초 | 7.768N |

시각 필드는 `observed_time_s`다. `time_s`는 1/60초 뒤의 다음 명령시각이므로 혼동하지 않는다. `actual_q105_rad`와 `actual_target105_rad`에서 실제 접촉각과 당시 팔12·선택 finger4 목표를 구분할 수 있다. 모든 후보의 q/target은 유한하고 실제 action bounds 안이었다. `corrected_target39_rad`는 다음 보정 요청이다. 기존 중지 teacher의 팔 feedforward는 `actual_target105_rad`/`current_target39_rad`를 사용한다.

원래 선택 finger4 목표는 같은 실행의 `report.json → goals[row].q_target105`, 원곡 식별자는 `target_id`·`source_note_index`에 있다. 후보 판정·하중 근거는 raw의 `candidate`, `wrong`, `active`, `wrist_shadow_failure`, `wrist_guide_excess_G_m`, `body_force_n`이다.

## 원래 audible 구간의 별도 근거

`02_contact_reward/ledger_fixed_B_fast_normal_guard`는 위 정적 실행과 다른 실행이다. `scope.json`의 원래 onset/end와 `trace240.npz`를 대조한 결과다. 힘의 분모는 valid audible 240Hz 끝점이며, 세 행 모두 해당 표본에서 candidate였고 wrong·wrist failure가 0이었다.

| source row | audible candidate/valid 끝점 | audible resultant 평균 / 최대 |
| --- | ---: | ---: |
| 검지 1 | 41/41 | 0.882 / 1.004N |
| 약지 16 | 39/39 | 3.563 / 4.939N |
| 소지 23 | 64/64 | 3.773 / 4.240N |

세 행 모두 원장 clean fraction 1, `timeline_complete`였다. 이는 당시 pad+wrist teacher 조건의 지정 단음 성과다. 위 정적 source의 순간 힘과 원곡 audible 평균/최대를 같은 조건의 값으로 합치지 않는다. resultant는 distal body의 순접촉힘이며 현 압력·접촉 상대·음향 성공을 인증하지 않는다.

## 손목 pose 복원과 도구

`teacher_fixed_B_export/poses60.npz → body_state`는 row 0,6,12,18,1,21만 저장한다. 검지 row1은 native 손목·기타 pose를 직접 확인할 수 있고 약지16·소지23은 actual q의 CPU FK 재구성이 필요하다.

기존 `wrist_pose_proposal_readonly.json`의 방식대로 준비 상태와 `guitar_learning/native/lower_body_release_v1/controller_horizontal_v4.py:full_fk()`를 사용하여 대표6행×14시점, 총84 native 표본의 교차검산을 재현했다. 최대오차는 위치 2.103µm, 회전 9.603e−7rad였다. 관련 FK·준비 소스 SHA는 당시 `inputs_before.json`의 pin과 일치했다. 기타 좌표 pose는 준비된 고정 기타 pose를 기준으로 변환하며, 약지·소지 값을 native 직접 readback으로 표기하면 안 된다.

기존 raw exporter는 `02_contact_reward/support/native_point_wrist_normal_guard_export_teacher.py`다. `teacher_exports_v2.json`·`wrist_teacher_exports_v2.json`은 중지 row8/9 결과와 SHA 목록이다. 조사 시점의 `03_short_learning/support`에는 `build*teacher` 범용 생성기가 검색되지 않았다.

## 아직 검증되지 않은 부분

- 기존 source는 pad+wrist를 읽어 팔12+선택 finger4를 함께 보정했다. 새 팔12 전용 고정 손목 teacher의 onset-local3초 조건에서 접촉이 재현된다는 근거는 아직 없다. source의 press-local3초 원장 성과도 이 새 조건에 상속하지 않는다.
- 따라서 세 손가락의 v2 teacher JSON 후보 자료를 준비할 수는 있지만, 검증된 arm-only teacher·정책 성과·자유 기타 성과라고 부를 수 없다.
- ledger의 `control60.npz`에는 q105·target105·action39가 있으나 native body_state와 561관측은 없다. 손목 후보 추출 가능성을 정책 pretrain 데이터 완성으로 확대하지 않는다.
