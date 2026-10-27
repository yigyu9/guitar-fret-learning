# 독립 검수

요약 판정: 문제없음. 소비 코드·원본 helper·실제 저장 기록·분석·최종 한국어 문서를 읽기 전용으로 검수했다. 물리/actor/solver/분석/렌더를 재실행하지 않았고 타인 파일을 수정하지 않았다.

- 변경은 source phase1의 adapter ENTRY→EXIT 선택에 원본 접근 시간 조건을 추가한 것이다. source의 현재 song_time_s·effective_target_time·masked first_offset·approach_lead를 읽으며 clock에 dt를 더하거나 source phase/latch/flags/detector/weights를 쓰지 않는다. 원본 step의 callback부터 approach 계산까지 clock이 유지되는 호출 순서를 확인했고 원본 helper 경계 검산 [F,T,T,F,T] 및 AST3.8을 통과했다. phase0 READY와 phase2 원본 clearance/회복gain2,기존 PI/PD/rate/history는 동일하다.
- 저장251개 actor 표본에서 source clock과 command clock이 exact이며 effective target은 해당 scheduled event의 float32 time과 일치한다. first_offset0·lead0.07의 float32 approach_start와 open 조건을 독립 재계산했다. entry/event-key latch와 phase1&&entry_latched&&approach_open의 EXIT 선택이 전 표본에서 exact다. 활성21개,열리기 전 활성0을 확인했으며 구성식 자체의 runtime check만 근거로 삼지 않았다.
- 비교 gain2와 초기 native81/state/PD/bounds/rate/gain 및 PREPARE49개 목표가 exact다. 전체300개 최종 float32 목표·held36·source30 history 역변환,251개 다음 observation history,phase0/1 PI antiwindup 및132개 phase2 이전 목표+2delta/적분 동결을 독립 재계산했다. raw native와 대응하는125개 표본의 실제81각도/pick/ChestDelta/currentG target도 exact다. 기존 adapter ENTRY 반경과 EXIT 거리의 기하 한계는 이번 변경으로 해결됐다고 인증하지 않는다.
- 실제1200 physics steps·151 camera/trace 표본·17개 계약 검사 통과,PREPARE49/PLAY251/HOLD0이며 source terminal/reset은 없다. native 입력1044개와 사전 소스 사본300개 SHA,종료 변경0을 확인했다. 현재1042개 exact와 승인 mainREADME/PLAN 두 문서의 원본 prefix를 대조했다. 분석 직접7개 입력 전후/current exact다.
- raw pulse 합산은 hit/physical hit/accepted release1/1/1,physical release/miss/wrong3/9/2,READY 성공1이다. hit은 control2.783333초,event3,string2,DOWN 및 source timing−33.18190765ms였다. 이전 event2 hit과 다른 음표이며 동등한 timing 개선 비교로 해석하지 않는다. wrong은 초기READY1.033333초/string3와 RECOVER4.666667초/string2다. clearance lifted4.583333초만 관측되고 reached/scheduled completion은0이며 목표 완료false다. 부분 running F1 0.153846과5초 PLAY 유지가 곡 전체 성공을 뜻하지 않는다.
- 독립 p/quaternion·controls 계산은 최소 PREPARE/PLAY25.211255/3.240488mm,기타 최대/종료 위치46.353646/36.279258mm·회전9.074870/6.594995°,범위 참241/300·195/251이며 분석/문서와 일치한다. 회복 gain은 동일해도 초기 경로가 달라졌으므로 회복 결과를 gain 단독 효과로 해석하지 않는다.
- capture151/302PNG SHA·readonly 기록,두 실제MP4 SHA/ffprobe151frames·30fps·5.033333초를 확인했다. 실제5초 손 프레임도 확인했고 최종 README/CHANGED_FILES의 모든 절대 링크가 존재한다. 카메라 마지막 simulation time5초와 MP4 duration을 구별한다.

소비 runner SHA:66e851cedfa9d8e2b24181737c9221aedbc8b2b53180ce0e53b09dc69f2cbd48. wrapper SHA:872565715a26f334223a9c4fac42d10fb8334616014da43bff3bb59e416306f6. 최종 README SHA:6551018c1e2a987264b04a7f46ce8cab535bc5c8620e76150775973797c47ed1. CHANGED_FILES SHA:e4e28bed90e8b9709e7e0ee35c73c534115486dd50041b478b5093d82ffbc2b5.

미해결 Critical/Warning 없음. PASS는 진단의 계약·관측·보존·설명 정합성 판정이며 반복 재현성, cooked 접촉, 정식 actor 자격 또는 전체 연주 성공을 인증하지 않는다. EFFORT 활성화 대안은 별도 실행·검수 범위다.

최종 판정: PASS
