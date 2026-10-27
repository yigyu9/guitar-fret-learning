# 현재 기타 기준 왼팔 OFF/ON 사전 검수

**요약 판정: 문제없음.** 검수한 변경에서 native 실행 전에 반드시 수정할 문제는 확인하지 못했다. 구현 파일을 수정하지 않았고 native trial을 실행하지 않았다.

- Critical: 없음.
- Warning: 없음.
- Suggestion: 없음.

## 범위와 근거

전체 저장소에는 다수 기존 변경이 있으며 stability_adapter_2는 untracked 디렉터리다. 따라서 지정한 신규 파일과 기존 `run_fret_fingers_arm_hold.py`·보존 wrapper의 직접 diff로 이번 변경 범위를 확인했다. 프로젝트 AGENTS.md, README.md, EXPERIMENT_WORKFLOW.md 및 FRET_CURRENT_GUITAR_ARM_PLAN.md의 관련 지침을 확인했다.

- [fret_current_guitar_arm.py:9](/home/ajou/yigyu/3/stability_adapter_2/fret_current_guitar_arm.py:9): Shoulder/Elbow/Wrist 왼팔9만 최적화하며, native 한계와 초기 목표 ±0.3rad를 교차한다. 실제 Chest p/q 보정과 `gp + gr.apply(wrist_G)`는 현재 source wrist 목표의 기타→world 변환에 일치한다. 준비 시 상대 회전은 보조 residual이며 상태·힘을 제출하지 않는다.
- [fret_current_guitar_arm.py:35](/home/ajou/yigyu/3/stability_adapter_2/fret_current_guitar_arm.py:35): 최적화 전 actual q의 FK/native 위치·회전 일치를 검사한다. 속도 0.8rad/s를 최적화 bounds에 포함하고, 제출 단계에서도 동일 속도 및 native 한계를 적용한다.
- [run_fret_current_guitar_arm.py:107](/home/ajou/yigyu/3/stability_adapter_2/run_fret_current_guitar_arm.py:107): 120회×4 physics step의 2초 준비 및 마지막 제출 left9 handoff를 유지한다. OFF는 준비 목표를 유지하고 ON만 solver로 교체한다. finger21 source 요청 합성 및 정책 freeze는 기존 흐름과 동일하다.
- [run_fret_current_guitar_arm.py:135](/home/ajou/yigyu/3/stability_adapter_2/run_fret_current_guitar_arm.py:135): 단일 소유자가 모든 목표를 제출하고 실제 제출 목표로 source pd_target/prev_action을 갱신한다. other36 및 root/하체 고정, 상태 보존, 범위·속도 확인이 유지된다.
- [run_fret_current_guitar_arm.py:153](/home/ajou/yigyu/3/stability_adapter_2/run_fret_current_guitar_arm.py:153): 기존 source evaluate_after_physics를 그대로 호출하고 첫 done에서 즉시 break한다. source 보상·실패·goal clock을 변경하지 않는다.
- [fret_raw_recording.py:7](/home/ajou/yigyu/3/stability_adapter_2/fret_raw_recording.py:7), [live_fret_recording_v2.py:20](/home/ajou/yigyu/3/stability_adapter_2/live_fret_recording_v2.py:20): 사용되는 capture는 IMAGE_COLOR를 별도 numpy 배열로 복사하고 PIL로 저장한다. depth 조회나 goal callback을 호출하지 않는다.
- [fret_current_guitar_arm_preserved_run.py:42](/home/ajou/yigyu/3/stability_adapter_2/fret_current_guitar_arm_preserved_run.py:42): import 전 입력 SHA/소스 보존 및 실행 후 동일 입력 대조를 유지하며, correction 인자를 새 runner로 전달한다. 기존 결과 경로를 덮어쓰지 않는다.

## 독립 실행한 검증

- 신규 Python 구현 4개 파일 AST parse 통과, shell wrapper `bash -n` 통과.
- `PYTHONDONTWRITEBYTECODE=1 /home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.test_fret_current_guitar_arm` 종료 코드 0, 11개 검사 모두 통과.
- 저장 native 2/4/8초 상태의 FK 최대 위치 오차 1.623e-7m, 회전 오차 2.812e-7rad. rate/envelope 검사 통과.
- 제출 목표와 일관된 합성 FK 상태에서 10mm 목표 이동의 예측 위치 오차는 10.000→4.764mm, 입력 상태는 보존됐다. 이 합성 검사나 저장 상태 검사는 실제 ON 물리 추종 성능을 입증하지 않는다.

실제 OFF/ON의 동역학, 원본 terminal 결과 및 raw camera 안정성은 후속 native 실행으로 확인해야 한다. raw COLOR 변경이 이전 crash 원인을 해결했다고 판정하지 않는다.

## 검수 대상 SHA256

| 파일 | SHA256 |
|---|---|
| fret_current_guitar_arm.py | ec25d6abded0dc7608ce245ec7efa4a07004d95e0cddf02a4028c2f784a23eb5 |
| fret_raw_recording.py | 6d88f469bac58aeb7db41b0584f7189d386eab4a3aac50f98c0e8de291277757 |
| run_fret_current_guitar_arm.py | 02711628041ab48a1332ccaed9a1c410267bee06fff1efbb471cd911efd63c65 |
| fret_current_guitar_arm_preserved_run.py | 9212c43e01dd891c1b3d606a258fd16b4d1d76742e8578dd507195e69990a6f0 |
| run_fret_current_guitar_arm.sh | 0342205ade7c42503131f5f9f4d2b4da72fb112cbe6f1b298e409a2cd9868d00 |
| test_fret_current_guitar_arm.py | 88805a3972a65b87202b8a7a5ee44d2da7102cab04fc7666f11f27196af74886 |
| FRET_CURRENT_GUITAR_ARM_PLAN.md | b65a675baf20de12beb2a8b057d69633710d3f5da463375f4fc2fe6ae2fbcfaa |
