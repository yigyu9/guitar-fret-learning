# 양손 형상 교차 감사 독립 검수

- 검수일: 2026-10-07
- 범위: 새 감사·대표 시점 hull 검증 코드, 저장 결과, README·색인·VISUAL §51.
- 검수자는 native 초기화·physics step을 실행하지 않았고 원자료·구현·기존 검수 문서를 수정하지 않았다.

**요약 판정: 문제없음. 남은 Critical / Warning / Suggestion 없음.**

## 코드·수치 검증

저장 241개 pose의 양손 각 17개 source shape, 289쌍 query와 집계를 대조했다. native contact는 완료 240 step 기록에서 양손 간 0행이며, native shape의 공통 exclusion bit와 로컬 SDK의 충돌 제외 조건이 일치한다. 접촉 행 0은 직접 측정한 반력·힘의 증거가 아니다.

대표 step 0 / 14 / 120 / 161 / 240의 독립 LP 결과는 각각 0 / 0 / 18 / 15 / 18 교차 쌍이다. world 변환, convex-hull halfspace 방향, AABB 선별, 공통 내부구 LP 및 feasibility 검사 범위를 검토했다. 검증 대상은 다섯 시점이며 전체 241 pose의 교차 개수나 최초 교차 시점을 확정하지 않는다.

별도 source STL·저장 body pose로 대표 세 쌍을 재구성했다. step 0과 step 14의 선택 쌍은 공통 내부가 없었고, step 161의 LH:pinky3–RH:palm은 약 6.642477 mm의 양수 내부구 반지름을 얻어 저장 결과와 일치했다. 이는 source convex hull의 부피 교차 증거이며 관통 깊이·PhysX cooked 형상 판정이 아니다. Capsule 다각형 근사에서 교차를 찾지 못한 결과도 정확한 capsule 부재 인증으로 확대하지 않는다.

75개 입력 SHA와 실행 전후 봉인 기록을 대조했다. native filter 감사의 초기화 1회·명시적 step 0회와 LP 검증의 native 0회가 분리되어 있다. 원 signed-query 결과, Python 3.8 실패, 중단된 전체 LP scan 기록은 보존되어 있다.

## 지적과 해소

- 큰 cutoff의 signed query 음수만으로 교차·onset을 확정하는 해석은 독립 hull 검증으로 교정됐다. step 14의 cutoff에 따른 부호 차이와 LP 결과를 근거로 첫 음수 시점을 onset으로 사용하지 않는다.
- VISUAL_REPORT.md:956의 접촉 0행은 양손 간 기록으로 한정됐고, 6.642477 mm 반지름은 step 161 / 0.670833초 표본으로 명시됐다.
- 색인의 verifier 진입점과 VISUAL §51 이미지 링크를 확인했다. 기존 step 120 preview를 재사용하며 새 렌더·물리 실행은 문서화 과정에 추가되지 않았다.

## 최종 문서 검수

README의 교차 표·반지름·cutoff 한계, native filter와 contact의 구분 및 VISUAL §51의 정정 문구가 저장 결과와 일치한다. 현재 질문에는 일부 저장 자세의 source convex hull 교차가 확인됐다고 답할 수 있다. 정확한 onset, 연속 구간 교차 수, cooked 형상 관통 깊이·힘·안정성은 인증하지 않는다. 현재 검수 문서는 동결 가능하다.
