# 독립 변경 검수

**요약 판정: 문제없음.** 승인된 GPU 왼손 목표 접근·손가락별 출력·PPO 신호 개선 범위에서 새 결함이나 계약 회귀를 발견하지 않았다. 구현과 기존 결과를 수정하지 않고 변경 전 원문과 지정된 변경만 검수했다.

- **Critical:** 없음.
- **Warning:** 이번 코드 변경에 대한 지적 없음.
- **Suggestion:** 없음.

## 코드 근거

- `guitar_learning/gpu/finger_reward.py:84`: 원거리 추종은 `(1+d/.04)^-2*(1+candidate)`이며 기존 상한과 선택기·준비창·분모를 유지한다. 명령 크기/변화·실제 표면속도의 감쇠는 다시 도입하지 않았다. `gpu/environment.py:805`의 LH21 제외와39축 분모도 유지한다.
- `guitar_learning/gpu/environment.py:485`: 접근 potential은 공통 선택기의 tracking slot0·유효 mask·해당 음의 기존 손가락 가중치를 사용한다. 다음/current potential과 terminal0 처리는 유지한다. 목표 교체와 H32를 포함한 할인합 telescoping 검사가 통과했다.
- `guitar_learning/gpu/finger_reward.py:140`: 동시 PIP/DIP60도 초과 항과 대기PIP 상한75도는 양성 자세 품질을 부드럽게 조절한다. 명령·native 범위·PD·독립 제어·접촉/음 성공·물리 종료 기준을 변경하지 않는다.
- `guitar_learning/skills/specialist_policy.py:55`: 명시적인 GPU 왼손 v8/544상태/8슬롯 계약에서만 새 분기를 만든다. `:119`의 네 분기는 각각 자기 관절/자세20열·마스킹된 현재/다음2토큰·shared context를 hidden128/Tanh에 제공한다. `:160`의 출력 재조합은 팔12+엄지5+네 손가락 각4축으로 기존33축 순서와 일치한다. `:132`에서 모든 새 파라미터를 actor optimizer에 포함하며 critic은 별도다. legacy 경로에는 추가 모듈/RNG 소비가 없다.
- `guitar_learning/training/ppo.py:56`: separate 모드는 rollout 전체에서 보상/비용 advantage를 각각 표준화하고 명시적 cost_weight로 결합한 뒤 기존 최종 표준화를 적용한다. joint 모드는 원식과 연산 순서가 같다. `:233`의 identity는 joint 기본 키를 제외해 이전 identity를 보존한다. `training/start.py:64`는 GPU 왼손만 separate/GAEλ.98로 선택한다. critic 목표·손실·KL guard·실패 rollback·cost_weight 업데이트는 기존 로직이다.
- `guitar_learning/training/runner.py:28`과`:72`의 joint 기본 필드 제외, `tests/test_ppo_logging.py:100`의 legacy identity config 전달은 기존 설정/대조 검사를 보존하는 최소 연결 변경이다. `.gitignore`는 이번 생성 압축파일 한 경로만 추가했다.

## 독립 검증

- CPU에서 직접88개 검사를 실행해 모두 통과했다: reward47, actor/specialist19, PPO signal8, PPO logging/GPU settings14. token NaN 마스킹·gradient·전축 모션 불변·상수/0 advantage·정확한 legacy PPO 모델/optimizer/RNG 대조·rollback·같은 계약 복원/구계약 거부를 포함한다. 검수자는 native/GPU/GL을 실행하지 않았다.
- 현재438개 소스 SHA 및 변경 전20개 원문 SHA를 직접 대조했다. 현재 문서4개·새 README·보존/검산 도구를 읽고 실제 검증과 전곡 성과의 한계를 구분하는지 확인했다. 검수 대상 SHA는 `independent_change_review.json`에 기록한다.
- root의 실제 large/1024/H32/seed7 GPU 실행은 fresh8회262,144전이와 재개1회32,768전이다. 두 GDB 정상 종료·report의 정상 close/입력 검사·optimizer8→9를 확인했다. fresh의25종료는 기타 이탈, 재개는0종료다.
- 보존 압축파일의 전체 SHA와 정확한41멤버·원본340,093,062바이트의 모든 멤버 크기/SHA를 검수자가 직접 스트리밍 대조했다. 실제 update 파일 수도8+1개다.
- 복사된 원자료288행을 독립적으로 gzip 끝까지 읽어 CRC/EOF·순서·환경별 배열1024개·update 보상/비용 평균·에피소드25/0 대응을 직접 확인했다. 입력583/584 SHA는 원래 임시 경로에 해당하면 검증된 archive 멤버, 나머지는 현재 실제 입력과 직접 대조했다.
- 압축파일 안의 checkpoint4개를 CPU로 직접 읽었다. 모델 모두 유한하고 fresh 최종→재개 초기의 identity/모델/두Adam/cost_weight/updates/CPU·NumPy·Python·CUDA RNG10항이 정확히 같다. 전체8+1회 이후 네 손가락 head가 모두 갱신됐고 비활성 오른손 encoder/head와 log_std는 그대로다.
- 최종 `verify_training.py`는 원자료·update·입력 pin·새 모델/계약·전체 복원·구v6 거부를 검사한다. root는 원본 임시 출력을 보존 후 해제했고 새 위치에 압축을 풀어 `--runs`로 재검산했다. `archive_replay_verification.log`의 PASS를 확인했다. 도중 PYTHONPATH 누락과 집계 변수 이름 수정 기록을 현재 성공 결과로 잘못 표현하지 않는다.

## 검증 한계

관련 CPU 전체218개 중217개 통과와 기존512/GPU544 가정 실패1개는 root의 개별 로그/집계에 근거한다. `tests/test_left_curriculum_runtime.py:218`의 오래된512 기대는 coordinator 사용 전 실패하며 이번 변경으로 수정하지 않았다. 전체 검사가 통과했다고 주장하지 않는다.

fresh8회는 환경당 약4.27초로 전곡 성능·자연스러움·장기 안전성 평가가 아니다. 이전v6 성과/영상도 v8에 상속하지 않는다. `README.md:47`에 기록한 약132MiB 저장공간으로 새 장기 실행을 시작할 수 있다고 판단하지 않는다. 후속 장기 실행은 공간 확보가 필요하다.

이전v7 정규33파일·v6 정규1511파일 전량 보존은 root의 `prior_preservation_verification.json`을 검토했다. 검수자가 이 대용량 이전 데이터 전체를 반복 재해시한 것으로 표현하지 않는다. 최종 phase 봉인과 정리 기록은 root가 생성한다. 이 검수 기록2파일 작성 뒤 모든 쓰기를 종료한다.
