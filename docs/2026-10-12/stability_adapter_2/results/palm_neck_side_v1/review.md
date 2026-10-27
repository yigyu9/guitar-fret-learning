# 파란 neck 측면–왼손 palm 초기 접촉 독립 검수

검수일: 2026-10-07. 검수자는 구현·원자료·기존 동결 기록을 수정하지 않았다.
범위: 이번 source 감사/FK·facet 검색, fresh native probe, 저장자료 검증기,
설명용 이미지 producer와 결과 README·CHANGED_FILES·누적 보고서·계획.

## 요약 판정

**문제없음.** Critical 없음, 미해결 Warning 없음, 미해결 Suggestion 없음.

## 확인 근거

- G→world target 변환, palm-local 점·법선 변환, 제한된 왼팔 FK와 facet 내부점/twist 계산을 읽기 검토했다. 초기각은 native 한계와 C02 기준 ±0.3 rad 교집합에 제한되며 나머지 초기 조건을 보존한다.
- Face-referenced neck 형상과 기존 all-vertex hull은 서로 다른 source 표현이다. 새로운 face-used 검사도 PhysX cooked collider 인증이 아니다. Signed 공통 내부구 LP의 중심 이동·mm 단위·중복 plane 처리와 독립 box 사례를 확인했다; 반환 반지름은 관통 깊이가 아니다.
- 저장 fresh 결과의 FK 일치·PD·절대 LA·상태 불변 계약과 첫 1-step/24-step prefix를 확인했다. 이번 probe는 초기 native PD 목표를 유지하는 진단이며 기존 팔 PI/새 palm feedback의 성능 비교가 아니다. 실행 중 pose 재주입이나 기타 고정은 없다.
- 첫 완료 step의 LH:palm–guitar 접촉 4점은 모두 raw λ=0이다. Step 2–24에는 해당 접촉이 없고 최대 기타 목표 오차는 5.107730 mm / 0.969008°다. 초기 접촉을 하중 지지·연속 접촉·안정화 성공으로 해석하지 않는다.
- 저장자료 검증기 13개 통과 항목과 초기화 11회·명시적 physics step 27회 집계를 대조했다. 검증 기록은 원본 87개 stat, Aug19 자료 49개 SHA, 이전 phase 613개 inventory 보존을 포함한다. 실패 및 역사 producer 증거는 별도로 유지된다.
- Front/side 비교 PNG를 직접 확인했다. Overlay의 입력 11개·출력 10개·producer SHA가 실제 파일과 일치한다. 청록 다각형은 가려진 면에도 보이는 설명용 투영이며, 빨간 표식은 저장 step-1 기타 pose로 변환한 raw 접촉 위치다. 별도 접촉 측정이나 cooked 형상 렌더가 아니다.
- README·인덱스의 절대 경로와 실제 줄 범위, fresh source gap 0.049807 mm, 면적·단위·실행 범위·접촉 해석을 확인했다. CPU PhysX/GPU pipeline 비활성화와 graphics backend identity 미확인을 구별한다.

## 지적 및 해소

- Warning: 초기 helper SHA 누락은 새 감사의 입력 봉인과 역사 producer 보존으로 보완됐다. 생산 당시 누락된 SHA를 소급 증명했다고 표현하지 않는다.
- Warning: probe 실패 집계는 현재 candidate index를 기준으로 계산해 중복 집계를 제거했다.
- Suggestion: source-proxy 명칭, CLI `--baseline`/`--search` 상호 배타·필수 조건을 반영했다. 혼합 입력 exit 2 로그는 native 초기화/물리 실행 없이 거절된 증거다.
- 문서 정정: 772.75 mm²는 palm facet 면적, 기존 6/10 mm 조건은 face-used 통과 후 각 native 1-step 진단, 77.049519 mm는 palm hull–blue polygon 직접 거리다. 기존 all-vertex neck hull과 혼동하지 않는다.

## 최종 검수

현재 결과·문서·이미지에 남은 finding은 없다. 검수자는 추가 native 실행이나 source query를 하지 않았다. 지속 palm 지지와 기타 안정성은 미달이며 후속 bounded FK/제어 진단은 아직 이번 결과에 포함되지 않는다. 이 검수 기록은 동결 가능하다.
