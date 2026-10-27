# 생산 엄지 후면 v3 회귀 준비

`run_regression.py`는 현재 생산 helper를 그대로 사용하는 원래 `thumb_contact_probe.main()`을 호출한다. 장면 생성 시 `diagnostic_guitar_mode='fixed'`만 지정한다. 원래 contact 모드 900 control/15초·240Hz 3600 endpoint·video 450 frame, −0.3mm 접근 일정, 판정·128점 선택·PD·힘·관절 범위·누적 codec은 변경하지 않는다. 별도 면 helper나 과거 A/B wrapper를 import하지 않는다.

출력이 이미 있으면 native import와 원래 probe 호출 전에 거부한다. base의 exclusive mkdir 뒤 source callback에서 dev/inode를 기록하며, 동일 소유 디렉토리일 때만 새 `production_regression.json`을 exclusive 작성한다. 기존 `report.json`과 원자료는 그대로 두며 그 안의 inherited free-guitar 문구도 수정하지 않는다. 새 보고서에 실제 fixed 요청/readback·scene closed·기존 판정·추가 source pin/검증을 기록한다. 새 보고서 completed는 원래 접촉/유지/해제/재접촉 프로토콜과 fixed-witness release 및 실행 감사를 모두 요구한다. 실패 원인은 원래 보고서와 추가 보고서에 남긴다.

CPU 준비 검사는 `CUDA_VISIBLE_DEVICES='' PYTHONPATH=. python support/self_test.py`에 해당하는 절대 경로로 실행한다. 실행 준비 당시 wrapper·base·생산 helper/진단/scene·이 문서의 SHA를 `precommit.json`에 저장한다. source 변경 시 실행은 native import 전에 거부한다. base는 자기 물리/자산/준비 입력 pin에 이 추가 pin을 포함하고 종료 시 함께 확인한다. CPU 검사는 native 실행 증거가 아니다.

GPU 실행은 root의 직렬 GPU 인계 후 아래 명령으로 수행한다. 여기서 GPU 인계는 팀 내부 자원 조정이며 추가 사용자 승인 요청을 뜻하지 않는다. 새 출력 폴더만 사용한다. 실행 전 root가 기존 rl38/Isaac Gym의 PYTHONPATH·LD_LIBRARY_PATH 환경을 설정한다.

```bash
taskset -c 0-13 /home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/thumb_rear_surface_v3/support/run_regression.py --out docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/thumb_rear_surface_v3/native_regression_01 --video
```

같은 명령에 `--dry-plan`을 추가하면 1개 job만 출력하고 폴더/native scene을 만들지 않는다. 후보는 동일 표본의 생산 기하와 native body resultant의 법선 성분에 의한 진단이며 접촉쌍 압력·피부 해부학·정책 학습 성과·자유 기타 성공을 인증하지 않는다. GPU 실행과 독립 검수는 root가 후속 진행한다.
