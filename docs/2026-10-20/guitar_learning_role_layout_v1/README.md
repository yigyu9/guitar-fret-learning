# guitar_learning 역할별 재배치

2026-10-20. 최상위에는 주요 진입점과 과제·증거 무결성 파일만 남기고 보조 구현과 단계별 문서를 역할별 하위 디렉토리로 옮겼다. 전체 CPU 검사683개와 실제 native 비교, 경로·입력 SHA 검증을 완료했다.

| 구분 | 이전 | 현재 |
|---|---:|---:|
| 최상위 Python | 79 | 5 |
| 최상위 Markdown | 13 | 3 |
| 최상위 일반 파일 | 93 | 8 |

최상위 Python은 `__init__.py`, `environment.py`, `train_parallel.py`, `music_task.py`, `historical_inputs.py`다. 뒤의 두 파일은 기존 과제 provenance와 원입력 SHA 검증에 연결되어 같은 위치·바이트를 유지했다. 안내 문서는 AGENTS/README/README_CURRENT다.

| 위치 | 역할 | 이동 Python |
|---|---|---:|
| core | 공통 환경·물리 제어·관측·접촉·안전·입력 검증 | 16 |
| runtime | native/headless/persistent 실행·초기화 세션 | 5 |
| training | 정책·PPO·수집·병렬 실행·로그·지표 | 14 |
| imitation | 시연 캡처·BC·초기화·PPO·평가 | 9 |
| timing | 타이밍 목표·시연·학습·평가·이전 | 7 |
| skills | 손별 전문가·스킬 환경·설정·실행 | 12 |
| quality | 접촉 준비·압현/타현·음악 품질·학습·평가 | 11 |
| docs | 단계별 계약·학습·로그·계보 안내 | Markdown10개 |

기존 contact_recovery/song/joint/transition/native/score/tool 등의 위치는 유지했다. 원본 origin_manifest.json은 assets/로 이동하고 역사적 내용은 보존했다. 새 위치에서 실행하는 예는 `python -m guitar_learning.skills.train_specialists --help`다. 현행 import·동적 patch·서브프로세스·도구 소스 pin과 문서 링크를 갱신했고 이전 루트 경로용 wrapper는 추가하지 않았다.

[정확한 이동표](move_map.json) · [현행 실행 안내](/home/ajou/yigyu/3/guitar_learning/README.md) · [이동 전 원문422개](/home/ajou/yigyu/3/guitar_learning/archive/20261020_before_role_layout/manifest.json)

[기존 검증 소스와의 대조](baseline_source_parity.json): 2026-10-19 전체680검사 통과 당시 Python373개가 모두 이번 이동 전 백업과 같은 SHA다. 새 package initializer7개·경로 검사1개·현행 native 검사 지원파일1개를 더해 현재 Python382개다.

## 입력 보존과 물리 동등성

원래 절대 경로/SHA/바이트는 backup 및 실행하지 않는 CAS에 보존했다. 기존 CAS 버전과 기본 SHA는 유지했다. 현재 실행 소스의 pin은 새 실제 위치를 사용한다. 기존 물리·목표·보상·strict checkpoint 검사를 완화하지 않았으며 실제 모델·mesh·native 구현은 그대로다. 기존 출력/체크포인트/실험 증거는 수정하지 않았다.

[실제 native 비교](native_parity.json): 3정책 tick/12물리 step의 전체 상태·105 target·PD·관절/바디 순서·자산·물리 플래그가 정확히 일치했다. 모듈 목록의 차이도 이동표와 새 package initializer뿐이다. 새로운 연주 성과를 주장하는 검사는 아니다.

[동일 원자료 품질 감사 비교](frozen_audit_parity.json): 이동 전 원본을 별도 임시 작업 영역에서 복원하고 동일한 Python 환경으로 실행했다. 생성 시각과 소비 소스 SHA/바이트 기록을 제외한 전체 결과는 정확히 일치했다. 이전 날짜의 다른 Python 환경 결과와 비교 시 초기 좌표 약1e-17 차이가 있어, 같은 환경의 복원 원본으로 최종 비교했다.

## 검증 기록

최종 전체 회귀 검사: **683개 통과**, 458.021초. 검사 전 봉인한 현재 Python382개의 SHA가 검사 후에도 모두 같고 추가/누락 파일은 없다. [전체 로그](full_tests.log)를 보존했다. 새 검사는 중첩 경로의 실제 입력 탐색, 원래 경로/보관본을 읽지 않는 과거 SHA 검증, 프로젝트 외부 작업 디렉토리에서의 새 module CLI 실행을 다룬다. 기존 검사는 실제 spawn·checkpoint·목표/물리/보상 검증을 계속 수행한다.

최초 검사에서 테스트에 저장된 실행 문자열의 이전 import가 드러나 수정했다. 다음 검사에서는 과거 결과 폴더의 isolated_cpu_probe.py를 직접 실행하는 테스트가 드러났다. 해당 역사적 스크립트는 보존하고 현행 tests/native_input_probe.py 사본에서 import2개와 ROOT 깊이만 조정했다. 같은 보호 조건·검증문을 유지했고 관련5검사가 통과했다. 신규 CAS 보호 검사는 현재 index 조회까지 차단했던 보호 조건을 수정했다. 첫 전체 검사는 중단 후 보존했고 수정된 소스로 전체 재검사를 시작했다. 원래 테스트 assert나 제품 검증은 완화하지 않았다.

[독립 검수](review.md) · [현재 소스 SHA](source_manifest.json) · [수정/이동 내역](changed_files.json) · [종합 검증](verification.json)

최종 경로 검증에서 최상위 일반 파일93→8, Python79→5, 이동85개(Python74/Markdown10/원본 manifest1)를 확인했다. native provenance190개와 tool provenance18개의 현재 SHA, backup422개, CAS 객체2134개와 기존2184개 버전의 보존을 검증했다. 활성 캐시는0개다. master_plan의 관련 문서 링크도 갱신했다.
