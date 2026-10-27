# 파지 확대·압현 감사 독립 검수

**요약 판정: 문제없음.** 발견한 관측범위 Warning1건은 v1을 보존한 v2 정정으로 해결됐다. 미해결 Critical·Warning·Suggestion과 전달 차단 문제는 없다. 검수자는 구현·원자료·타인 보고서를 수정하지 않고 이 보고서와 대응 JSON만 작성했다.

## 오른손 이미지와 파지 수치

`render_pick_grip_v1.py`와 재사용 static renderer를 읽고 여섯 시점 이미지 및 `right_hand_detail.png`를 직접 열어 확인했다. 최신 오른손 평가 episode0의 tick251 마지막 native step1008, 정책4.200초 표본이다. 엄지 주황·검지 파랑·피크 기준점의 노란 반지름2.5mm 표시와 몸통/기타 숨김, source mesh 재생·새 물리0·접촉력/압력 미검증 설명이 명확하다. 새 정책 실행이나 물리 적분 호출은 없다.

여섯 화면의106개 body world pose readback은 위치오차0m·회전오차약5.09e−16rad·시계0이다. 렌더 입력115개의 현재 SHA가 모두 입력 목록에 일치하고, report의7개 이미지 SHA도 일치한다. 실제 피크 형상이나 PhysX cooked 접촉면을 표시한 것으로 확대하지 않는다.

원XML에서 `RH:pick`이 `RH:index2`의 위치[.007,−.048,−.005]m인 geom0/joint0 자식임을 직접 확인했다. 별도의 물리 피크를 엄지/검지가 마찰로 잡는 파지 구조가 아니다.

실제1,680개 표본을 별도 scalar/quaternion 계산으로 재집계했다. RH 손가락21축은 정책 행동에서 제외된 유지 목표이며, 초기 실제 관절값 대비 최대 변화는4.86895442e−5rad=0.00278970539도, 목표 대비 최대오차는.000460386276rad다. 피크 기준점의 검지 상대 위치는 XML과 최대1.456369893e−7m 차이다. 이 수치는 정해 둔 손 모양·고정 자식 관계의 유지 근거이며 물리 파지력·미끄러짐·이탈이나 엄지/검지 사이 피크 접촉을 인증하지 않는다.

추가된 `grip_body_geometry_v1.json`의 손바닥 상대22개 RH body 진단과 README 표현도 대조했다. 초기 대비 최대 원점 이동7.79037126µm·회전0.00514344808도는 관절각과 구분해 기록되었고, 표면 접촉·파지력 주장으로 확대하지 않았다. 이 보충 수치는 생산자 산출물과 문서의 정합성만 확인했으며 별도 재집계하지 않았다.

## 압현 판정·현재 보상

현행 `fretting_v1`·`TaskMeasurement`·skill/timing/actionable wrapper와 이전 `tab2body`의 FretReward를 읽어 비교했다. 최신 `fret_audit_v2.md`의 설명은 코드와 정합한다.

- 현행 candidate는 지정 손가락2/3·목표 현·cell margin·양성 native lambda·witness/거리/높이를 만족하는 feature가 하나 이상 있는지 검사한다. 원점 거리15mm와50ms dwell을 raw candidate의 필수조건으로 혼동하지 않는다.
- 거절 이유는 feature별 중첩 진단이며 정상/오압현/미압현의 배타적 음악 class가 아니다. 목표 candidate False는 아무 접촉 없음과 다른 위치 접촉을 최종 class로 분리하지 않는다. 가슴/팔/허벅지 지지의 raw 거절 이유를 오압현 횟수로 세지 않는다.
- 목표 feature가 참일 때 다른 거절 feature가 있어도 candidate를 veto하지 않는다. 현행 타이밍 보상에는 별도 오압현 감점이 없고, 유지 미달 miss는 창 종료 후1회다. wrong crossing은 압현 오류와 다른 항목이다.
- 이전 FretReward의 금지 압현 veto·NO_PRESS·명시 감점(.35 설정)을 현재 보상이 그대로 사용한다고 설명하지 않는다. 현행 최종 보상은 timing 교체와 첫2초 준비 접촉 항을 따라가며, 계약에 남아 있는 기본 보상 계수만 보고 활성 보상으로 판단하지 않는다.

## 실제 분모와 해결된 Warning

최신 왼손420tick/1,680physics를 독립 재집계했다. 목표 candidate 참963·거짓717, raw evidence28,074·유효 목표 evidence2,658, 목표 참과 거절 evidence 공존963/963, 좁은 넥 진단의 거절 records2,585·목표 참과 공존963/963이 일치한다. 이것은 반복 표본/feature record 수이며 독립 음악 오류 수가 아니다.

v1 문서88행은 **거절된 feature 하위집합의 같은 현 높은 cell 관측0**을 전체 관측 부재로 넓혀 읽힐 수 있었다. 독립 집계에서 valid 여부를 제한하지 않으면 같은2번현·명목 cell8인 runtime-valid `ring3–G:fret7` feature가1,843개/950physics에 존재했다. 최초 `731:34`의 y=.009140713372m는 목표 cell7 하한.009845992366m를.705279mm 넘지만 기존±2mm margin 안이다. 이는 실제8프렛 압현/음향 오류의 증거가 아니다.

`fret_audit_v2.md`와 `correction_v2.json`은 v1·코드·원자료를 보존하고 이 범위와 분모를 정확히 정정했다. 최초 evidence·수치·trace SHA가 독립 결과에 일치하고 README도 v2를 정본으로 연결했다. Warning은 해결됐다.

최초 목표 후보2.991667초의 유효 `718:33`은 실제 `LH:ring3`이며 동시 `718:31`은 pinky3–fret8/최근접3번현이다. 목표 후보 유지와 거절 feature 공존을 보여주지만 실제 뮤팅이나 피치 오류를 인증하지 않는다. 실제 보상 합도 hold2.7044·획득.25·성공1·정밀도.5와 작은 action-change 비용이고 miss/wrong/preparation은0으로 감사와 일치한다.

fret v1 입력13개·v2 정정 입력5개·grip 입력9개 SHA를 재검사해 변경0을 확인했다. 이미지·보고서의 최신 주장과 물리/음향 미검증 범위는 정확하다. 새 실험·학습·성공 재분류 없이 검수를 마쳤으며 이 두 검수 파일을 최종 확정한다.
