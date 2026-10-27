# 현재 자세에서 Fret·Strike 두baseline 연결

현재어깨전방1cm초기자세에Fret035000·Strike010000을함께연결했다. **연결은확인됐지만연주는완주하지못했다.**2초준비후정책을실제로각3회추론·적용했고2.05초에Fret손목Z/손가락뒤위치안전조건으로원본첫done이발생했다. Strike_done=False이며그평가시간도0.05초로짧다. 음악품질/42곡전체성공률은판정하지않는다.

[사진 설명·실측·두checkpoint경로](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/artifacts_v1/README_V2.md:1)이정식산출물문서이다.영문본문/단위표기보정전V1도보존했다.

![초기부터Fret안전종료까지실제전신영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/dual_checkpoint_shoulder_v1/checkpoint_connection/whole_body.mp4)

## 실제실행과판정

| 항목 | 결과 |
|---|---|
| native1 |초기/두sourceview검증뒤녹화카메라키누락·0steps/정책0·영상없음|
| native2 |카메라만보완·물리492steps/123controls·2.05초실제종료|
| 준비/연주 |PREP2초120controls / PLAY.05초3pairedinferences|
| 원본종료 |Fret wrist_safety/finger_back True, Strike_done False, 두goal_finished False|
| 압현/타현 |압현0·타현hit없음·해결joint event0/crossing0;곡전체0/42판정아님|
| 기록영상 |전신·손각63frames/30fps=2.1초;물리끝2.05초터미널frame포함|
| 기타최종 |63충돌조각BB중심9.617284mm/전체SO3 2.983343°|
| 기타최대 |중심10.455249mm/회전3.343712°;최종값과구분|
| 전환후관찰 |2.00→2.05초.037970mm/.012452°;인과적정책효과로확정하지않음|

초기전체native상태/PD/질량은직전1cm정지시험과exact. 첫2초q81/rootp exact·정규화회전차0rad·기존480행오른팔effort명령exact. 두정책출력은저장관측독립CPU재생에서각3tick오차0이고right12의posture가실제최종scene.target을소비했다. 남은21목표/기존상완가상점요청cap10N과gravity/유한PD는유지했다. source각30을one81owner로합친뒤같은물리4substeps만진행했다. 기타자유/root하체고정/무스트랩/자체충돌·직접기타힘/부착/state덮어쓰기없음·새학습0이다.

실패시왼손목sourceG=[.128451675,−.093393892,−.568670034]m였고왼손이아직기타뒤쪽에있어안전Z조건을벗어났다. 원finger_back3회연속조건도같이발생했다. 마지막Strike_info의entry_ready=False/tip_target_distance=.082541637m도단순준비미확보관측이다. **다음은2초준비동안왼손을현재기타의압현준비영역으로옮기고오른pick READY도맞춘후handoff해야한다.**기다리는시간만늘리거나원안전판정을끄는방식으로해결하지않는다. 이준비동작은아직구현하지않았다.

## 원자료·계획·변경 파일

- [계획V1](/home/ajou/yigyu/3/stability_adapter_2/DUAL_CHECKPOINT_SHOULDER_PLAN_V1.md:1) · [카메라보완V2](/home/ajou/yigyu/3/stability_adapter_2/DUAL_CHECKPOINT_SHOULDER_PLAN_V2.md:1) · [완료/후속](/home/ajou/yigyu/3/stability_adapter_2/DUAL_CHECKPOINT_SHOULDER_COMPLETION_V1.md:1)
- [정식분석v3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/connection_verification_v3.json:1) · [원source/모델](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/native_v2/source_contract.json:1) · [원시controls](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/native_v2/controls.json:1)
- [native독립검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/review_native_v1.md:1) · [분석보완이력](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/ANALYSIS_NOTES_V1.md:1)
- [영상색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/dual_checkpoint_shoulder_v1/INDEX_V1.md:1) · [변경 파일/줄](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/CHANGED_FILES_v1.md:1)

분석v1의quat표현exact검사중단과v2의rawOBJ중심좌표오류를보존했다. 값은XMLbody.pos포함63조각의G중심[0,−.4,−.055937985]m를검증한v3만사용한다. sourceprofile정규화범위와nativeXMLhardlimit를동일시하지않고sourceCOM속도/historyinverseclip/보수적crossing판정한계도유지한다. 새로운모델학습이나checkpoint원래고정기타성능재현인증이아니다. 원본·실패·기존계획/자산·기존stability_adapter/와학습기본값은보존했다.

## 연결 결과 문서·영상 색인 보완

최신 설명은 [결과 문서 V3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/artifacts_v1/README_V3.md:1)와 [영상 색인 V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/dual_checkpoint_shoulder_v1/INDEX_V2.md:1)를 따른다. 영상 사본 4개는 이번 연결 실행 전신·손 2개(물리 2.05초, 영상 63프레임·2.1초)와 이전 정지 기준 전신·손 2개(물리 5초, 영상 151프레임·5.033333초)다. JointMusicClock의 joint는 양손 공동 음악 평가이며, 이번 짧은 PLAY에서 정산된 공동 음악 이벤트와 현 crossing은 각각 0건이다. 이전 문서·영상은 보존한다.

이번 최신 변경 목록은 [変更ファイル V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/CHANGED_FILES_v2.md:1)에 정리했다.
