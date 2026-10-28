# 과거 전문 학습·실험 보관 결과

앞으로 사용하지 않을 과거 전문 학습·실험을 활성 코드에서 분리했다. **활성 Python474개→281개(193개 감소,40.7%)**, 도구139개→40개, 검사/fixture189개→119개다. 현재 J 기본 학습의 연결32파일(구현24+초기화8)과533개 정의·계산은 그대로 유지한다.

원문은 [보관 색인](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_legacy_retirement_v1/ARCHIVE_INDEX.md)에 모았다. [manifest.json](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_legacy_retirement_v1/manifest.json)은 변경 전527파일(활성 Python474개와 당시 문서/해설)의 SHA이며, [retired_files.json](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_legacy_retirement_v1/retired_files.json)은 실제 활성에서 제거한220파일의 원래 위치·SHA·보관 위치다. 전용 설정·FPU 진단 C/공유 라이브러리도 보존했다. 기존 학습 결과·영상·곡 데이터는 정리 대상에서 제외했다.

## 보관과 유지 범위

| 영역 | 처리 |
| --- | --- |
| `local_skills`, `joint`, `song`, `song_reward_v2` 실험 | 초기 전문가·BC·단음 양손·과거 전곡 정책·이전·평가 보관 |
| `transition`, `transition_refinement`, `transition_refinement_runtime_v2`, `contact_recovery` 실험 | 전환 교사·정밀화·구형 회복/자료·FPU 진단 보관 |
| `skills`, `imitation`, `timing` | 과거 전문 학습 패키지 전체 보관 |
| `quality` | 전문 환경·이전·실행6파일 보관, 공용 fretting/strike 측정과 초기화 파일 유지 |
| 과거 전문 CLI·timing 전용 영상 | 학습/평가/시연 실행기와 전용 재생 도구 보관 |
| 과거 전용 검사·설명 | 69개 검사 모듈+1개 fixture, 전문 설명6문서를 구현과 함께 보관 |
| 현재 학습·도구 | J v3 학습·평가·영상·short_finger_learning·곡 입력·로그·현재 손가락/엄지 진단 유지 |
| 기존 song·CPU·오른손 | `train_legacy`와 공용 환경·정책·세션 유지 |
| native·자산·CAS | 모두 유지, provenance·SHA 검증 유지 |

보관한 Python193개는 구현/실행123개와 전용 검사/fixture70개다. 현재 `tool/experiments`에는 `short_finger_learning`만 남아 있다. `quality`에 남은 두 측정 파일은 현재 CPU 곡과 감사 도구의 의존성이 있으므로 과거 전문 환경과 구분했다. 최상위 README·문서 색인·학습/도구 안내·코드 해설도 현재 배치에 맞췄다.

## 공용 기능 분리

기존 song과 손가락 시연이 과거 전문 환경 파일의 준비0초 클래스3개를 사용했다. 이를 `runtime/persistent_environment.py`의 `PreparedFreeGuitarEnvironment`, `PreparedContactEnvironment`, `PreparedPersistentContactEnvironment`로 옮겼다. 준비 시간 계산·접촉 snapshot·MRO·지속 세션 재사용·실패 시 종료 처리는 원문과 같다. 이 분리로 전문 timing→skills→imitation import 연결을 제거했다.

공용 검사를 보관 전용 검사와 구분했다. recorded-session fixture는 기존 `test_training_environment.py`에 모았고, 현재 song·초기 자세·과거 CAS·native/렌더·로그·정책·도구 검사는 유지했다. 혼합 검사에서 과거 전문 CLI와 전문가 preflight 부분만 보관하고 현재 song 계약·초기화 수명주기 검사를 보강했다. 보관본을 현재 import하거나 예전 위치에 facade를 두지 않았다.

## 검증

- 활성281개 Python 구문 검사 통과, 보관된 모듈을 향하는 활성 import0개. 문자열 실행과 외부 Python 참조도 조사했다.
- 기본32파일의 AST 계산은 보관 전과 동일하다. 이번 작업 전 다른 창에서 삭제된 runner 설명4줄은 보존했고, 기존 검증본과의 차이가 그 모듈 설명뿐임을 SHA로 확인했다.
- 공용 초기화34개 검사, 공용 native/곡/로그 등25개 검사와 추가 현재 렌더10개 검사를 통과했다. 별도 검수자가 관련44개를 독립 통과시켰다.
- 전체 CPU117모듈·923개 검사:100모듈 통과·17모듈 실패. 실패 사례와 마지막 예외 문구는 변경 전과 동일하며 **새 실패0개**다. 보관한 검사69모듈 중 기존 실패14개는 해결한 것으로 세지 않는다.
- 내부 native/provenance190파일과 원문 보관527파일·실제 보관220파일의 SHA에 불일치가 없다. native 좌표 probe는 assets107개·원본 parity160개·FK 최대1.56e−16m, renderer106몸체 위치오차0을 확인했다. 이 모델/좌표 검사는 `MUJOCO_GL=disable` 조건이며 새 영상 생성은 아니다.

| 실제 GPU 검사 | 조건 | 학습·저장 결과 |
| --- | --- | --- |
| [새 학습](/home/ajou/yigyu/3/docs/2026-10-28/guitar_legacy_retirement_v1/gpu_smoke/J/report.json) | small/2환경/H8 | 2회·32전이, optimizer2 |
| [동일 소스 재개](/home/ajou/yigyu/3/docs/2026-10-28/guitar_legacy_retirement_v1/gpu_resume/J/report.json) | 같은 설정 | 추가1회·16전이, optimizer3 |
| [독립 전곡 평가](/home/ajou/yigyu/3/docs/2026-10-28/guitar_legacy_retirement_v1/gpu_evaluation/report.json) | small/2환경/전곡 | 2에피소드 모두1969tick 완료 |

두 실행 모두 completed·lifecycle_verified·GPU PhysX·CUDA pipeline·장면 close를 확인했다. changed_inputs/missing_import_pins/cleanup_errors는 빈 배열이다. 최초 계획32전이·전곡 전환 문턱8전이를 재개 뒤에도 유지했고 누적 committed48전이를 복원했다. 짧은 검사는 실행 연결 확인이며 장기 성능 향상을 주장하지 않는다.

전곡 평가는 각 환경의 첫 에피소드를 고정 분모로 사용했고 실패를 분모에서 제외하지 않는다. 실제3952전이 중 선택 에피소드3938전이이며, 물리/손목 실패0·평균 달성1/67음이다. 2회 갱신 모델의 연결 검사로 기존 장기 결과와 성능 비교하지 않는다. [GPU 검증 요약](/home/ajou/yigyu/3/docs/2026-10-28/guitar_legacy_retirement_v1/validation/gpu_verification.json)에 새 학습·재개·평가와 소스 불변을 기록했다.

독립 change-reviewer의 최종 판정은 **문제없음**이다. 공용 초기화 MRO·fixture 계산·보관 SHA·문서·새 GPU학습/재개/평가를 별도 확인했다. [독립 검수](/home/ajou/yigyu/3/docs/2026-10-28/guitar_legacy_retirement_v1/validation/review_findings.md).

## 참고 자료

[현재 코드 읽기 지도](/home/ajou/yigyu/3/guitar_learning/docs/CODE_STRUCTURE.md) · [상세 코드 해설](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/README.md) · [정리 계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_legacy_retirement_20261028.md)

상세 동등성·전체 CPU 원문·입력 SHA·독립 검수는 `validation/`에, 실제 GPU 설정/모델/로그/장면 감사는 `gpu_*` 하위 디렉토리에 있다. 보관으로 활성 소스 목록이 달라져 이전 checkpoint는 현재 트리에서 strict 재개·평가되지 않는다. 기존 pin을 바꾸거나 archive 파일로 대신 검증하지 않는다. 현재 소스에서 새로 저장한 checkpoint만 동일 소스·계약에서 재개한다.
