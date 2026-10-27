# 허벅지·왼손 초기 지지 접근 독립 검수

- 검수일: 2026-10-07
- 범위: 초기 후보 생성·실행·저장 분석 코드, 5개 short 실행, canonical render_v2 및 결과 문서.
- 검수자는 native 초기화·physics step을 추가하지 않았으며 이 새 검수 파일만 작성했다.

**요약 판정: 문제없음. 남은 Critical / Warning / Suggestion 없음.**

## 초기 배치·실행 경계

기타는 최초 생성 위치만 이동하고 회전은 유지한다. 이동한 위치를 유지 목표로 두며 실행 중 pose를 덮어쓰지 않는다. 하체/root 물리 고정, 몸통·손가락·오른팔 초기 조건, 기존 PD 및 팔24 PI는 유지된다. 왼쪽 Wrist3+Elbow_x 변경은 기준 ±0.025rad와 기존 C02/native 범위 안이다. calibrated spherical FK 후보를 fresh native 환경에서 첫 step 전에 대조하는 구조를 확인했다.

5개 실행 모두 25 states/trace, 24 controls/contacts, 6 PI 업데이트다. 하체8 body의 전체 state 불변, 실행 중 절대 LA 고정, 기준 raw5의 이전 fixed-lower prefix exact를 저장 원자료로 확인했다. 팔24의 e+2I, 조건부 적분·clip·float32 목표 전달을 재계산했으며 target 오차는 2e−7rad 이내다. 24개 pre-step cable law와 다음 trace의 적용 장력을 대조한 최대 오차는 1.78e−15N 이하였다.

세 50/100/150µm 후보 LA는 1.1018136421554945m, near2µm LA는 1.1018469719600776m이며 기준은 1.1010801317960974m다. 모든 후보의 R_Hip contact는 24 step, LH:palm contact는 0 step이다. near2µm의 초기 source hull gap 1.896279µm는 step24에 38.065514mm로 열린다. 초기 손–손 교차는 없지만 마지막 source 표본에는 1쌍이 있다. 근접 배치나 contact 행은 지지 힘·관통 깊이·안정성 인증이 아니다.

## 지적과 보존 경계

시작/종료 SHA 봉인, 역사 SHA의 병합 전 검사, invalid normal/projection 거절, 기준 raw5 입력 봉인 및 FK 실패 JSON·finally cleanup 보완을 확인했다. 과거 실행을 수정된 계약으로 소급 인증하지 않는다. 실제 실행 SHA와 맞는 search/runner 사본으로 각 버전을 구분했으며 native 재실험은 요구하지 않았다.

canonical comparison_validated.json의 111개 입력 SHA 및 9개 역사 snapshot 해석을 대조했고 5개 측정 row는 기존 두 comparison의 row와 exact다. 새 analyzer는 실제 helper·XML·mesh를 봉인한다. 기존 분석·실패·거절 탐색·원자료는 보존되어 있다.

renderer의 종료 SHA 검사에서 저장 map을 복제하던 문제는 실제 파일 재해시로 교정됐다. canonical v2의 116 입력, 5 helper, 40 asset, 4 output SHA와 실행 직전 producer 사본이 현재 내용과 일치한다. v1 media/manifest는 원 경로와 render_v1에 같은 바이트로 남지만 당시 producer 원문 사본이 없다는 한계가 문서에 공개되어 있다.

## 최종 영상·문서 검수

ffprobe로 H264/yuv420p, 1920×720, 25 frame, 12fps, 2.083333초를 독립 확인했다. v1/v2 영상 byte exact를 확인했고 실제 decoded step0/12/24의 시간·오차·카메라·저장 strap 표시를 직접 봤다. 초기 v2 annotation도 직접 확인했다. 표식은 가림을 무시하는 설명 overlay이며 R_Hip baseline witness 이동 참고점과 후보 palm witness를 구분한다. 재생은 saved pose에 대한 mj_forward이며 native 초기화·physics step 및 mj_step 추가는 없다.

README의 후보별 LA 표와 CHANGED_FILES의 실제 elbow_wrist 설정 경로를 교정 확인했다. 추가된 near2µm의 4관절 delta/초기각 및 기타 world XYZ 이동 표도 저장 search/settings와 일치한다. 결과 수치·VISUAL §52·계획의 미채택 판정이 일치한다. 현재 후보는 왼손 접촉·지속 지지에 실패했고 0.5초 연장이나 안정/연주 성공 채택은 없다. source capsule 근사·cooked collider 차이·첫 solver phase는 미확정이다. 현재 검수 문서는 동결 가능하다.
