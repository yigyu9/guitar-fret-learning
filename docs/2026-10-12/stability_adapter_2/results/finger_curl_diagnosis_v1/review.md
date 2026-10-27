# 손가락 굽힘 저장자료 진단 독립 검수

요약 판정: **문제없음**. 소유권은 이 review뿐이며 검수자는 원자료 읽기·AST compile·별도 scalar 계산만 했다. Analyzer main/native/actor/훈련/이전 phase 분석을 재실행하거나 다른 파일을 수정하지 않았다.

## 코드·계획·실제 출력

- [analyze_finger_curl.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_finger_curl.py:13)의4checks와 전체1201state/1200control·contact step coverage를 확인했다. 23–27행은 실제 LH21개 관절을 선택하고1200개의 final_target이 각각constant인지 검사한뒤 초기/.5초/5초 scalar q를 degree로 요약한다. Prefix 선택·state120/1200 인덱스·rad→degree 계산이 원자료와 맞고 AST compile을 통과했다.
- 16–22행은 distal finger3 body별 guitar접촉의 raw lambda>0인 step을 중복없이 집계한다. 양의 step수/처음·마지막/2초이후(480step포함)/상대 guitar body 이름을 각5body에서 독립 재계산해 exact 확인했다. 모든 finger 표면의 간격/정확한 pad/힘 방향·N/연속지지의 인증은 아니다.
- 실제 analysis의4checks/10입력 SHA 전후/current SHA, execution exit0·4소스 전후 SHA·log SHA, source_before의producer/plan/frozenrunner/외부 invocation script4사본 SHA가맞다. OUT은 root wrapper가사전준비했다. 검사자 사전열람당시없던결과디렉터리를 analyzer가스스로생성한다고주장하지않는다. 새 native/physics/actor/train 집계는각0이다.
- Analyzer SHA `e3d59fc2e152b01704dbc667bf6cc3f666c570a5e45372b3d8f10afcb13d9a38`, plan SHA `dd6ce20dc5c848aad45abe5e796c7d368bb69ae151ed1bdcd580d23761e857a9`로고정된소비본을검수했다. Wrapper/frozenrunner사본과기존source결과를수정하지않았다.

## 원자료에서 확인한 해석 범위

| scalar joint | 초기 ° | 유지목표 ° | .5초 실제 ° | 5초 실제 ° |
|---|---:|---:|---:|---:|
| middle1_x | 44.130761 | 47.860112 | 47.334181 | 47.859392 |
| middle2 | 62.181380 | 64.343141 | 64.040448 | 64.344227 |
| middle3 | 60.145874 | 60.684346 | 60.608886 | 60.684182 |
| index3 | 7.062720 | 7.991137 | 7.852637 | 7.975140 |
| ring3 | 5.169164 | 2.954326 | 3.254661 | 2.954649 |
| pinky3 | 32.154413 | 33.026748 | 32.908961 | 33.026840 |

Middle3는이미초기60.15°이며고정목표60.68°를향해유지된다. Middle2/1_x도함께굽혀진목표이므로화면의전체중지굽힘을distal3하나의원인으로환원하지않는다. 이는현재고정PD목표와실제scalar좌표가맞는다는관측이며 길이때문에그각도가필수·접촉이과도한굽힘을유발·해부학적으로부자연스럽다는인과인증은아니다.

Middle3 positive rawλ는18step,26~44step(약.1083~.1833초),상대body G:fret4이며2초이후0이다. Index3는1145step,54~1200step,2초이후721step이고상대guitar본체다. Thumb3는9step35~43,ring3/pinky3는0이다. 비접촉기간의기하gap을이집계만으로정하거나모든손가락동시접촉을필수로만들지않는다.

[FINGER_CONTACT_REGION_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/FINGER_CONTACT_REGION_PLAN.md:15)의손가락이름·guitar-local finite영역·실제접촉점·후보표면과간격선·현재/누적접촉구분은위관측의식별을돕는설계다. 18–22행은해부학pad/임의source triangle/좌표변환미검증을구분하고표시자체가제어/reward를바꾸지않음을명시한다. 24–34행의soft자세선호/8월19일범위참고/activeplayingfinger/나머지과도한curl회피·모든손가락강제접촉금지·별도새자세gate도범위에맞다. Finger1 FK 실패를승급하지않고LA고정/자유G/root하체/몸통목표/최종66권한을유지한다.

Critical: 없음. Warning: 미해결 코드·저장진단 blocker 없음. Suggestion: 없음. 이기록은코드·계획·실제analysis출력검수이며아직전달되지않은최종설명문서의검수는포함하지않는다.


## 최종 설명·표·재사용 이미지 추가 검수 및 동결

요약 판정: **문제없음**. 최종 README SHA `9548f660499373e18ba0961246fdb739bb58e0c11901f2dfa84746d0852d5067`, CHANGED_FILES SHA `3aee43798554359bbb0f2feaaf6a48e7e3e8d30e569dad60f63328c373eae69a`를읽었다. 이추가검수는요청된최종설명/표/기존이미지/계획범위에한정하며이전phase전수감사를반복하지않았다.

- [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_curl_diagnosis_v1/README.md:5)의검지/중지/약지/소지 finger2목표·finger3초기/유지목표/5초실제값16개를저장21joint rows와소수3자리반올림까지대조해일치함을확인했다. 중지2/1도함께큰목표를갖는다는설명·scalar좌표/전체해부학회전분리·길이counterfactual부재가자료범위에맞다.
- README의5distal body접촉표는기존독립재계산결과와일치한다. Middle3의18step26~44/G:fret4/2초이후0과index3의1145step54~1200/2초이후721을명시하며rawλ를N·패드·표면gap·지속지지인증으로확대하지않는다.
- Plus008의00000/00150 hands PNG를실제로다시열어 native 시작/5초프레임·주황스트랩경로/LA표시와출처를확인했다. 두이미지는분석입력SHA로보존된이전native재사용이며새진단렌더가아니다. 문서가접촉영역/finger-label overlay미구현을명시하고이미지만으로닿는손가락을판정하지않는점이맞다. 새plot/native/video/actor/train0이며기존134영상체계를추가실행으로바꾸지않았다.
- Plan의guitar-local finite허용영역·후보patch/실제접촉feature분리·좌표변환검증·현재/누적접촉구분은관측용미구현계획으로정확히표현됐다. 표시자체는제어를바꾸지않고후속soft자세/activeplayingfinger평가가필요하며모든손가락동시접촉을강제하지않는다. LA고정/자유G/root하체·몸통목표/최종66권한·finger1미인증범위도유지한다.
- CHANGED_FILES의한국어설명·절대클릭링크·실행4checks/21constanttargets/5distal rows·새실행0표현이맞고두문서의모든직접링크가존재한다. Main README1023/PLAN1821/VISUAL_REPORT1904(§103)의추가분은같은수치·소스trial·재사용설명·한계와일치한다.

Critical: 없음. Warning: 미해결 중대 문제 없음. Suggestion: 없음. 이 review를최종동결하며root의별도보존감사/봉인진행에검수blocker없음. 검수자에의한추가physics/producer실행및다른파일수정은0이다.


### 최종 CHANGED_FILES 소폭 추가 대조

요약 판정: **문제없음**. 최신 CHANGED_FILES SHA `90eb0231afeb5a2ef11e22b469723e5b1071d143ade9e4af0dda5cee5318713f`를 확인했다. 마지막 추가된 main README1023/PLAN1821/VISUAL_REPORT1904 링크는 위에서 실제 검수한 추가분을 가리킨다. 마지막 문구는 산출물 담당자의 문서2개 추가와 root의 저장자료 분석을 구분하고 새plot/native/actor/train0을 명시하여 전체phase를 문서만 추가한 작업으로 오해할 여지를 해소한다. 나머지 검수 판정은 유지한다. 이 추가 확인 후 review를 다시 동결하며 봉인 blocker 없음.
