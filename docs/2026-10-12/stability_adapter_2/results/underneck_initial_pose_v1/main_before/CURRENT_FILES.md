# 현재 작업에서 볼 파일

2026-10-09 정리 후 안내다. 루트의 종료된 실험 파일 508개와 캐시를 제거했다. 남은 파일에는 현재 실행 코드뿐 아니라 녹화 코드가 원본 해시로 확인하는 필수 과거 소스도 포함한다. 이 의존 파일을 단순히 이름이나 버전으로 삭제하면 실행이 깨진다.

## 계획과 설계

- [메인 계획](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1)
- [허용 범위 안에서 연주하는 계약](/home/ajou/yigyu/3/stability_adapter_2/PLAYABLE_ENVELOPE_CONTRACT.md:1)
- [수평 넥 초기 후보](/home/ajou/yigyu/3/stability_adapter_2/HORIZONTAL_NECK_INITIAL_DECISION.md:1)
- [연주 checkpoint 연결 설계](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_PRIOR_ADAPTATION_PLAN.md:1)와 [계약 보완](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_PRIOR_CONTRACT_CORRECTION.md:1)
- [몸통 유지·내부 충돌](/home/ajou/yigyu/3/stability_adapter_2/TORSO_HOLD_AND_NATIVE_COLLISION_PLAN.md:1)
- [작업 절차](/home/ajou/yigyu/3/stability_adapter_2/EXPERIMENT_WORKFLOW.md:1)

## 현재 도구와 환경

| 용도 | 진입 파일 |
|---|---|
| 물리 없는 기타 위치·Euler 회전 조작 | [open_guitar_pose_static.sh](/home/ajou/yigyu/3/stability_adapter_2/open_guitar_pose_static.sh:1) |
| 정적 조작 가이드 | [GUITAR_POSE_STATIC_GUIDE.md](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_POSE_STATIC_GUIDE.md:1) |
| 자유 기타·하체 고정·내부 충돌 환경 | [self_collision_environment.py](/home/ajou/yigyu/3/stability_adapter_2/self_collision_environment.py:1) |
| 초기 겹침 검사 | [initial_overlap.py](/home/ajou/yigyu/3/stability_adapter_2/initial_overlap.py:1) |
| 초기값·실제 스트랩 표시 5초 녹화 | [run_strap_recorded_trial.py](/home/ajou/yigyu/3/stability_adapter_2/run_strap_recorded_trial.py:1) |
| 연주 목표와 보정 합성의 CPU 구현 | [playing_target_bridge.py](/home/ajou/yigyu/3/stability_adapter_2/playing_target_bridge.py:1) |

`assets/`는 고정 하체 등 자산, `trials/`는 기존 입력값, `tests/`는 CPU 계약 검사다. 이 세 폴더는 보존했다. 범위 판정·새 기타 자세의 연주·보정 정책 학습은 아직 완성된 기능이 아니다.

## 과거 파일을 다시 확인할 때

[정리 결과·삭제 목록·원본 ZIP](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/directory_cleanup_v1/README.md:1)을 따른다. 기존 결과·영상·로그는 docs에서 그대로 볼 수 있다. 삭제된 옛 코드/계획 링크와 옛 재현 명령은 압축본의 해당 경로를 별도 작업 사본에 복원해 사용한다. 현재 디렉토리 전체에 ZIP을 덮어쓰지 않는다.

기존 near-contact diagnostic CLI의 현재 지원 proposal은 `three_face_initial_same_target_v1/proposal.json`이다. 다른 과거 proposal과 유지된 helper의 과거 단독 main까지 모두 지원하는 것은 아니며, 그 실험의 소스 closure를 복원해야 한다. 현재 지원 범위와 전체 유지/삭제 경로는 [최종 manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/directory_cleanup_v1/cleanup_manifest_v3.json)에 있다.
