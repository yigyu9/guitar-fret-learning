# 양팔 정렬 source4: 형상 감사와 float32 여유 보완

source3는native실행없이eligible=false로보존했다. 팔정렬 자체는R.000020mm/.0000036°,L.077903mm/.208837°로통과했고변경은팔24축뿐이다. 실패1은RElbow float32간격6.999998673mm가엄격7mm보다1.327nm작은경계설계였다. 실패2는기존cross-actor helper가실제비활성LH:thumb_pad–guitar를collision_relevant=True로일괄표시해source2대비악화를거부한것이다. actualnativefilter thumb1048575 &G4096=4096≠0이므로원래비활성이다. 기존코드/결과/실패는바꾸지않는다.

## 새source4 단위
- source3의왼팔q는이미허용된오차/활성selfgap을만족하므로exact재사용한다. 이전leftfit max_nfev180종료(success=False)는보존/명시하고최적화수렴성공으로설명하지않는다.
- 오른팔은source3 seed에서RElbow목표7.05mm로여유를두고palm-G/Shoulder.5mm조건을재fit한다. gate7mm를완화하지않는다.
- 사전pin한 native_static_v4/native_properties.json의actualhuman/guitarfilter로각capsule–Gbody source쌍의활성여부를구분한다. actor간disabled row도출력하지만새관련교차gate에서는제외한다. 실제nativepolicy는변경0;같은actor parent/exclude/filter도그대로. chair는helper기존관련성판정을유지하며확인범위를명시한다.
- 모든새state/q/support/upperdelta/upper_target,source2및FOOT기준fullpair/BOX/좌석/지면감사와SHA를새경로에서수행한다. Gpose/몸통/하체/Root/chair/손가락과왼팔seed그대로,onlyright12 추가변경.
- RShoulder 지지는현재capsule distal fraction1.0 부근의측면접촉이다. 기타전면이나proximal30%접촉으로주장하지않는다.

## 체크리스트
- [ ] source4 strict7mm/실제mask/movingarmselfpairs/105limits/zero8/새팔외q와state보존/SHA.
- [ ] 독립검수후V2 worldright/Chest3mm/성공발제어로native5초신규시험.
- [ ] 기존전체15gate유지, 통과시동일설정재현→압현/타현/해제. 아직PPO0.
