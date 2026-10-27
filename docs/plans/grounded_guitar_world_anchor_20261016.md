# 자유 기타 지지 V2: 초기 world 오른팔 목표 비교

## 근거와 범위
V1 native_static_v1 actual5초 완료·모든 무결성/양발gate 통과. 전체 회전8.831869°(5°미달), 넥2.941035°(통과),1..5s Chest actualpositive0 / 위팔100%. 기존14.912811°보다 초기기하로개선했지만 움직이는기타를따르는오른팔목표와지속가슴지지는미해결이다. 소스/실험 V1은 보존한다.

V2는 같은 source_v1와동일발/몸통/좌석/gain/cap에서 오른팔 목표frame만 비교한다. 초기native RH:palm world p/r와 RShoulder 실제materialpoint를한번저장해10Hz right12 IK목표로사용한다. 초기넥+.4°를그대로유지하는비교이므로currentGneck보정은명시OFF. human supporttask의RShoulder goal은기존4mm preload를포함한초기worldpoint로저장하고goalvelocity=0으로한다. IK anchor와task anchor는구분한다. Chest는실제G최근접기하/속도를계속사용한다.

기타의pose/velocity/state를변조하거나 G직접힘/부착/고정을쓰지않는다. 인체의고정점constraint도추가하지않는다. 원본finite joint목표·명령rate·PD·caps로실제인체를추종시킨다. 하체 최종Hip/leg소유권은성공runtime6 유지. 기존effort의righttask항만같은nativeJacobian으로차감/새항을더한뒤원본caps를재적용하며,POSITION48와zero8 explicit effort0/lowerstablePD그대로.

## 체크리스트
- [ ] 초기 anchors/4mm차이, 실제point/palm오차·속도, IK잔차, old/newtask·제출105토크를기록.
- [ ] 독립검수와문법검사.
- [ ] actualstatic5s 실행, V1과전체0..5/1..5/4..5 및첫접촉대조.
- [ ] 동일기준으로판정하고실패원인또는재현시험으로이어간다.

성공gate는 grounded_guitar_support_20261016.md의전체15gate를유지한다. static실패중압현/타현/해제/PPO는실행하지않는다. 고정worldgoal자체가접촉/마찰/Chest지지를보장하지않으며그효과를실제원자료로검증한다.
