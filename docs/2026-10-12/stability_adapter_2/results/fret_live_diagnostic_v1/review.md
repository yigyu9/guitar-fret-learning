# 현재 기타 기준 Fret 실시간 진단 v1 독립 검수

## 사전검수

**요약 판정: 문제없음(사전검수).** 표시 Warning 1건은 실행 전 수정본에서 해소됐다. native 실행과 원본 baseline 대조는 아직 수행 전이다.

- **Critical:** 없음.
- **Warning:** 없음. 최초 draft의 화면 밖 끝점 조기 return은 [live_fret_recording.py:31](/home/ajou/yigyu/3/stability_adapter_2/live_fret_recording.py:31)의 카메라 앞/finite 검사와 화면 안 표본 구간 표시로 교체됐다. 최초 draft는 `source_pre`, 실행 전 수정본은 `source_pre_revision`에 별도 보존됐다.
- **Suggestion:** 없음.

검수 범위는 새 `live_fret_geometry.py`, `live_fret_recording.py`, `run_live_fret_diagnostic.py`, `run_live_fret_diagnostic.sh`와 새 단위검사다. git에서는 `stability_adapter_2/` 전체가 미추적이므로 변경 diff 대신 이 신규 파일과 직접 호출하는 원본 인터페이스를 읽었다. 다른 파일은 수정하지 않았다.

원본 `run_fret_fingers_arm_hold.py`를 그대로 호출하고 recorder/view 생성 두 연결만 임시 교체하며 `finally`에서 복원한다. 보존 wrapper는 native runner import 전 입력을 hash/snapshot한다. actor-root box를 현재 회전의 표시 기준점 offset만큼 이동하는 정의, Pelvis RFU, 최단 상대 회전각, 지정 손가락별 목표 할당, pluck_range 접촉 제외는 계획과 맞는다. 실제 손끝 body 원점 거리와 one-sided pad 접근거리를 분리한다.

capture는 native state/제출 target을 전후 비교하고, 현재 native 상태를 source view에 복사한 다음 `goals.current()` 및 `observe_fret_v2_state()` 전후 view/goals/reward의 tensor를 대조한다. source 조회에는 tracker 갱신 호출이 없다. `goal_frame_at_capture`로 capture의 현재 frame을 기록하며 t0는 view 생성 전이어서 목표 미초기화다. 원본은 240Hz 물리의 8step마다 30fps capture하고 최소 2초 준비 후 첫 source done까지 실행하며, 종료가 격자 밖이면 마지막 capture를 추가한다. 수정본은 `terminal_reset_requested`를 읽어 그 추가 frame을 `TERMINATED` / `after terminal evaluation`로 식별한다. runtime 비변이와 baseline 제어 exact 일치는 실행 결과에서 확인해야 한다.

독립 검증: rl38 Python으로 `python -m unittest stability_adapter_2.test_live_fret_geometry -v` **5/5 PASS**, `bash -n stability_adapter_2/run_live_fret_diagnostic.sh` **PASS**.

## 후속 결과 검수

**최종 요약 판정: 재작업 필요(전체 녹화 미완료).** 두 실행 모두 첫 source done 이전에 native camera 파일 저장 중 exit 139로 중단됐다. 코드를 수정해 재사용하지 않고 원본/partial을 보존한 별도 v2 저장 경로로 검증을 이어간다. 확인된 논리·보안 Critical은 없으나 v1을 성공한 full run으로 보고할 수 없다.

첫 native 실행은 exit 139로 중단됐다. [native_crash.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_live_diagnostic_v1/native_crash.json)은 기존 native camera 저장 호출에서의 stack 위치와 원인 미확정을 기록하며 source done으로 설명하지 않는다. 동일 소스 재시험도 [retry/native_crash.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fret_live_diagnostic_v1/retry/native_crash.json)에 기록된 exit 139로 중단됐고 마지막 완전 frame은 step 200 / 0.833333초다. 두 번째 실행의 root 입력 감사는 1176개 파일 변경 0개다. 두 실행의 partial MP4는 각각 보존됐다.

첫 실행의 저장된 capture 27개는 step 0~208, 8step 간격, t=0~0.866667초다. 전 frame에서 `source_readonly`, `render_preserves_states`, `submitted_targets_unchanged`가 참이다. t0의 목표는 null/미초기화이며 이후 현재 goal frame 0의 목표를 기록한다. 손 근접 표시 frame `00026.png`를 실제로 열어 3번 현/6품/약지의 87.3mm 손끝 거리, 145.1mm 손목 거리, 접촉 body pair 10개, Pelvis RFU 및 회전 표시를 해당 capture row와 대조했다. 화면 밖으로 이어지는 box edge 표시도 확인했다. 이 접촉은 압현 성공 인증이 아니다.

사전 보호 목록 `protected_before.json`의 1327개 파일 SHA를 독립 대조해 변경 0개를 확인했다. v1의 full baseline 제어·trace 및 terminal coverage는 미검증으로 남긴다. 후속 v2 검수는 별도 `fret_live_diagnostic_v2/review.md`에 기록한다.

최종 README 검수: 첫 시험/재시험의 마지막 완전 frame 27/26개, step 208/200, 0.866667/0.833333초와 crash 기록이 일치한다. native 원인은 미확정, 준비/PLAY 미도달, full live 미완료를 명시했고 보존 partial 링크는 모두 존재한다. v2의 조회 crash로 writer 단독 원인 결론을 내릴 수 없다는 제한도 정확하다. 문서상 추가 Critical/Warning/Suggestion 없음. 검수 기록을 닫으며 v1 전체 live 실행은 미완료 상태로 보존한다.
