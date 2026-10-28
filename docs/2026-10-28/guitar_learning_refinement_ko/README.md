# 기본 학습 코드 중복 정제와 한글 주석

2026-10-28. 기본 `finger-skill` 학습의 정적 연결40개 파일(구현31개·패키지 초기화9개)을 정리했다. 각 파일의 역할·읽는 순서와 기존 설명 주석·docstring을 한글로 작성했다. 별도 도구·검사·구형 실험을 포함한 전체487개 파일을 번역한 것은 아니다.

## 정리한 중복

| 중복 | 기존 공용 구현 | 제거한 중복 함수 정의 |
| --- | --- | ---: |
| geometry·scene·초기 입력·과거 증거·악보·로그의 파일 SHA | `training/recording.py::digest` | 7 |
| 전문가·손가락 정책의 가치망 매개변수 선택 | `Policy.value_parameters` | 2 |
| 장면의 자세·속도 행 변환 | `_body_row` | 1 |

기존 함수 이름은 모듈별 별칭으로 유지했다. 파일 해시는1MiB 단위로 읽고, 가치망 매개변수와 상태 직렬화 순서를 유지한다. 새 Python 파일은 추가하지 않았다. 기본 구현31개·정적 연결40개·전체 활성487개라는 파일 수는 직전 통합 후와 같다.

CPU/GPU 단계 가중치는 값이 달라 합치지 않았다. JSON 정규화 해시와 과거 경로를 해석하는 해시도 입력 의미가 달라 유지했다. 각 생성자의 count/device를 캡처하는 짧은 지역 함수는 별도 추상화를 늘리지 않았다. [중복 조사](duplicate_audit.json).

## 한글 설명과 보존 범위

40개 파일 모두 한글 역할 설명을 갖는다. 기존 설명 주석·docstring에 영어만 남은 항목은0개다. 변수·함수명·스키마·로그 키·오류 메시지 등 실행 문자열은 유지했다. [파일별 점검](annotation_audit.json).

33개 파일은 docstring을 제외한 실행 AST가 원문과 같다. 나머지7개는 위 중복10개를 공유하는 변경이다. 기본 입력·행동·보상·종료·물리·PPO 계산은 유지했다. native의 설명이 바뀐4개 파일에 대해 provenance의 현재 `internal_sha256`만 갱신하고 원본 SHA는 보존했다. 출처190개를 다시 검증했다.

수정 전 Python487개·문서28개·provenance1개, 총516개 원문과 SHA는 [변경 전 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_refinement_ko/manifest.json)에 보존했다. 현재 기본 코드의 읽는 순서는 [CODE_STRUCTURE](/home/ajou/yigyu/3/guitar_learning/docs/CODE_STRUCTURE.md)를 따른다.

## 검증 결과

| 검사 | 결과 |
| --- | --- |
| 활성 Python487개 구문 검사 | 통과 |
| 정책9조건의 초기화·RNG·행동·확률·가치 및 가치망 매개변수 순서 | 원본과 정확히 일치 |
| SHA7별칭 × 파일 크기6종(빈 파일·1MiB 경계·2MiB 포함) | 일치 |
| 같은 모듈의 해시 별칭에 대한 독립 patch | 유지 |
| 전체 CPU188모듈·1,318건 | 157모듈 통과, 기존30모듈 실패 유지, 구형 고정 소스 pin 검사1모듈 추가 실패 |
| GPU 새 학습 | 2환경/H8/2회·32전이·optimizer2 완료 |
| 같은 소스의 GPU 엄격 재개 | 추가1회·16전이·optimizer3 완료 |

전체 CPU 검사는 모두 통과한 상태가 아니다. 추가 실패는 `test_contact_recovery_checkpoint_provenance.test_historical_and_live_files_verify_exactly`다. 이 검사는 일회성 구형 체크포인트 이전 도구의 고정 소스 SHA·바이트 수를 현재 파일에 요구한다. 이번 `music_task.py`·`song/task.py`·`score/`의 한글 주석 변경으로 원문 바이트가 달라져 검증이 거부된다. 기존 고정 허용 목록과 테스트를 수정하거나 현재 SHA로 재정의하지 않았다. 나머지30개 실패 모듈은 변경 전과 실패 사례·예외가 같다. [전후 비교](test_comparison.json) · [전체 CPU 출력](cpu_test_output.txt).

새 학습과 재개는 모두 입력 변경·누락 소스 pin·정리 오류0이며 GPU 장면을 정상 종료했다. 이는 코드 연결·저장·복원의 짧은 검사이며 장기 압현 성능 개선을 측정한 결과는 아니다. [GPU 검증](gpu_verification.json) · [정책 동등성](policy_equivalence.json).

주석 변경도 소스 SHA를 바꾼다. 변경 전 체크포인트의 현재 트리 재개·평가·이전은 고정 검증에 의해 거부될 수 있으며, 동일 소스로 생성한 새 체크포인트의 엄격 재개만 확인했다.

검수·재현 자료: [독립 검수](review_findings.md), [수치·검사 요약](validation.json), [검증 시 소스 SHA](source_freeze.json), [작업 계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_refinement_ko_20261028.md).
