# 다면 grip 접근 진단 독립 검수

검수일: 2026-10-08. 이번 search / source audit / native runner / analyzer / 최종 산출물·문서만 검수했다. 코드·원자료·이전 동결 자료를 수정하거나 native 실행을 추가하지 않았다.

## 요약 판정

**문제없음.** 남은 Critical / Warning / Suggestion 없음. 미완성 접근 진단의 기록·검증·산출물 검수 완료이며 세 면 grip·지속 지지·안정성 성공 판정은 아니다.

## 코드·실행 자료

- v1 source 후보 거절과 v2 중단 자료를 보존하고 v3의 source-clear 두 후보를 별도 접근 진단으로 실행한 범위를 확인했다. v2 중단에 완료 end-seal을 주장하지 않는다. Exp(Bq)는 source FK 가설이며 실제 t0 body pose 대조를 요구한다.
- 최종 LP source 사람–기타 / 양손 / 비인접 왼손 교차, palm-up proxy, fresh FK 오차는 실행 전 hard gate다. 세 면 3 mm 미달은 별도 관측으로 남는다. graph-distance≤2 제외와 capsule 근사 등 source 검사 범위를 cooked clearance로 확대하지 않는다.
- baseline / seed1 / seed2의 3 init·3600 step, 조건별 1200 step / 5초 기록을 확인했다. 초기 81 native DOF는 제출 초기 target과 exact이고 비선택 48 DOF·PD·LA·solver·기타 목표와 전체 초기 기타 상태가 공통이다. 초기 q는 native 한계 안이며 seed1/2의 왼팔 최대 변화 .209931/.207081 rad는 ±.3 안이다.
- 분석 7개 계약과 현재 2386개 입력 SHA를 확인했다. 1201 state/trace/task, 1200 control/contact, 60 Hz constant target 일정 및 151 frame의 두 뷰 coverage 검사를 읽었다. 기존 baseline 첫 24 step 일치는 runner 계약 범위다.
- 저장 body pose에서 기타 위치 오차와 quaternion half-angle cosine을 독립 재계산했다. 위치 곡선 차이는 최대 1.43e−14 mm, 회전 cosine 차이는 4.45e−16 이하이며 named-body 접촉 행·양의 λ step 집계는 exact다.
- 영상 ffprobe 기록은 여섯 파일 모두 151 frame / 30 fps / 5.033333초다. 물리 길이 5초와 endpoint frame을 포함한 컨테이너 길이를 구분한다.

## 수정 사항·최종 미디어

- analyzer의 두 Warning은 해소됐다: frame마다 whole_body/hands 두 항목을 요구하고, raw·초기값·report·admission·capture의 recursive finite 검사와 최종 allow_nan=False를 추가했다. 두 이전 producer 사본 SHA는 당시 analysis 입력과 exact이고 summary/curves는 최종판과 exact다.
- artifact의 전체 151 PNG×두 뷰×세 조건과 font 입력 봉인 누락을 보완했다. 현재 926개 입력 및 두 출력 SHA가 일치하고 시작/끝 봉인 코드와 실행 exit0 기록을 확인했다. 이전 producer·PNG·manifest·실행 기록은 artifacts_attempt_v1에 exact 보존됐다.
- 최종 두 PNG를 직접 확인했다. 곡선 단위·0–5초 범위·세 조건과 실제 hands 카메라의 t=0/5초 프레임 6개가 정확하다. 새 물리나 source 재생 장면이 아니다.
- 무관한 LH 추적점 표 열 제거, 원자료 출처·미완성 진단 설명, nonexistent archive 링크 정정, 날짜별 README:424 / VISUAL §71:1310의 중복 통합을 확인했다. root README / PLAN / VISUAL은 마지막 양의 palm λ121과 λ0 접촉행134를 구분한다. IMPLEMENTATION_FILES의 실제 경로·줄 연결도 확인했다.

## 검수한 주요 소스 SHA256

- search: `d551cf191aae123c5991dcf35d970c2dde62b70a2c3b61808ba78af0ea7682f2`
- fresh audit: `ceda4e2d5350ec0905e12d10326a619a05e83c3429cf3a92e5f533e37b6b3bdb`
- runner: `48b1d333288fdf09cd1657f4204d0bd25f4d6d1b03a39171fc5bd67733be0063`
- analyzer: `d52888cc2109af25d4f821f36e5d48ef0555cbed1e73bbaed9b046792230877e`
- artifact producer: `b67548e39ac4b6ab1c81475d2f4996497cdbd77ac2718a3a74fac167b106185f`

## 한계·다음 계획·동결

seed2의 최대 기타 오차 26.773 mm / 8.323°는 이번 기준 82.047 mm / 10.831°보다 작다. 하지만 초기 세 면 접근은 모두 미달이고, seed2 palm 양의 λ는121 / 전체 행은134까지만 남는다. 종료 thumb/index/middle 행은 연속 지지나 면별 접촉·하중 인증이 아니며 raw λ는 N으로 교정되지 않았다. 5초 전체 source 자기교차·cooked clearance도 인증하지 않는다.

다음 PALM_REFINEMENT 계획은 seed2 주변 국소 범위와 기존 baseline/native box의 교집합, source hard 검사·유한 면 정의·공통 물리 조건을 유지하는 미실행 계획이다. seed2의 최종 안정 자세 채택이나 새 feedback·학습 구현을 주장하지 않는다. 원본 87경로 / Aug19 49 SHA 및 이전 inventory 보존 검사 기록도 확인했다.

이 검수 기록을 동결한다. 이후 완료 체크·최종 source/inventory 봉인은 상위 작업자가 담당한다.
