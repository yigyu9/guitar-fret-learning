# 최신 오른손 파지와 압현 판정 점검

최신 actionable_preparation 최종 손별 PPO 평가 기록을 읽어 점검했다. 학습·환경·보상·물리 자산은 변경하지 않았고 새 물리 실험도 수행하지 않았다.

## 오른손 확대 이미지

![엄지와 검지 확대](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_pick_fret_audit_v1/right_hand_detail.png)

- 주황=엄지, 파랑=검지, 노랑=피크 기준점 표시용 구(반지름2.5mm). 실제 피크 물체나 형상은 아니다.
- 실제 최신 오른손 평가의 정책4.200초/native step1008이다. 타현 기하 통과 약4.206초 직전 표본이며, 전신·기타를 숨겨 손을 드러낸 소스 시각 mesh 재구성이다. PhysX에서 새로 렌더링/시뮬레이션한 영상이나 접촉면 인증이 아니다.
- [여섯 방향 전체 이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_pick_fret_audit_v1/media_views_v1/right_hand_views.png).
- 표시한6개 화면에서 모든 body world 자세를 readback으로 확인했다. 최대 위치 오차0m·회전 오차약5.09e−16rad, 새 physics step0이다. 실제 렌더링 입력 자산은 최신 평가의 기록된 SHA와 일치했다.

오른손 손가락21축은 PPO39행동에 포함되지 않으며 준비 자세의 고정 목표를 유한 제어로 유지한다. 실제7초·1,680표본에서 초기 실제 관절각 대비 최대 변화는 약0.002790도였다. 목표값 대비 최대 오차는약0.0004604rad다. 따라서 **이 실행에서 정해 둔 손 모양은 잘 유지**되었다고 설명할 수 있다. 매 step 손가락의 실제 상태를 덮어쓰는 구조는 아니다. 보고 관절각과 별개로 손바닥 상대 RH body 자세도 확인했으며, 초기 대비 최대 body 원점 이동은약7.79µm·회전 변화는약0.00514도였다. 이는 표면 접촉·파지력 검사와 구분한다. [제어권](/home/ajou/yigyu/3/guitar_learning/control.py:30), [목표 유지](/home/ajou/yigyu/3/guitar_learning/control.py:126).

그러나 `RH:pick`은 `RH:index2`의 빈 자식 body이며 별도 geom·자유관절이 없다. 검지 상대 위치는 XML의[0.007,-0.048,-0.005]m에 고정되고, 실제 기록과의 최대 차이는약0.146µm다. **엄지·검지가 물리 피크를 눌러 마찰로 잡는 구조는 아니며, 파지력·미끄러짐·피크 이탈은 검증하지 않았다.** 그림의 손 모양을 실제 피크 파지 성공으로 확대하면 안 된다. 기준점이 엄지·검지 접촉면 사이에 있는지도 이 이미지/양성 타현 성공만으로 인증하지 않는다. [자산의 피크 기준점](/home/ajou/yigyu/3/tab2body/assets/smpl_mpl_hands_body.xml:321).

## fret 압현: 이전 보상을 그대로 쓰지 않는다

[상세 코드 비교·실제 표본 감사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_pick_fret_audit_v1/fret_audit_v2.md).

| 구분 | 현재 구현과 한계 |
|---|---|
| 목표 압현 후보 | 지정 손가락2/3 body·목표 현·목표 fret cell·양성 native 접촉·witness/거리/높이를 검사한다. 압력/음향 인증은 아니다. |
| 오압현 | 다른 손가락·현·프렛은 개별 feature의 거절 이유로 남는다. 목표 후보와 동시에 존재해도 전체 성공 후보를 무효화하지 않으며 별도 오압현 감점도 없다. |
| 미압현 | 목표 후보False로 기록한다. 아예 안 누른 것과 다른 곳을 누른 것을 최종 class로 분리하지 않는다. 현재stage1은 시간창 종료까지 단계 유지 성공을 못 하면−0.5다. |

이전 고정 기타의 `FretReward`에는 PRESS/NO_PRESS/DONT_CARE, 금지 압현 veto와 오압현 감점이 있었다. 현재 timing wrapper는 action_change/terminal_failure만 보존하고 timing 보상으로 교체하며, actionable wrapper가 첫2초 접촉 준비 보상을 추가한다. 기존 보상 전체를 그대로 옮긴 구현이 아니다.

실제 최신 왼손 평가에서는 목표 후보가 참인963개240Hz 표본 모두에서, 지지부위를 제외한 다른 LH 손가락 넥 접촉 feature도 공존했다. 예를 들어2.991667초에 목표 약지/2번현7프렛 후보와 새끼손가락/최근접3번현8프렛 접촉이 동시에 있었다. 따라서 기존 목표 접촉 유지율100%는 **오압현 없이 정확한 연주100%**를 의미하지 않는다. 추가 접촉이 실제 소리를 바꾸었는지/뮤팅했는지는 검증하지 않았으며 feature 반복 표본을 독립 음악 오류 횟수로 세지 않았다.

후속 개선이 필요하다면 현재의 목표 양성 후보와 별개로 허용/금지 접촉을 정의하고, 목표 미접촉과 다른 위치 접촉 및 동시 오류를 나눠야 한다. 화음·바레·왼손 넥 지지처럼 허용할 접촉을 먼저 정의해야 하므로 모든 추가 접촉을 일괄 감점하는 것은 적절하지 않다. 이번 요청에서는 판정/보상이나 과거 성공 결과를 바꾸지 않았다.

## 검증·원자료

- 시각화 코드: [render_pick_grip_v1.py](/home/ajou/yigyu/3/guitar_learning/render_pick_grip_v1.py). 기존 전신 renderer를 수정하거나 대체하지 않는 새 확대 시각화 기능이다.
- [시각화 입력·자세 readback](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_pick_fret_audit_v1/media_views_v1/report.json).
- [파지 실제 관절·피크 상대 위치 수치](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_pick_fret_audit_v1/grip_audit_v1.json).
- [압현 feature 예시·분모·입력 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_pick_fret_audit_v1/fret_audit_v1.json).
- 첫 파지 분석에서 `joint_names105` 키를 잘못 가정해 산출 전 중단된 시도는 failed_attempts_v1에 보존했다. 실제105개 이름의 키 `joint_names`로 수정한 분석을 실행했으며 원자료는 변경하지 않았다.

압현 감사의 v1은 원본 보존용이다. 최신 v2는 같은 목표 현의 높은 기하 cell에 관한 관측 범위를 정정했다. 거절된 feature 하위집합에서는0이었으나 전체 좁은 기하 범위에는 유효 판정 feature1,843개가 있었다. 접촉 body는fret7이고 cell 경계±2mm 허용 구간에 걸친 값이므로 실제8프렛 압현이나 음향 오류로 인증하지 않는다. 세부 근거는 correction_v2.json에 보존했다. 목표963표본·다른 넥feature 공존·별도 오압현 veto/감점 부재 결론은 유지된다.

보충: 손바닥 상대 실제 body 자세 변화는 grip_body_geometry_v1.json에 기록했다.
