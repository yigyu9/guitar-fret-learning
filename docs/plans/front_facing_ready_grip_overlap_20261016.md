# 재파지 손·중간몸통 원형상 감사의 범위 공백 진단

## 목적

현재완료한source-plane전행감사는4support/RH5..T와LH완전해제15초를포함한다. 사용자조건의과도한겹침금지와압현준비복귀를평가하려면LH접근·닫기·grip상태의원형상과Spine/Torso도확인할필요가있다. 기존필수12gatePASS를전체신체형상완전인증으로확대하지않는다.

## 이번 읽기전용 진단

- [ ] 이미닫힌native_regrasp_v6의16/36/37/38/40/42초6시점을사용한다. 현재저장중인v7은읽지않는다.
- [ ] LH전체/L_Wrist/L_Elbow와추가Spine/Torso 원shape의모든native활성physicalG89쌍을대조한다. source support interval과unitnormal직접투영으로기존1mm per-pair방향분리이동예산충족가능성을진단한다. 새로운수치문턱을추가하거나기존판정을소급수정하지않는다.
- [ ] 기존sourceplane1/2 helpers를재사용하고새body선택은context scope내임시binding으로만추가해정상/예외모두원객체를복원한다. 실제원XML·mesh·nativefilters와compiledsource배치의차이도확인한다.
- [ ] 모든shape/pair누락·최적화실패·불충분certificate를보존한다. g<−1mm나제한된normal탐색실패를실제침투깊이/물리오류로단정하지않는다.
- [ ] LHinactive thumb_pad 및비물리proxy는진단으로별도공개하고실제force를전달하는활성physicalsurface와구분한다.
- [ ] 원모델108/actualcfg/raw/원helper/source/leaf를사전SHA·원문으로닫고CPU/사후불변검사뒤동결한다.

이것은6시점표본이며전기간·시간연속·PhysXcooked형상을인증하지않는다. 새control/기타힘/접촉정책/native/PPO는0이다. 원42초접촉95실패·후속43초미검증상태는그대로둔다. 결과에따라추가전행검사가필요한지Root가판단하며새producer/물리변경을자동채택하지않는다. 소유권은분석담당의diagnose_grip_overlap_v1/에한정하며기존다른담당자료는수정하지않는다.
