# 엄지 후면·손가락 전면·손바닥 옆면 근접 자세의 실제5초 비교

요청한 세 면 지지를 목표로 source12+3후보를검사했고, source support 조건은15개모두미달했다. 그중source겹침0인근접후보하나로기존손가락목표/새초기21목표의실제Isaac Gym두조건을각5초실행했다. **아직요청한옆면손바닥지지와세면grip을달성하지못했다.** 새초기21목표는기타이동·회전을악화시켜채택하지않는다.

## 실제결과

| 조건 | 최대이동mm | 최대회전° | 종료이동mm | 종료회전° |
|---|---:|---:|---:|---:|
| original_targets | 25.779645 | 7.800837 | 22.034643 | 7.092339 |
| initial_finger_targets | 37.615076 | 8.587915 | 33.170294 | 7.291649 |

두실행의초기81관절각/Gp·q/PD/solver/LA는exact같다. 변경은왼손21개PD목표뿐이며팔12와나머지48목표는같다. 스트랩LA1.1018469719600776m,초기경로1.089152306228229m(여유12.694666mm)다. 실제초기값의named81각/Gworld p·xyzw q/속도/목표/gain/법칙/physics는아래JSON에있다.

- [기존목표초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/native/original_targets/initial_values.json)
- [새손가락초기목표조건초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/native/initial_finger_targets/initial_values.json)
- [완료원자료검증·요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/analysis_v2.json) / [면패치별SDKfeature 위치](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/native_feature_analysis.json)

240Hz1200step을실제로적분했고각카메라151frame(t=0..5s)을30fps로인코딩해5.033333초다. pose재생이나소스그림이아니다. PhysX CPU 실행이며SDK CUDA/context·일부visualgeom warning은로그에보존했다. 실제초기FK/접촉/step/render불변성과영상coverage검증은완료했지만이것이모든visualmesh로드나cooked관통없음인증은아니다.

## 초기·종료실제장면과이동곡선

!['초기/종료실제Gym장면'](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/artifacts/native_initial_and_end.png)

위:기존목표,아래:새초기손가락목표. 왼쪽초기0초,오른쪽5초다. 녹색왼손/자홍색오른손/파란기타를보인다. 손바닥이넥가까이보여도요청한파란옆면patch접촉을뜻하지않는다.

![기타이동·회전원자료곡선](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/artifacts/native_guitar_motion.png)

World초기목표p/q에서의거리mm·회전각°를원자료로재계산했다. 새초기21목표주황조건이최대/종료오차를증가시킨다. 두조건모두평형에가까워져도초기상태에서이탈한상태이며초기복원성공이아니다.

## 실제접촉해석

기존목표의thumb3 body 양λ고유1010step·last1200은있다. 그러나요청후면source patch근접(투영내부+plane±2mm)양λ는고유30step·last260(1.083333초)뿐이다. middle3전면patch근접1082step·last1200, index3는30·last107이다. palm body양λ13step·last132이지만요청옆면patch근접은0이며그feature의finite patch거리19.323948~20.518808mm였다.

새초기21목표에서는thumb3후면근접2step·last19, pinky3전면979·last1200, ring3전면26·last93이었고palm옆면근접은0이다. palm body양λ17step·last298에도feature거리25.512921~25.721650mm가남는다. 따라서thumbbody의종료접촉이나palmbody행만으로세면grip을선언할수없다.

SDK guitar-side localfeature를post-step nativepose로G-root에옮겨finite source패치와비교했다. 2mm는진단근접기준이며면정체성/뉴턴접촉력/연속지지/cooked관통인증이아니다. pre/post feature 이동과SDKnormal 양부호는원자료에같이있고normal은분류gate에쓰지않았다. Root/하체는모든state에서exact고정,실제양손접촉고유step0과상향proxy위반0이었다. 몸통9PD목표는같아도실제최대좌표drift는4.228004/4.255594°로측정됐다. 최종양팔·양손66제어권을유지한다.

## 실제0~5초영상

기존목표 — 손근접:

![기존목표실제Gym손5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/native/original_targets/hands.mp4)

기존목표 — 전신:

![기존목표실제Gym전신5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/native/original_targets/whole_body.mp4)

새초기손가락목표 — 손근접:

![초기손가락목표실제Gym손5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/native/initial_finger_targets/hands.mp4)

새초기손가락목표 — 전신:

![초기손가락목표실제Gym전신5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/native/initial_finger_targets/whole_body.mp4)

## source탐색과후처리보존

![15source후보대표점오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/artifacts/source_fifteen_candidates.png)

왼쪽12개wide33/right3개support-plane후보의thumb/palm대표점목표오차mm다. Source정적검색이며Gymtrial15회가아니다. 모두source support거절이다. 서로다른시작점·목적함수이므로인과ablation으로해석하지않는다. Native에사용한support-plane old_near17의thumb/palm source유한patch거리구간은2.583857/2.157375mm였다. Fresh nativepose source거리상한은2.583829/2.157424mm이며smallFK차이가있다. 엄지대표점margin.886486mm/pointgoal4.872187mm,palmgoal6.304313mm로source support조건은유지해서미달로기록했다. Native입장은겹침0·up/nativebounds/초기FK만의별도진단이다.

첫후처리가자신의live로그를input에넣어SHA검사에서중단됐고분석JSON은생성하지않았다. [실패원본보존](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_near_contact_diagnostic_v1/analysis_failure_v1/preservation.json)과새v2명시적입력분석으로고쳤다. 추가물리실행0이다. Source거리검증의첫nearesttriangle 투영수치문제도wider phase에보존했고centeredquad halfspace검증으로30개실제witness를대조했다. 최적화flag false를최적해로표현하지않는다.

Luna산출물·독립검수요청은agent thread limit오류로실행되지못해이번그림/문서는root가작성했다. 원자료/실제PNG QA와root보존검증을독립검수완료로표현하지않는다.

다음은 [손바닥옆면우선초기배치](/home/ajou/yigyu/3/stability_adapter_2/PALM_PATCH_PRIORITY_INITIAL_PLAN.md)다. 기존81목표·LA를유지하고요청옆면의지점과전체형상을먼저맞춘뒤엄지/손가락의작은개별목표를비교한다. 기타고정/손부착/매step pose덮어쓰기/기타목표외력없이초기복원·유지및연주중안정화목표를이어간다.
