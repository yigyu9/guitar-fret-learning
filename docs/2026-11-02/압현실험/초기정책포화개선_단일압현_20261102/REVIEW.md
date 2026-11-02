# 독립 검수

요약 판정: **문제없음**. 계획한 `research_v1` 출력 경로와 이번 단독 목표 비교 범위에서 실행 전 필수 수정 사항은 없다. 실제 GPU 실행은 검수자가 하지 않았다.

## 확인한 범위와 결과

- `tools/runtime.py`와 `test_runtime.py`: 최종 CPU 검사 7개 통과. 동일 seed7/17의 원래 정책과 비교해 state_dict 변경은 `core.support_head.bias[1]` 한 원소뿐이다. 초기 결정론 행동도 이 축만 바뀌고, 요청각은 약−0.1도 차이다. std·실제 초기 자세·가동 범위·decoder·forward·load는 보존된다. 학습으로 bias를 바꾸면 ±0.9를 넘어 양쪽 전체 행동 범위를 사용할 수 있다. 추가 검사에서 초기화 metadata와 부모 transition/runtime SHA 계약도 함께 유지됨을 확인했다.
- 새 정책 schema와 초기화 계약, 양쪽 runtime 소스 SHA, 부모 입력 봉인을 유지한다. 구형 정책·다른 조건·엄지 활성화를 거절한다. 문맥 종료 시 부모 전역과 runner patch가 복원된다.
- `tools/run_study.py`: 검증된 부모 process/analyze helper를 재사용한다. GPU 점유 확인과 실행 전후 source 검사를 거친 새 runtime 실행이며 기존 중단 supervisor를 재개하지 않는다. 기술 smoke 네 단계 뒤 두 seed를 각각 fresh 19updates로 학습하고 mean32·mean128·sampled32를 분리 평가한다. 이후 대표 영상 한 쌍과 분석을 남기고 종료하며 자동 장기 연장·전환·곡 학습은 없다.
- baseline 로딩을 CPU에서 실행해 두 seed 모두 622,592경험·mean32임을 확인했다. 같은 예산끼리 비교한다.
- 검증 목록은 중복 없는 528셀이고 모두 `not_tested`다. 전체 검증 성공을 선언하지 않으며 실제 결과 반영은 중지·3번줄·8프렛 한 셀에 한정한다.

## 선택 개선

최초 검수에서 `interpret()`의 registry 평가 경로 고정을 선택 개선으로 보고했다. 실행 전에 실제 `out`을 전달하도록 수정된 것을 확인했으며 이 지적은 해소됐다.

## 아직 확인하지 않은 것

새 wrapper의 실제 GPU 학습·저장·strict 재개·평가·native 렌더와 본학습 성과는 실행 후 별도 확인해야 한다. CPU 통과나 기존 helper 검수는 압현 성공의 증거가 아니다.

## 추가 검수: 실제 새 GPU 기술검증 완료

2026-11-02 감독 시작00:39:27 이후의 `research_v1/jobs` 산출물을 읽기 검수했다. 검수자가 새 GPU 작업을 실행하지 않았다.

- `smoke_train2`: large·1024환경의 GPU PhysX/CUDA pipeline에서 2updates 완료, lifecycle 검증 통과. 실제 `initial.pt`의 새 정책 schema와 초기화 계약이 metadata/settings에 동일하게 저장됐고, 초기 `core.support_head.bias[1]=1.472219467`이었다. 양쪽 runtime 소스 SHA도 기록돼 있다.
- `smoke_resume1`: strict 재개로 1update 추가 완료, 누적 optimizer_updates=3, lifecycle 검증 통과. 원래 smoke final과 재개 initial을 CPU로 직접 읽어 updates=2·identity 동일·model 모든 원소 완전 동일을 확인했다. 학습된 해당 bias=1.472260356이 그대로 복원돼 constructor의 초기값으로 다시 제한되지 않았다.
- `s7_smoke_mean32`: 32개 최초 episode 평가 완료, lifecycle 검증 통과, 입력 변경 및 정리 오류 없음.
- `smoke_render`: 150프레임 native 렌더 완료, lifecycle/source_pins_unchanged/source_checkpoint_pins_validated/native_pixels 모두 true, 입력 변경 및 정리 오류 없음.
- 감독 source_seal 511개를 실제 SHA와 직접 대조해 변경 없음도 확인했다.

이 결과는 새 초기화와 학습·저장·재개·평가·렌더 경로의 **기술 검증 통과**다. `s7_train19` 본학습 시작까지 확인했으며, 본학습 완료 또는 압현 성과 통과로 해석하지 않는다.
