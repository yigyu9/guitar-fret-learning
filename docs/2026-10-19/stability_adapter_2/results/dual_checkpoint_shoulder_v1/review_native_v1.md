# Native 검수 — 어깨1cm 자세의 두 checkpoint 연결

요약 판정: **문제없음.** Critical 0 / Warning 3 / Suggestion 0. 두 frozen actor의 직접 연결·한 physics owner 경로를 확인했다. 실제 연주는 원Fret 안전종료로 실패했으며, 곡 완주·새 학습 성공 인증은 아니다.

- native1은OM_appearance 첫capture KeyError의0 physics/0 control/0 effort 셋업 실패로 보존한다. native2는2초PREP120control 뒤 두actor PLAY3회,총123control/492 physics/2.05초를 완료하고 `first_source_terminal`로 멈췄다. Fret done true/Strike false이고 두 goal_finished는 false다. 완료 실행과 정상곡 완주는 다른 양이다.
- 기존shoulder1cm 정지 초기 native state 전체·PD·mass exact를 직접 확인했다. 첫2초의 q81/rootp와 기존480 effort/upper 명령도 exact다. raw quaternion 기록은 기존unit quaternion과 수치가 다르지만 정규화 후 동일 회전0rad임을 확인했다. [분석 보완 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/ANALYSIS_NOTES_V1.md:1)의 실패v1/중간v2를 수정하지 않고 canonicalv3로 구분한다.
- [effort helper:103](/home/ajou/yigyu/3/stability_adapter_2/dual_shoulder_effort_v1.py:103)의 posture가 매physics step 해당control의 최종 `scene.target`을 읽음을492행에서 확인했다. COM 점속도·상완cap10N·child J열·posture·Jᵀ torque 합산/모델 clip을 재계산한 최대오차8.88e−16Nm다. 123개의 normalize→model/rate 목표와 held21도 재계산했다. 원30+30 요청의 비중복 ownership·한81 제출/오른12 effort·다른69 POSITION·forearm force0·root/하체 고정·strap OFF·자유 기타·기타 직접힘/부착/state 쓰기 금지 경로가 유지된다.
- endpoint/music callback은 각각492개로 같은 physics_step에 연결되고, POSITION69/state123검사 및 금지API0을 확인했다. 입력 attempt와 canonical producer의 SHA가 검수시 현재 일치한다. [분석v3:33](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/analyze_connection_v3.py:33)의 원checkpoint strict load/저장obs deterministic 재생 코드와 actor별3회/오차0 결과를 검토했다. 리뷰어는 새 actor 추론을 실행하지 않았다.
- [분석v3:40](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/dual_checkpoint_shoulder_v1/analyze_connection_v3.py:40)의 실제XML body.pos 포함63조각 bbox 중심 `[0,−.4,−.055937985]m`를 재계산했다. canonical 최종BB9.617284mm/최대10.455249mm,SO3 2.983343°/최대3.343712°,2→2.05초BB .037970mm/SO3 .012452°가 raw trace와 일치한다. 원v2의25.609mm는 잘못된 로컬OBJ 중심을 쓴 폐기 수치이며 성공근거로 사용하지 않는다.
- 원control PLAY0/1/2의 wrist/finger streak1→2→3과 최종 wrist G-local Z−.568670m/finger 최소Z 약−.470057m를 확인했다. 원안전판정은 wristZ와finger_back으로 종료했다. joint resolved/crossing0이며 음악은 완료하지 못했다. 실행기간 전체상완presence458/492,왼팔손/Head/오른원위접촉0은 이 짧은 기간에 한정한다.

Warning 1 — 2.05초 중 실제정책 적용은 .05초/3회뿐이다. 종료이후 미관측 구간·검열된 곡을 완주로 부르거나, 전환후의 작은 기타 변화로 두정책의 안정화 효과·인과 또는 장기 안전을 확정하지 않아야 한다. 기존5초 정지·별도자세의 팔꿈치 운동 검증도 이번 양손 연주 인증이 아니다.

Warning 2 — Fret source profile/정규화와 native XML/model target범위가 다르다. source `joint_limit_usage`를 native 물리 hard-limit 위반 인증으로 동일시하면 안 된다. inverse history clipping·EMA·현재EFFORT posture 경로 및 conservative240Hz crossing 진단은 원고정기타 성능 동등성/학습ready detector 인증이 아니다. 실제공간 wristZ/finger_back 안전판정과 관절각 한계를 구분한다.

Warning 3 — 분석v1은 raw quaternion 표현 차이로 중단했고 v2는 body.pos 미포함 bbox 수치가 잘못됐다. 이 두 producer/실패·중간출력과 0-step native 셋업 실패를 역사자료로 보존하되 canonicalv3만 기타중심 수치의 권위로 사용해야 한다. 현재v3는 root/COM/BB 및 final/max 구분이 맞다. 요청point힘/raw lambda를 실제지지력·힘분담으로 해석하지 않는다.

추가 native/학습/정책추론/소스 수정0. 이 기록은 코드·원자료·수식 및 canonicalv3 핵심 결과에 한정한다. 최종문서·PNG·영상사본/provenance·main append 및 전수 보존 봉인은 후속 범위다.

canonical verification SHA256: `89f3678351c3e3f287f8bbf765ace508ff4361d59e74f20308336ddb4cae70d2`.
