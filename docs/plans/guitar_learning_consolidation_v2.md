# 기본 학습 코드 추가 통합

사용자의 추가 통합 요청에 따라 기본 구현31개를24개로 줄인다. 기존 원문·해설·SHA는 `guitar_learning/archive/20261028_before_learning_consolidation_v2/manifest.json`에 보관했다. 현재 보상·종료·물리·PPO·텐서/악보 의미는 유지하며 구형 체크포인트의 소스 검증은 완화하지 않는다.

## 통합 배치

- `music_task.py`와 `song/wrist_guide.py` → `song/task.py`. CPU 손목 계산의 NumPy·frame은 필요한 함수에서만 import하여 기본 악보 입력 경계를 유지한다.
- `score/events.py` → `score/canonical.py`. 이름이 충돌하는 내부 helper만 구분한다.
- `song/left_curriculum.py`·`gpu_left_curriculum.py` → `song/curriculum.py`. CPU/GPU 클래스·설정·상수는 명시적인 이름으로 구분하며 값과 판정을 합치지 않는다.
- `training/recording.py` → `training/training_log_io.py`. JSON 별칭이 표준 json을 덮지 않도록 정리한다.
- `gpu/geometry.py` → 공통 좌표 계산은 `gpu/control.py`, 표면·압현면·손목 영역은 `gpu/contact.py`. finger_reward와 contact의 순환 참조를 만들지 않는다.
- `native/lower_body_release_v1/common.py` → `native/paths.py`. NumPy는 restore에서 지연 import한다. 과거 출처 original SHA를 유지하고 내부 경로·현재 SHA를 갱신한다.

활성 호출부·도구·검사의 import/patch/현재 소스 참조를 새 경로로 옮긴다. 과거 증거의 원래 경로·고정 SHA는 임의로 바꾸지 않는다. 기존 위치에 facade 파일을 남기지 않는다.

## 체크리스트

- [x] 수정 전 활성 코드·문서와 해설 보관
- [x] 영역별 통합과 활성 참조 갱신
- [x] native provenance와 정적 연결·구문 검사
- [x] 전후 전체 CPU 검사 및 주요 계산·정책·악보 동등성 대조
- [x] 새 소스의 짧은 GPU 학습·엄격 재개
- [x] README·CODE_STRUCTURE·코드해설 재배치 및 링크 갱신
- [x] 별도 change-reviewer 검수·최종 기록

완료: 구현31→24, 정적연결40→32(초기화8), 활성 Python487→480. CPU188모듈1,318건의 결과는 기존157PASS/31실패와 동일, 정책9사례exact, 새GPU32전이+재개16전이 통과. 결과와 최신해설은 docs/2026-10-28/guitar_learning_consolidation_v2/README.md 및 docs/2026-11-02/코드해설/README.md.
