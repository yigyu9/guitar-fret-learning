# GPU 왼손 손가락의 움직임 비용 제거

사용자 요청으로 기본 GPU 왼손의 **엄지를 포함한21축**에서 움직임 비용을 제거했다. 보상은v7, 표면 추종률은v4다. 현재544상태·8우선순위 입력과39행동·3331단계 상태는 유지한다.

| 항목 | 변경 |
|---|---|
| 손가락 명령 변화 감점 | LH21을 공통 `action_change`에서 제외 |
| 손가락 이동 요청 크기 감쇠 | 추종 품질의 요청속도 제곱항과 거리별 비용 배율 제거 |
| 실제 표면속도 감쇠 | 원하는 접근/감속속도 대비 오차항 제거 |
| 추종 품질 | `exp(-distance/.02)*(1+candidate)`만 사용 |
| 팔·손목 명령 변화 감점 | 원래39축 분모·축당계수 유지; 새 비용 추가 없음 |

고정된 위치·접촉·자세에서 손가락 명령과 표면속도만 바뀌어도 추종 품질과 손가락 명령변화 감점은 변하지 않는다. 손가락의 실제 움직임을 차단/평활화하거나 자동으로 쉬는 자세에 고정하지 않는다. 기존 helper의 `velocity`/`actions` 인자는 호출 호환과 형태 검사만 유지하며 보상값에는 쓰지 않는다. 관측과 진단에는 실제 속도를 계속 제공한다.

거리·접촉 후보·오압현/누락·누적clean 성공·자세 보상·목표 선택/준비창·손가락 균형·PBRS·물리안전과 실패비용은 유지한다. 따라서 손가락이 기타를 이탈시키거나 물리 종료를 일으킨 결과에는 기존 안전 비용이 적용된다. 전체 관절속도50rad/s 초과 종료도 유지한다. 이는 일반적인 손가락 움직임 비용과 구분한다. 제어·가동범위·PD/힘상한·PPO/std는 변경하지 않았다. CPU 왼손과 GPU 오른손의 보상/비용은 변경하지 않았다.

구현은 [추종 보상](/home/ajou/yigyu/3/guitar_learning/gpu/finger_reward.py), [환경의 명령 변화 감점](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py), [단계 복원](/home/ajou/yigyu/3/guitar_learning/song/curriculum_runtime.py)이다. 보상 계약을v7로 분리해 이전v6 저장본의 strict resume를 허용하지 않는다. 같은v7끼리만 모델/양Adam/RNG/3331상태를 복원한다. 과거 성과를 자동 이전하지 않는다.

변경 전9파일은 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261022_before_finger_motion_free_v1/manifest.json)에 원래 경로·SHA와 함께 보관했다. [이전v6 장기 결과](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v6/README.md)의 모델·로그·영상·봉인은 변경하지 않는다. 현재 소스의 새 보상과 과거 동결 소스의 평가 결과를 혼용하지 않는다.

CPU 검증은 [회귀 결과](cpu_regression.json)와 모듈별 `cpu_before_*`/`cpu_after_*` 로그를 따른다. 명령·속도 불변성, 손가락 전축/엄지·반전/혼합 명령, 팔·손목의 원계수와 오른손 원식, 성공/물리 종료·관절 제어·부분reset/H32·단계 복원·구계약 거부를 확인한다. 변경 전 두 모듈은 통과했고, 변경 후 전용34개 검사는 모두 통과했다. 추가12모듈107개 중106개가 통과했으며 기존 `test_left_curriculum_runtime`의512/GPU544 기본값 가정 오류1건이 남았다. 변경 전 coordinator로 같은 실패를 재현하고 해당 test/start.py가 이전v6와 SHA 동일함을 확인했다([기존 실패 분리](existing_failure.json)). 이 무관한 테스트는 수정하지 않았다. 총141개 중140개 통과이며 Python3.8의436파일 AST도 통과했다. [최종 검증 요약](validation_summary.json), [전용 검사](cpu_targeted.json)를 따른다.

이번에는 보상 구현과 CPU 검증을 수행한다. 새 실제GPU 학습·저장/재개·곡 성능·자연스러움 개선을 검증한 결과는 아니다. 다음 학습은 새v7 모델에서 시작한다. [현재 명령](/home/ajou/yigyu/3/docs/2026-10-26/learning_flow/README.md)의 새 출력 경로를 사용하며 이전 결과 디렉토리를 덮어쓰지 않는다.
