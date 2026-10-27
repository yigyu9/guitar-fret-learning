# Quiet 손목 Z 목표 응답 실행 leaf

[봉인된 Z축 계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_Z_SUPPORT_AUTHORITY_PLAN.md:1)을 실행한다. 기존 quiet 초기81각·자유 기타 fullstate·고정 LA1.1018469719600776m·root/하체고정·몸통9 KP×2/KD×√2·L_Wrist_x ±.005rad 1Hz 파형을 유지한다. L_Wrist_y 추가보정0, 손가락 전체 목표와 Wrist_z밖80목표는원baseline과exact다.

- [ ] 새Z runner/분석/수집코드·AST·1200명령 독립검산·독립 사전 검수
- [ ] plus/minus 각 ONE 초기화, fresh15직접검사·같은초기화 실제5초/151frame/스트랩포함두영상
- [ ] 42저장분석검사·몸통실제각7검사·Y/Z유한응답 비교·문서/그림/보존검수

60Hz 목표와240Hz물리다. Z추가목표는0~2초0,2~2.5초선형ramp,5초까지±.005rad로held한다. 기존compose의66offset±.3rad/native목표한계를지키며clipping·gain변경·state/pose덮어쓰기·기타복원력·강제부착은없다. 초기native전체source/selfgate통과는cooked동적침투인증이아니다. 최대2actual초기화·자동retry없음이며오류는partial/원출력보존후다음행동결정이다.

이번2초quiet진단구간은연주필수WAIT과정이아니다. 전체66권한을유지한다. 학습/actor추론은0이며source-profile초기각일치를본목표의성공으로대체하지않는다. 원Y두5초/25감사검사·3658파일/이전7161파일보존기록은수정하지않는다. Y/Z응답은동일원baseline에대한t5 world위치와world회전log차분으로비교하고,변화량을계산할때서로다른길이/각도단위의스케일을명시한다. 두열이6D전체제어권을보장하지않으므로독립성·방향/오차기여를확인한뒤측정범위내제한feedback을설계한다.
