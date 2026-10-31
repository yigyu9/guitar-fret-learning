# 손가락 추종 진단 변경 검수

요약 판정: 문제없음. 현재 검수 범위에서 미해결 Critical·Warning·Suggestion 없음.

기준은 Git의 과거 누적 변경 전체가 아니라 `guitar_learning/archive/20261029_before_tracking_diagnostics_v1/`의 변경 직전 원문이다. 실제 변경된 구현 4개와 검사 3개, 기록 안내를 읽었다. 검수자는 구현을 수정하지 않았다.

- `gpu/scene.py`: 이미 활성화된 DOF force sensor의 tensor 획득·갱신·조회만 추가했다. 선택 reset 환경의 낡은 힘은 반환값에서만 0 처리하고 native tensor를 덮어쓰지 않는다.
- `training/rollout.py`: 기존 제어식과 같은 준비 기준·비대칭 범위에서 제한 전 목표를 별도로 계산한다. 기존 `scene.step`과 `environment.substep` 뒤에만 240Hz 표본을 기록한다. 제어·보상·종료 식 변경은 없다.
- `gpu/episode_diagnostics.py`: 요청/적용/실제각을 분리하며 제출 힘과 native 일반화 합력을 구분한다. 센서 비유한값은 관절별 유효 분모에서 제외하고 상세 로그에는 null로 기록한다. 모터 단독 토크·포화로 오인하지 않도록 설명과 제출 가능 mask를 제공한다.
- 환경별 요약은 선택 reset에서만 지우며 H32 수집 경계에서 이어진다. 상세 기록은 reset과 무관하게 대표 환경의 최초 2400개 물리 끝점으로 제한한다. 종료 직전 요약과 pool close의 진행 중 요약을 구분한다. 기존 전체 활성 소스 봉인에 포함되어 과거 체크포인트 검증을 완화하지 않는다.

독립 CPU 검증: 실제 `rl38` Python, CUDA 숨김으로 `test_gpu_finger_motion_diagnostics`, `test_gpu_scene`, `test_gpu_training` 23개 검사 통과(5.396초). 표본 분모·H32 유지·선택 reset·상한 비율·센서 무효값·입력 불변·상세 기록 한도와 episode identity를 확인했다. `git diff --check` 통과.

실제 GPU 검증 근거를 독립 확인했다. large·8환경·H32로 20회 학습(640제어 tick/환경)과 저장본 strict 2회 재개 모두 completed=true·failure=null이다. 실행과 재개 단계 report SHA가 `verification.json`과 일치한다.

- 학습 상세 gzip을 끝까지 읽어 CRC·JSON을 확인했다. 정확히 2400행에서 닫히며 episode_id 0/1을 모두 포함한다. 21축 native sensor가 기록되고 목표가 있는 패드 표본 4449건도 존재한다.
- 기존 `iter_episode_rows`로 공통 메타데이터를 복원한 종료 에피소드 8개 모두 새 진단을 가진다. 종료 에피소드와 8개 진행 중 요약의 물리 표본 합은 20480 = 2560 × 8로 실제 장면 실행량과 일치한다.
- strict 재개의 상세 gzip은 256행이며 종료 에피소드 0개, 진행 중 8개 표본 합 2048 = 256 × 8이다. 짧은 실행도 close에서 유효한 상세·부분 요약을 남긴다.
- 실행 전후 활성 Python 281개 SHA가 모두 동일하다. root의 확대 CPU 72개 통과 기록(`cpu_related.log`, 9.702초)도 확인했다.

검증 범위는 로그 기록·표본 회계·저장·재개 동작이다. 장기 학습 성능 향상이나 모터 단독 토크 측정을 검증한 결과가 아니다.
