# JSON v2 실행 전 독립 검수

판정: **문제없음 / 정적 검수 PASS**. 남은 blocker는 없다. 이 문서는 구현·도구의 사전 검수이며 현재 실행의 완료·성능을 인증하지 않는다.

## 확인한 범위

- `training/json_io.py`와 해당 검사: NumPy Dragon4와 Python `iterencode`를 기본 경로로 사용하고, NumPy는 float를 실제로 기록할 때 import한다. 명시적 custom encoder, JSON 옵션·float key·음수 0·비유한 값 처리·예외 전파가 일관된다. 전역 JSON·Decoder·FP 상태를 바꾸지 않는다.
- `verify_training.py` / `analyze_training.py`: 저장된 300+150+350회와 새 1200회를 연결한다. optimizer offset은 0/300/450/800이고 유효 체인은 2000회·65,536,000전이다. 미저장 8+35+20회·2,064,384전이는 제외한다. 세 재개 지점의 모델·두 optimizer·RNG·curriculum을 정확히 비교하고 3331값 이력을 순서대로 재생한다. 과거 427/427/429개 소스는 각 동결본, 마지막 429개 소스는 현행 파일과 대조한다. 첫 JSON 변경은 4개 writer 수정과 2개 파일 추가, 다음 변경은 helper와 그 검사 2개 수정으로 제한한다.
- 평가·영상 4파일: 초기 0회와 최종 2000회 정책을 각각 strict 복원하고 자체 curriculum을 고정한다. 환경별 첫 곡 1024개만 채점하며, 사전 지정한 최종 환경 0~7은 reset 전에 실제 자세를 기록한다. 선택 규칙·native 종료·기존 메시 자세 재생·프레임/시계/입력 SHA 감사와 복구 체인 전달이 일관된다.
- `finish_workflow.py`: 학습 PID와 시작 시각을 묶어 종료를 기다리고 두 최종 보고서를 읽은 뒤 검증→분석→평가→비교→OSMesa 영상을 직렬 실행한다. 입력 SHA·exclusive 출력·실패 보존 경계를 확인했다.
- `progress.py` / `compare_evaluations.py` / `native_trace.gdb`: global offset 800, 보고서 작성 중 읽기 예외 처리, 음별 원장 재집계와 개선/하락 부호 필터가 맞다. GDB는 실제 신호 번호를 기록하고 `128+signum`을 반환한다.

분석의 all/safe/matched-safe 분모, global 100/250회 cohort, 프로세스별 메모리 잔차 기준선과 300/450/800 경계를 확인했다. 작은 prefix에는 미래 경계를 표시하지 않는다. 수집 통계·고정 정책 평가·음향 성공·독립 seed 일반화를 구분한다.

## 수행한 검사와 한계

JSON helper의 허용된 CPU 검사 8개를 독립 실행해 0.878초에 통과했다. 경계값과 임의 10만 float64 패턴의 유한 값에 대한 텍스트·복원 bit 대조, 옵션·오류·C encoder 미호출·lazy import 검사를 포함한다. 나머지 현재 phase 도구는 실행하지 않고 소스와 기존 인터페이스를 읽어 검수했다.

GPU 학습·평가, native 장면, Renderer, GL 컨텍스트는 실행하지 않았다. 동결 소스·자산·과거 phase를 수정하지 않았으며 이 검수 문서만 작성했다. 현재 1200회 실행·전체 검증·새 평가·영상의 실제 성공은 실행 후 증거로 별도 검수해야 한다. 비정상 FP 상태의 근본원인, 장기 무실패, 학습 성능 향상을 이 사전 검수로 입증하지 않는다.

## 검수한 SHA256

아래 phase 파일은 모두 이 디렉토리 기준이다.

| 파일 | SHA256 |
| --- | --- |
| `guitar_learning/training/json_io.py` | `f9a727744d7db663ae4b1913c7f14561cd344eedb1311034abbad6a12507e3e0` |
| `guitar_learning/tests/test_json_io.py` | `c5f48ea8775a01b459d1f54b4bcae099c65ea6be8e83fa94afa64aa46706b4ce` |
| `verify_training.py` | `ac0421c9724e1f50a9864f2ec65f6253cb928862dc9b1754c0ab1b1eb4434986` |
| `analyze_training.py` | `b54b02e3019f32950dd185aa71f272de4738b1308b65f362d02ade80f5bbcb95` |
| `evaluate_checkpoints.py` | `ae6e3138e87398b77f822401716b1cfce1ef5fa6412ffc3294602e3200e5cde4` |
| `render_video.py` | `5a5e3a1c3317e87c01832e8f3300f76080a14c71ae11edc0970a6e1a83604d6b` |
| `test_video_workflow.py` | `7aeb1375ddc7c7b35a2621b13666f90f1d25888bd183ae14dc4fd4ef74577ec4` |
| `video_workflow.md` | `75c16408a862c27832eb3be3f21b19010448291ffe1aae9e569a71c7ccec2396` |
| `finish_workflow.py` | `b43c6d508760c82f2dc5f56224741f6d5b659d2b8102159ba756728bde1878dc` |
| `progress.py` | `ced19b6799f30af11f330dd156f3a208a9e48e40835f455095754572d6cb2542` |
| `compare_evaluations.py` | `54d309657908b5cb17aa8050bdca6e325865c19f1e70f8b9a6626ec7d6ff90aa` |
| `native_trace.gdb` | `d89a239593fcfa95ee446a0545932da6c55acdd8aa73bf4af7b349c09c6a0fb6` |
