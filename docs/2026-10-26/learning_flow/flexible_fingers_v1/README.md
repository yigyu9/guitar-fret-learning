# 왼손 손가락 제어 v1

2026-10-20 구현·검증. 문서 위치의 날짜는 사용자가 지정한 학습 흐름 디렉토리를 따른다. 기본 `guitar_learning.train --hand left`에 적용한다. 오른손과 기존 전문 경로는 기존 계약이다.

## 변경

| 항목 | 기존 왼손 | 새 기본 왼손 |
| --- | --- | --- |
| LH21 목표 범위 | 준비 기준 중심의 제한 범위 | 원 자산의 관절 하한~상한 전체 |
| 행동0 | 035/v14 기준 목표 | 동일 |
| 목표 속도 한계 | 1.5rad/s | 4rad/s, 정책 변환과 최종 native 제출 모두 |
| 평활화 계수 | 0.2 | 0.45 |
| POSITION stiffness/damping | 20/5 | 검지~새끼12/1.5, 엄지8/1.25 |
| effort 상한 | 엄지4Nm, 나머지20Nm | 동일 |

팔과 다른 활성축의 범위·속도·평활화, 오른손 파지, 하체 제어, 관절 한계와 drive mode, 자유 기타·중력·안전 종료 기준을 유지한다. LH21 PD 변경은 원 준비 상태 복원 후 물리0step에서 한 번만 수행하고 실제 속성·상태·목표 readback을 확인한다. 이후 reset은 새 속성 예상표와 기존 자세를 검증하며 속성을 다시 쓰지 않는다. 원 `native/` 파일은 변경하지 않았다.

엄지를 특정 각도나 넥 접촉점에 고정하지 않는다. 이전 비교 이미지의 B 자세도 적용하지 않았다. 초기035/v14 자세는 그대로다. 정책이 엄지를 굽히고 펴고 움직일 수 있다. 낮춘 강성과 감쇠는 접촉 순응을 위한 시작값이며, 힘 품질이나 인간과 같은 움직임을 검증한 수치는 아니다.

왼손 관측은512차원을 유지하지만 목표 제어 계약에 프로필을 기록하므로 이전512 왼손 checkpoint의 strict resume는 거부한다. 새 프로필로 저장한 checkpoint끼리 재개할 수 있다. 오른손500과 기존 전문 경로는 이전 계약을 따른다.

## 실제 동작 확인

동일한 정규화 입력으로 기존 제어와 새 제어를 각각4초 실행했다. 매60Hz 행동마다240Hz 물리 표본4개를 검사했다. 학습된 연주가 아닌 고정 굽힘·펴짐 진단이며, 끝에서 같은 native 장면을 초기 자세로 reset했다.

| 측정 | 기존 | 새 프로필 |
| --- | ---: | ---: |
| 물리 step / 정책 tick | 960 / 240 | 960 / 240 |
| 첫 검지 목표 증가 | 0.025rad | 0.066667rad |
| 검지 첫 굽힘축 이동 폭 | 11.74도 | 30.76도 |
| 엄지 끝 관절 이동 폭 | 18.72도 | 32.80도 |
| 전체 관절 최대 속도 | 0.778rad/s | 3.046rad/s |
| 기타 최대 변위 | 2.28mm | 3.85mm |
| 기타 최대 회전 | 0.00706rad | 0.01258rad |
| 안전 실패 / 실행 입력 변경 | 0 / 0 | 0 / 0 |

[새 제어 원자료](motion_flexible/report.json), [기존 제어 원자료](motion_legacy/report.json), [초기 복원](motion_flexible/reset_initial.json), [반복 복원](motion_flexible/reset_again.json)을 보존했다. 목표 속도 한계와 실제 관절 속도는 다른 값이다.

[동작 영상](video/finger_motion.mp4)은 실제 Isaac Gym에서 저장한 자세를 원본 메시로 재생한 영상이다. 새 물리 시뮬레이션이나 생성 이미지가 아니다. 1280×720·30fps·121프레임이며 앞/뒤 화면에서 손가락과 엄지의 움직임을 확인했다. [영상 검증](video/report.json)에 원자료·자산 SHA와 프레임 검사를 기록했다.

## 학습·회귀 검증

기본 왼손32전이/PPO1회와 오른손20전이/PPO1회를 실제 실행했다. 왼손 저장 모델을 재개해32전이/PPO1회를 추가했고 누적 업데이트가1→2로 이어졌다. 재개 직후 모델·optimizer·난수·커리큘럼 상태는 이전 저장본과 metadata를 제외하고 동일하다. [최종 검증](verification.json)을 따른다. 전체 검사는 모듈별 별도 프로세스에서 실행하며, 이전 단일 프로세스 실행의 SIGFPE가 해결됐다고 주장하지 않는다. 첫 실행은129개 모듈 중128개·749검사 통과였다. 기존 `test_transition_teacher_proof`의 실제 장면 생성 전 CPU preflight에서 JSON 직렬화 중 SIGFPE가 발생했다. 해당 모듈의 [단독 재시도](module_tests/test_transition_teacher_proof_retry.log)는6검사 모두 통과했다. 합계755개 검사가 통과했지만, 최초 실행이 전부 통과한 것으로 보고하지 않는다. 첫 오류와 집계는 [module_tests_summary.json](module_tests_summary.json)에 그대로 보존했다.

이 검증은 제어 연결·물리 동작·짧은 PPO 실행에 한정된다. 곡 완주, 압현 품질, 보상 단계 진급, 장기 학습 수렴을 달성한 결과는 아니다.

## 구현·보존

- [고정 프로필](/home/ajou/yigyu/3/guitar_learning/core/control.py), [목표 변환](/home/ajou/yigyu/3/guitar_learning/core/control.py), [native 세션](/home/ajou/yigyu/3/guitar_learning/runtime/finger_session.py)
- [실제 동작 기록·재생 도구](/home/ajou/yigyu/3/guitar_learning/tool/demonstration/finger_motion.py), [도구 실행법](/home/ajou/yigyu/3/guitar_learning/tool/README.md)
- [전체 학습 흐름](../README.md), [작업 계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_flexible_fingers_20261020.md)
- 변경 전458개 파일을 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261020_before_flexible_fingers/manifest.json)에 기록했다. 과거2778개 CAS 버전과 보호 대상 원문을 보존하고 현재 소스410개를 [source_manifest.json](source_manifest.json)에 봉인했다. [보존 검사](preservation_verified.json) 참조.
