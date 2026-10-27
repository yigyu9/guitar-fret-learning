# palm_finite_response_v1 독립 검수

검수일: 2026-10-07.
범위: 이번 runner·fitting·capture·analyzer·plotter, trial/raw 및 최종 네 PNG·설명·변경 인덱스·메인 문서의 이번 추가 부분.
검수 과정에서는 native 초기화·physics step·원자료 변경을 하지 않았으며 이 검수 파일만 작성했다.

요약: 문제없음. 0.1초 교정·분리 비교 및 산출물 검증 완료; 지속 지지·기타 안정화·연주 성공은 미달성이다.

판정: Critical 없음 / Warning 없음 / Suggestion 없음.

## 원자료·계산 검증

- 분석의 12계약·21init/504steps와 입력 295개 현재 SHA를 확인했다. 기준 tracking의 이전 0.5초 current 첫 24step 원자료 5배열, 두 camera 실행의 headless 원자료 5배열이 각각 exact다.
- 독립 NumPy/SciPy 재계산에서 B 차이 0, heldout point 예측 차이 0.000522763104835mm, 법선 rotation-vector 차이 0.0000179245°였다. bounded LS 보정 차이는 5.64e−17rad 이하다. 실제 float32 전달 목표 차이를 분모로 사용하며, 작은 heldout 결과를 큰 보정·장기 응답 인증으로 확대하지 않는다.
- 두 tracking의 12업데이트를 별도로 재계산했다. antiwindup mask는 exact, 잔차·적분 차이 ≤7.64e−17, float32 목표는 exact였다. 19 headless 실행의 passive strap pre-step 법칙 차이는 0이다. 신규 B를 기존 feedback Jacobian에 넣지 않았다.
- 실제 연산에 사용하는 context·normal·source geometry·strap helper 및 원자료의 입력 봉인을 확인했다. 모든 import-only 모듈까지 증명했다는 뜻은 아니다. 이전 7phase 보존 검사와 별도 보호 자료 검증은 기록된 검사 범위로 읽는다.

## 최종 미디어·문서

- 네 PNG를 직접 확인했다. Constant와 tracking 곡선은 분리되며 mm/°·0.08m/rad 환산·0~0.1초 축과 저장값이 맞는다. Camera montage는 실제 Gym step0/24의 front/side이며 청록 목표면·주황 facet 점은 같은 시점의 source overlay다; cooked 접촉점 인증이 아니다.
- Plotter는 데이터 읽기/helper import 전에 60입력을 봉인하고 종료 때 재검사한다. 60입력·4출력 SHA가 현재 파일과 일치하며 인덱스 55개 절대 링크의 파일·줄이 유효하다. 최종 README·CHANGED_FILES·메인 계획/README·dated index·VISUAL 1112행 이후의 수치와 해석을 대조했다.
- 평행/native camera 분류/tracking별 contact window/계획 경로의 문구 정정이 반영됐다. Baseline tracking contact는 step1–2, quarter는 step1–4로 구별되고 두 조건의 raw lambda 0을 실제 지지력 0으로 단정하지 않는다.

## 검수한 실행 소스 SHA-256

- run_palm_finite_response.py: `edfc8f1b942b7bcfe9a5954b9cb6e1edd35c0c610fec7dc57ab6d5da3e64e5c5`
- fit_palm_finite_response.py: `d77008a685b6deb44bac03e40d6be0072cd091b1198aaaa29f04847d5cb653c8`
- capture_palm_finite_response.py: `df2eb2dd41dbc5c4c0654ec5079b26ddc9a85d3e46be2dc6e412d21e315c12fd`
- analyze_palm_finite_response.py: `d990dbdf27fdce9a98aea853c3e0173437cbe5549d8e1bf5dede472a0ff39ff2`
- plot_palm_finite_response.py: `442b13226f5be898ca47d095e6d8f21c5d91c03630af6d252b0ad6f53adfe993`

## 최종 범위와 한계

전체 보정은 point14.208→6.671mm지만 기타 최대5.108mm/.969°→8.219mm/1.292°로 악화했다. Quarter tracking은 point9.712mm/source normal gap9.524mm가 남고 기타 차이는 약0.014581mm/0.000453°다. 초기 접촉과 작은 오차 차이는 지속 지지 인증이 아니며 새 bias/LA를 최종 채택하지 않았다. 이 단계의 코드·원자료·산출물 검수는 완료했고 남은 actionable finding 없이 본 기록을 동결한다.
