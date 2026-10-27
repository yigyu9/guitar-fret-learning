# 허리 추가 완화 산출물 brief

선택은native_add8_static(현재4° 완화 자세에서추가8°),비교는native_add4_static(추가4°). 이전 기준은waist_upright_right_arm_v1/native_relief4_static이다. 새phase의posture_final_v1.json·analysis_final_v1/analysis.json과실제native 초기값/trace/캡처/MP4를읽는다. 새물리실행없이native이미지와영상만정리한다.

현재4° 기준의초기Torso/Spine/Chest local-Z world전방기울기proxy는32.729141/34.403368/61.412311°다. 선택추가8°의초기값은29.529143/28.403364/53.412323°,5초최종은32.244674/31.474369/56.421877°다. 시작후Chest가약3.010°다시숙였지만기준의최종63.364037°보다덜숙인다. local-Z축의투영proxy이며임상적허리굴곡각/관절scalar합이아니다. 현재기준대비parent-child회전차이는Pelvis→Torso3.200°,Torso→Spine2.800°,Spine→Chest2.000°. 이전waist원기준대비Chest초기완화총12°다.

기타초기G39 p/q는현재4°기준과최대9.9960e-8m/1.3009e-7rad,원waist와최대2.1126e-7m/2.6018e-7rad차이다. 초기기타가새로옮겨진것이아니다. Root/하체고정,strapOFF,selfcollisionON,자유기타,기존finitehuman81목표(33EFFORT+48POSITION)와기존gain/currentG점제어다. Sourcefitting에서Thorax근접선호/최대간격gate만제거해몸통펴기를우선했으며source최소간격/전체겹침/상완/자연팔/전완여유/waist/모델한계는유지했다. 기타힘/고정/부착/실행중pose덮어쓰기없음.

|조건|물리경과|최대기타BB중심이동|최대SO3|최종BB/SO3|2~5초BB/SO3|
|---|---|---|---|---|---|
|현재4°기준|5초|14.545447mm|8.012684°|12.267181mm/5.598054°|3.735037mm/1.650240°|
|추가4°|5초|13.040470mm|7.353169°|12.305455mm/5.955726°|1.893491mm/.893689°|
|선택추가8°|5초|12.882340mm|7.542856°|11.814982mm/6.015451°|.381862mm/.143808°|

두새시험각1200physics/300control/5초완료,합2400/600,새팔꿈치파동/CKPT/학습0. 두조건모두waist접촉1198/1200,후기120/120양의rawlambda,근위상완후기120/120,Thorax후기0,오른전완/손기타접촉0. 왼손손가락기여는남는다. 추가4° waist전체양의표본1197/1200이며presence1198과구분한다. 두블록지속끼움/왼손없는수동안정/연주성공/반복강건성주장없음. Rawmambda를N으로부르지않는다.

생성: 현재4°와선택추가8°의동일native전신카메라초기비교및같은crop확대. 카메라행렬실제확인후일치여부기록. 선택의0/2/5초전신·손갤러리. 새정지2조건의전신/손MP44개원본byte-exact복사(물리5s/30fps151frames/재생5.033333s)와색인/manifest. 입력/producers사전·사후SHA및PNG원프레임대조.

담당소유는results/waist_straighten_v1/artifacts_v1와video/waist_straighten_v1만이다. 한국어README.md와절대경로·실제줄번호,manifest_v1.json,provenance_v1.json으로기록한다. 원본/소비소스/A/main/다른phase/review/최종봉인파일수정금지.
