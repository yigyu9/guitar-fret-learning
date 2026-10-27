# finger-skill 기본 구조 전환 검증

현재 기본 명령은 `python -m guitar_learning.train --out NEW`다. GPU 왼손 finger-skill v2/J33/561상태/K1을 직접 실행하며 `--learning-family finger-skill`은 생략할 수 있다. 기존 song/CPU/오른손/v24는 `python -m guitar_learning.tool.training.train_legacy`로 분리했다.

- 기존 설정 생성 함수의 AST는 원문과 완전히 동일하다. 기본 선택 및 진입 경로만 변경했다.
- 보상·종료·물리·제어·정책·PPO·평가/영상 함수는 원문을 유지했다. 공유 환경 상속은 활성 코드로 남겼다.
- song 전용 GPU runner는 tool/training/legacy_gpu_runner.py로 이동했다. 프로젝트 루트 계산과 import/caller를 갱신했다.
- 소스 목록은 archive에 진입하기 전에 제외한다. 외장 보관 링크의 읽기 오류가 현행 소스 수집을 막지 않는다. 실제 사용하는 입력의 SHA/읽기 실패는 계속 오류로 처리한다.
- 변경 전 Python/문서537개 원문 SHA를 모두 확인했다. 보관 안내는 ARCHIVE_INFO.md, 원래 프로젝트 README는 README.md로 구분했다.

## 검사 결과

63개 CPU 검사 모듈에서596개 검사 중594개 통과,2개는 외장 저장소 읽기 오류로 완료하지 못했다. skip으로 숨기거나 성공 처리하지 않았다. 기본 CLI/설정/직접 runner 연결, 공유 보상·종료·제어·정책, 구형 실행 분기와 로그 기록 검사를 포함한다. 상세는 cpu_checks.json이며 최초 실행 결과는 cpu_checks_initial.json에 보존했다. 단독 검사에서 발견한 새 테스트의 모듈 mock 범위 문제는 수정 후 재검사했다.

미완료 검사:

1. test_gpu_press_learning.PressLearningTests.test_v22_preserved3331_roundtrip_and_v7_identity_rejection_without_mutation: 외장 저장소로 연결된 archive/20261022_before_targeted_finger_learning_v1/manifest.json을 읽을 수 없음(OSError errno5).
2. test_simple_start.SimpleStartTests.test_supplied_settings_are_permanent_and_pinned_before_native_start: 구형 CPU 경로가 참조하는 paper/initial_pose/lower_body_release_v1/front_facing_pose_v1/source_v9/report.json 읽기 오류. 첫 실행에는 같은 외장 저장소의 inputs_v5/hip_load_bias_report.json에서도 오류가 발생했다.

현행 GPU 경로는 _pins를 실제 입력으로 실행하여655개 경로의 SHA를 모두 재검증했다(input_check.json). 이 검사에서는 native 장면·학습을 시작하지 않았다. 전체 활성 Python510개 문법 검사와 내부 import 경로 검사도 통과했다.

독립 검수는 review.json을 따른다. 이번 작업에서 새 GPU 학습·성능 평가·영상 렌더는 실행하지 않았다. 이전 checkpoint의 소스 SHA 검증을 완화하지 않으므로 변경 전 모델을 현재 트리에 자동 재개/평가하지 않는다.

## 파일

- [현행 실행 안내](/home/ajou/yigyu/3/guitar_learning/README.md)
- [학습 흐름](/home/ajou/yigyu/3/docs/2026-10-26/learning_flow/README.md)
- [보관 안내](/home/ajou/yigyu/3/guitar_learning/archive/20261026_before_finger_skill_default/ARCHIVE_INFO.md)
- [변경 목록](changes.json), [구조 검사](structural_checks.json), [CPU 결과](cpu_checks.json), [현행 입력 검사](input_check.json)
