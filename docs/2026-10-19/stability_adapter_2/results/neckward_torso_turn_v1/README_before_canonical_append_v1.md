# 넥 쪽 상체 회전 · 숙임 감소

숙임을 늘려 받침을 만드는 방향에서, 상체를 넥 쪽으로 조금 돌리며 숙임을 줄이는 초기 후보를 만들었다. 세 source 조합 중두개가 통과했고 **추가 앞굽힘2° + 몸통 넥쪽yaw12°**를 실제5초 검사했다. 머리 yaw 목표도 몸통목표의60%(7.2°)로 주었다. root·하체는고정이며 기타초기회전은이전안정후보와같다. 기타BB중심은이전후보에서world[-15.000,-15.000,+7.800]mm로조정하고오른팔지지각을다시맞췄다. 기존소스/학습기본값은덮어쓰지않았다.

| 실제5초 자세 지표 | 이전정지후보 | 새정지후보 | 변화 |
|---|---:|---:|---:|
| Chest→Neck 축 앞쪽 기울기 | 53.576° | 48.348° | -5.228° |
| 정면+Y에서넥−X쪽 heading | 12.643° | 22.199° | +9.556° |
| 같은 축의전체수직기울기 | 53.590° | 48.763° | -4.828° |

이 값은원래Chest→Neck축/직교front축을native Chest회전으로운반해world축에서측정한값이다. **source추가2°/12°·DOF scalar각과다르다.** 이전/새정지는초기상태가다르며여러초기각과기타위치를동시에맞춘비교다. body-right6°는 yaw 앞의 초기목표성분을유지한것이며 실제world측경6°유지를뜻하지않는다(2.535°→−10.951°). 숙임은감소했지만여전히일부남는다. 자연스러움은영상으로판단한다.

## 실제 영상·이미지

![이전정지와넥방향회전새정지5초비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/old_vs_neckturn_static.mp4)

![새후보팔꿈치운동5초원본](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/native_v2/elbow_neckyaw12/media/whole_body.mp4)

[초기/종료이미지·같은좌표확대·실제자세설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/README_V2.md:1) · [이전참고2개+새4개원본영상색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/neckward_torso_turn_v1/INDEX_V1.md:1) · [원본복사해시/프레임검사](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/neckward_torso_turn_v1/manifest_v1.json).

## 기타 유지와 팔꿈치 움직임

| 새후보조건 | 초기대비5초바디BB중심이동 | 전체SO3회전 | 실제팔꿈치2.5~5초왕복 |
|---|---:|---:|---:|
| 정지 | 3.944mm | 1.473° | 0.030° |
| 팔꿈치목표±5° | 3.876mm | 1.455° | 10.084° |

두새조건의native 초기상태와2.5초까지trace는exact다. R_Elbow_y scalar목표만2.5~4.5초.5Hz한주기±5°로바꿨다. DOF이름suffix는world회전축이아니다. 같은시각정지와비교한기타추가차이최대는 **0.099629mm·0.053043°**로이번소동작진단을통과했다. 정지기타원점변위11.512mm와BB중심3.944mm는다른양으로구분한다.

모든원위오른팔(전완/손목/손가락)·머리·왼팔/손의기타접촉0/1200 endpoint표본이다. 상완1169/1200·오른허벅지1193/1200은두조건에서같다. R_Thorax접촉0이며몸통압착은확보되지않았다.

**접촉위치의tradeoff:** 엄격한상완시작0~35%+기타상단볼록영역판정은이전1171/1200에서새조건둘모두0/1200으로바뀌었다. 새정지actual 상완축fraction은.353796~.508880,움직임은.353853~.508880이다. 최소점도35%경계보다조금팔쪽이다. 따라서 전체상완지지와기타유지는관측했지만, 이전근위35%구간이나겨드랑이접촉유지로등록하지않는다. raw lambda/접촉수는N이나하중분담이아니다. source목표상완0~30%와actual측정위치를구분한다.

## 제어·검증·보존

기존right12 EFFORT 사람중력보상/유한자세PD/상완사람점cap10N(초기world목표4mm안쪽,K2000/D30), 전완점force0와나머지69POSITION을유지했다. 상완Jacobian의Elbow/Wrist열0·토크합산/모델effortclip/소유권/물리step당1회·POSITION69readback/state보존을검사했다. 기타자유/strapOFF/leftgripOFF/root·lows고정/자체충돌활성. 직접기타힘/고정/강제부착/진행중pose또는실제관절state덮어쓰기없음.

source초기gap은근위30%2.279mm·전완13.998mm·오른허벅지.199mm·R_Thorax32.929mm이며전체source겹침검사를통과했다. 이수치는PhysX cooked clearance인증이아니다. 왼팔/손가락54초기scalar와모델한계를유지했다. 정지gate는중심10mm/회전3°/접촉제약/2~2.5초정착과실제heading증가≥5°·앞기울기감소≥3°로검사했으며새motion prep에원자료SHA를핀했다.

두실제실행은각240Hz×5초=1200physics·60Hz×5초=300control·151frame30fps(영상5.033초)를끝까지계산했다. 증분관절응답RMSE0.048544°와절대moving q−target RMSE0.131056°를구분했다. 한초기후보/한팔꿈치scalar한주기/5초의결과이며, 장시간·반복·손목·큰동작·fret/strike연주는미검증이다.

새후보를이미지검토용및후속진단기준으로보관한다. 기존안정후보/공용모델/원기타/이전실험은수정하거나삭제하지않았다. 다음은회전·숙임감소를유지하며접촉점을조금더어깨쪽으로돌리는소단계다.

[전체결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/result_summary_v1.json) · [실제자세trace](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/torso_posture_v2.json) · [동시간팔꿈치비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/elbow_comparison_v1.json) · [공간접촉판정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/contact_region_v1.json) · [초기81각/Gp·q](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/search_v1/bend2_neckyaw12/candidate.json) · [실행설정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/motion_candidate_v1/config_motion.json) · [계획](/home/ajou/yigyu/3/stability_adapter_2/NECKWARD_TORSO_TURN_PLAN_V2.md:1) · [완료기록](/home/ajou/yigyu/3/stability_adapter_2/NECKWARD_TORSO_TURN_COMPLETION_V1.md:1).
