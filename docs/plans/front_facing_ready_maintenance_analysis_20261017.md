# 새유지목표 core 분석9 — 사전계획

2026-10-17 KST. 원analyze8/결과를보존하며새analyze9만작성한다. 실제native/새IK/geometry생산/분석main은독립검수와RootACK전0이다. 다른담당수정은되돌리지않는다.

1. 원core29/baseline·30/action 이름과모든수치문턱/11–16hold/105제출검사/동적기준을유지한다. action은명시baseline필수다.
2. 원Controller요청→oldBody9→16증분→Chestlast→parentMotion중간→새hand유지→foot11→rate/F32/zero8/POS48을분리검사한다. 중간목표는실제제출이라부르지않고원raw를부모raw로치환하지않는다.
3. actual16/e16/직전3836held12/손목G참조를독립재구성한다. gripped desiredfit10µm/.01°와F32(desired−e16)의원bounds/qref/principal 및별도commandFK를분리한다. phase별thumb절대공식/경계held26/나머지92·고정7·다른13/RH21을검사한다.
4. actualrelease_start로개방을측정하고thumb선언량만ramp-awareclosed/open에서재계산한다. 실제15초raw0/901source2mm/손목60mm와재접촉95·동일축5초/새closed오차를원기준으로검사하고원actual10/oldclosed진단도보존한다.
5. Root handoff flatmap의필요subset/모델108/실제schema를SHA고정한다. body bounded/thumb선정의conditional-only·actualdynamic/adoptFalse를유지한다. raw/mesh큰사본은만들지않는다.
6. 실제작은schema+저장IK응답/합성metadata계약CPU로경계·누락·부호·가짜단계순서·채널변조를거부한다. 기존공통math전행재계산은하지않는다. 별도posthold/feet/source/manual/health/fretting은Root AND외부필수다.
