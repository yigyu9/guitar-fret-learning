# 손바닥 finite옆면 우선 검색의 첫 실행 계약

이전손바닥goal의Gy=.045/Gz=.0045 고정은사용자의파란영역전체보다좁은임의지점이었다. 이번에는동일finite파란patch에서Gy/Gz투영을허용하고 각경계3mm안쪽을선호한다. GX는그Gy의넥옆면식+clearance.3mm다. 매현재point에서goal을다시계산하며전체patch/대표point margin검사는유지한다. 최초/종료goal도저장한다. 면의필수평행조건은추가하지않는다.

목적함수의palm point weight8,thumb point1,front point.25로변경한다. 기존orientation soft2/wholehull plane50,000·겹침분리50,000/up위반100/각regularizer2는유지한다. source분리penalty는같은face-plane집합의최대값을사용한다. 각hull센터방향에가까운기존face8개에서clearance+1e-10m이상분리가증명된경우만penalty0으로조기반환하고나머지는원dense식으로계산한다. 임의축이나근사hull을쓰지않아기존penalty와동일하다. root가두실제seed와겹침seed에서기존dense penalty대조후검색한다. hard source최종LP교차gate는그대로다.

두seed: wide old_near17/support-plane old_near17. 왼팔12±.15/finger21±.3rad와native/Aug19/C02/oldPDtarget차이교집합·other48/qG/LA/gain/solver유지. 최대80nfev/후보두개로제한한다. Source지지조건은그대로보고한다. 끝난source에겹침없는근접후보가있으면그후보를별도native안전/FK진단으로검토하고기존81목표부터actual5초/스트랩포함영상으로확인한다. source미달을grip성공으로재분류하지않는다.

- [ ] dense-equivalent shortcut와bounds/seed/goal투영 사전검사
- [ ] source후보2개/전형상·거리witness 검사
- [ ] 안전근접후보actual5초/초기값·스트랩영상/접촉위치

새phase: docs/2026-10-12/stability_adapter_2/results/palm_patch_priority_initial_v1. 이전검색/plan/source/outputs를수정하지않고expectedSHA보존복사후newvariant를실행한다. 사용자자율진행지침을따른다. 독립검수도구불가시root검증과구분하고진행한다.
