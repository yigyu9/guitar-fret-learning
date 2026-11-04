# RH6 수습 독립 검수

검토 대상은 새 도구 learning.py의 AlignedPool.reset이다. 검토한 SHA256은 `133e0b5aaf8ae0f1d815b70b1f4b45f8eb531f0d59d86a8d77c91310ddbee083`이다.

기존 NaturalPool.reset이 정렬 도착 상태의 오른손 미세 오차를 비활성 행동으로 재주입하던 문제를 새 wrapper에서 교정한다. 오른손 6축의 실행 유지 행동과 hold_action, execution_hold_action, last_applied_action, previous_action을 정확히 0으로 맞추고, controller.target과 scene.target은 기준 각도로 맞춘다. 직접 2차원 인덱스로 대상 Tensor를 수정하며 부분 초기화에서는 지정한 환경 행만 수정한다. 마지막에 관측을 다시 만든다. 기존 비활성 손 행동 검사와 물리 DOF, 원본 파일은 변경하지 않는다.

CUDA_VISIBLE_DEVICES를 빈 값으로 두고 새 도구의 --self-test를 독립 실행했으며 종료 코드 0으로 통과했다. 부분 초기화, RH6의 정확한 0, 목표 Tensor 반영, 정책 초기 분산과 floor, strict 저장·복원, factory 예외 복원이 포함된다. 검토 범위에서 추가 차단 결함을 발견하지 못했다.

이 검수에서는 GPU 실행이나 학습을 하지 않았다. 실제 초기 상태의 물리 유지 및 압현 성공은 별도로 실행 중인 oracle_static_v2 결과를 확인해야 한다.
