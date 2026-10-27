# v20 A 500회 학습·반복 평가

사용자 승인으로 기본 v20 A를 large/1024/H32/seed7·전곡67음·자유 기타에서 새500회(16,384,000전이) 학습하는 실행이다. 손 전체 B대기 최대0.02/초·압현 분담shape0·자동복귀 C 없음. v19 모델을 이전하지 않으며, 초기72모델텐서가v19새학습초기값과정확히같음을 검증했다.

- [실행계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_v20_A500_20261025.md)
- [학습 진행 상태](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_v20_A500/pipeline_status.json)와 [학습 상세 진행](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_v20_A500/train500/status.json)
- 후처리 전체 상태는 [postprocessing_status.json](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_v20_A500/postprocessing_status.json)이다. 학습 감독의 `training_audited/completed`는500회 학습·로그 감사의 완료만 뜻한다. 평가·영상·분석까지 완료했는지는 후처리 상태를 확인한다.
- [실제 시작·초기값 검증](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_v20_A500/startup_verified.json) · [실행 전 검수](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_v20_A500/review_preflight.json)

## 실행과 보존

시작 시각은2026-10-25 18:59:45 KST다. 학습은대화종료와독립적으로지속되며 모든GPU실행은순차다. 검증한462개Python을 source_training에 보존하고 training_source_manifest.json에 SHA를 봉인했다. 학습중활성소스와자산·입력을바꾸지않는다. 초기·250회·마지막500회 checkpoint를저장한다. 최초속도는약13~14초/업데이트로, 학습에약2시간·평가와영상에추가시간이든다. 이는진행속도추정이며완료시간보장이아니다.

```bash
python -m guitar_learning.train \
  --hand left --song 05_BN2-131-B_solo \
  --physics gpu --device cuda:0 \
  --size large --num-envs 1024 --horizon 32 \
  --updates 500 --checkpoint-every 250 --seed 7 \
  --out /home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_v20_A500/train500
```

이미실행중인명령의기록이다. 위출력에다시실행하거나기존결과를덮어쓰지않는다.

## 종료 후 자동 처리

1. 정상종료·PPO반영16,384,000전이·전체gzip CRC/EOF·checkpoint/입력SHA를검산한다.
2. 새v20 A500과v19 checkpoint500을교대로각3회·1024환경첫종료곡으로고정평가한다. 모든환경의첫실패또는완주를포함하고, 다른환경을계속진행시키기위한뒤이은곡은분모에섞지않는다.
3. 각평가의사전지정env0..7 실제자세를60Hz로저장한다. 새모델repeat1의최소ID안전완주(없으면최장)로전신·왼손영상을생성한다. 최고득점장면선택규칙이아니다. 영상은저장된실제자세표시이며물리를재적분하거나자세를합성하지않는다.
4. 학습로그·3반복성과·악보고정대기창복귀·초기품질감소·손가락관절각과압현·오압현/누락·안전성을분석해 analysis.json과 RESULTS.md를새로저장한다. 완주/실패와예정/실제노출분모를구분한다.

v19 비교는원래v19정책의정확한계약/가중치와기존2초시간idle4입력을유지하는명시적현재물리평가다. 공통물리·제어·성공·기하소스와계약을검증하며, archive소스를실행용으로import하지않는다. 원래459개소스의보관SHA와현재462개실행SHA를분리한다. 이평가의보상값은현재v20로재계산되므로v19실제학습보상과비교하지않고음악·물리·자세진단만비교한다. 기존원본평가6.9375/67음·안전1018/1024는별도의역사기준으로보존한다.

## 해석과 후속 단계

학습중부분수집평균과고정모델전곡평가를구분한다. 추론3반복은독립학습seed3개가아니며단일곡·초기자세·seed7에대한결과다. 관절각분포영상은사전지정8환경60Hz표본이고전1024환경240Hz극값이아니다. 접촉·clean은하중과기하proxy로실제압력·음향을인증하지않는다.

500회성적만으로복귀학습불가능을판정하지않는다. 음악성과와자세의개선·악화·미관측을함께보고A연장/.04계수비교/선택분담B/필요시C별도구현을구분한다. 3,000회후속학습은500회평가판정뒤진행할단계이며지금자동시작하지않는다. 학습·평가실패와영상오류는상태파일에별도로기록하고미완료를성공으로표시하지않는다.

후처리 감독을2026-10-25 19:15:43 KST에기동했다. 학습 종료·감사 뒤순차 실행하도록대기중이며, [최종 후처리 사전검수](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_v20_A500/review_postprocessing_preflight.json)와30개CPU검사를통과했다. GPU평가·영상·성과가이미완료됐다는뜻은아니다.

## 후처리 종료

2026-10-25T13:01:46.849899+00:00 UTC. 500회 학습·감사·반복 평가·분석을 마쳤습니다. 영상 오류: [].

[결과 분석](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_v20_A500/RESULTS.md) · [분석 원자료](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_v20_A500/analysis.json). 3,000회 연장 채택은 결과 검토 대상입니다.

[실제 완료 결과 독립 검수](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_v20_A500/review_results.json): 입력1,185SHA·체크포인트3개·각버전3회집계·두영상1969프레임/60fps 검증을통과했다. 이는결과계산/완료의검수이며성능향상의판정이아니다. A는평균달성·안전·복귀채택기준미달로3,000회연장하지않았다.
