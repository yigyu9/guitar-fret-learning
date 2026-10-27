# CP157 학습 재개 독립 검수

요약 판정: **문제없음**. [복구 래퍼:5](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/start_long_v2.py:5)는 이전 종료 코드 −11을 확인하고, 실행 전에 CP157의 완료 평가·입력 불변·체크포인트 SHA와 과거 입력 closure를 검사한다. CP157 파일·평가 메타데이터·새 supervisor의 SHA 일치를 직접 확인했으며, 이전 평가의 completed 및 inputs_unchanged도 true다. Critical·미해결 Warning은 없다.

[복구 래퍼:16](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/start_long_v2.py:16)와 [실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/stability_support_nominal_v1/supervisor_long_v2.json)은 같은 interpreter·기존 launch_run_v2·동일 환경으로 CP157에서 새 long_on_v2 출력 경로를 사용한다. 배타적 로그·기록 생성으로 기존 결과를 덮어쓰지 않는다. 마지막 로그 192와 복원 갱신 157을 구분하고, **미저장 갱신 158..192는 복원되지 않으며 새 물리 장면에서 재개**함을 명시한다. supervisor PID 3982607은 실행 기록값이며 이 검수만으로 향후 생존·갱신 성공·완료를 인증하지 않는다.

이번 검수는 위 두 파일과 CP·평가 식별 근거의 읽기 전용 대조다. 추가 native 실행·학습 및 기존 파일 수정은 하지 않았다. 검수 SHA256: start_long_v2.py `0c3dab3a661b1a77f644c4c9ca2bb376f27a2d7a6bd3ca3cc4803aa3592376df`, supervisor_long_v2.json `cef819cde2ef0eeb233fa49d2ec4769cb9fec0d7c5c45a062406cb48b608b0b3`. 이전 SIGSEGV의 원인과 새 실행의 최종 결과는 검수 범위 밖이다.
