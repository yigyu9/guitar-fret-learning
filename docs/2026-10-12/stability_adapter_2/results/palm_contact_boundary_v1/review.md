# palm_contact_boundary_v1 독립 검수

검수일: 2026-10-07.
범위: 새 analyzer·trial·네 native run, 재사용 두 조건 및 최종 plotter/그림/설명/메인 추가 문서.
저장 자료만 읽고 계산했다. native 실행·원자료·코드 수정은 하지 않았으며 이 검수 기록만 작성했다.

요약: 문제없음. 이산 alpha 접촉 경계·좌표·원자료 계약 검증 완료; 지속 지지·기타 안정화는 미달성이다.

판정: Critical 없음 / Warning 해소 / Suggestion 없음. 남은 actionable finding은 없다.

## 검증과 수정 확인

- 새 .30/.35/.40/.45는 4init/96steps이며 이전 .25/.50은 저장 자료를 재사용했다. 최종 7계약·247입력 봉인과 같은 초기 조건·상수 목표 범위를 확인했다.
- Alpha identity 누락 Warning을 해소했다. analyzer:28–29,38–51은 여섯 후보를 미리 봉인하고 baseline bias+alpha×fit delta를 candidate/report와 exact 대조하며 실제 float32 목표 24개도 exact 검증한다. 최종 분석 SHA는 `674ef15538bf98cbc92378f0e71a3545a190f73f914480222ea87989fbe41a98`다.
- 독립 계산에서 실제 bias와 전달 목표 차이 0, WORLD actual-minus-configured-goal 벡터 차이 ≤1.71e−16, native 실제 t0 대비 벡터 차이 0, 위치 trace 차이 ≤8.68e−19m, 다섯 scalar secant 차이 ≤4.45e−15였다. 회전은 `(R_actual R_goal^-1)`의 world rotvec이며 Euler/관절좌표 차가 아니다.
- Configured 목표와 native t0 float32 readback 차이를 별도로 남기는 수정이 맞다. 이전 두 실패는 native 0회 후처리 실패로 보존되었고 물리 재실행으로 처리하지 않는다.
- Canonical PNG를 직접 확인했다. 기타 설정 목표 오차/실제 t0 drift·source normal gap·raw lambda의 단위와 시점이 맞으며 t0 lambda를 인위적으로 삽입하지 않는다. Plot 14입력·출력 SHA와 인덱스 파일/줄 링크가 일치한다.
- README:24–29의 기존 canonical 출력 경로 Warning은 새 `/tmp/stability2_boundary_replot_01` 및 no-overwrite 안내로 해소됐다. 누적 VISUAL §64와 메인 추가 문서가 새 네 조건/재사용 두 조건 및 한계를 정확히 구분한다.

## 검수 소스 SHA-256

- analyze_palm_contact_boundary.py: `771fdf1225e5b50f87bdd868d152fce43c2722c529065a505b8c265ecd9d58bd`
- plot_palm_contact_boundary.py: `e44a1a1bcc2a056fdb8f14b3d67a98b760ed14fc90f98c66e9c16bd127b8d6ff`

## 최종 범위와 한계

.40은 양의 palm raw lambda가 없고 .45는 step2 두 행만 있다. 기타 최대 오차는 5.047986mm/.967032°에서 5.341201mm/1.006166°로 커졌다. 이 샘플의 경계는 유일한 임계값·원인·지지력(N)·지속 지지 인증이 아니며 scalar secant를 12축 feedback으로 해석하지 않는다. 새 bias 채택 없이 이번 분석·산출물 검수를 완료했고 본 기록을 동결한다.

## 역사적 plot producer 보존 한계 추가 확인

`artifacts/`의 복원 producer SHA `5a4a05cea85faf203090b9c24d8a500c2bc0ecd8a91b8700729beed952b5758a`, `artifacts_validated_attempt_v1/`의 `23443ddb5e8373086828bd2d08dcf4ab9855de7c212b48c2658d690c37113963`는 각 당시 manifest와 exact다. `artifacts_attempt_v1/`의 manifest가 요구하는 `f90ddd64aa6d64496ab3d5e11d28898d784b14bf7d4acaba4cfd61b197869e60` 원문은 미보관·복원 불가로 남았다; 추정 producer를 만들어 일치한다고 주장하지 않는다. 해당 과거 초안의 코드 재현성은 인증하지 않으며, 현재 canonical `artifacts_validated/`의 source/input/output exact 검증과 구분한다. 이 보존 한계는 현재 수치·물리 진행을 무효화하지 않는다. 추가 확인을 포함해 기록을 최종 동결한다.
