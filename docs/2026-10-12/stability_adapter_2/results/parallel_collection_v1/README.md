# 병렬 환경 수집과 초기 노이즈

기존 단일 환경의 마지막 복구 CP315를 보존한 뒤 독립 spawn 물리 환경4개와 CUDA 정책 배치4를 연결했다. 상체81/825D관측/512→256정책과기존PD·제어·보상·root/하체고정·자유기타·self-collision·원본스트랩·두baseline은 유지한다. CPU 물리 환경을 별도 프로세스로 실행하며 그래픽 없는 학습과 대표1환경의 별도전체영상평가를 유지한다.

## 초기 노이즈

초기 관절각·기타 위치/회전·속도·스트랩의무작위노이즈는0이다. 모든환경은검증된같은초기상태에서시작한다. 학습행동에는Gaussian latent 탐색이있고tanh와부위별radian residual을거친다. 원본CP315의평균latent std는 body/head 약0.006738, arm/finger 약0.018315다. 이는무차원latent값이며관절각rad/deg가아니다. 영상평가는deterministic 평균행동이다. [실제초기노이즈분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/initial_noise_analysis_v1.json:1).

## 실제 검증

- CPU7검사: 환경별종료/절단bootstrap의시점,다른환경의GAE연결,rollout연속수집,worker오류의미완성batch거절,부분spawn실패정리,실제N2PPO갱신/RMS고정과source변조거절.
- 실제N2를각5초/300control/1200physics 진행했다. 초기native상태가exact일치하며서로다른행동이실제DOFq 차이를만들었다. 양쪽금지API0과13×1200원본strap호출을확인했다. 원시상태와초기/최종관측차이를별도로기록한다.
- 실제N4/T64=256transition의CUDA1갱신으로CP315→316을완료했다. 이행/초기재저장의model/Adam/RMS/RNG/counters는원본과exact일치한다. GPU정책입력배치4,수집shape[64,4]를기록했다. 수집4.451639초/57.506910transition/s는전체PREP인이번짧은batch이며기존PLAY포함평균과의속도향상인증이아니다.
- 정책KL0.019905004650354385≤0.02/RMS고정,Actor/Critic갱신을확인했다. 초기/갱신평가는각16.366667물리초/982control/3928physics/492frame/전신·손2영상을완주했다. MP4재생길이는16.4초다. 두baseline동결과금지API0·안전위반없음·원본strap호출을확인했다. 음악성공은각0/42여서병렬화검증을연주성공으로해석하지않는다.

[실제검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/verification_v1.json:1) · [N2 native원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/probe_v1/report.json:1) · [구현계획](/home/ajou/yigyu/3/stability_adapter_2/PARALLEL_COLLECTION_PLAN_V1.md:1).

## 생산 설정과 마감

검증CP316에서N4/T256으로재개했다. 갱신당1024transition,미니배치128,에폭4로최대32미니배치갱신기회를갖는다. 각기회에서기존guard가최대8번재시도하므로optimizer.step의전체시도횟수상한을32로부르지않는다. 학습률3e−5/KL≤.02/RMS고정은그대로다. N/T는수집기록에,물리·관측·제어계약과source추가는checkpoint ABI에기록한다.

5분복구저장·30분공식checkpoint/전체영상·11:40학습cutoff를유지한다. 초기영상평가시간때문에이번남은학습시간에서5분복구/30분공식평가가돌아오지않을수있고최종전체영상을따로만든다. 마감과저장은협조적이며native호출을강제선점하지않는다. 새완료/부분평가영상은 `/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_long_v1/<평가label>/`에SHA검사후자동보관한다. 아직이번N4/T256의전체완료·실제처리량향상·연주성공을인증하지않는다. 실제결과는다음항목에추가한다.

## 보존과 검수

기존실행·소스·공용자산·stability_adapter/는수정·삭제하지않았다. 단일환경종료전로그는319회까지지만이행한저장본은315회다. 미저장316–319는복구하지않았고새316회는새병렬갱신이다. 두숫자를같은실행으로연결하지않는다. main4는각실행이끝난틈에원문prefix를보존하며append하고native동안동결한다.

[사전검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/review_preflight_v1.md:1) · [재개검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/review_resume_v1.md:1) · [이전종료/보존](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/previous_stop_snapshot_v1.json:1).


## 생산 실행 완료

11:40학습cutoff뒤CP320/84992transition의전체평가영상까지완료했다. N4/T256 생산4갱신/4096transition의실제처리량은수집·최적화합산평균36.5024개/초,첫배치수집만44.1943개/초다. 이전single의첫배치합산참고값14.8839개/초는다른CP/데이터/시점이어서통제benchmark가아니다. 모든갱신KL≤.02/RMS고정/1024transition/counter연속성을검증했다. [생산분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/production_analysis_v1.json:1).

최종실행종료코드0/입력SHA유지/보관오류0,대표초기·최종평가각16.3667physics초/16.4MP4초·full982control3928physics·baseline동결·금지0를확인했다. [완료검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/completion_verification_v1.json:1) · [최종전체영상](/home/ajou/yigyu/3/docs/2026-10-12/video/parallel_long_v1/cutoff_000320/README.md:1). 이번생산run은마감설정에따라종료된상태다. 초기평가뒤학습구간이5분보다짧아생산복구용CP는0개이고최종CP320은보존돼있다.

음악성공은0/42다. CP316→320 밖비율59.78→55.19%와초기기타대비최대SO393.93→91.21°는낮아졌으나최대rootbox이탈30.45→33.99cm/평균5.82→8.49cm는커졌다. 기타바디중심의자연범위인증이아니며기타안정화·연주성공을주장하지않는다. 위의생산진행중문단은실행전기록이고이완료항목이최신확인상태다.


## 최종 영상·그림·수정 색인

[CP316→320 native 프레임과 영상 설명 정정본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/artifacts_v2/README_V3.md:1) · [영상 전체 색인 V7](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V7.md:1) · [실제 변경 경로·줄 번호](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/parallel_collection_v1/CHANGED_FILES_V1.md:1). 기존 산출물 원본은 보존하며 최신 정정본을 우선합니다.

[최신 영상 색인 V8](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V8.md:1)은 이전 V7을 보존하며 CP320 설명 정정본을 연결합니다.
