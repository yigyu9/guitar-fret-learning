# 기타 모델·초기 자세 자료 모음

사용자가 지정한 `docs/2026-10-19/`에 현재 기타 형상, 스트랩 없는 초기 자세, 이미지와 영상을 모은다. 이 날짜는 자료 정리 경로다. 기존10-12 실험의 실행일·원자료 경로를 바꾸거나 새로 실행한 결과로 표시하지 않는다. 계획·구현·실제 자산은 `/home/ajou/yigyu/3/stability_adapter_2/`에 유지한다.

## 현재 기타

Grellier OM 도면을 바탕으로 바디 외곽과 외부 두께를 근사한 회색 모델이다. 바디 길이491.957mm·최대 폭380.632mm·국소 두께 약85~107.198mm이며 기존 넥과 fret/strike 물리 영역을 유지한다. 6현 선 표시는 영상 확인용으로 물리적 상호작용이 없다. 목재 내부·음향·질감이나 사진 속 제품의 정확한 재현은 포함하지 않는다. 현재총질량4.648716kg은 이전 모델값을 유지한 것으로 실제 중공 기타의 질량 재현값이 아니다.

## 현재 초기 자세

스트랩을 끄고 왼팔·왼손을 떼어 둔 상태에서 기타가5초 동안 넘어가지 않는 후보를 동일 초기 조건2회 확인했다. 이때 오른쪽 상완(어깨 아래)·가슴·오른 허벅지 접촉이 관측됐다. 각 접촉의 지지 힘/모멘트 기여를 분리 측정한 것은 아니다. root·하체 고정, 기타 자유, 오른팔12 EFFORT 제어와 다른69 POSITION PD를 사용한다. 기타에 직접 외력·부착·런타임 pose 덮어쓰기를 하지 않는다.

| 측정 | 값 |
|---|---:|
| 초기 대비 바디 bounding-box 중심 이동 | 40.207mm |
| 초기 대비 actor-root 이동 | 53.017mm |
| 초기 대비 전체 SO(3) 회전 | 11.071° |
| 2→5초 바디 중심 추가 이동 / 추가 회전 | 0.073932mm /0.028843° |
| 상완 / 왼팔·왼손 / Head 접촉 끝점 | 1187 /0 /0 (각1200개 중) |
| 물리 경과 / 녹화 길이 | 5.0초 /5.033333초 |

초기 정착 변화와 오른팔의 큰 초기각·손목 한계 접근이 남는다. 연주 중 안정성, 접촉력 분포 및 cooked 관통 검증은 이번 정리 결과에 포함하지 않는다. raw lambda와 접촉 관측 횟수를N 단위 힘이나 지지 비중으로 해석하지 않는다.

## 자료 구성

- `guitar/`: 모델 형상·치수·두께·출처 설명
- `posture/`: 초기값·제어 방식·5초 결과·미검증 사항
- `images/`: 기타 모델 확인 이미지, 초기·측면 자세,0→5초 비교
- `video/candidate/`: 최종 후보와 동일 조건 반복의 전신·손 영상
- `video/diagnostics/`: 이전 실패 시험의 전신·손 영상
- `data/`: 원본 그대로 복사한 초기값·모델 정보·검증 자료

복사한JSON 내부의 기존 절대경로는 원실험 추적용으로 그대로 둔다. 이 복사본을 새로운 실행 설정으로 간주하지 않는다. 원본과 사본의 해시는 정리 provenance에 기록하며, 이번 작업의 새 물리 실행·학습·모델 변경은0회다.

## 바로 보기 — 검수 보완본 v2

[기타 형상·치수·출처와 참고 이미지](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/guitar/README_v2.md:1) · [초기 자세·조건·측정 결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/posture/README_v2.md:1) · [전신·손 영상22개 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/INDEX_v2.md:1) · [원자료 복사본 안내](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/README.md:1)

![현재 후보의 초기와5초 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/images/native11_zero_to_five_comparison_v2.png)

![현재 후보 환경 시작부터5초 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/candidate/native11_whole_body.mp4)

초기 정리본 v1은 영상 색인의 일부 원본–사본 연결과 접촉 주기 설명에 오류가 있어 이력을 보존했다. 실제 영상 사본은 원본과 같으며, 현재 안내는 링크가 정정된 v2를 사용한다. [정정 영상 manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/manifest_v2.json:1)와 [보완 provenance](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/provenance_v2.json:1)에서 원본과 사본의 대응을 확인할 수 있다.


## 최신 오른팔 자세 수정 결과

[참고 사진에 따른 오른팔 수정과 실제5초 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/README.md:1). 이전 교차 팔은 연주 자세로 채택하지 않는다. 새 팔 모양은 개선됐지만 기타 유지에는 실패했고, 작은 위쪽 보정은 머리접촉으로 거절했다. 이전 이미지·영상과 실패 기록도 모두 보존한다.


## 최신 몸통 기울임·겨드랑이 접근

[왼쪽4°·초기배치조합·상완누름의실제5초비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/README.md:1). source근접에도상완접촉0/1200이며세조건모두기타유지에실패했다. [전체·손영상6개](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/INDEX_V2.md:1). 이전자료는보존하고반대방향과의명확화는대기중이다.


## 최신 바디 쪽 몸통 기울임: 방향 확정 및 실제 비교

사용자 확인 방향은 정면 screen-left=player-right=기타 바디 쪽이다. 추가Chest4°/Torso1°/Spine2.5°와 자연 오른팔 조정·기타 초기 이동을 구성하고 같은 초기값을 실제5초2조건 비교했다. 스트랩OFF·왼손지지없음·root/lower고정·기타자유를 유지했다. 전완 제어 / 상완 추가에서 바디 중심48.051/47.501mm, 전체회전52.174/47.662°, 넥고도−15.921/−10.019°로 초기회전 유지에 실패했다. 상완접촉968/256 of1200이며 머리/왼팔0이다.2초뒤정착을성공으로해석하지않는다. 이전넥쪽기울임 기록은반대방향진단으로보존한다.

[초기 배치·그림·실제 영상·결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/README.md:1), [현재 계획](/home/ajou/yigyu/3/stability_adapter_2/BODY_SIDE_LEAN_AXILLA_PLAN_V6.md:1), [초기81각·기타p/q](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/search_v5/right4_close_support/candidate.json:1). 다음은 누름 증가보다 허벅지·상완·전완 지지점 배치 조정이다.


## 최신 위 볼록부·겨드랑이 접근: 실제 접촉 구간 확인

어깨쪽0~35%초기source간격을14.150→5.669/5.029mm로줄이고실제5초3조건을시험했다. 강한두조건은머리접촉/114°·82°회전으로거절했다. 같은6°초기값에서전완접근방향을이전방향으로맞추고상완접근2mm/cap5N으로줄인조건은전체상완1075/1200·머리/왼팔0,바디59.465mm/회전53.935°후2→5초거의정지했다. 그러나접촉은상완중간이며지정어깨쪽35%·기타위볼록영역접촉0/1200으로겨드랑이지지성공이아니다. source4/5추가앞굽힘/기타초기이동해는거절해native실행하지않았다. 세actual의기타p/q는같고조건2/3fullnative초기도같다. root/lower고정·strapOFF·기타자유·직접기타힘/부착/pose쓰기없음을유지했다.

[초기장면·실제접촉점·영상6개·한계](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/README.md:1), [현재제어계획](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BOUT_AXILLA_PLAN_V6.md:1). 이전양호초기값은보존하고상완전체접촉을겨드랑이접촉으로등록하지않는다.

## 어깨 쪽 받침과 팔꿈치 영향 분리

정지/팔꿈치±2°/±5°의 동일 초기값5초 Isaac Gym 비교를 저장했다. ±5°에서 실제10.08°왕복, 정지 대비기타 추가최대0.027241mm/0.009348°, 오른 전완·손목·손가락 접촉0이다. 작은 한관절 진단으로만 해석하고 source30%/실제35%영역과 R_Thorax접촉0을 구분한다.

[결과·이미지·영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/README.md:1) · [원본 영상6개](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/axilla_elbow_isolation_v1/INDEX_V1.md:1).

## 넥 쪽 상체 회전과 숙임 감소

이전/새실제영상과새정지·팔꿈치±5°5초비교를보관했다. actualChest→Neck전경5.228°감소·넥heading9.556°증가,정지G중심3.944mm/회전1.473°,팔꿈치추가영향.099629mm/.053043°. 접촉점이근위35%경계바깥으로옮겨진한계와기존후보보존을기록했다.

[결과·초기/종료이미지·비교영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/README.md:1) · [원본영상색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/neckward_torso_turn_v1/INDEX_V1.md:1).


## 덜 굽히고 더 회전한19° 초기 자세

추가앞굽힘+2°/넥쪽yaw12°에서−6°/19°로몸통분산초기목표를조정했다. actual전경8.501°감소/heading5.788°증가,정지5초기타BB중심9.549mm/회전2.995°·팔꿈치±5°추가최대.077660mm/.042115°다. 상완근위35%+위볼록영역1117/1200접촉·후기상완120/120,root/lower고정·strapOFF·leftgripOFF·기타자유를유지했다. 최종gate여유.004602°/최대회전3.314°를구분해반복강건성/연주성공으로채택하지않는다. 실패조건/원소스/학습기본값보존.

[UPRIGHT_NECKWARD_POSE_PLAN_V5.md](/home/ajou/yigyu/3/stability_adapter_2/UPRIGHT_NECKWARD_POSE_PLAN_V5.md:1) · [UPRIGHT_NECKWARD_POSE_COMPLETION_V1.md](/home/ajou/yigyu/3/stability_adapter_2/UPRIGHT_NECKWARD_POSE_COMPLETION_V1.md:1) · [README.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/README.md:1) · [README_V2.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/artifacts_v1/README_V2.md:1)


## 오른 어깨에서 팔을 조금 앞으로

오른Shoulder3초기각만조정해팔꿈치전방+9.893mm/5초이전동시각대비+10.711mm(기타front수평+Y)를만들었다. 몸통19°·나머지78초기각·기타초기전체상태exact,정지5초BB9.425mm/회전2.888°·상완후기120/120·머리/왼팔손/원위팔0이다. 최대10.455mm/3.344°는최종gate와구분한다. 지정근위35%+위볼록영역presence1062/positive237(기존1117/1113)의접촉tradeoff를기록한다. 새팔꿈치운동/연주·반복강건성미검증,원본/실패/학습기본값보존.

[계획](/home/ajou/yigyu/3/stability_adapter_2/SHOULDER_FORWARD_PLAN_V2.md:1) · [완료](/home/ajou/yigyu/3/stability_adapter_2/SHOULDER_FORWARD_COMPLETION_V1.md:1) · [그림/실제영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1/README_V3.md:1) · [결과/변경색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/README.md:1)


## 어깨 전방1cm 자세의 Fret·Strike 동시연결

Fret035000/Strike010000두frozen actor를2초뒤동일60Hz음악clock/단일81목표로실제로연결했다. right12EFFORT의posture는scene.target을소비하고기존gravity/상완가상점cap10N을합쳤다. native1은카메라키누락0step실패보존,보완native2는492steps/123controls·2.05초에FretwristZ/finger_back3streak로안전종료(PLAY3/Strike_doneFalse). 연결확인과곡완주실패를구분한다. 첫2초q/rootp/480effort exact·정규화회전0;기타최종BB9.617mm/SO32.983°. 왼손준비위치가필요하고오른pick READY도미확보였다. 모델재학습/원고정기타성능인증없음.

[계획](/home/ajou/yigyu/3/stability_adapter_2/DUAL_CHECKPOINT_SHOULDER_PLAN_V1.md:1) · [완료/후속](/home/ajou/yigyu/3/stability_adapter_2/DUAL_CHECKPOINT_SHOULDER_COMPLETION_V1.md:1) · [초기/종료사진·전체영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/artifacts_v1/README_V2.md:1) · [결과/변경색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/README.md:1)

## 연결 결과 문서·영상 색인 보완

최신 설명은 [결과 문서 V3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/artifacts_v1/README_V3.md:1)와 [영상 색인 V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/dual_checkpoint_shoulder_v1/INDEX_V2.md:1)를 따른다. 영상 사본 4개는 이번 연결 실행 전신·손 2개(물리 2.05초, 영상 63프레임·2.1초)와 이전 정지 기준 전신·손 2개(물리 5초, 영상 151프레임·5.033333초)다. JointMusicClock의 joint는 양손 공동 음악 평가이며, 이번 짧은 PLAY에서 정산된 공동 음악 이벤트와 현 crossing은 각각 0건이다. 이전 문서·영상은 보존한다.

## 왼손의 넥 아래·뒤·앞면 근처 초기 배치

왼쪽33 초기각만 조정해 손바닥을 넥 아래면, 엄지를 뒷면, 네 손가락을 현 앞면에 작은 간격으로 놓았다. 그 외48각/기타 초기state·몸통·오른팔/root·하체·무스트랩 조건은 유지했다. 실제 초기 선택facet gap은 손바닥12.569mm/엄지11.150mm/앞손가락4.932~10.293mm다. source whole-mesh LP·fresh native 초기 FK/실제pose source 감사를 통과했으며 cooked 연속 비접촉 인증과 구분한다.

기존왼팔POSITION5초는 손이 처졌고, 높은외부PD는1.833333초 안전중단됐다. 낮은외부PD+gravity와현재기타기준 손목 준비 추종을 써서5초 손목오차max17.018mm/왼팔·손 접촉presence0/1200,기타BB9.296mm/SO3 2.835°를 관찰했다. 최종 손바닥gap31.537mm로 초기6면 간격을 일정하게 유지했다는 뜻은 아니다. 한human81 토크명령의24EFFORT·57POSITION/모델cap이며 기타힘·부착·state덮어쓰기없음.

같은초기2초뒤 준비추종OFF 후 Fret035000/Strike010000을26회씩 동작시켰고2.433333초에Strike wrong-crossing-count로 종료했다. Fret손목/finger-back안전종료는False지만압현0·완주아니다. 기타BB33.065mm/SO3 11.217°. 다음은오른pick의현재G기준READY·타현진입과왼Fret음별압현확인이다. 이번 native5시도/4정상실행종료+1물리안전중단·학습0,원본/실패보존.

[완료·조건](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_NEAR_INITIAL_COMPLETION_V1.md:1) · [현재 초기 설정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/config_v1/config.json:3) · [최신 결과·초기 이미지·영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/README.md:1)


## 2026-10-19 오른쪽 두 블록 받침 자세 검증

몸통과 오른 Thorax/Shoulder 초기각을 조정한 source7 seed0에서 초기 기타 p/q·root/하체·손가락42를 보존했다. 스트랩 없이 실제 native 정지5초와 R_Elbow_y 목표±5° 한 주기5초를 비교했다. 실제 팔꿈치 운동범위10.114°에서도 기타가 빠지지 않았고 정지 대비 같은 시점의 추가 BBcentre 변화 최대0.071mm/SO3 0.032°였다. 운동 구간 두 블록 접촉 존재480/480step·동시양의rawlambda223/480,후기존재120/120·동시양의rawlambda56/120이다. rawlambda는힘N/분담률아니다.

초기 대비 최대BBcentre5.329mm/SO3 4.495°,몸통9실제scalar최대편차0.761°였다. 오른전완/손·머리접촉0이나 왼LH:thumb3와허벅지접촉은남아두블록만의수동유지인증이아니다. 몸통9+팔24 EFFORT/머리6+손가락42 POSITION,전체81목표를사용하며기타고정/직접힘/부착/runtime덮어쓰기없음. native12시도중11회5초완료/1회5physics중단,CPU14후보중2수락,학습0/체크포인트연결0.

이자세를다음진단기준으로두고왼엄지기여분리·다른작은팔운동을확인한뒤2초준비와Fret/Strike연결을평가한다. 기존학습구조나연주완주판정을대체하지않는다. [구현·완료기록](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_BLOCK_CRADLE_COMPLETION_V1.md:1) · [선택81초기각](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/search_v7/seed0/candidate.json:1) · [결과·실제영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/README.md:1) · [native독립검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/review_native_v1.md:1)


## 오른 허벅지 waist 걸침 초기 배치

기타를 휴머노이드 오른쪽 약9.6cm·앞3.0cm·아래4.9cm로 재배치하고 앞판을 local G_Y −5° 기울였다. 넥의 world 방향·root/하체·finger42·형상/질량을 유지하며 몸통/양팔 초기각을 재맞췄다. 첫 자세는4.783초에 이동 보호 중단됐고, 기울기5° 후보의 정지 및 팔꿈치±5° 목표 두 조건은 각각5초를 완료했다. 실제 오른 허벅지 접촉1198/1200step 모두 정의한 오목한 곡면 범위에 있었고 양의 raw lambda 및 후기120/120도 유지됐다. 중앙 점 부착/힘 N 인증이 아니다.

팔꿈치 실제 범위10.096°,정지 대비 같은 시점 추가 기타 변화 최대0.155mm·0.149°,초기 대비 wave 최대BBcentre11.725mm/SO3 6.095°였다. 몸통 실제 scalar 편차 최대2.235°. 후기 지지는 허벅지·상완·왼손 손가락이며 Thorax 접촉0이므로 이전 두 블록 지속 지지를 승계했다고 주장하지 않는다. 왼 접촉은 중지2/검지2/새끼3이고 소비된 계획의 왼엄지 표기는 최종 기록에서 정정했다. full81 목표/33EFFORT+48POSITION·strap OFF·기타 자유 상태를 유지했고 checkpoint/학습0이다.

waist 걸침을 다음 초기 진단 기준으로 사용하고 Thorax 접촉 회복과 왼손 접촉 의존성 분리를 확인한 뒤2초 준비/Fret·Strike를 평가한다. [초기값·구현·상세 결과](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_THIGH_WAIST_COMPLETION_V1.md:3) · [실제 영상과 결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/README.md:1). 기존 실험/모델/소비 버전을 보존했고 source1의 mesh before 누락은 제한으로 기록하며 이후37개 실제human mesh pin을 보완했다.
