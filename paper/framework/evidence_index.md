# 프레임워크 초안의 근거 색인

확인일: 2026-11-02. 이 색인은 구현 설명의 근거를 연결한다. 학습 효과·전곡 성공을 입증하는 결과 색인이 아니다. 확인한 파일의 SHA-256은 [소스 확인 기록](source_snapshot.json)에 남긴다. 파일이 바뀌면 해당 절을 재확인하고 새 결과와 이전 실행을 구분한다.

| ID | 설명·연결 절 | 직접 소스 | 해석 범위 |
| --- | --- | --- | --- |
| E1 | Overview, Method 1: 오프라인 전사·운지 배정 | [pipeline.py](../../tab2fingermapping/pipeline.py), [전처리 안내](../../tab2fingermapping/README.md), [기본 번들 manifest](../../data/song_bundles/05_BN2-131-B_solo/manifest.json) | 현재 학습은 검수된 사전 계산 목표를 사용. 원시 파형의 온라인 정책 입력·무수정 전곡 보존을 뜻하지 않음 |
| E2 | Model: 105채널 신체, 자유 기타, 240Hz 물리 | [scene.py](../../guitar_learning/gpu/scene.py), [GPU 기타 manifest](../../guitar_learning/assets/gpu_rigid_guitar_v1/manifest.json) | native 기타는1강체·89형상, 논리 마커39. [기존 자산 설명](../object/README.md)의 역사적 readback과 구분 |
| E3 | Model·Method 4: 상대 좌표, 목표각·변화율·유한 제어 | [control.py](../../guitar_learning/gpu/control.py), [준비 상태 복원](../../guitar_learning/runtime/prepared_reset_v1.py), [v9 기준각](../../guitar_learning/assets/prepared_reset_v1/left_standby_v9.json) | 정책 목표 요청과 실제 각도·속도·힘 구분. 구형81축 JointTargetContract를 현재 계약으로 사용하지 않음 |
| E4 | Model 목표·시간, Method 1·2 | [song/task.py](../../guitar_learning/song/task.py), [canonical.py](../../guitar_learning/score/canonical.py), [타현 계획 읽기](../../guitar_learning/score/strike_goal_compiler.py) | press는 준비 시작, onset은 발음 시작. 줄별 시간·원음 ID·오프셋을 보존. 현재 bundle의 원음 보존과 원오디오 전체 정확도는 별개 |
| E5 | Model 압현, Method 5 | [contact.py](../../guitar_learning/gpu/contact.py), [environment.py](../../guitar_learning/gpu/environment.py), [finger_reward.py](../../guitar_learning/gpu/finger_reward.py) | 패드 표면·기하·몸체 순접촉합력의 대리지표. pair contact나 실제 현 압력·음향으로 해석하지 않음 |
| E6 | Overview, Method 2·3 | [현재 학습 안내](../../guitar_learning/README.md), [FingerSkillPolicy](../../guitar_learning/training/policy.py), [최종 환경](../../guitar_learning/gpu/finger_skill_environment.py) | 기본557상태·일반64/우선8토큰·활성33축, support17/finger16. 과거 좌우 두 Actor 구조와 구분 |
| E7 | Method 5·6: 최종9항·종료 비용 | [finger_skill_environment.py](../../guitar_learning/gpu/finger_skill_environment.py), [관측/평가 누적](../../guitar_learning/gpu/environment.py) | 부모가 계산하는 모든 항을 합산하지 않음. 연속 달성 문턱과 음 전체 유지 구분 |
| E8 | Method 7: PPO·수집·노출 일정 | [ppo.py](../../guitar_learning/training/ppo.py), [rollout.py](../../guitar_learning/training/rollout.py), [runner](../../guitar_learning/training/finger_skill_runner.py), [실행 설정](../../guitar_learning/training/launch.py), [구간 정의](../../guitar_learning/song/finger_phrases.py) | H32는 episode 끝이 아님. 25% 전이 문턱과 실제 구간/전곡 자료 비율 구분 |
| E9 | Method 8: 손가락별613상태 확장 | [finger_progress.py](../../guitar_learning/gpu/finger_progress.py), [실험 진입점](../../guitar_learning/tool/experiments/song_finger_progress.py), [검사 범위](../../docs/2026-11-02/압현실험/손가락별진행상태/README.md) | 기본 진입점과 별도. 여섯 상태는 관측·진단. 조기 목표 노출·준비 보상 변경을 포함. CPU 검사로 학습 성공을 주장하지 않음 |
| E10 | 초기 자세 실제 화면 | [v9 설명](../../docs/2026-11-02/압현성공/initial_pose/초기자세_v9/README.md), [실제 검증](../../docs/2026-11-02/압현성공/initial_pose/초기자세_v9/native_verification.json), [원본 화면](../../docs/2026-11-02/압현성공/initial_pose/초기자세_v9/native_images/adjusted_full.png) | 실제 GPU5초 유지 시점의 장면. 연속 연주·학습 정책 성공의 증거로 사용하지 않음 |

## 설명을 따라 읽을 자료

[코드해설 전체 안내](../../docs/2026-11-02/코드해설/README.md)의 정책·PPO, 물리 장면·제어, 접촉·손가락 보상, 곡·목표 일정 문서를 읽으면 위 소스의 역할을 연결할 수 있다. 요약 문서는 이해를 돕는 자료이며 실제 실행 성과는 해당 실행의 원자료로 별도 확인한다.

## 이번에 반영하지 않은 결과

단일 압현 전수 진단, 목표 전환 학습, 동시 압현의 개별 실행 수치를 이 초안의 성능으로 합치지 않았다. 최종 경로를 선택한 뒤 해당 코드·입력·저장 모델과 평가 조건을 식별하여 Experiment·Result에 반영한다. 따라서 기존 [논문 근거 색인](../evidence_index.md)의 2026-10-19 결과를 이번 작성일의 결과로 갱신하지 않는다.
