# guitar_learning 역할별 경로 정리

사용자 승인: “주요 파일들만 남겨두고 … 역할별로 … 하위 디렉토리로 모아줘”. 이 요청 범위에서 수행한다. 기존 물리·학습·strict checkpoint 계약은 변경하지 않는다.

- [x] 현재 AGENTS/README와 경로·import·입력 SHA 계약 확인
- [x] 역할별 이동표 작성, 활성 소스·설정·문서와 CAS index 원문 백업
- [x] 이동 전 실제 native 12스텝 기록
- [x] 원래 경로/SHA를 실행하지 않는 CAS에 보존
- [x] 공통 core/runtime/training 및 imitation/timing/skills/quality로 이동, 현재 import와 경로 갱신
- [x] 보조 문서를 docs/로 이동하고 현행 문서 링크/명령 갱신
- [x] provenance의 현재 SHA 갱신, 원본 SHA 보존
- [x] 전체 CPU 검사·실제 native 물리 비교·현재 링크/소스 경로 검사
- [x] 별도 change-reviewer 검수와 최종 결과 기록

완료 기준: 최상위 Python 79→5, 실제 물리 결과 유지, 전체 CPU 검사 통과, 현재 경로/링크와 입력 pin 유효. music_task/historical_inputs는 주요 과제·원입력 무결성 계약 파일이므로 최상위에 유지한다. 이전 import용 빈 wrapper는 만들지 않는다. 변경 전 증거 파일은 고치지 않고 정확한 원문으로 검증한다.

진행 중 확인: 최초 회귀 호출은 테스트 안의 문자열로 저장된 서브프로세스 import가 이전 경로여서 중단했다. 해당 테스트의 실행 문자열도 새 import로 갱신했다. 신규 CAS 보호 테스트는 현재 index 조회까지 금지했던 보호 범위를 원문/보관본 금지로 수정했다. 제품의 검증 규칙은 그대로다. 최초 로그도 결과 디렉토리에 보존한다.

추가 경로 회귀: 과거 docs 결과 폴더의 isolated_cpu_probe.py를 직접 호출하던 현행 검사 참조를 tests/native_input_probe.py로 분리했다. 원본은 불변이며 사본은 ROOT 깊이와 이동 import2개만 다르다. 보호 검사5개 통과. 최종 전체 호출은 source_manifest.json의382개 Python과 일치하는 소스로 진행한다.

완료: 전체683검사 통과, 실제 native12물리스텝과 동일 환경의 품질 감사 결과 동등, 현재382개 Python SHA 고정, native190/tool18 SHA 검증, 기존 CAS2184버전 보존, 별도 코드 검수 문제없음.
