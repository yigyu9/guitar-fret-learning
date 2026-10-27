# 곡 단위 손별 GPU 학습의 실행 흐름

**2026-10-25 현행: GPU 왼손 보상 v20·B 대기 복귀 개선(A 기본).** B±15° 평탄대역 밖 품질을 `1/(1+Σ(excess/30°)²)`로 바꾸고, 고정4분모·손 전체 최대0.02/초(손가락당0.005/초)를 사용한다. `--finger-standby-rate 0.04`는 별도 비교 옵션이며, `--finger-shape`를 명시한 비교군만 추종 중 DIP−PIP 50° 초과를 완만하게 낮추는 전체 최대0.004/초 선호(B)를 추가한다. 기본 B분담항은0이며 자동 복귀 제어 C는 미구현이다. 실제 B gate 4열을 `standby_gate`로 관측하며 상태544·손가락별 직접입력20·토큰24열·우선8·단계3331은 유지한다. v19 이하 저장본은 거부하고 계수·옵션까지 같은 v20 전체 계약만 strict resume한다. v19 최초접촉 분할·clean/성공·LH21 움직임 비용0·PD/힘·누적제어·자유 기타·035/v14·PPO를 유지한다. **검증 진행 중이며 효과는 미확인**이다. [구현·검증 현황](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_finger_recovery_v20/README.md).

이전 v19 도입 시 검증 기록: v19는 관련 CPU299개·독립 검수와 실제16환경/H32/65업데이트 및65→66 재개 검증을 통과했다. 작은 실행의 평균달성은 v18 0.625/67→v19 0.5625/67, 안전완주는16→15/16으로 성능 향상은 확인하지 못했다. 구동·접촉분할·저장/재개 검증과 장기성과를 구분하며 [확정 결과](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/README.md)를 따른다. large1024/H32의12업데이트 구동도 완료했지만6.4초 동안 기타 변위 물리종료33회가 발생했고 전곡완주는0이다. OOM은 없었으며 이는 자원·기록 구동 검사이고 장기 안정성이나 성능 향상 검증이 아니다.

**이전 v17 장기 학습 완료(2026-10-24).** large/1024환경/H32/seed7의 새 2,000업데이트·65,536,000전이와 평가·분석·영상 저장을 완료했다. 고정 1024환경 첫 종료곡의 평균 달성음은 초기 0.2979/67, 평가한 학습모델 중 최고 1,000회 5.9961/67(safe949), 최종 2,000회 5.6045/67(safe887)이다. 연속 clean 달성의 학습 지표이며 현행 v20 성과나 음향 성공률이 아니다. [v17 결과·영상](/home/ajou/yigyu/3/docs/2026-10-24/guitar_learning_long_training_v17/RESULTS.md).

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

GPU 왼손의 **544상태·8우선순위 토큰·손가락별 전용 출력 분기**는 유지한다. 손가락움직임비용0·원거리접근신호·동일목표potential·reward/cost advantage개별정규화·GAEλ0.98은유지한다. 현재 v20은 B 대기 복귀를 개선하고 v19 최초접촉 분할·음별 접촉 관측·v16의행동변화.05무감점대역/손목1/4계수와v15음감점정규화/최장streak부족률・추종/접촉/달성을유지한다. 전체 가동범위·독립 누적제어·PD·물리·안전 기준, CPU 왼손·오른손 경로는 유지한다. 이전 v8~v19 결과는 각 계약의 기록이며 현행 v20 성과로 상속하지 않는다. [v8 기반 구현](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_targeted_finger_learning_v1/README.md).

이전 v8의 실제 large/1024/H32 새 모델8회와 동일계약 재개1회(총294,912전이)는 정상 종료·로그/입력SHA·모델/두Adam/RNG/3331복원을 검증했다. 관련CPU218개 중217개 통과, 기존512/544가정 실패1개는 분리했다. 이 짧은 검증은 전곡 성능이나 자연스러움 향상의 증거가 아니다.

**이전 보상v6 장기 결과:** large/1024환경/H32/seed7의 유효1300+재개700회·65,536,000전이를 완료하고 전체 선택 raw·3331·입력 SHA·모델/양 optimizer·새700 정상 close를 검산했다. 저장 공간·NTFS/FUSE EIO로 중단된 별도 분기80회는 합산하지 않으며, 원실행의 전체 EOF/정상 close나 연속 fresh2000회를 주장하지 않는다. 동일1024환경 고정 평가에서 초기3.8408203125/67음·safe1024, 평가한 학습모델 중 best500은5.4287109375음·safe414, 최종2000은0.7451171875음·safe961이다. 사전 선정 규칙의 평균 달성은 높아졌지만 안전성이 크게 낮아졌고 후반 성과가 퇴행했으므로 장기 연주 개선·수렴으로 분류하지 않는다. 모든 모델은 단계0·67음 전체 성공0이며, 실제 자세 캡처에서도 끝관절 편중·대기 자세 문제가 남았다. [장기 결과·평가·자세·영상](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v6/README.md) · [학습 수집 해석](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v6/training_findings.md).

**이전v5 개선:** 당시 GPU 왼손 보상은v5였다. 이전 최종 영상에서 실제 중간 관절이 거의 펴지고 끝관절만 크게 굽혀지는 현상을 확인해, 실제 몸체 회전 기반의 부드러운 관절 분담 보상과 비사용 손가락의 넓은 대기 자세 보상을 추가했다. 손가락별 추종 보상은 해당 손가락의4축 요청만 보며 기존 축당 계수1/21을 유지한다. 전체 가동범위·독립 누적 제어·PD·물리·관측512·기존 성공/안전 기준은 유지한다. 보상v4 저장본은 strict resume할 수 없어 새v5 모델로 시작한다. 짧은 GPU 검증을 자연스러운 연주 학습의 완료로 해석하지 않는다. [손가락 관절 분담 개선·검증](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_coordination_v1/README.md).

이전 보상v4의436소스로 GPU 왼손 `large/1024환경/H32/seed7` fresh2,000회·65,536,000전이를 약6시간18분 동안 끊김 없이 학습하고 정상 종료했다. 같은 고정1,024환경 첫 곡 평가에서 초기4.02734375→최종5.42578125/67음, 안전 완주1,024→1,019개다. 평가한500/1000/1500/2000회 중 최종 모델이 가장 좋았지만 단계0·중지/소지0음·67음 전체 성공0이며, 손가락별 성과 유지가 부족하다. 이 장기 실행은 진단 추가만의 성능 효과나 소지 추종 잔차 해결을 입증하지 않는다. [보상v4의436소스 장기 학습·분석·영상](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v4/README.md).

이전 진단v2 변경은 손가락 실제 자세 로그였다. 종료 에피소드의 `left_finger_motion.base_rotation`에4개 기저 관절의 palm 상대 회전 y와 zero-y 명령 참조 대비 전체/국소xz 회전오차 RMS·최대를60Hz로 기록한다. reset t0와240Hz 극값은 이 통계에 포함하지 않는다. 관측512·보상v4·누적 제어·물리·PPO 흐름은 유지하고 진단 계약은v2다. 전체 계약이 다른 구 checkpoint를 strict resume하지 않으며 아래435소스 학습 결과는 과거 실행으로 보존한다. [진단 범위·미해결 추종 오차](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_tracking_fix_v1/README.md).

코드·문서 확인일은 2026-10-25다. 현재 물리 계약은 GPU aggregate v3, GPU 왼손 보상은 v20·표면 관측은 `left_surface_events.v5`다. 사용자 요청에 따라 기본 실행을 GPU PhysX·GPU 텐서 제어/측정/보상으로 전환했다. 이 문서의 날짜 디렉토리는 실행 날짜를 뜻하지 않는다. 이전 CPU 흐름은 [원문 보관](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_gpu_batch_v1/previous_cpu_learning_flow.md), 이전 보상v6의 장기 검증 범위는 [유효1300+700회 실행·평가](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v6/README.md)을 따르며, 이전 보상v4 실행은 과거 결과로 구분한다. [2000업데이트 실행·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/README.md)은 이전 보상v2·동결 소스의 결과이며, [초기 전환 기록](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_gpu_batch_v1/README.md)은 과거 결과로 보존한다.

## 실행 명령

아래는 B 대기 복귀 보상 v20 기본 A로 새로 학습하는 명령 예시다. CLI 기본값은 medium/128환경/100회이며, 여기서는 large/1024환경/2000회를 명시한다. 이번 적용 작업에서 장기 학습을 실행했다는 뜻은 아니다. v19 이하 checkpoint는 사용하지 않고 아직 존재하지 않는 출력 경로에서 시작한다.

```bash
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3${PYTHONPATH:+:$PYTHONPATH}
export PYTHONDONTWRITEBYTECODE=1

python -m guitar_learning.train \
  --hand left \
  --song 05_BN2-131-B_solo \
  --device cuda:0 --physics gpu \
  --size large --num-envs 1024 \
  --horizon 32 --updates 2000 --checkpoint-every 250 --seed 7 \
  --out /home/ajou/yigyu/3/runs/left_song_finger_recovery_v20_01
```

`--out`은 아직 없는 새 경로다. 위 명령은 2,000회·65,536,000전이 예산의 예시이며 v20의 실제 완료·연주 성과를 뜻하지 않는다. v8의 장기 결과와 실제2000→2001 복구는 위의 이전 결과 보고서에 보존한다.

**이전435소스 압현 접근·유지 개선100회:** GPU 왼손의 실제 압현면 접근·감속·유지 보완을 구현했다. 실제 large1024/H32 fresh100회·3,276,800전이, 동결435Python·580입력·로그/저장·실제100→101재개 검증을 통과했다. 다만 고정0/100 평가에서 평균3.8046875→0.0/67음, 안전 완주1024→1021/1024로 연주 성능 향상을 입증하지 못했다. 해당435소스100회 평가 당시에는 지속 한방향 명령이 남아2000회 장기 실행을 진행하지 않았다. 이전 보상v4의436소스의 장기 결과는 위 기록을 따른다. 충돌하지 않는 현 중심선 대신 pin된 넥 mesh에서 추출한 압현면을 접근 관측·보상 목표로 사용하며, 현재 음 우선 선택과 실제 속도/지속 이동 명령을 함께 보는 유한 양성 보상을 추가했다. 관절 가동범위·누적 제어·PD·물리·기존 접촉/성공 판정은 유지한다. 새 보상v4/표면 관측v2 계약으로 fresh 시작하며 보상v3 모델의 strict resume를 거부한다. [이번 개선·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_press_control_v1/README.md).

**이전 보상v3 누적 제어 검증:** GPU 왼손21축 누적 제어 구현과 검증을 완료했다. CPU843개·GPU84명령시험·large1024/H32 fresh100회·실제100→101재개를 통과했고 실제 굽힘/펴짐을 확인했다. 다만 고정1024평가에서 평균 달성4.200→0.978/67음, 안전 완료1023→311곡으로 회귀해 조건부2000회 장기 학습은 실행하지 않았다. CPU·오른손·팔/손목·PD·보상·PPO는 유지했고 이전 위치제어 모델은 새 행동 계약에 strict resume할 수 없다. [구현·검증·영상](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_incremental_fingers_v1/README.md).

**누적 제어 적용 전 GPU 왼손 장기 결과:** 보상v3·표면 관측v1의 새 정책을 `large/1024환경/H32/seed7`로 시작해 저장본 복구를 포함한2,000회·65,536,000전이 경로를 완료했다. 마지막1,200회는 정상 종료했고 전체CPU831검사·원시64,000행·3331값 단계 재생·입력SHA 검증을 통과했다. 초기/최종 고정1024환경 평가는 평균3.861→8.301/67음, 안전 시간축 완료1024→1020곡,67음 전체 달성0→0곡이다. 최종 달성98.624%는 검지이고 중지0·약지111·새끼6개로 편중돼 곡 연주 학습 완료로 해석하지 않는다. 접촉 단계1에 머물렀다. 앞선 세 SIGFPE와 미저장63회는 별도 보존하며 끊김 없는 단일2000회 실행은 아니다. 로그 실수 변환은 기존 Dragon4 방식으로 우회했고 x87 근본 원인은 미확인이다. [결과·분석·전신영상](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/README.md). 물리·힘·성공·보상/PPO 계약은 이번 기록 오류 수정에서 바꾸지 않았다.

**과거 보상v2 실행:** 이전 동결소스에서 같은 large/1024/H32 예산의 왼손 학습을 2000업데이트·65,536,000전이·5시간41분25초 동안 정상 완료했다. post-cache GPU 여유는 최저 7.374GiB·최종 8.206GiB였고 비Torch 추정 증가 136MiB 이후 일정하게 유지됐다. 전체 raw 64,000행/CRC·에피소드 대응·568입력 SHA·423소스·최종 167유한 텐서 검사도 통과했다. 이는 이전 보상v2의 실행 검증이며 현재 보상v20의 결과나 연주 수렴을 뜻하지 않는다. 오른손 실행은 `--hand right`로 바꾸지만 위 장기 결과는 왼손에 한정된다. 선택하지 않은 손의 정책 행동은 0이며 과거 전문가 모델·BC·성공 평가를 준비할 필요는 없다.

위 이전 보상v2 학습 중 종료 34,069회는 곡 시간축 완료 31,524회와 물리 실패 2,545회이며, 67음 전체 과제 성공은 0회다. 당시 curriculum은1788업데이트에진행도1.0(압현 단계)에진입했고다음 단계 조건은접촉 후보 평균60%였다. 초기/최종 고정 정책의 각 1024환경 별도 평가도 종료·입력 검증을 통과했다. 안전 타임라인 완료는 1024→1023곡, 전체 첫 곡의 평균 달성 음은 3.969→4.232/67이며 전곡 과제 성공은 모두 0이다. 두 모델의 curriculum 관측이 다르고 특정 음의 향상·저하가 공존하므로 일반적인 연주 향상이나 수렴을 뜻하지 않는다. 첫 평가의 native 종료 실패와 보완 후 정상 재평가도 [별도 평가 분석](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/README.md)에 구분해 기록했다.

기본 설정은CUDA/자동GPU물리·128환경·medium·H32·100업데이트·seed7이다. GPU가 없으면 기본 실행은 오류로 종료한다. 환경 수는1~1024이며1환경/H1처럼 총 표본이1개인 설정은 허용하지 않는다. GPU 기본 PPO minibatch는4096, epoch은2다. 모델 크기와 배치 크기가 메모리 사용에 영향을 준다.

접근과 positive는 같은 지판 압현면·프렛 셀 안쪽2mm와 지정 finger3 패드를 사용한다. 하중/법선이 부족해도 접근 거리는 유한하게 제공하고, positive만 동일점 법선cos≥0.1·높이−1~+3mm·횡3mm·동일끝마디하중0.01N을 요구한다. 추종v7은거리식에2cm 근접시최대20% 법선배율만곱하며candidate접촉배율은1이고상한2/초다. PBRS는 거리만 사용하며 손가락 명령·속도 비용0을 유지한다. [상세 측정](/home/ajou/yigyu/3/docs/2026-10-26/왼손보상구조/02_측정과성공판정.md), [추종식](/home/ajou/yigyu/3/docs/2026-10-26/왼손보상구조/04_손가락추종과자세.md)을 따른다.

GPU 왼손 손가락21축의 행동은 현재 목표에 `행동×4/60rad`를 누적하는 이동 명령이다. 0은 목표 유지, 반대 행동은 다음틱부터 목표 반전이며 native 한계 밖으로 누적하지 않는다. 팔·손목은 초기 자세 기준 위치 제어를 유지한다. H32 경계에서도 손가락 목표를 유지하고 곡 종료/실패 환경만035/v14로 복원한다. 이전 위치 제어 checkpoint는 새 누적 행동 계약에 strict resume할 수 없어 fresh로 시작한다. [변경·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_incremental_fingers_v1/README.md).

## v20 대기 복귀와 분담 비교 옵션

기본 실행은 A: 전체 B보상 최대0.02/초·고정4분모·각0.005/초다. B±15° 안은 같은점수이며 밖은 `1/(1+Σ(excess/30°)²)`로 완만하게 낮춘다. 시간/접촉/근접 보호는 유지하고, 관측의 마지막4열은 실제 `standby_gate`로 바꾼다. 최신240Hz 표본의 gate를 캐시하여 직전접촉이 사라지는 끝점도 보상과 같으며 선택reset 이외에는 초기화하지 않는다. 상태544·각손가락직접입력20·우선8은 같다.

- `--finger-standby-rate 0.04`: B전체최대0.04/초·각0.01/초의 별도 비교군.
- `--finger-shape`: 추종 목표가 있는 손가락의 `relu(DIP-PIP-50°)`를 완만하게 낮추는 전체최대0.004/초·각0.001/초 선호를 기존coordination슬롯에 추가. 기본은0이며 압현·clean 중에도 적용한다.

두옵션은 GPU왼손만 허용한다. 재개시에도 원래 계수·옵션을 동일하게 지정해야 한다. C 자동대기복귀 제어보조는 미구현이며 행동0은 여전히목표유지다. 손가락움직임비용0·PD/힘/가동범위·4rad/s·자유기타·035/v14·성공/안전·PPO는 유지한다. 구동검사와 비교학습의 결과는 [검증 진행 현황](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_finger_recovery_v20/README.md)에서 구분한다.

## 곡과 PPO 수집 구간

기본 곡은67음·1969control tick·약32.8167초이며, 정책 준비3초·원곡·말미0.5초를 포함한다. native 대기시간은0이다. 물리240Hz·정책60Hz이므로 행동 한 번마다 실제 물리4단계를 진행한다.

H32는 한 환경에서0.5333초를 수집한 뒤 PPO를 갱신한다는 뜻이다. 업데이트 경계에서 물리·곡 시계·음별 원장은 초기화하지 않는다. 곡 종료나 물리 실패인 환경만 저장 초기 자세로 돌아간다. 다른 환경은 계속된다.

1024환경/H32라면 업데이트당32,768전이다. 위2,000업데이트는65,536,000전이·환경당64,000control tick(누적 정책 시간 약1,066.667초)의 수집 예산이며 곡 재시작과 PPO 갱신을 포함한다. 이전 v6의 마지막700회는8175.3926초(약2시간16분15초)에 정상 종료했다. 원1300회와 복구·중단 시간을 하나의 연속 wall로 합치지 않는다. 이전 v4의2000회 연속6시간18분은 시간 참고일 뿐 현재 실행의 wall이나 다른 장비의 보장이 아니다. `--checkpoint-every 250`으로250회마다 추가 저장하며 CLI 기본 간격도250이다. 실패·부분 궤적은 전곡 완주로 세지 않으며 이 예산이67음 성공 횟수를 보장하지 않는다.

## 호출되는 코드

| 순서 | 파일 | 역할 |
| --- | --- | --- |
| 1 | [train.py](/home/ajou/yigyu/3/guitar_learning/train.py) | 사용자 진입점 |
| 2 | [training/start.py](/home/ajou/yigyu/3/guitar_learning/training/start.py) | 손·곡·모델·GPU 설정 결정, 전체 악보 확인, GPU runner 선택 |
| 3 | [training/gpu_runner.py](/home/ajou/yigyu/3/guitar_learning/training/gpu_runner.py) | 입력 SHA·모델·PPO·로그·자원 보호·저장/실패 처리 |
| 4 | [training/gpu_pool.py](/home/ajou/yigyu/3/guitar_learning/training/gpu_pool.py) | 한 GPU 장면과 제어·측정 연결, terminal bootstrap과 선택 reset |
| 5 | [gpu/scene.py](/home/ajou/yigyu/3/guitar_learning/gpu/scene.py) | 한GPU PhysX simulator의N환경·환경별aggregate·CUDA 상태/접촉힘/Jacobian·경계 reset |
| 6 | [gpu/control.py](/home/ajou/yigyu/3/guitar_learning/gpu/control.py) | 유한 목표·힘·하체 stable PD/IK·중력/상체 지지 |
| 7 | [gpu/environment.py](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py) | GPU 관측544/500·240Hz 보상/안전·곡 원장·종료 |
| 8a | [gpu/wrist_region.py](/home/ajou/yigyu/3/guitar_learning/gpu/wrist_region.py) | 작업 프렛 중심·실제 넥 아래 경계에서 영역 생성, 곡 시각 보간·최근접 안내·밖 감점 |
| 8b | [gpu/fingertip_pad.py](/home/ajou/yigyu/3/guitar_learning/gpu/fingertip_pad.py) | finger3 패드 triangle clip·128면적층화 표본·법선·양성 기하 |
| 8c | [gpu/finger_reward.py](/home/ajou/yigyu/3/guitar_learning/gpu/finger_reward.py) | 공통 손가락별 추종/다음 목표 선택·거리/접촉 품질·실제 자세 보상률 |
| 8 | [gpu/geometry.py](/home/ajou/yigyu/3/guitar_learning/gpu/geometry.py) | 회전·COM 상대 운동·실제 메시 표면과목표현선분의최근접오차 |
| 9 | [skills/specialist_policy.py](/home/ajou/yigyu/3/guitar_learning/skills/specialist_policy.py) | 선택한 손의 actor와 보상/비용 critic |
| 10 | [training/ppo.py](/home/ajou/yigyu/3/guitar_learning/training/ppo.py) | GAE·PPO·KL 보호·optimizer·strict checkpoint |
| 11 | [song/curriculum_runtime.py](/home/ajou/yigyu/3/guitar_learning/song/curriculum_runtime.py) | 완료곡 기반 단계:GPU왼손3331값/CPU기존27값 checkpoint buffer |

환경별 aggregate는 68몸체·145shape 용량에 human→guitar→chair 순서로 생성하고 self-collision 및 기존 group/filter를 유지한다. 기타는 native 1강체/89shape이며 기존 39논리마커를 복원해 native 68/논리 106몸체를 구분한다. 질량·COM·관성에는 두 proxy의 기여도 남지만 두 proxy 충돌은 의자/지면을 포함해 완전히 제외한다.

관측·행동·보상·비용·수집 버퍼는GPU에 남는다. 완료 요약과 로그·모델 파일을 저장할 때 CPU로 전달한다. 환경마다 별도 Python 프로세스를 만들지 않는다.

## 초기 자세와 제어

기존035/v14의 실제 준비 snapshot에서105관절 위치·속도와 자유 기타의 자세·속도를 읽는다. Root·의자는 고정, 기타는 자유·중력ON·스트랩OFF다. reset은 에피소드 경계에서 한 번만 수행하고 실행 중 기타 상태를 덮어쓰거나 직접 기타 보조 힘을 주지 않는다.

105입력·97비영 범위·zero8, native POSITION48/EFFORT57와 기존 힘 상한을 유지한다. 왼손21은 전체 native 범위·최대4rad/s·손가락K/D12/1.5·엄지8/1.25다. 현재 GPU 누적제어는 손가락 위치평활화를 우회(alpha1)하며 CPU 초기자세 비례 위치제어만 평활화0.45를 유지한다. 엄지는 별도로 고정하지 않는다.

GPU에서 하체 기하 질량행렬·stable PD·고정 반복 DLS IK와 상체 유한 지지 제어를 계산한다. CPU solver와 수치적으로 같은 결과라고 주장하지 않으며 차이를 새 제어 계약에 기록한다. 제어가 비유한 값이거나 지지 계산을 인증할 수 없으면 물리 진행 전 중단한다. 유한하고 인증된 최근접점의 지지 방향만 정의되지 않는 경우는 `support_control_invalid` 물리 실패다. 해당 환경에 마지막 유효 힘을 현재 tick 끝까지 유지한 뒤 종료 관측으로 bootstrap하고 선택 reset한다. 정상 방향이 돌아와도 그 tick의 실패를 취소하지 않으며 양성 보상을 억제하고 기존 종료 실패 비용 +5를 부과한다.

현재 GPU 왼손은 기존 실행 중 안전 비용과 종료 실패 비용 +5를 유지하고, 물리 실패 때 남은 곡 시간에 비례한 비용을 한 번 추가한다: `5 × max(곡 길이 − 실패가 발생한 실제 control tick 뒤의 곡 시각, 0)`(초당 5). 이는 측정한 미래 비용이 아닌 고정률 absorbing-failure 모델이며 curriculum 비중으로 낮추지 않는다. CPU와 오른손 비용 계약은 변경하지 않았다.

GPU reset의 몸체 변환은 다음 실제 물리단계 전까지 native FK가 갱신되지 않을 수 있다. reset 관측에는 저장된 준비 몸체 snapshot을 사용하고, 실제 물리단계 후 native GPU 상태를 사용한다. 이 관측용 값은 몸체 상태 주입이 아니다.

## 새 GPU 압현 후보와 보상 단계

사용자가 접촉 판정까지 GPU 방식으로 재설계하는 경로를 선택했다. 새 후보는 실제 손가락 충돌 STL의 표면 샘플·현의 유한 구간·프렛 셀·해당 몸체의 접촉 합력을 사용한다. 개별 접촉 몸체 쌍이나 실제 witness가 없으므로 기존CPU clean 판정·실제 현 압력·음향 성공을 상속하지 않는다. 표면 샘플 사이의 접촉은 놓칠 수 있다. 기준과 한계는`training_contract.json`에 저장한다.

GPU 왼손은544상태와64×24 일반 음 토큰·8×24 우선순위 토큰을 받는다. `left_surface_events.v5`의 토큰9/10(0부터 세는 인덱스)은 새로운 pad candidate와 기존 full-surface wrong이다. 16~21은 지정 finger3 패드점에서 지판 압현면 목표 선분까지 오차/실제 기타 상대속도(scale3cm/0.5m/s), 22/23은 같은 선택점의 `pad_normal_cos`/`pad_signed_height`(scale1/3cm)다. 중복 strict deadline2열을 교체하므로 상태·토큰 차원은 늘리지 않는다. 토큰11(left)은 v12부터 유지한 현재 onset~end의 `clean_streak_s`다. v19의 토큰12/13은 현재 접촉streak/tau와 최장 접촉streak/tau(scale1)이며 tau=min(50ms,end−press)다. 일반·우선 토큰 모두 같은 의미이고 544/24/8차원은 유지한다. 이전 누적held/음길이비율 관측은 교체하되 실제 누적clean/held 계산·유지보상·원장·로그는 보존한다. 압현면은 source neck Gz약9.3mm이고 프렛 셀 안쪽2mm를 유지한다. 원래 현 중심12.3mm와 full finger2/3·엄지 샘플은 wrong/지지 검사에 남으며 pad positive와 구분한다. 실제 선택점 속도를 쓰고 최근접 샘플 교체 차분을 속도로 쓰지 않는다. 하중은 몸체 합력이므로 현의 실제 압력·접촉 pair를 인증하지 않는다.

접근 보상은 공통 손가락 목표 선택기의 유효 tracking slot0만 최대4개 합산하는 시간 의존 potential `Φ=Σ_selected w_f·exp(-표면거리/0.03)`에 `γΦ(next)−Φ(current)`를 적용한다. γ는 PPO reward γ와 같은 0.99이며 접근 계수는 단계와 무관하게 1이다. 실제 terminal의 다음 potential만 0으로 하고 H32 경계에서는 이어간다. 접근 potential과 양성 접촉·유지·음 달성에는 `w_f=M/(곡에 존재하는 손가락 수×그 손가락의 음 수)`를 적용한다. 기본67음의 검지/중지/약지/새끼 가중치는 약0.670/0.931/1.396/1.396이다.

지정 손가락·현·프렛의 pad기하는 유지하며, GPU왼손 음별달성만 onset~end의 연속clean_streak가 min(D,max(50ms,0.4D))를 처음 채울 때로 변경한다. 누적clean·held와 유지보상은 유지한다. 40%는 학습용 중간달성이며 음끝까지 완전한연주를 뜻하지 않는다. v19 최초접촉은 press~end 안의 최장 연속 candidate 진행률 증가분마다 원시0.5b 예산을 분할한다. 같은 길이의 짧은 접촉 반복에 재지급하지 않으며 contact_done은 실제 연속 min(50ms,end−press) 문턱을 채워야 참이다. 기존 이진 보너스를 별도로 주지 않는다. 실패tick 양성억제와 단계가중치를 유지하므로 contact_progress는 소진한 원시 예산 진행률이며 실제 받은 금액이 아니다. 실제 지급은 song_left_contact로 확인한다. 음 진행 중에는 `2×Δclean/음 길이` 유지 보상을 달성 이후에도 계속 준다. 연속 clean 달성 문턱을 처음 넘을 때의 보너스는 기존0.5이며 이후 끊겨도 left는 유지하고 다시 지급하지 않는다. 이 양성 항들은 손가락 가중치와 해당 단계 비중을 적용한다. wrong/missing원시감점은각각−sum(b*wrong_dt/D),−.5sum(b*missing_dt/D)이고미달성은−.5sum(new_missed*b*(1−min(best_clean_streak/required,1)))다. 기존legacy단계계수와행동변화/terminal/안전비용은유지한다. 진단wrong/missing초누적과이진미달성음수는그대로다.

GPU 왼손 단계는 **표면 접근 → 접촉 → 유지·전환**이다. 최근256개 종료곡이 쌓인 뒤 안전 완주90% 이상이고 곡에 존재하는 모든 손가락의 접근 달성 평균이각 20% 이상이면0→1을 진행한다. 접근 달성은 준비 시작2초 전~음 끝에 표면거리10mm 이내 누적100ms(구간 길이를 넘지 않음)다. 1→2는 접근 기준 대신 각 손가락의 연속 contact_done 달성 평균20%를 사용하며 안전90% 조건은 유지한다. 실패곡은 모든 지표0으로 포함하고 부분 궤적은 제외하며, 새 안전 완주가 포함된 committed PPO 수집 뒤 최대0.1만 올린다. 이256곡은 독립 seed256개를 뜻하지 않는다.

단계0/1/2의 그룹 계수는 손목0.2/0.1/0.05, 접촉0.5/1/1, 유지·달성0.5/1/2, 접근1/1/1이며 중간 진행도는 선형 보간한다. 손목 항은 v9에서 양성 보상이 아니라 영역 밖 감점이다. 영역 안·경계는 0이고 안쪽 위치나 회전을 더 선호하지 않는다. 모든 단계에서 접촉·유지 보상은 유효하며 손목 ready는 압현이나 단계 전환의 gate가 아니다. 구체적 경계·수식은 [손목 영역 항](/home/ajou/yigyu/3/docs/2026-10-26/왼손보상구조/03_접근접촉유지보상.md:30)을 따른다.

완료곡의 `episodes.jsonl`에는 `left_note_ledger`(v7의 현재contact_streak·최장best_contact_streak·소진예산contact_progress 및 음별 표면 최단거리·노출/접근시간·기하/하중·오프렛/오손가락 원인·clean/contact/달성), 손가락별 지표와 `reward_components`를 저장한다. 최소거리0은 노출시간0일 수 있으므로 함께 해석하고, 기하/하중/원인별 시간은 겹칠 수 있다. `learning_metrics.jsonl`에는 수집 전이 기준 `reward_component_means`와 단계 요약을 기록한다. 업데이트별 JSON 사본은 새 GPU 실행에서 만들지 않는다. GPU 단계 이력은 3331값 checkpoint buffer로 저장하며 CPU의8곡/27값 계약은 유지한다.

초기 latent Gaussian std는 기존 `exp(-3)≈0.049787`을 유지한다. std0.08 확대는 후속 분리 비교 실험이며 이번 기본값 변경에 포함하지 않는다. 기본 학습률·안전 비용 설정은 유지한다. GPU왼손의 PPO는 reward/cost advantage 각각 표준화 후 cost_weight로 결합하고 최종 표준화하며 GAEλ는0.98이다. H32·rewardγ0.99/costγ1·critic 손실은 유지하며 기존 KL retry의 자동 actor LR 감소는 적용한다. 설정 고정과 학습 중 파라미터 불변을 혼동하지 않는다.

모든안전비용·힘상한·종료기준은단계에따라완화하지 않는다. CPU/오른손은기존관측·보상·단계계약을유지한다.

## 수집·종료·저장

1. H32개의 행동과각4개 물리단계를 진행하며240Hz 접촉 후보·비용·실패를 측정한다.
2. 종료 관측으로 다음 가치값을 계산한다. 진짜 terminal이면 bootstrap은0이며 시간제한 truncation은 종료 관측으로 bootstrap한다.
3. 종료된 환경만 reset하고 나머지 환경의 시계·원장을 이어간다.
4. 수집 버퍼로 PPO를 갱신하고 journal의 해당 전이를 committed로 기록한다.
5. 왼손 단계와 업데이트 보고서를 저장하고 다음 구간을 수집한다.

| 출력 | 의미 |
| --- | --- |
| `settings.json`, `training_contract.json`, `inputs_before.json` | 실행 설정·새 GPU 계약·입력 SHA |
| `initial.pt` | 새 모델 또는 strict load 직후 모델·optimizer·난수·curriculum |
| `checkpoint_*.pt` | 주기적 저장 |
| `final.pt` | 정상 종료 시 최종 상태 |
| `failure_last_valid.pt` | 저장 가능한 유효 상태에서 실패한 경우의 복구 모델; 부분 PPO 갱신 중에는 생성하지 않음 |
| `transitions.jsonl.gz` | 수집된 reward/cost/종료 배열과 sampled/logged/durable/committed/discarded 구분 |
| `episodes.jsonl` | 실제 완료/물리 실패·GPU왼손 음별표면/접촉원장·손가락별지표·보상성분 |
| `learning_metrics.jsonl` | PPO·보상/비용·단계·처리시간·reward_component_means, 상세 에피소드는 ID로 참조 |
| `episode_metadata.json` | 에피소드 공통 계약·목표·관절 이름, 첫 종료 에피소드부터 생성 |
| `checkpoint_manifest.jsonl` | 초기·중간·최종·복구 저장본의 크기·SHA·저장 시간 |
| `status.json`, `resources.jsonl`, `events.jsonl` | 진행·가용 RAM·단계/실패 기록 |
| `gpu_scene_initial.json`, `gpu_scene_final.json` | 실제GPU flags·CUDA 텐서·장면 소유권·종료 |
| `report.json`, `song_report.json` | 실행 결과·실패·자원·원곡 완료 요약 |

`sampled`나 로그가 남았다는 사실만으로 PPO에 반영됐다고 판단하지 않는다. 실패한 부분 수집은 discarded로 기록한다. `report.completed`는 실행·소스·종료 검사를 통과한 뜻이며 연주 수렴을 뜻하지 않는다.

새 GPU 기록은 `python -m guitar_learning.tool.inspect_gpu_training_log --run /absolute/path/to/run`으로 검사한다. `guitar_learning.training.gpu_log_records`의 스트리밍 독자는 새 정본·메타데이터를 합쳐 이전 에피소드 구조를 복원하며 기존 로그도 읽는다. 과거 날짜별 결과 폴더의 검증·분석 스크립트는 당시 동결 형식 전용이므로 새 실행에는 사용하지 않는다. 상세 저장·진단 범위는 [로그 안내](/home/ajou/yigyu/3/guitar_learning/docs/LOGGING.md)를 따른다.

## 저장 모델 재개

같은 GPU 물리·제어·측정·보상·계수/옵션·모델·PPO 전체 계약의 v20 checkpoint만 새 출력 경로로 strict resume한다. v19 이하 저장본은 차원이 같아도 B 보상·standby_gate 관측 계약이 달라 거부한다. 아래는 v20 저장본 생성 후 명령 예시다. 모델·두 optimizer·RNG·3331값을 복원하되 물리 장면·곡 시계·부분 곡은 035/v14에서 새로 시작한다. 현재 검증 진행 범위는 [v20 구현·검증 현황](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_finger_recovery_v20/README.md)을 따른다. 이전 v17·v16 장기 결과를 이번 성능으로 상속하지 않는다.

```bash
python -m guitar_learning.train \
  --hand left --song 05_BN2-131-B_solo \
  --device cuda:0 --physics gpu \
  --size large --num-envs 1024 --horizon 32 --updates 1 \
  --checkpoint-every 250 --seed 7 \
  --resume /home/ajou/yigyu/3/runs/left_song_finger_recovery_v20_01/final.pt \
  --out /home/ajou/yigyu/3/runs/left_song_finger_recovery_v20_resume_01
```

이전435소스·진단v1 보상v4 계약의 실제100→101 GPU 재개에서 모델·두 optimizer·난수·3331값 curriculum이 initial.pt에 정확히 복원됐고 두 optimizer와 왼손 actor가 갱신됐다. 비활성 오른손 actor는 유지됐고 이전v3·동일누적codec 저장본은 보상/관측 계약 차이로 strict load를 거부했다. [이전435소스 실행·재개 검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_press_control_v1/resume_verification.json)을 따른다. 이전 누적v3 재개는 [과거 기록](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_incremental_fingers_v1/resume_verification.json)이다. 이전 위치제어 계약의64→65검증은 [과거 기록](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_fretting_v1/verification.json)이다.

이전 보상v2·당시 동결 소스의2000→2001 GPU 재개에서는 32,768전이·569입력 SHA를 검증했고 초기 nonmetadata 상태가 모두 정확히 복원됐다. 모델·두 optimizer·CUDA를 포함한 난수·curriculum·trainer 상태를 복원한 뒤 두 optimizer와 왼손 모델이 갱신됐으며 비활성 오른손은 유지됐다. [실제2000→2001 재개 검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/resume_verification.json). 물리 환경은 초기 자세에서 새 에피소드를 시작하며곡 중간 물리 상태 복원은 아니다. 기존CPU512/500 checkpoint도 새GPU 계약과 다르므로 strict load가 거부된다. 모델 크기나 다른 제어/측정 계약으로 암묵 이전하지 않는다.

CPU 물리 재현은`--physics cpu`로 명시한다. 이전 native·quality·전문 도구는 별도 재현 경로이며 새GPU 측정 성과를 상속하지 않는다.


이전 v19 변경 전 학습흐름 원문은 [별도 보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261025_before_press_acquisition_v1_flow_docs/manifest.json)에 보존한다. [압현 획득 진단·개선](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/README.md)에서 실제 검사·GPU 구동·진단의 확정 범위를 확인한다. 위2000업데이트 명령은 실행 예시이며 장기 학습 완료를 뜻하지 않는다.


이전 v19의3,000회학습·고정평가·영상은 [당시 결과](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_long_training_v19_3000/RESULTS.md)에 보존한다. 해당결과를 v20 성과로 상속하지 않는다.
