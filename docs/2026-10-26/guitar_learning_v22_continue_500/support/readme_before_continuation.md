# 자유 기타 학습

**2026-10-26 현행: GPU 왼손 보상 v22·엄지 기하 접근과 접촉 후보의 분리.** v21의 선별 손가락 충돌·음 사이 B 복귀와 추종 동기화를 유지한다. 엄지3 패치의 같은 점·법선으로 기하 품질 Q를 측정하고 `.01×Q + .01×Q×contact_candidate`/초, 전체 최대 .02/초를 지급한다. 후보는 같은 점의 부호 간격 −1~0.5mm·유한 영역 내부·법선cos≥.1·기타좌표계 뒷면 바깥 법선 방향 thumb3 몸체합력≥.01N을 함께 요구한다. 힘이 더 커져도 점수는 늘지 않으며 접촉쌍·현 압력 인증은 아니다. 상태552(기존544+엄지8열)·토큰24열·우선8·손가락 직접입력20·단계3331이며 v21 이하 저장본의 strict resume를 거부한다. 기본 B전체 .02/초·shape0, LH21 움직임 비용0·전체 가동범위·독립4rad/s 누적제어·PD·035/v14·자유 기타는 유지한다. **CPU418검사·실제 접촉 시험·1024 저장/재개·128환경100회 학습/평가를 완료했다. 평균2.016/67·안전112/128이며 B복귀80%·약지 극단 자세·엄지 지속 접촉 학습은 미충족이다.** [현행 결과](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_hand_contact_v22/README.md)를 따른다.

이전 v21의 기하 전용 엄지 보상·551상태 결과는 [과거 비교 결과](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_hand_contact_v21/COMPARISON_RESULTS.md)에 보존했다. 같은 초기 모델·seed7·128환경·100업데이트의 B 계수 비교에서 .04/초는 평균0.34375/67·안전128/128, .02/초는5.1484375/67·안전128/128이었다. .04를 기본으로 채택하지 않고 .02를 유지한다. 단일 seed의 짧은 이전 버전 비교이며 v22 성과나 장기 수렴 증거가 아니다.

이전 v19 도입 시 검증 기록: v19는 관련 CPU299개·독립 검수와 실제16환경/H32/65업데이트 및65→66 재개 검증을 통과했다. 작은 실행의 평균달성은 v18 0.625/67→v19 0.5625/67, 안전완주는16→15/16으로 성능 향상은 확인하지 못했다. 구동·접촉분할·저장/재개 검증과 장기성과를 구분하며 [확정 결과](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/README.md)를 따른다. large1024/H32의12업데이트 구동도 완료했지만6.4초 동안 기타 변위 물리종료33회가 발생했고 전곡완주는0이다. OOM은 없었으며 이는 자원·기록 구동 검사이고 장기 안정성이나 성능 향상 검증이 아니다.

**이전 v17 장기 학습 완료(2026-10-24).** large/1024환경/H32/seed7의 새 2,000업데이트·65,536,000전이와 평가·분석·영상 저장을 완료했다. 고정 1024환경 첫 종료곡의 평균 달성음은 초기 0.2979/67, 평가한 학습모델 중 최고 1,000회 5.9961/67(safe949), 최종 2,000회 5.6045/67(safe887)이다. 연속 clean 달성의 학습 지표이며 v18 성과나 음향 성공률이 아니다. [v17 결과·영상](/home/ajou/yigyu/3/docs/2026-10-24/guitar_learning_long_training_v17/RESULTS.md).

**이전 v16 장기 학습 완료(2026-10-24).** large/1024환경/H32/seed7의 새2,000업데이트·65,536,000전이와 검증·고정평가·로그분석·영상 후처리를 완료했다. 고정1024환경 첫 종료곡 평균 달성음은 초기0.2334/67, 평가한 학습모델 중 최고1,500회7.2949/67(safe937), 최종2,000회5.2803/67(safe949)다. v16의 연속clean 달성 수치이며 누적clean 달성인 과거v8과 같은 성공 정의로 직접 비교하거나 v17 성과로 상속하지 않는다. 보상 항별 인과 효과·자연스러움 향상은 이 실행만으로 확정하지 않는다. [결과·상태·영상](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_long_training_v16/README.md) · [완료 상태 원문](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_long_training_v16/pipeline_status.json).

**이전 팔·손목 행동변화 감점 v16 구현·CPU 검증 완료(2026-10-23).** GPU왼손은정규화된명령차이|Δa|≤.05에서행동변화감점0,초과분e=max(|Δa|−.05,0)에만제곱감점을준다. 엄지포함LH21계수0・왼손목xyz .0025/초・나머지비손가락 .01/초이며기존39분모/60Hz를유지한다. .05는각도/속도문턱이나행동크기제한이아니다. 실제움직임·힘·제어평활화는바꾸지않고v15음감점・B권고・손가락움직임비용0・물리/PPO/035reset은유지한다. v15이하저장본을거부하고v16fresh/동일전체계약strictresume만따른다. 도입당시GPU/native・학습과감점유무비교학습은미실행이었다. 이후v16장기완료와별개로감점유무의인과효과는미확인이다. 관련28모듈274개CPU검사(기존265+새9)와독립20개검사·74개scalar감점대조를통과했다. [구현・검증 현황](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_action_change_v1/README.md).

**이전 오압현·누락·미달성 보상 v15 구현·CPU 검증 완료(2026-10-23).** GPU왼손은 wrong/missing 감점을 음길이D로 정규화하고 기존손가락균형계수b를 적용한다. 미달성 감점은 최장 audible연속clean `best_clean_streak`가 달성문턱에 얼마나 부족했는지에 비례한다. 이진left/미달성음수·연속달성문턱·한번지급은 유지한다. 원장에몸체별audible오압현원인·프렛범위·경계모호/다음음준비진단을추가하되wrong판정·준비창무감점은변경하지않는다. B약한권고·움직임비용0·물리·제어·PPO·reset은유지한다. v14이하저장본은거부하고v15fresh/동일전체계약strictresume만따른다. GPU/native·학습은이번미실행이며관련27모듈265개CPU검사(기존247+새18)와독립61개검사,별도810개원인bool/270개프렛범위/27개지원·모호·다음준비조합대조를통과했다. [구현·검증 현황](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_press_penalties_v1/README.md).

**이전 B 대기 자세 권고 보상 v14 구현·CPU 검증 완료(2026-10-23).** GPU왼손은 상시 관절분담 보상을0으로 하고 사용자가 선택한B에 가까운 대기 자세에만 최대0.01/초의 약한 보상을 준다. 어느 손가락이라도 압현준비창 press−2~end에 있거나 접촉·오압현·목표4cm이내이면 손 전체의 B보상은0이다. B는 필수경유·통과조건·벌점·제어목표가 아니며 압현 중 손가락 움직임을 제한하지 않는다. 기존035/v14초기자세·엄지·움직임비용0·v13추종·연속최초접촉/달성·물리·제어·PPO는 유지한다. v13이하 저장본은 거부하고 v14fresh/동일전체계약 strict resume만 따른다. 관련25모듈247개CPU검사(기존236+새11)를통과했고독립82개검사와172quality·43gate/rate scalar대조를통과했다. 이번GPU/native·학습은미실행이다. 간접적인 정책영향0이나 성능향상을 보장하지 않는다. [구현·검증 현황](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_preparation_B_v1/README.md).

**이전 접촉 배율 없는 추종 보상 v13 구현·CPU 검증 완료(2026-10-23).** GPU왼손 활성 pad 추종에서 candidate가 참일 때의2배만 제거한다. 거리품질 `(1+d/.04)^-2`와 기존2cm 이내최대20% 근접법선배율을 유지하며 추종률 상한은4→2/초다. 같은 패드위치·법선이면 접촉여부만으로 추종 보상이 바뀌지 않는다. 연속50ms 최초접촉·누적clean 유지보상·연속40% 중간달성·움직임비용0·물리·제어·PPO는 그대로다. 후반단계 추종축소는 이번에 적용하지 않는다. v12이하 저장본은 거부하고 v13fresh/동일전체계약 strict resume를 따른다. 관련24모듈236개CPU검사(기존229+새7), 독립65개검사와212slot선택/품질·53rate scalar대조(오차1e-14 이내), candidate반전시정확동일을통과했다. 이번GPU/native실행·실제학습은수행하지않았다. [구현·검증 현황](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_tracking_contact_independence_v1/README.md).

**이전 연속 clean 달성 보상 v12 구현·CPU 검증 완료(2026-10-23).** GPU 왼손의 음별 달성을 onset~end 안에서 clean이 연속 `min(D,max(50ms,0.4D))` 유지될 때로 변경한다(D=음 길이). 끊기면 clean_streak는0이며 한 번 달성한 left 플래그와 보너스는 음별 한 번 유지한다. 누적clean·held 진단과 `2×clean증가/D` 유지 보상은 그대로다. press~end의 연속50ms 최초접촉과 달성의 onset~end 창을 구분하며, 40%는 학습용 중간 달성으로 음 끝까지의 완전한 수행을 뜻하지 않는다. 손끝패드·손목영역·물리·제어·PPO·손가락 움직임 비용0은 유지한다. v11 이하 저장본은 거부하고 v12 fresh/동일전체계약 strict resume를 따른다. 관련23모듈229개 CPU검사(기존215+새14개), 최종0음길이guard 이후8모듈82개재검사와 독립75개검사·1152개 substep-target scalar대조를 통과했다. 이번 GPU/native·실제학습은 수행하지 않았다. [구현·검증 현황](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_continuous_clean_v1/README.md).

**이전 연속 최초접촉 보상 v11 구현·CPU 검증 완료(2026-10-23).** GPU 왼손의 최초접촉 보너스를 press~end 안에서 유효 candidate가 연속 `min(50ms,end−press)` 유지될 때 음별 한 번 지급하도록 바꾼다. 중간에 끊기면 contact_streak는0으로 돌아가며 누적 contact_time은 진단으로 남긴다. 보너스0.5×손가락균형계수×단계계수와 clean 누적40%/최소50ms의 음별 성공, 손끝패드·손목영역·물리·제어·PPO는 유지한다. 후반 시점별 차등 보상은 추가하지 않는다. v10 이하 checkpoint는 재개하지 않고 v11 fresh/동일v11 전체 계약끼리 strict resume한다. 관련22모듈215개 CPU검사(새 전용13개 포함)와 독립61개 검사·비정렬 시간창640개 substep-target의 scalar대조를 통과했다. GPU학습·장기 실행은 이번에 수행하지 않았다. [구현·검증 현황](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_continuous_contact_v1/README.md).

**이전 손끝 패드 기반 압현 v10 구현·짧은 GPU 검증 완료(2026-10-23).** GPU 왼손의 접근과 양성 압현 후보를 지정 손가락 끝마디 finger3의 굽힘 안쪽·끝부분 표면으로 제한한다. 접근과 positive는 같은 지판 압현면·프렛 셀 안쪽2mm를 쓰며, positive는 동일 패드점의 위치·법선과 해당 끝마디의 몸체 하중을 함께 요구한다. 이는 접촉 몸체 쌍·실제 압력 인증이 아니다. 손목의 넓은 영역, 관측544·8우선토큰·3331 curriculum·손가락 움직임 비용0·제어·물리·PPO는 유지한다. v9 이하 저장본은 재개하지 않고 v10 fresh로 시작하며 동일v10 전체 계약끼리만 strict resume한다. 관련 CPU21모듈202검사·독립68검사·NumPy77목표 대조와 실제 large/1024/H32/seed7의 새2회+재개1회+목표구간8회(합계11업데이트·360,448전이)를 통과했다. 두 재개 경계에서 모델·양Adam·RNG·3331값 상태를 정확 복원했고, 목표 활성4.267초 구간에서 접근·추종·접촉·유지 신호 연결을 확인했다. 완료곡은0이며 종료11개는 모두 물리실패였다. 이 짧은 구동·저장·복구 검증은 장기 성능·자연스러운 자세·물리 무실패의 증거가 아니다. [이번 구현·검증 현황](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_fingertip_pad_v1/README.md).

**이전 손목 영역 보상 v9 구현·구동 검증 완료(2026-10-23).** GPU 왼손의 점·초기 회전 추종을 작업 프렛 묶음 중심 ±6cm, 넥 아래 1~8cm, 지판 뒤 연주자 쪽 2~11cm의 기타 상대 영역으로 바꾼다. 영역 안·경계에서는 손목 위치 보상 0, 밖에서는 초과 거리만 감점하며 중심·특정 회전을 강요하지 않는다. 준비 3초를 포함해 모든 물리 표본에서 적용한다. v8 이하 저장본을 재개하지 않고 새 v9로 시작하며 동일 v9 전체 계약끼리만 strict resume한다. 관련 CPU174개 검사와 실제 large/1024/H32 새2회·재개1회 구동·저장·복구를 확인했다. 별도 확장 검사에는 기존512/544 가정 불일치1개가 남아 있다. 장기학습 성능은 확인하지 않았다. [구현·검증 현황](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_wrist_region_v1/README.md).

**이전 v8 장기 학습 완료(2026-10-23):** large/1024환경/H32/seed7의 fresh2000업데이트·65,536,000전이를 약6시간46분에 정상 종료하고 전체CRC/EOF·438소스·583입력SHA·3331·모델/양Adam·실제2000→2001 strict resume를 검증했다. 고정1024 첫곡 평균은 초기3.863281/67음→평가한 학습 모델 중 최고1500회7.826172음(safe999)→최종2000회6.738281음(safe990)이다. 모든67음 성공0·단계0이고, 검지/중지 부족·최종 소지 성과 소실·끝관절 집중이 남았다. 같은 안전965환경에서도 후반 하락이 확인돼 장기 연주 수렴·자연스러움 개선 완료로 분류하지 않는다. 대표/최종 전신·손 영상과 비교본을 보존했다. [결과·로그·영상](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/README.md).

GPU 왼손은 **552상태·8우선순위 토큰·손가락별 전용 출력 분기**를 사용한다. 기존544열과 손가락별 직접입력20을 보존하고 엄지 기하·후보8열을 더했다. 손가락 움직임 비용0·원거리 접근신호·PBRS·reward/cost advantage 개별정규화·GAEλ0.98을 유지한다. 현행v22는 선별 충돌·음 사이 B·추종 동기화·엄지 안내를 바꾸며 이전v8~v20의 성과를 상속하지 않는다. 성공문턱·전체 native범위·독립 누적제어·PD·안전·CPU왼손/오른손은 유지한다.

이전 v8의 실제 large/1024/H32 새 모델8회와 동일계약 재개1회(총294,912전이)는 정상 종료·로그/입력SHA·모델/두Adam/RNG/3331복원을 검증했다. 관련CPU218개 중217개 통과, 기존512/544가정 실패1개는 분리했다. 이 짧은 검증은 전곡 성능이나 자연스러움 향상의 증거가 아니다.

**이전 보상v6 장기 결과:** large/1024환경/H32/seed7의 유효1300+재개700회·65,536,000전이를 완료하고 전체 선택 raw·3331·입력 SHA·모델/양 optimizer·새700 정상 close를 검산했다. 저장 공간·NTFS/FUSE EIO로 중단된 별도 분기80회는 합산하지 않으며, 원실행의 전체 EOF/정상 close나 연속 fresh2000회를 주장하지 않는다. 동일1024환경 고정 평가에서 초기3.8408203125/67음·safe1024, 평가한 학습모델 중 best500은5.4287109375음·safe414, 최종2000은0.7451171875음·safe961이다. 사전 선정 규칙의 평균 달성은 높아졌지만 안전성이 크게 낮아졌고 후반 성과가 퇴행했으므로 장기 연주 개선·수렴으로 분류하지 않는다. 모든 모델은 단계0·67음 전체 성공0이며, 실제 자세 캡처에서도 끝관절 편중·대기 자세 문제가 남았다. [장기 결과·평가·자세·영상](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v6/README.md) · [학습 수집 해석](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v6/training_findings.md).

**이전v5 개선:** 당시 GPU 왼손 보상은v5였다. 이전 최종 영상에서 실제 중간 관절이 거의 펴지고 끝관절만 크게 굽혀지는 현상을 확인해, 실제 몸체 회전 기반의 부드러운 관절 분담 보상과 비사용 손가락의 넓은 대기 자세 보상을 추가했다. 손가락별 추종 보상은 해당 손가락의4축 요청만 보며 기존 축당 계수1/21을 유지한다. 전체 가동범위·독립 누적 제어·PD·물리·관측512·기존 성공/안전 기준은 유지한다. 보상v4 저장본은 strict resume할 수 없어 새v5 모델로 시작한다. 짧은 GPU 검증을 자연스러운 연주 학습의 완료로 해석하지 않는다. [손가락 관절 분담 개선·검증](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_coordination_v1/README.md).

이전 보상v4의436소스로 GPU 왼손 `large/1024환경/H32/seed7` fresh2,000회·65,536,000전이를 약6시간18분 동안 끊김 없이 학습하고 정상 종료했다. 같은 고정1,024환경 첫 곡 평가에서 초기4.02734375→최종5.42578125/67음, 안전 완주1,024→1,019개다. 평가한500/1000/1500/2000회 중 최종 모델이 가장 좋았지만 단계0·중지/소지0음·67음 전체 성공0이며, 손가락별 성과 유지가 부족하다. 이 장기 실행은 진단 추가만의 성능 효과나 소지 추종 잔차 해결을 입증하지 않는다. [보상v4의436소스 장기 학습·분석·영상](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v4/README.md).

현재 환경·측정·학습·평가 코드는 이 패키지에서 관리한다. 새 손별 학습은 아래 기본 실행에서 시작한다. 연구 범위·실험별 성과는 [master_plan](/home/ajou/yigyu/3/master_plan/README.md)을 따른다. 상태 차원이나 파일 버전이 같아도 목표·보상·입력 SHA가 다른 checkpoint를 혼용하지 않는다.

이전 진단v2 변경에서는 손가락 실제 자세 진단을 추가했다. `episodes.jsonl`의 `left_finger_motion.base_rotation`은 검지·중지·약지·소지 기저의 palm 상대 회전과 zero-y 명령 참조 대비 회전오차를60Hz RMS/최대로 기록한다. 두 관절각의 추종 오차만으로 실제 전체 자세를 판단하지 않는다. 실제 N6 대조에서 굽힌 소지의 벌림 추종 잔차가 남았고 물리 반복4→16도 개선하지 못해 기본4를 유지했다. 이번 변경은 진단v2이며 상태512·보상v4·제어·PPO는 같다. 전체 계약 비교가 달라지므로 기존 checkpoint의 strict resume를 완화하지 않는다. 과거435소스 결과를 이전 보상v4의436소스 학습 성과로 상속하지 않는다. [추가 진단·검증](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_tracking_fix_v1/README.md).

## v22 손가락 충돌·B 복귀·엄지 안내

B품질은 `1/(1+Σ(excess/30°)²)`·각 중심±15도 평탄대역이며 기본 전체 최대 .02/초·고정4분모·각 .005/초다. v22 B gate는 손가락별 악보의 press~end 보호구간 합집합을 사용하며 달성 플래그가 켜져도 음 끝까지 보호한다. 끝난 뒤 .05초 해제 유예+.1초 fade, 다음 press 전 .35초 준비 보호+.1초 fade를 쓴다. 같은 손가락의 gap≤.25초는 직접 전환, .25~.6초는 부분 B, .6초 이상은 전체 B 후보이며 실제 fade가 겹치면 후보보다 gate가 작다. 지난 candidate/wrong와 4cm 근접 veto는 제거하고 관련 목표의 비유한 거리 보호는 유지한다. 손가락 추종 v8은 악보 idle의 보완값 `1−idle_weight`를 곱해 B와 경쟁을 줄이며 손목·팔의 기존 2초 안내는 유지한다. 최신240Hz의 실제 gate를 관측에 캐시하고 H32경계에서는 목표·원장·gate를 초기화하지 않는다.

- `--finger-standby-rate 0.04`: B전체최대0.04/초·각0.01/초의 별도 비교군.
- `--finger-shape`: 추종 목표가 있는 손가락의 `relu(DIP-PIP-50°)`를 완만하게 낮추는 전체최대0.004/초·각0.001/초 선호를 기존coordination슬롯에 추가. 기본은0이며 압현·clean 중에도 적용한다.

두 옵션은 GPU왼손만 허용하며 재개 때도 같은 계수·옵션을 지정한다. 자동 B복귀 제어는 없고 행동0은 현재 목표 유지다. PD·힘상한·전체 native범위·4rad/s·LH21 움직임 비용0·035/v14·자유 기타를 유지한다. 엄지 전용 `song_thumb_support`는 thumb3 굽힘 안쪽 패치128표본의 같은 점·법선을 사용한다. 목표는 유한 source 넥 뒷면의 폭 중앙50%·작업 프렛 중심 Gy±4cm다. 간격0~3mm에서 거리품질 최대이며 부드러운 거리·방향·영역 품질과 −1mm 이하0 조건을 유지한다. v22는 기하 품질Q에 `.01×Q + .01×Q×contact_candidate`/초를 지급한다. 후보는 같은 점의 gap −1~0.5mm·영역 내부·법선cos≥.1과 thumb3 합력의 뒷면 바깥 법선 성분≥.01N을 함께 요구한다. 힘 크기에 비례한 추가 점수는 없고 전체 최대 .02/초를240Hz 적분하며 기존 approach계수·실패tick 양성억제를 적용한다. 한 표본의 합산 지급률이 가장 큰 점을 선택하고 동률은 품질·거리 순으로 정하므로 다른 점의 기하와 하중을 섞지 않는다. 기하·하중 후보는 접촉쌍·압력·음향 인증이 아니다. 강제 부착·직접 기타 힘·새 실패/reset·관절 목표 주입은 없다.

선별 충돌은 물리LH15마디의 서로 다른 손가락90쌍만 켜고 다른 쌍의 기존 관계를 보존한다. aggregate self_collisions=True만으로 이전 공통필터128의 차단이 해제되지는 않았으므로 새 필터와 native readback을 계약에 기록한다. 구동·보상/제어 검증과 실제 학습성과는 [v22 결과](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_hand_contact_v22/README.md)에서 구분한다.


## 곡 단위 손별 학습 시작

`guitar_learning.train`은 합의한 초기 자세에서 새 손별 정책으로 곡 전체를 학습한다. 기본 곡은 검수된 `data/song_bundles/05_BN2-131-B_solo`의67음 전부다. GPU 왼손은 실제 손가락 표면 접근·압현·곡 연결을 단계적으로, 오른손은 타현을 학습하며 선택하지 않은 손의 정책 행동은0이다. 시작 전에 BC·전문가 모델이나 과거 성공 평가4회를 준비할 필요가 없다.

프로젝트 루트에서 Isaac Gym Preview4가 설치된 `rl38` 환경을 사용한다. 먼저 실행 환경을 설정한다.

```bash
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3${PYTHONPATH:+:$PYTHONPATH}
export PYTHONDONTWRITEBYTECODE=1
```

학습할 손을 골라 아래 명령 중 하나를 실행한다. `--out`은 아직 존재하지 않는 새 출력 경로로 지정한다.

```bash
python -m guitar_learning.train --hand left --device cuda:0 --physics gpu --song 05_BN2-131-B_solo --out /home/ajou/yigyu/3/runs/left_song_press_v1
python -m guitar_learning.train --hand right --device cuda:0 --physics gpu --song 05_BN2-131-B_solo --out /home/ajou/yigyu/3/docs/2026-10-20/right_song_01
```

흐름은 **곡 입력 확인 → 하나의 GPU PhysX 장면에 환경별 aggregate로 배치 → 합의한035/v14 초기 자세 복원 → 준비3초와 곡을 연속 진행 → 32tick마다 GPU PPO 업데이트 → 모델 저장**이다. native 대기는0초이며 첫 tick부터 정책이 행동한다. 기본 곡은 원오디오29.3064초에 정책 준비3초·말미0.5초를 더하고60Hz 경계로 올린1969tick, 약32.8167초다. 원곡 시간축과67음 전체를 유지하며GPU왼손552상태/오른손500상태·39행동·실제240Hz 접촉/안전 측정을 사용한다.

기본 GPU 실행은 환경128개·수집32tick·PPO100업데이트·`--device cuda:0`·seed7·medium 모델이다. `--num-envs`는1~1024를 지원한다. 누적 제어 적용 전 위치제어 계약의 과거2000회 결과는 [실행·평가·영상](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/README.md)을, 구현 초기 검증은 [표면 압현 개선·검증 현황](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_fretting_v1/README.md)을 따른다. 이전 보상v2의 `large`/1024환경 장기 결과는아래 과거 기록이다. 곡 전체는1969tick이며32tick의 PPO 경계에서도 시계와 음별 원장이 이어진다. `--horizon`을 짧게 지정해도 PPO 업데이트 경계에서 장면·기타·곡 시계·음별 원장을 초기화하지 않고 다음 수집으로 이어간다. 곡 종료나 물리 실패 때만 초기 자세로 돌아간다. `--updates 1`은 PPO 업데이트 한 번을 뜻하며, 물리 실패가 있으면 곡 완주를 보장하지 않는다.

**이전435소스 압현 접근·유지 개선100회:** GPU 왼손의 실제 압현면 접근·감속·유지 보완을 구현했다. 실제 large1024/H32 fresh100회·3,276,800전이, 동결435Python·580입력·로그/저장·실제100→101재개 검증을 통과했다. 다만 고정0/100 평가에서 평균3.8046875→0.0/67음, 안전 완주1024→1021/1024로 연주 성능 향상을 입증하지 못했다. 해당435소스100회 평가 당시에는 지속 한방향 명령이 남아2000회 장기 실행을 진행하지 않았다. 이전 보상v4의436소스의 장기 결과는 위 기록을 따른다. 충돌하지 않는 현 중심선 대신 pin된 넥 mesh에서 추출한 압현면을 접근 관측·보상 목표로 사용하며, 현재 음 우선 선택과 실제 속도/지속 이동 명령을 함께 보는 유한 양성 보상을 추가했다. 관절 가동범위·누적 제어·PD·물리·기존 접촉/성공 판정은 유지한다. 새 보상v4/표면 관측v2 계약으로 fresh 시작하며 보상v3 모델의 strict resume를 거부한다. [이번 개선·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_press_control_v1/README.md).

**이전 보상v3 누적 제어 검증:** GPU 왼손21축 누적 제어 구현과 검증을 완료했다. CPU843개·GPU84명령시험·large1024/H32 fresh100회·실제100→101재개를 통과했고 실제 굽힘/펴짐을 확인했다. 다만 고정1024평가에서 평균 달성4.200→0.978/67음, 안전 완료1023→311곡으로 회귀해 조건부2000회 장기 학습은 실행하지 않았다. CPU·오른손·팔/손목·PD·보상·PPO는 유지했고 이전 위치제어 모델은 새 행동 계약에 strict resume할 수 없다. [구현·검증·영상](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_incremental_fingers_v1/README.md).

**누적 제어 적용 전 GPU 왼손 장기 결과:** 보상v3·표면 관측v1의 새 정책을 `large/1024환경/H32/seed7`로 시작해 저장본 복구를 포함한2,000회·65,536,000전이 경로를 완료했다. 마지막1,200회는 정상 종료했고 전체CPU831검사·원시64,000행·3331값 단계 재생·입력SHA 검증을 통과했다. 초기/최종 고정1024환경 평가는 평균3.861→8.301/67음, 안전 시간축 완료1024→1020곡,67음 전체 달성0→0곡이다. 최종 달성98.624%는 검지이고 중지0·약지111·새끼6개로 편중돼 곡 연주 학습 완료로 해석하지 않는다. 접촉 단계1에 머물렀다. 앞선 세 SIGFPE와 미저장63회는 별도 보존하며 끊김 없는 단일2000회 실행은 아니다. 로그 실수 변환은 기존 Dragon4 방식으로 우회했고 x87 근본 원인은 미확인이다. [결과·분석·전신영상](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/README.md). 물리·힘·성공·보상/PPO 계약은 이번 기록 오류 수정에서 바꾸지 않았다.

**이전 보상v2의 장기 실행 검증:** 환경별 aggregate를 적용한 GPU 물리 `guitar_learning.gpu_batch.v3`와 왼손 보상 `guitar_learning.gpu_tensor_song_reward.v2`에서 `large/1024환경/H32/seed7` 왼손 학습을 2000업데이트·65,536,000전이·5시간41분25초 동안 정상 완료했다. 전체 raw 64,000행의 CRC·에피소드 대응, 입력 568개 SHA·동결 Python 423개·최종 모델/optimizer의 유한 텐서 167개 검사를 통과했다. Torch 캐시 반환 후 GPU 여유는 최저 7.374GiB·최종 8.206GiB였으며 비Torch 메모리 추정 증가는 136MiB 이후 일정하게 유지됐다. 이전 보상v2·동결 소스의 해당 실행 조건에서의 검증이며, 현재 보상v22의 장기 결과로 상속하지 않는다. 모든 설정의 메모리 누수 해결이나 물리적 무실패를 뜻하지 않는다. [2000업데이트 실행·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/README.md) · [실제2000→2001 재개 검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/resume_verification.json).

위 이전 보상v2 학습 중 종료 34,069회는 곡 시간축 완료 31,524회와 물리 실패 2,545회이며, 67음 전체 과제 성공은 0회다. 당시 curriculum은 1788업데이트에 진행도 1.0(압현 단계)에 진입했고 다음 단계 조건은접촉 후보 평균60%였다. 초기/최종 고정 정책의 각 1024환경 별도 평가도 종료·입력 검증을 통과했다. 안전 타임라인 완료는 1024→1023곡, 전체 첫 곡의 평균 달성 음은 3.969→4.232/67이며 전곡 과제 성공은 모두 0이다. 두 모델의 curriculum 관측이 다르고 특정 음의 향상·저하가 공존하므로 일반적인 연주 향상이나 수렴을 뜻하지 않는다. 첫 평가의 native 종료 실패와 보완 후 정상 재평가도 [별도 평가 분석](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/README.md)에 구분해 기록했다.

**과거2026-10-20 GPU v1 진단:** 대규모 GPU 배치에서 행동0만으로도 기타 이탈·회전 실패가 재현됐다.128은 현재 설정의 기본값이며 안정적인 학습 권장값으로 검증된 수가 아니다. [실제 CPU/GPU 무행동 비교 영상과 원인 범위](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_gpu_failure_video_v1/README.md)를 먼저 확인한다. 이 결과는 현재 aggregate v3 적용 전 진단이며, 당시 1024환경의 장기 안정 학습을 권장하지 않은 근거다.

**과거2026-10-21 GPU v2 완화 수정:** GPU 기타를39개 몸체·38개 고정 관절에서 하나의 자유 강체로 바꿨다. 질량·COM·관성과89개 실제 충돌 형상을 유지하고, 기존39개 마커는 강체 자세에서 복원한다. 두 비물리 proxy의 충돌은 완전히 제외했다. 수치 폭발은 크게 줄었지만 긴 무행동 시험의 느린 이탈이 남으므로 안정화 완료나1024환경 권장으로 해석하지 않는다. [원인 분리·수정·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_contact_fix_v1/README.md)을 따른다. 이전GPU v1 checkpoint도 새GPU v2 물리 계약에 strict resume할 수 없다.

**aggregate 적용 전 장기 실행 점검:** 사용자가 자연스러운 이탈/종료는 허용했다. 다만 실제`large/H32` 학습에서1024환경은39업데이트까지 진행한 뒤PhysX 메모리 부족으로 중단됐고,512환경도후반 GPU 여유가약9.2→1.8GiB로 감소해94업데이트에서정상중단했다. 환경 수를줄이는것만으로긴학습준비가됐다고판정하지않는다. 당시에는장기학습권장환경수가미확정이었다. [전체점검·수정·원자료](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_run_check_v1/README.md)를따른다. 기록RAM누적·PPO전체평가피크·Torch캐시경쟁을줄였고관련60개검사와실제저장모델94→95재개는통과했지만,당시네이티브메모리증가는미해결이었다. 이후 aggregate v3의 2000업데이트 결과는 위 이전 보상v2 검증과 구분한다.

추가 저장 간격은 `--checkpoint-every N`(기본250, 양의 정수)으로 지정한다. 초기·마지막 상태는 간격과 무관하게 저장하며, 2,000업데이트라면 총9개다. 모델·두 optimizer·RNG·curriculum을 보존한다. GPU는 `checkpoint_manifest.jsonl`에 각 파일의 크기·SHA·저장 시간을 기록하고, `report.json`에서 초기·중간·마지막·실패 복구 저장을 집계한다. `song_report.json`은 v2의 counter/`episodes_path`를 쓰며 counter는 PPO에 반영된 수집 기준이다. 오류·중단 때 원시 기록의 미반영분은 journal의 discarded와 구분한다. 실행 완료와 음악 성공은 별개다. 현재 GPU 저장 구조와 읽기 명령은 [로그 안내](docs/LOGGING.md)를 따른다.

기본 실행은 GPU가 없으면 오류로 종료한다. `--device auto`를 명시하면 CUDA를 사용할 수 있으면 `cuda:0`, 그렇지 않으면 CPU를 선택하며 실제 장치를 `settings.json`에 저장한다. 필요하면 `--num-envs`, `--updates`, `--horizon`, `--device auto/cpu/cuda:0`, `--physics auto/cpu/gpu`, `--seed`, `--size`로 바꾼다. `--physics auto`는CUDA 정책이면GPU 물리, CPU 정책이면CPU 물리를 선택한다. 이전 CPU 물리 경로는 `--device cuda:0 --physics cpu` 또는 `--device cpu --physics cpu`로 명시하며 환경1/2/4/8/16·기본수집전곡 조건을 유지한다. `--device cuda:0`를 명시하면 CUDA를 사용할 수 없을 때 오류로 종료한다.

`--song`은 `data/song_bundles` 아래의 곡 식별자다. 시작 전에 전체 악보·타현 계획·오디오 길이를 확인하고 지원하지 않는 입력은 거부한다. 현재 검수된 압현음·일반 타현/명시적 재타현 곡을 지원하며 열린현이나 지원되지 않는 동작을 임의로 생략하지 않는다. 확인된 곡은 아래와 같다.

| 곡 식별자 | 목표 음 수 | 준비·말미 포함 길이 |
| --- | ---: | ---: |
| `02_Jazz1-200-B_solo` |42|17.9초|
| `03_Rock1-130-A_solo` |59|25.65초|
| `05_BN1-129-Eb_solo` |46|25.8333초|
| `05_BN2-131-B_solo` |67|32.8167초|
| `05_Rock2-142-D_solo` |84|30.55초|

실행 설정은 출력의 settings.json에 저장한다. 같은 계약의 재개는 같은 손·설정과 새 출력 경로에 `--resume /절대경로/checkpoint.pt`를 지정한다. 관측·행동·목표·보상·물리·PPO의 전체 계약을 엄격 비교하고 실행 입력 SHA는 별도로 검증한다. GPU왼손 v22는552상태/8우선순위·새 충돌·B/추종/엄지 보상 계약이므로 v21 이하와 과거563단음·500전곡·512위치제어 모델의 strict resume·자동 Actor이전을 거부한다. 동일v22 전체 계약끼리만 재개한다. 오른손500은 GPU/CPU 물리·제어·접촉 계약 차이 때문에 기존 CPU checkpoint를 재개할 수 없다. 기존GPU v1/v2도 현행 물리 계약과 호환되지 않는다.

같은 실행 안에서 PPO 수집을 나눌 때는 곡 중간 상태를 유지한다. 새 프로세스의 `--resume`은 모델·optimizer·난수 상태를 복원하고, 물리 환경은 초기 자세에서 새 곡 에피소드를 시작한다.

선택한 손의 보상과 전곡 성공을 학습 기준으로 삼는다. 양손 협응 성공과 원래50/100ms 음악 판정은 별도 진단이다. `song_report.json`은 실제 종료 에피소드와 손별 성공·물리 실패를 저장한다. 진행 중인 곡의 원장은 메모리에 유지하며 이 파일에 부분 원장 snapshot을 저장하지 않는다. 부분 수집을 완주 성공으로 세지 않는다. 접촉·기하 타현의 성공을 실제 음향 성공으로 해석하지 않는다.

## GPU 물리·관측·보상

기본 실행은 환경마다 프로세스를 만들지 않는다. 하나의 GPU PhysX 시뮬레이터에서 모든 환경을 동시에 진행하고, 관절·몸체·접촉 힘·Jacobian·유한 하체/상체 제어·관측·보상·PPO를CUDA 텐서로 처리한다. 환경마다 68몸체·145shape 용량의 aggregate에 human→guitar→chair를 넣고 self-collision을 유지한다. 완료 에피소드 요약과 로그만 CPU로 옮긴다. 물리240Hz·정책60Hz이며 선택한 환경만 에피소드 경계에서 초기화한다.

GPU 왼손v10은 실제 finger3 충돌mesh의 패드 후보 표면을 잘라128개 면적층화 표본을 만든다. positive는 같은 패드점의 목표현 횡오차≤3mm·지판면 signed높이−1~+3mm·프렛셀안쪽2mm·패드 법선cos≥0.1 및 같은 finger3 몸체의GPU 접촉합력≥0.01N을 요구한다. full finger2/3·엄지 표면은 wrong/지지 검사에 남긴다. 패드의 source 해부학 label은 없고 기하로 정의한 실험적 부분집합이다. GPU 합력은 pair/witness·현 압력·음향을 인증하지 않으며 CPU pair-feature 경로와 구분한다.

하체는 GPU 기하 질량행렬·유한 stable PD·반복 IK, 상체는 중력 보상·Chest/오른팔 지지 제어를 사용한다. native힘 상한과관절 제한을 유지하며 세부 solver 차이를 새 계약에 기록한다. 초기035/v14·자유 기타·중력ON·스트랩OFF·왼손 유연 프로필을 유지한다. 기존 CPU512/500 checkpoint도 새GPU 실행에 strict resume할 수 없으며 새 GPU 계약의 checkpoint끼리 재개한다.

구현은 `gpu/scene.py`·`gpu/control.py`·`gpu/environment.py`·`gpu/geometry.py`, 수집과 학습은 `training/gpu_pool.py`·`training/gpu_runner.py`다. CPU 재현 경로와 전문 실험기는 기존 구현을 유지한다.

`gpu/rigid_guitar.py`와`assets/gpu_rigid_guitar_v1/`은GPU 전용 강체 표현이다. native몸체는환경당68개, 관측의 논리몸체는106개다. 논리 기타 마커의 위치·회전·각 마커 COM 속도를 복원하며, 기타 전체 접촉 합력은 논리root에만 표시한다. 마커별 접촉력을 만들어 배분하지 않는다. native질량행렬도CUDA에서 제공됨을 확인했으며, 현재 기하 질량 경로는 별도 비교 후 유지한 명시적 구현 선택이다.

## 왼손 손가락 제어

GPU 기본 왼손은 손가락21축(엄지5축·검지~새끼각4축)에 `guitar_learning.gpu_left_incremental_fingers.v1`을 사용한다. 매60Hz 틱에 `목표_next = clamp(목표_previous + 행동×4/60, native하한, native상한)`으로 움직인다. 행동0은 현재 목표 유지이고 반대 명령은 다음틱부터 목표를 반전한다. 한계 밖 누적값을 남기지 않는다. 초기035/v14는 에피소드 경계에서 복원하고 H32 수집 경계에서는 목표를 이어간다. 실제 관절 반응은 접촉과 native PD를 따른다.

| 항목 | GPU 왼손 손가락21축 |
| --- | --- |
| 목표 변화율 | 행동×4rad/s, 최대4rad/s |
| 목표 평활화 | 손가락은 우회; 팔/손목 등은 기존0.2 |
| 목표 범위 | 기존 native 관절 하한~상한 전체 |
| 검지·중지·약지·새끼 native K/D | 12/1.5 |
| 엄지 native K/D | 8/1.25 |
| 기존 effort 상한 | 엄지4Nm, 다른 손가락20Nm |

CPU 왼손은 기존 `flexible_left_fingers.v1`의 초기 자세 기준 비례 위치·평활화0.45를 유지한다. GPU 오른손·팔/손목·전문 실행기도 기존 제어를 따른다. native PD 프로필은 준비 자세 복원 후 step0에서 한 번 적용하고 이후 reset에서 유지한다. 관절 한계·POSITION 모드·힘 상한과 물리 안전은 그대로다. 엄지는 넥에 고정하거나 비교 이미지의 후보 자세를 강제하지 않는다.

누적 제어 도입 당시에는 관측512·행동39 차원이 같아도 행동 의미가 달라 이전 위치 제어 checkpoint를 strict resume하지 않는다. 새 정책에서 시작하며 새 계약끼리만 재개한다. 이전 장기 결과는 누적 제어 성과로 상속하지 않는다. [누적 제어 구현·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_incremental_fingers_v1/README.md).

구현은 [GPU 목표 제어](gpu/control.py), 기존 PD 프로필은 [손가락 설정](core/finger_control.py)과 [native 세션](runtime/finger_session.py)을 따른다. 종료 에피소드의 움직임 진단은60Hz 제어 끝점으로 집계하며 실제240Hz 극값이나 압현 성공과 구분한다.

## 왼손의 보상 단계

GPU 왼손은552상태와64×24 음 토큰·손가락별 우선순위8×24 토큰을 받는다. 표면 관측v5의 토큰9/10은 pad candidate/full-surface wrong이다. 토큰16~21은 지정finger3 패드 실제 mesh 표면에서 **넥 압현면의 목표 선분**까지의 오차와 실제 상대속도다. pin된 충돌 neck mesh의 상향 평면을 추출하고(현재Gz9.3mm), 현의x/y를 유지해 투영한 뒤 프렛 셀 안쪽2mm~안쪽2mm·유한 현 범위로 제한한다. 현 중심Gz12.3mm·기존±3mm 접촉 판정과 구분한다. 속도는 실제 선택점의 움직이는 기타 프레임 상대속도 음수이며 샘플 교체 차분이 아니다. scale3cm/0.5m/s는 유지한다. 실제 cooked 접촉·하중은 별도 검증 대상이다.

접근 보상은 공통 손가락 목표 선택기의 유효 tracking slot0만 최대4개 합산하는 시간 의존 potential `Φ=Σ_selected w_f·exp(-표면거리/0.03)`에 `γΦ(next)−Φ(current)`를 적용한다. γ는 PPO reward γ와 같은 0.99이며 접근 계수는 단계와 무관하게 1이다. 실제 terminal의 다음 potential만 0으로 하고 H32 경계에서는 이어간다. 접근 potential과 양성 접촉·유지·음 달성에는 `w_f=M/(곡에 존재하는 손가락 수×그 손가락의 음 수)`를 적용한다. 기본67음의 검지/중지/약지/새끼 가중치는 약0.670/0.931/1.396/1.396이다.

지정 손가락·현·프렛의 pad기하는 유지하며, GPU왼손 음별달성만 onset~end의 연속clean_streak가 min(D,max(50ms,0.4D))를 처음 채울 때로 변경한다. 누적clean·held와 유지보상은 유지한다. 40%는 학습용 중간달성이며 음끝까지 완전한연주를 뜻하지 않는다. press~end에서 최장 연속 contact_streak의 문턱 min(50ms,end−press) 대비 증가분에 원시 예산 최대0.5b를 분할하고, contact_done은 실제 연속 문턱을 채운 때만 참으로 하며, 음 진행 중에는 `2×Δclean/음 길이` 유지 보상을 달성 이후에도 계속 준다. 연속 clean 달성 문턱을 처음 넘을 때의 보너스는 기존0.5이며 이후 끊겨도 left는 유지하고 다시 지급하지 않는다. 이 양성 항들은 손가락 가중치와 해당 단계 비중을 적용한다. wrong/missing원시감점은각각−sum(b*wrong_dt/D),−.5sum(b*missing_dt/D)이고미달성은−.5sum(new_missed*b*(1−min(best_clean_streak/required,1)))다. 기존legacy단계계수와행동변화/terminal/안전비용은유지한다. 진단wrong/missing초누적과이진미달성음수는그대로다.

GPU 왼손 단계는 **표면 접근 → 접촉 → 유지·전환**이다. 최근256개 종료곡이 쌓인 뒤 안전 완주90% 이상이고 곡에 존재하는 모든 손가락의 접근 달성 평균이각 20% 이상이면0→1을 진행한다. 접근 달성은 준비 시작2초 전~음 끝에 표면거리10mm 이내 누적100ms(구간 길이를 넘지 않음)다. 1→2는 접근 기준 대신 각 손가락의 연속 contact_done 달성 평균20%를 사용하며 안전90% 조건은 유지한다. 실패곡은 모든 지표0으로 포함하고 부분 궤적은 제외하며, 새 안전 완주가 포함된 committed PPO 수집 뒤 최대0.1만 올린다. 이256곡은 독립 seed256개를 뜻하지 않는다.

단계0/1/2의 그룹 계수는 손목0.2/0.1/0.05, 접촉0.5/1/1, 유지·달성0.5/1/2, 접근1/1/1이며 중간 진행도는 선형 보간한다. 손목 항은 v9에서 양성 보상이 아니라 영역 밖 감점이다. 영역 안·경계는 0이고 안쪽 위치나 회전을 더 선호하지 않는다. 모든 단계에서 접촉·유지 보상은 유효하며 손목 ready는 압현이나 단계 전환의 gate가 아니다. 구체적 경계·수식은 [손목 영역 항](/home/ajou/yigyu/3/docs/2026-10-26/왼손보상구조/03_접근접촉유지보상.md:30)을 따른다.

완료곡의 `episodes.jsonl`에는 `left_note_ledger`(음별 표면 최단거리·노출/접근시간·기하/하중·오프렛/오손가락 원인·clean/contact/달성), 손가락별 지표와 `reward_components`를 저장한다. 최소거리0은 노출시간0일 수 있으므로 함께 해석하고, 기하/하중/원인별 시간은 겹칠 수 있다. `learning_metrics.jsonl`에는 수집 전이 기준 `reward_component_means`와 단계 요약을 기록한다. 새 GPU 실행은 업데이트별 JSON 사본을 만들지 않는다. GPU 단계 이력은 3331값 checkpoint buffer로 저장하며 CPU의8곡/27값 계약은 유지한다.

현재 song_finger_tracking은240Hz마다0~2/s의 양성률을 적분한다. 지정finger3 패드 거리품질 `(1+d/.04)^−2`와2cm 이내의 약한 법선배율에 악보 기반 `1−idle_weight`를 곱하며 candidate 접촉배율은1이다. 실제속도·요청행동·감속/정지 비용은 없다. PBRS는 기존 pad거리만 사용한다. 전역action_change는 LH21계수0·팔등 .01/s·왼손목xyz .0025/s·normalizedΔa .05이내 무감점·39분모를 유지한다. 기본 coordination0·선택shape .004/s·손가락별 B·엄지 뒷면 안내와 실제보상 로그를 구분한다. 전체 관절속도50rad/s 안전종료는 남는다. v21 이하 strict resume는 거부한다.

초기 latent Gaussian std는 기존 `exp(-3)≈0.049787`을 유지한다. std0.08 확대는 후속 분리 비교 실험이며 이번 기본값 변경에 포함하지 않는다. 기본 학습률·안전 비용 설정은 유지한다. GPU왼손의 PPO는 reward/cost advantage 각각 표준화 후 cost_weight로 결합하고 최종 표준화하며 GAEλ는0.98이다. H32·rewardγ0.99/costγ1·critic 손실은 유지하며 기존 KL retry의 자동 actor LR 감소는 적용한다. 설정 고정과 학습 중 파라미터 불변을 혼동하지 않는다.

CPU 왼손의 기존 손목→접촉 단계와 오른손 보상은 이번 GPU 표면 계약을 자동 상속하지 않는다. [표면 압현 개선·검증 현황](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_fretting_v1/README.md)을 따른다.

현재 GPU 왼손은 기존 실행 중 안전 비용과 종료 실패 비용 +5를 유지하고, 물리 실패 때 남은 곡 시간에 비례한 비용을 한 번 추가한다: `5 × max(곡 길이 − 실패가 발생한 실제 control tick 뒤의 곡 시각, 0)`(초당5). 이는측정한 미래 비용이 아닌 고정률 absorbing-failure 모델이며 curriculum 비중으로 낮추지 않는다. CPU와 오른손 비용 계약은 변경하지 않았다.

## 전문 실험과 이전 실행 재현

2026-10-20 기준. 실험 수치·완료 여부는 [master_plan의 검증 결과](/home/ajou/yigyu/3/master_plan/09_curriculum_and_evaluation.md)와 연결된 원자료를 따른다. 루트 CURRENT_STATUS의 첫 전곡 V1 요약을 최신 실행 경로 전체의 결과로 해석하지 않는다.

| 목적 | 진입점 | 계약·범위 |
|---|---|---|
| 접촉 회복 평가·교사 수집 | `guitar_learning.tool.experiments.contact_recovery.run evaluate/collect` | 상태500·왼손33/전체39. native 원자료·240Hz 회복 기록. 새 PPO를 시작하지 않음 |
| 회복 자료 감사·내보내기 | `guitar_learning.tool.experiments.contact_recovery.dataset_v2` | 실제 회복·원 음악·안전·교사 보정이 감사된 행만 채택 |
| 왼손 정밀화 평가·PPO | `guitar_learning.tool.experiments.transition_refinement_runtime_v2.run eval/train` | 상태500·오른손0. 새 보상·탐색·시연 자료·초기 평가4회와 runtime 감사 |
| 전곡 보상 V2 | `guitar_learning.tool.experiments.song_reward_v2.train/evaluate` | 전곡67음·500상태·33+6행동·정책 준비3초·1969tick |
| 단음 양손 기준 경로 | `guitar_learning.tool.experiments.joint.train/evaluate` | 상태1132·Actor 각569·33+6행동 |
| 초기 전문가 생성·검증 | `guitar_learning.tool.experiments.local_skills` | 이전563상태 품질 경로. 이후 초기화 검증이 일부 함수를 재사용 |
| 입력 생성·검수·진단 | `guitar_learning.tool` | [도구별 명령](tool/README.md) 참조 |

실제 명령·설정·전제는 [회복](/home/ajou/yigyu/3/guitar_learning/tool/experiments/contact_recovery/README.md), [정밀화 runtime V2](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement_runtime_v2/README.md), [전곡 V2](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song_reward_v2/README.md), [양손 단음](/home/ajou/yigyu/3/guitar_learning/tool/experiments/joint/README.md) 문서를 따른다. 기존 결과는 해당 원입력 또는 명시적 이전 절차에서 재현한다. 파일 정리만으로 기존 checkpoint의 계약 불일치를 허용하지 않는다.

## 코드 구조와 공용 기반

루트의 실행 진입점은 `train.py` 하나다. 일반 학습은 아래 공용 코드로 이어지고, 전문 실험·평가·시연·입력 생성은 `tool/`에서 찾는다.

```text
guitar_learning/
├── train.py                 # 곡 단위 손별 학습 시작
├── music_task.py            # 공통 악보·목표 계약
├── historical_inputs.py     # 이전 입력의 정확한 원문 검증
├── training/                # 설정·runner·정책·PPO·수집·기록
├── gpu/                     # 기본 GPU 물리·배치 제어·관측·접촉 후보·보상
├── core/ · runtime/         # 기존 CPU 환경·접촉·안전·native 세션·reset
├── skills/ · imitation/     # 손별 정책과 재사용하는 행동·모방 기반
├── timing/ · quality/       # 시간창·준비·음악 품질 환경과 기록
├── score/ · song/           # 악보·전곡 환경·손별 보상·worker·요약
├── native/ · assets/        # 물리 구현과 모델·자세·설정
├── tool/                    # 부가 실행·전문 실험·검증 도구
├── tests/ · docs/           # 회귀 검사·세부 계약
└── archive/                 # 실행하지 않는 이전 원문
```

`training/start.py → training/gpu_runner.py → training/gpu_pool.py → gpu/`가 기본 GPU 실행을 연결한다. `song/task.py`가 전체 곡을 확인한다. 명시적인 CPU 재현은 `training/runner.py`와 `song/runtime.py`의 worker·요약 및 `song/hand_environment.py`의 손별 보상·성공을 사용한다. 전곡 환경·측정·판정은 `song/`의 공용 라이브러리로 모았으며 기본 실행은 `tool/`의 전문 실행기를 import하지 않는다.

이전 `train_parallel.py`는 `training/runner.py`로 옮겼고, 사용되지 않는 루트 `environment.py` facade는 보관했다. 전문 실행기17개는 `tool/training/`, `tool/evaluation/`, `tool/demonstration/`으로, 검증 전용 환경·rollout은 `tool/validation/`으로 모았다. 전문 패키지8개는 `tool/experiments/`에서 관리한다. [도구 안내](tool/README.md)를 따른다.

공용 환경의 구버전 접미사는 삭제 근거가 아니다. 현재 환경의 상속·호출과 checkpoint 계약에 필요한 구현은 남겼다. `song/task.py`와 `music_task.py`는 이전 checkpoint가 검증하는 경로·원문을 보존한다. 곡 단위 학습이 기본 경로가 되어 환경·측정·보상6개 모듈을 `song/`의 공용 라이브러리로 승격했고, 과거 BC 이전·평가·전문 실행기는 `tool/`에 유지한다. 검사도 이동 전후의 동작·물리·checkpoint 계약을 확인하므로 유지한다. [파일 배치와 유지 이유](docs/CODE_STRUCTURE.md)에 상세히 기록했다.

## 물리와 입력 계약

Root 고정·하체 유한 제어·105입력/97비영 범위/8원 영범위를 유지한다. 정책 행동은 왼손33+오른손6이며 왼손 과제에서는 오른손 정책 행동이0이다. 기타는 자유 강체·중력ON·스트랩OFF이고 직접 보조 힘·부착·실행 중 상태 덮어쓰기를 사용하지 않는다. 가슴 접촉 지속은 성공의 필수조건이 아니다. 물리240Hz·정책60Hz와 실제 표본 기반 음악/안전 판정을 유지한다. 기본 왼손의 손가락21축만 위의 명시적 제어 프로필을 사용하며, 나머지 제어 gain·관절 한계·힘 상한·안전 종료 기준을 유지한다. GPU 제어 solver와 접촉 후보의 차이는 위 새 GPU 계약을 따른다.

초기 자세는 기존035/v14를 기준으로 하며 현재 자산은 내부 `assets/`에서 읽는다. 준비·정착·정책 pre-roll은 경로별 설정을 따른다. 과거 정착2초 규칙을 native0초인 전곡·전환 경로에 자동 적용하지 않는다. 자세 연구의 새 후보도 학습에 자동 적용되지 않는다.

`assets/native_provenance.json`은 원본과 현재 SHA를 구분한다. `historical_inputs.py`와 실행하지 않는 `assets/historical_inputs/` 원문은 기존 gate·checkpoint의 정확한 입력을 검증한다. 내부화·정리 전 원문 검증을 현재 실행 소스의 검증과 섞지 않는다. 외부 Isaac Gym, `data/song_bundles`, 기존 `docs`·`paper`의 checkpoint와 증거는 계속 필요하다.

Actor 초기값 이전과 strict resume를 구분한다. 새 목표·보상·탐색·자료 계약에는 명시적 이전·검증이 필요하다. 이미 성공한 초기 모델이나 교사 자료를 새 정책의 성공으로 상속하지 않는다. 정밀화 단음의90% 유지와 전곡의 원 유지 기준·strict50/100ms는 별도 계약이다.

## 실행과 검사

프로젝트 루트 `/home/ajou/yigyu/3`에서 Isaac Gym Preview4가 설치된 `rl38` 환경을 사용한다. native 진입점은 Isaac을 NumPy·Torch보다 먼저 import한다. 실제 설정과 새 출력 디렉토리를 지정하고 기존 실행 결과를 덮어쓰지 않는다.

```bash
PYTHONDONTWRITEBYTECODE=1 /home/ajou/miniconda3/envs/rl38/bin/python -B -m unittest discover -s guitar_learning/tests -t . -v
```

`settings.json`·`training_contract.json`·`inputs_before.json`은 실행 계약, `transitions.jsonl.gz`는 전이, `episodes.jsonl`은 실제 에피소드 종료다. `learning_metrics.jsonl`, 최종 `report.json`, native/runtime 감사와 checkpoint를 함께 확인한다. sampled/logged/durable/committed/discarded와 완주·음악·안전·런타임 실패를 구분한다. 상세는 [LOGGING](docs/LOGGING.md)을 따른다.

저장 모델의 strict load는 같은 관측·행동·목표·보상·물리·PPO 계약에서만 허용한다. 접촉 후보·기하 타현·음악 성공·안전 완주·정상 실행 완료를 각각 보고한다.

## 이전 단계 문서

[TRAINING](docs/TRAINING.md), [SPECIALIST_TRAINING](docs/SPECIALIST_TRAINING.md), [SKILL_CURRICULUM](docs/SKILL_CURRICULUM.md), [IMITATION_TRAINING](docs/IMITATION_TRAINING.md), [TIMING_TRAINING](docs/TIMING_TRAINING.md), [ACTIONABLE_PREPARATION](docs/ACTIONABLE_PREPARATION.md), [MUSICAL_QUALITY](docs/MUSICAL_QUALITY.md)는 단계별 계약·구현 근거다. 그 안의 과거 실행 설정이나 성공을 최신 과제에 자동 상속하지 않는다. [CODE_LINEAGE](docs/CODE_LINEAGE.md)는 원구현의 역사적 대응을 설명한다.

구형 프로젝트 여섯 디렉토리는 [legacy 보관소](/home/ajou/yigyu/3/archive/legacy_guitar_20261019/README.md)에 있다. 구조 정리 전 소스는 [20261019_before_structure_cleanup](archive/20261019_before_structure_cleanup/manifest.json)에 보존했다.

2026-10-19 구조 정리의 도구 이전·보관 범위·동등성 검증은 [정리 결과](/home/ajou/yigyu/3/docs/2026-10-19/guitar_learning_structure_cleanup_v1/README.md)에 기록했다.

2026-10-20 역할별 파일 이동표·경로 검증은 [재배치 기록](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_role_layout_v1/README.md)에 기록했다.

새 기본 손별 실행의 단기 학습·저장·재개 확인은 [실행 결과](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_simple_start_v1/README.md)에 기록한다.

2026-10-20 메인·도구 재정리의 전체 파일 검토·이동표·검증 범위는 [정리 결과](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_main_tools_v1/README.md)에 기록한다.

현재 곡 단위 기본 실행의 변경·검증 범위는 [전곡 시작 결과](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_song_start_v1/README.md)를 따른다.


이전 v19의3,000회학습·고정평가·영상은 [당시 결과](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_long_training_v19_3000/RESULTS.md)에 보존한다. 해당결과를 v22 성과로 상속하지 않는다.
