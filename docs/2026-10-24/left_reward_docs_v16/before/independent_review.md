# 보상 문서 v8 독립 검수

검수일은 2026-10-23이며 검수자는 change-reviewer `/root/review_reward_docs_v8`다. README와 00~10장, source_audit 및 pre-review 기록을 현행 코드·기존 결과와 대조했다. 파일 수정이나 GPU/native·학습·렌더는 수행하지 않았다.

## 판정

문제없음. Critical·Warning·Suggestion으로 남은 사항은 없다.

- 13개 합산 항과 18개 로그 키, 단계별 양성·음수 가중치가 일치한다.
- v8의 공통 목표 선택 potential, 비용 없는 추종, LH21 행동 변화 제외, 네 자세 위반과 PIP 대역이 일치한다.
- GPU 왼손의 개별 advantage 정규화와 GAE λ0.98을 공용 기본값과 구분한다.
- 누적 달성·오압현 판정, 최근 결과 수치·분모·표본 한계를 정확히 설명한다.
- 별도 v7 해제 실험과 미적용 엄지·오압현 개선안의 범위가 분명하다.
- 현재 소스 438개와 추가 근거 22개의 SHA를 독립 대조했고 문서 링크 누락이 없다.

## 수정 반영

원인별 higher/lower/assignment 시간의 창을 press_s~end_s로 명시하고, 소스 표의 실제 적분 함수명을 substep으로 수정했다. 최종 재검토에서 두 사항이 반영됐음을 확인했다.

## 검수 범위

이 판정은 문서와 현재 구현·기존 증거의 정합성에 대한 것이다. 제안된 엄지 보상이나 오압현 보완의 효과·계수 최적성을 검증한 것이 아니다. 이전 v6 문서 검수 원문은 docs/archive/left_reward_structure_before_v8_20261023/independent_review.md에 보존했다.
