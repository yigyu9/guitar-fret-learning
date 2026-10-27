# Native 기타 구현 내부화 검증

현재 Scene(runtime_v15), Controller(runtime_v12), FinalTargetScene(scene_v8)의 실제 의존 모듈과 접촉·촬영·렌더·FK helper를 `guitar_learning/native`로 옮겼다. 과거 실행기의 전체 패키지 감사·CLI는 포함하지 않았다.

자산은 `guitar_learning/assets` 안에 원본의 상대 구조대로 보존했다. 휴머노이드·현재 OM 기타 XML과 각 mesh, 자세·gain·manifest·선택 실행 설정의 원문 바이트는 그대로다. 설정의 파일 경로 값만 실행 시 내부 경로로 대응한다. 미등록 legacy 실행 입력은 즉시 실패한다.

원본→내부 경로와 두 SHA는 `guitar_learning/assets/native_provenance.json`에 기록한다. `verify_provenance()`는 모든 현재 파일을 매 호출 재해시하며, 과거 SHA 검증은 별도의 내부 원문 보존본을 사용한다.

검증: Python 문법/모듈 closure, 실제 Isaac Gym 바인딩을 통한 native import, 구형 패키지 미로드, XML/mesh 내부 경로, 원본 파일 불변, 모든 자산 원문 SHA, 66개 body의 2가지105관절 FK 오차0, lower stable-PD 출력 완전일치를 확인했다. GPU 장면/학습 검증은 상위 작업 기록을 따른다.

`common.pin(extra=...)`의 legacy 증거 입력은 원래 절대경로 key와 내부 CAS 원문 SHA를 보존한다. 대응된 현재 native/assets 파일도 별도로 고정하므로 과거 gate identity와 현행 구현 검증을 함께 유지한다. 미등록 실행 입력은 계속 차단한다.
