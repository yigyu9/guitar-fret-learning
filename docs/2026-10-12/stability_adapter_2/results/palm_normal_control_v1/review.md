# palm_normal_control_v1 독립 검수

검수일: 2026-10-07. 구현·원자료·다른 검수 기록은 수정하지 않았다.
범위: normal task, 저장 FK/첫-step 응답 재계산, runtime cap, runner/analyzer, 그림과 결과 문서.
검수 중 native 초기화·physics 실행·source replay는 0회다.

## 요약 판정

문제없음 — 코드·원자료·수학·그림·문서 검수 통과. 지적은 해소됐고 남은 actionable finding은 없다. 이 검수 기록을 동결한다.

## 정확성·실행 경계

- shortest normal rotation의 방향·영점·180° 예외와 법선축 twist 불변성을 순수 수학으로 확인했다. FK/응답 행렬 독립 차이는 각각 4.46e-15/9.26e-16 이하, heldout 위치 오차는 0.682894µm다.
- 저장 네 조건의 총 24회 업데이트를 다시 계산했다. 적분 rollback/blocked mask/최종 box/잔차 ±0.15rad/rate 1rad/s가 일치했고 float32 전달 차이는 최대 6.15e-8rad로 2e-7rad 허용치 안이다. 초기각 변경과 runtime ±0.3/0.5 확대는 분리돼 있다.
- 8회 초기화·123 explicit physics steps, 짧은 비교의 25상태/24step/6업데이트, Full 이전 raw5 재현 및 camera/headless raw6 일치를 확인했다. 관측된 접촉·기타 동일성을 성공 gate로 강요하지 않는다.
- 현재 analyzer의 11개 계약과 157개 실제 입력 SHA를 확인했다. 소비한 교정 자료·helper를 읽기 전후 봉인하도록 보완한 Warning과 mode/cap/step 검사는 해소됐다. 이전 producer는 정확한 보관본으로 연결하며 과거 사본을 현재 코드로 소급 대체하지 않는다.
- 최종 그림 두 장을 직접 확인했다. 26개 입력 SHA, producer SHA, 두 PNG SHA가 manifest와 일치한다. 단위·같은 시점 source 표식·이전 camera 재사용·절대 경로/줄 링크가 맞다.

## Critical / Warning / Suggestion

Critical: 없음. Warning: 남은 항목 없음. Suggestion: 남은 항목 없음.
해소 확인: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_normal_control_v1/README.md:14`와 `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1062`가 실제 추적점 오차 및 예측 오차로 정정됐다. README:3/18의 camera 실행 1회 포함 총계와 별도 palm-up proxy·해부학적 검증 한계도 명확하다.

## 검수한 현재 소스 SHA256

| 파일 (`/home/ajou/yigyu/3/stability_adapter_2/`) | SHA256 |
|---|---|
| palm_normal_task.py | 011e4ca848e9470ef0735deb4b8e8720dad0e9d7f8ffd696db5c1fd71a22a1a9 |
| fit_palm_normal_response.py | 07ffd810c7bf2610b92d3e077685e02dc42ccb0d07f127ed4a263f084b45a5cc |
| fit_palm_normal_cap.py | 6e158cef0d5c4f42484f03156b9633d1b9d96268498106cff5e094e51f5a8218 |
| run_palm_normal_control.py | dcfed6806cfff13c3a3bd1421da0213ed48946423a013a13480ebe29adfe7cbc |
| analyze_palm_normal_control.py | 0c5dd1bf1672170b942f317d9bed1c394c6e073555692964dbf1933b17ff8ff8 |
| plot_palm_normal_control.py | 19ffe782184710fa9b95adf7182aac39c325068507f33ddb6a4a58fd6bc239db |

## 물리 결과와 검수 한계

Normal ±0.3/0.5의 source 추적점 최대오차는 12.186877/11.963341mm, 면각 최대는 1.280689/1.434722°다. 첫-step 실제 잔차 0.085002/0.100337mm는 선형 예측 0.00004393/0.00002599mm와 달라 외삽 정확성을 인증하지 않는다.
두 확대 조건의 palm 접촉은 step1–2 총 7행/raw lambda0 뒤 사라졌다. 네 조건 기타 body states와 오차 5.107730mm/0.969008°는 같고 전체 trace는 다르다. 지속 지지·기타 안정화·연주 성공으로 판정할 수 없다. ±0.3은 다음 진단 기준이며 cooked 접촉점·해부학적 법선·유효 하중·미래 안전 우선순위 구현을 인증하지 않는다.
