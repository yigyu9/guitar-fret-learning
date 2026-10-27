# 독립 검수

요약 판정: 문제없음. 새 gain2 코드 차이·실제 저장 기록·분석·최종 문서를 검수했다. 검수자는 물리/actor/solver/분석/렌더를 재실행하지 않았고 다른 파일을 수정하지 않았다.

- gain1 대비 변경은 source phase2 R9 증분 gain1→2와 기록값뿐이다. local IK delta±0.15 rad→raw increment±0.3 rad이며 누적 actuator goal은 native bounds와 float32 rate3.2 rad/s로 최종 제한한다. READY/APPROACH PI,회복 중 적분 동결,손가락 policy와 source phase/latch/detector/waypoint/음표 시간/weights는 동일하다. 사전 AST3.8 및 경계 검토 PASS.
- gain1과 초기 native81각도·state/PD/bounds/rate/gain이 exact이며 첫150개 최종 목표와 step≤600 native 표본도 exact다. 전체300개 float32 목표 조립/held36/source30 history 역변환,146개 다음 actor observation history를 독립 재계산했다. phase0/1의 조건부 PI antiwindup 및33개 phase2 previous-goal+2delta/적분 동결/entry selector/event key가 exact다. 저장 native와 대응하는73개 actor 표본의 actual81/pick/ChestDelta/currentG target도 직접 대조했다.
- 실제1200 physics steps·151 camera frames·16개 계약 검사 통과,PREPARE49/PLAY146/HOLD105이다. source terminal3.25초(step780) 뒤 goal/history/song clock은 동결되고 같은 native 초기화의 물리 기록은5초까지 계속된다. step780 terminal 추가 표본으로 trace는152개이며 camera151개와 구별한다.
- raw pulse 합산은 target/physical hit/accepted release1/1/1,physical release/miss/wrong5/4/4다. 첫 hit2.483333초/string2·기존 timing45.179844ms는 이전과 동일하다. RECOVER physical release0,lifted2.55초,reached와 scheduled recovery-complete pulse2.95초1회를 확인했다. control3.033333초 source 결과가 phase1로 전이하고 다음3.05초 control부터 phase1 분기가 재개된다. scheduled pulse를 별도 full recovery/곡 완료로 해석하지 않는다.
- wrong4회는 초기READY1.033333초/string3와 회복 뒤phase1의3.166667초/string3,3.2초/string2,3.233333초/string1이다. 이후 추가 인정 hit은 없고 목표 완료false다. 부분 running F1 0.200000은 조기 terminal로 이벤트 기회가 달라진 기록이므로 이전0.153846 대비 성능 향상 근거가 아니다. 최종 문서가 이 범위를 정확히 구별한다.
- 독립 p/quaternion·controls 계산은 최소 PREPARE/PLAY/HOLD25.211255/2.938625/16.182470mm,기타 최대/종료 위치46.353646/23.937022mm·회전9.019638/2.250558°,전체/policy 범위 참182/300·101/146이며 분석표와 일치한다.
- native 입력1038개와 소스 사본294개 SHA를 대조했다. 종료 변경0이며 현재1038개 전부 exact다. 분석 직접7개 입력도 전후/current exact다. capture151개/302PNG SHA·readonly,두 actual MP4 SHA·ffprobe151frames/30fps/5.033333초를 확인했고 실제5초 손 프레임을 보았다. 최종 README/CHANGED_FILES의 절대 링크는 모두 존재한다.

소비 runner SHA:646c6e7d36c333b1fc9bfb0cafa5f9b162a89c1257af493a18204651ebf52357. wrapper SHA:29a3fe89652fa9f96f847216f04cc8804ebe8ea18e6915e5fde2e628ed070c6c. 최종 README SHA:49a582934c1ed994eab177d806f26a7457808fa96d46552f4dd42f9abc44c2e9. CHANGED_FILES SHA:8aa73c532d357b75da2fbc76bf173ee5eb564ad4126d6e100c9cd0002db175ca.

미해결 Critical/Warning 없음. PASS는 이번 진단의 관측·계약·보존·문서 정합성 판정이다. 한 회복 구간의 빠른 완료는 후속 타현/전체 연주 성공·반복 재현성·정식 actor 자격 인증이 아니다. 후속 approach timing 변경은 아직 별도 후보이며 이번 소비 소스에 소급하지 않는다.

최종 판정: PASS
