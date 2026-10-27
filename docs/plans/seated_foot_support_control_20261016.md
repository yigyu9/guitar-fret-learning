# 접지 V2: 실제 엉덩이 움직임을 반영하는 발 관절 목표

2026-10-16. native_static_v1/analysis_static_v1 보존. static5 완료·14초기검사/무결성/SHA 통과. 하지만 1..5초 왼발 positiveground0%, 오른발56.087%, 양발동시0%. 마지막1초 왼발bottom .494~.507mm/tilt.0077°로평평하지만λ0. 오른ankle bottom최대13.324mm/tilt4.349°, toe최대17.537mm/tilt4.775°. 속도·흔들림은작지만접지실패다. 기타가슴0/회전14.873°/넥5.191°의전체실패도보존.

## 다음 한 단계

기존lower rotational stablePD는gravity보상을포함해현재source+.5mm를유지한다. 또한 Rhip−.08rad지지목표에대한actualhip운동을원래고정ankle목표가worldlevel로상쇄하지않는다. 강도를키우지않고새runtime_v2에서원제어targets의최종command직전10개Knee_x/Ankle_xyz/Toe_x만재계산한다. Hip목표·상체·gain/cap·기타물리는불변.

매60Hz 실제105q/새rootcalibrated FK를사용해양발bottom4가수평worldZ목표를따르도록boundedIK한다. 초기+.5mm에서.5초동안smoothstep으로desired−1.5mm까지내린다. 음의값은힘을유도하는관절목표의source기하일뿐초기/실제state관통주입이아니다. 실제접촉solver가반응하며유한PD·원cap이유지된다. 정상목표는이전source각±.6rad/원본한계;ballnorm160°이내. 다른관절목표소유권은유지. 현발XY는softreference, 초기좌우배치와넥은변경하지않는다. sourceIK잔차/최저점/span·ramp를targets에보존한다.

새run_v2→native_static_v2/static5_v2.json에서5초검사. 접지/안전/형상·전체자세기준은원계획그대로, 결과에맞춰완화하지않는다. actual새wrapper/class/controller검증을위해미수정analyze_v1을보존하고analyze_v2를만든다. 실패와남은기타안정성은따로보고. Rootfixed라양발전체체중지지/자유Root균형성공이라하지않는다. 새PPO/15초손해제 없음.
