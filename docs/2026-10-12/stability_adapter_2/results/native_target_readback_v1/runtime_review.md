# Native 목표 readback 통합 검수

검수일: 2026-10-07. 대상은 현재 24-step 실행·readback 원자료와 provenance, 새 plotter, 결과·계획·누적 보고서다. 코드와 원자료·기존 동결 검수를 수정하지 않았으며 reviewer native 실행은 없다.

## 요약 판정

**문제없음. 남은 Critical / Warning / Suggestion 없음.** 이번 SDK getter의 저장 목표와 제출 목표가 같다는 관측이며 실제 자세 추종·PD 원인이나 기타 유지 성공의 증명은 아니다.

## 원자료·제어 연결 독립 대조

- 실제 실행 메타는 fresh 1회·24step·exit 0이다. Native 13개·observer 5개 검사와 명시 입력 SHA 180건을 확인했다. 이전 sensor 성공 실행의 states/trace/controls/contacts/hands/queries/leg_torques 7개 배열에서 25/24개 prefix를 직접 대조해 exact를 확인했다.
- 48×105 finite 배열의 순서는 before-step k, after-step k+1의 24쌍이다. 최초 before-step0은 실제 getter 기록이다. 모든 stored/submitted 값이 exact이며 전체 최대 차이는 0 rad로 독립 계산됐다. 이 차이는 관측이고 zero를 통과 gate로 요구하지 않는다.
- 각 pair의 팔24 제출 목표를 해당 controls[k]와 대조했다. 비팔81 목표는 초기 목표로 유지됐고 pair의 제출 목표도 같다. 읽기 전후 상태·목표·PD 불변성은 observer의 각 getter 주변 검사 범위이며, physics step 전후 실제 상태가 같다는 뜻이 아니다. 기존 target-only PALM_RATE와 물리 조건을 재사용한다.
- 기타 최대 위치/회전 오차 6.874400844 mm/1.519676367°와 LH source-center 최대 이탈 47.473935095 mm는 이전 기록과 일치한다. 전달값 불일치는 이 짧은 표본에서 관측되지 않았지만 큰 손 이탈은 남는다.

## 표시 수정·최종 매체

비영 차이를 가릴 수 있던 고정 y축 상한과 소수 한 자리 max 표기를 수정했다. 상한은 `max(0.05, derived_max×1.1)`, 비영 max는 유효숫자로 표시하며 exact 문구는 raw-derived max가 0일 때만 사용한다. 현재 producer의 표시 AST를 0/0.0001/0.125 rad로 독립 실행해 상한·표시값·조건부 문구를 확인했다. 이는 표시 분기 검증이며 실측 원자료 변경이나 새 native trial이 아니다. 최초 producer·PNG·manifest·실행 기록은 보존됐다.

실제 지원 CLI를 새 `/tmp` 출력으로 실행하여 `artifacts_validated`의 2357×1029 PNG byte/RGBA 일치, report/readbacks/native report/producer/output과 embedded 180 SHA를 확인했다. 그림을 직접 열어 rad 단위·48개 before/after 순서·중복 시점·실제 t0 조회와 조건부 관측 문구를 확인했다.

## 최종 문서·동결

README:7·9–17·27, CHANGED_FILES:4–8, VISUAL_REPORT:872·878·880 및 NATIVE_TARGET_READBACK:26·PLAN:969·adapter README:442의 값·조건·현재 validated 경로가 맞는다. 존재하지 않던 별도 analyzer 링크도 삭제됐으며 이번 단계에는 별도 analyzer가 없다.

SDK 목표 roundtrip 일치를 actuator 토크·PD 부족·후기 추종·물리 지지·기타 안정성으로 일반화하지 않는다. 기타 초기 위치 Z+5mm와 기존 회전, 고정 LA 및 PD/solver/제어는 유지됐고 어깨 stiffness 변경은 승인 전이다. 이 소단계 검수를 완료하며 본 runtime_review를 동결한다.
