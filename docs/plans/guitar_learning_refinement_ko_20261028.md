# 기본 학습 코드 중복 정제·한글 주석 (2026-10-28)

범위: 기본 정적 경로40개 Python 파일(구현31개+초기화9개). 사용자 요청에 따라 같은 동작의 중복을 정리하고 설명을 한글로 작성한다. 별도 도구·검사·보관본 전체를 번역하는 작업은 아니다.

## 체크리스트

- [x] 변경 전 원문·문서·native provenance와 SHA 보관
- [x] 중복 함수/블록 조사, 동일 동작만 기존 공용 구현으로 통합
- [x] 구현31개와 패키지 초기화9개의 주석·docstring 한글화
- [x] native 현재 SHA 갱신, original SHA와 물리·자산 유지 확인
- [x] 주석 제거 AST와 수치 동등성·전체 CPU 검사 전후 대조
- [x] 짧은 GPU 학습·엄격 재개 확인
- [x] 독립 change-reviewer 검수와 결과 기록

동일한 이름·모양이라도 CPU/GPU 판정이나 상태 계약이 다른 구현은 임의로 합치지 않는다. schema·로그 키·오류 메시지 등의 실행 데이터 문자열은 번역하지 않는다. 기본 입력·보상·제어·종료·PPO 계산을 유지한다.

변경 전 코드는 `guitar_learning/archive/20261028_before_refinement_ko/`에 보존한다. native 설명을 바꾸는 경우 `assets/native_provenance.json`의 internal_sha256만 현재 원문에 맞추고 original_sha256은 유지한다. 기존 체크포인트의 소스 검증을 완화하지 않는다.

검사 기준은 직전 작업의487개 소스 봉인과188모듈·1,318건 결과(158PASS/기존30실패)다. 새 오류·수치 차이가 없는지 구분해 검증한다.

완료 결과: docs/2026-10-28/guitar_learning_refinement_ko/README.md. 정책9조건 exact·GPU새학습/strictresume 통과. 전체CPU157/188모듈 통과, 기존30실패 유지와 구형 고정소스pin1실패를 명시했다. 고정pin·기존검사는 완화하지 않았다.
