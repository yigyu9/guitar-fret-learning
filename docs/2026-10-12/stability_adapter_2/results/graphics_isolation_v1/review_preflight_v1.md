# 그래픽 분리 후보 사전 검수

요약 판정: **문제없음(수정 반영 후 사전 코드 검수)**. 기존 native7·runner8과 변경 후보 6파일을 읽기 전용으로 비교했다. 실제 graphics −1 생성·반복 reset·물리 궤적 동일성·CUDA 갱신은 실행 후 확인할 사항이며, EGL SIGSEGV의 완전 방지를 인증하지 않는다.

## Critical

미해결 항목 없음. 최초 probe는 recording=False의 last_step을 영상 평가의 controls.json과 그대로 비교하므로, 영상 평가에서만 추가되는 teacher/source/nominal guard 3필드 때문에 반드시 불일치했다. [수정된 probe:69](/tmp/stability_graphics_isolation_v1/run_graphics_reset_probe_v1.py:69)는 step 전에 teacher nominal·source actions를 복사하고, step 후 raw last_step을 보존하면서 같은 3필드를 추가한다. 기존 [native6:45](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v6.py:45)의 필드 정의·시점과 일치하여 이 구조적 비교 오류는 해결됐다.

## 확인 결과

- [graphics_wrapper:6](/tmp/stability_graphics_isolation_v1/deadline_graphics_v1.py:6)는 기존 GraphicsGym의 하위 클래스다. create_sim에서 학습 −1·기록 평가 0을 전달하고 compute·engine·SimParams는 유지한다. 학습의 render API 조회를 거부하며 실제 전달 인자를 기록한다. [native8:9](/tmp/stability_graphics_isolation_v1/deadline_native_v8.py:9)는 reset 범위에서만 wrapper를 교체하므로 기존 GraphicsGym → StrapForceGuard → InitializationGuard 체인과 타입 검사를 유지한다. 기록 평가의 카메라 경로·제어·물리·보상 메서드는 상속한다.
- [이관 검사:15](/tmp/stability_graphics_isolation_v1/deadline_graphics_migration_v1.py:15)는 원본 schema/digest·PPO 설정·source를 제외한 ABI core의 완전 동일성, 기존 source SHA 유지, 정확히 6개 추가 source만 허용한다. 모델·Adam·RMS·RNG·counter는 변경하지 않고 ABI·digest·resume_scope만 바꾼 새 파일을 배타적으로 저장한다. [runner9:161](/tmp/stability_graphics_isolation_v1/run_deadline_training_v9.py:161)는 이를 기존 strict load와 RNG 복원으로 읽는다. 따라서 변경된 코드 ABI의 제한적 이관이며 원래 ABI 그대로의 resume라고 설명하면 안 된다.
- [runner9:130](/tmp/stability_graphics_isolation_v1/run_deadline_training_v9.py:130)의 평가 child는 runner9를 사용한다. 학습은 비녹화이고 초기·공식 평가는 녹화한다. [224행](/tmp/stability_graphics_isolation_v1/run_deadline_training_v9.py:224)의 5분 복구 checkpoint는 모델/Adam/RMS/RNG/counter와 SHA를 남기며 영상 평가를 실행하지 않는다. 공식 30분 checkpoint와 영상, 11:40 학습 cutoff 및 평가 child timeout은 기존 흐름을 유지한다.
- [probe:42](/tmp/stability_graphics_isolation_v1/run_graphics_reset_probe_v1.py:42)는 기본 60회 reset의 초기 상태·PD·graphics −1·render 조회 0을 검사한 뒤, 고정된 기존 CP의 deterministic trace와 controls 전체를 비교한다. 불일치 시 원자료를 남기고 거부한다. 이는 실행 전 검증 계약이며 아직 실제 통과 판정은 아니다. [CPU 테스트:17](/tmp/stability_graphics_isolation_v1/test_deadline_graphics_v1.py:17)의 9개 테스트 정의와 변경/삭제 source·ABI/config/digest 거부 반례를 확인했다. root가 보고한 CPU 9개 통과와 별개로 검수자는 추가 native·학습을 실행하지 않았다.

## Warning

[runner9:224](/tmp/stability_graphics_isolation_v1/run_deadline_training_v9.py:224)의 저장은 갱신 완료 뒤 수행된다. 수집·optimizer·동기식 평가가 길면 5분/30분 시각을 넘길 수 있다. [64행](/tmp/stability_graphics_isolation_v1/run_deadline_training_v9.py:64)의 cutoff도 제어/optimizer 진입 전 협조적 검사이므로 네이티브 호출을 강제 선점하지 않는다. 결과 문서에는 예정 간격과 실제 저장·종료 시각을 구분하고 강제 마감·무충돌 보장을 주장하지 않는 것이 맞다.

## 검수한 후보 SHA256

| 후보 파일 | SHA256 |
|---|---|
| [deadline_graphics_v1.py](/tmp/stability_graphics_isolation_v1/deadline_graphics_v1.py:1) | `1b277fca96d01ae4a117336cf9ef7b86b01c88d431cf9bab3c54039895df1a6f` |
| [deadline_native_v8.py](/tmp/stability_graphics_isolation_v1/deadline_native_v8.py:1) | `b6c02b25069cce1d53feb6de3f863e3c02996df55d67a2666a6523a2c13f5a7d` |
| [deadline_graphics_migration_v1.py](/tmp/stability_graphics_isolation_v1/deadline_graphics_migration_v1.py:1) | `dd9651d4ccfa056dbd267da8731db3c995683cde59dd6a29f6aceb469e584c1e` |
| [run_deadline_training_v9.py](/tmp/stability_graphics_isolation_v1/run_deadline_training_v9.py:1) | `ee236a724b5a1718416b2fd1d0a845f4c7647713473db6a03f3e8ed803944884` |
| [test_deadline_graphics_v1.py](/tmp/stability_graphics_isolation_v1/test_deadline_graphics_v1.py:1) | `924dedbce5fc452fcc2ba60d20921daafad48ab3a9f4d16ce09dc0b996e70f42` |
| [run_graphics_reset_probe_v1.py](/tmp/stability_graphics_isolation_v1/run_graphics_reset_probe_v1.py:1) | `181ff8d73d361e33cc3224bd2ee8ce6b0122f9d2674b455b1728b1fe6d0163ef` |

소유한 이 검수 파일 외 수정은 없으며 기존 A/main·입력·로그·체크포인트를 변경하지 않았다. 위 SHA는 /tmp 후보 시점 기준이다. 적용·실행 시 실제 A 사본 및 입력 봉인과 대조해야 한다.

적용 대조 완료: 실제 `/home/ajou/yigyu/3/stability_adapter_2/`의 같은 이름 6파일을 다시 읽어 /tmp 후보와 bytes/SHA가 전부 동일함을 확인했다. [실행 전 source 봉인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/source_before_native_v1.json:1)의 6파일 SHA와도 일치한다. 위 후보 링크의 실제 행 번호는 적용된 A 사본에서도 동일하다. 실제 반복 reset 결과의 통과 여부는 사전 검수 범위에 포함하지 않는다.
