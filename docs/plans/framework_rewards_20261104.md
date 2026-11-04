# 세 정책의 보상 구현·제안 정리

사용자 요청: 압현·타현·전신제어의 보상 중 구현된 항목을 정리하고, 미구현 항목은 제안한다. 이전 요청을 이어 `paper/framework/정리.txt`의 기존 원문을 보존하고 뒤에 추가한다.

범위: 문서만 변경. 학습 코드·보상 계수·실행 중인 실험·모델은 수정하지 않는다. 새 학습이나 GPU 검사는 실행하지 않는다.

- [x] 압현의 최종9항목과 compact v3 동시 유지 변경을 실제 코드에서 확인.
- [x] 타현의 PPO 보상·진단 지표·right27 별도 실행 연결을 구분하여 조사.
- [x] 전신37축 정책·보상 미구현과 기존 유한 제어·안전 비용을 구분하여 조사.
- [x] 원문 뒤에 구현분과 미구현 제안을 기존 들여쓰기 형식으로 추가.
- [x] 독립 검수 후 원문 prefix와 활성 Python 해시 보존 확인.

확인 범위: 구현과 문서 대응이며 성능·물리 성공에 대한 새 검증이 아니다. 현재 기본 압현, compact v3, 기존 오른손/right27의 서로 다른 보상 경로를 한 구현으로 섞지 않는다.

구현 근거:

- 압현 최종9항·정산·실패 비용: [finger_skill_environment.py](/home/ajou/yigyu/3/guitar_learning/gpu/finger_skill_environment.py:475), [부모 원시 적분](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1048).
- v3 동시 유지 예산: [compact_press_v3.py](/home/ajou/yigyu/3/guitar_learning/gpu/compact_press_v3.py:97).
- 타현 최종 합산: [environment.py](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1302), [준비점 접근](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:941).
- 진단의 준비·분리: [right_strike_environment.py](/home/ajou/yigyu/3/guitar_learning/gpu/right_strike_environment.py:16), [진단을 상속하지 않는 right27 환경](/home/ajou/yigyu/3/guitar_learning/tool/experiments/right27/environment.py:9).
- 전신의 기존 유한 제어: [whole_body_control.py](/home/ajou/yigyu/3/guitar_learning/core/whole_body_control.py:3), [GPU 제어기](/home/ajou/yigyu/3/guitar_learning/gpu/control.py:410), [Root 고정](/home/ajou/yigyu/3/guitar_learning/gpu/scene.py:69).
- 현재 J/compact의 연속 안전 비용 비활성: [finger_skill_environment.py](/home/ajou/yigyu/3/guitar_learning/gpu/finger_skill_environment.py:469). 기존 오른손은 부모의 연속 안전 비용과 실패 비용을 유지하므로 같은 설명을 적용하지 않는다.

조사 메모: right27의 실제 입력은 상태500/목표24이며, 정리.txt 앞부분의 타현 상태440/목표16은 별도 설계다. 현재 전신37축 actor·runner·전용 보상은 없고 고정Root 및 유한 지지 제어가 구현된 상태다.

검수 완료: `press_ppo_audit`가 계수와 구현/제안 구분을 독립 확인했다. 실패 제어 주기의 양의 보상 억제 조건 한 문장을 보완했다. 기존 정리.txt 10,238바이트를 그대로 앞부분에 보존했고 활성 Python345개 SHA256 변경0개를 확인했다. 문서 변경만 수행하여 학습·물리 실행·코드 테스트는 새로 실행하지 않았다.
