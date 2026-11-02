# 재현

프로젝트전체복사본: `/home/yigyu/local-research/index_middle_transition_20261101_v1/project`. Conda prefix를복사하는대신이PC rl38/IsaacGym Preview4를사용했다. source_snapshot과study_seal의실제바이트SHA가기준이며Git HEAD만으로dirty/untracked파일을복원하지않는다.

```bash
cd '/home/yigyu/local-research/index_middle_transition_20261101_v1/project'
PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
 /home/yigyu/miniconda3/envs/rl38/bin/python scripts/tab2body.py \
 --cache-root /home/yigyu/.cache/tab2body run -u \
 docs/2026-11-02/손가락전환실험/도구/runtime.py train \
 --updates 100 --seed 7 --num-envs 64 --size large --noise-profile base \
 --out docs/2026-11-02/손가락전환실험/진단/NEW_REPRO_TRAIN
```

기존출력은보존되며NEW_REPRO_TRAIN도없어야한다. 이후같은명령에`--resume docs/2026-11-02/손가락전환실험/진단/NEW_REPRO_TRAIN/J/final.pt`와새out을지정하여추가100회를엄격재개한다. seed17은첫실행과재개모두`--seed 17`로맞춘다.

평가: `runtime.py evaluate --checkpoint ABSOLUTE_PT --action-mode mean --num-envs 32 --out NEW_EVAL`. sampled는`--action-mode sampled`,진단축소는추가`--std-scale .5`,확장은`--num-envs 128`. 기본정책·metadata를바꾸지않는다.

영상: `runtime.py render --checkpoint ABSOLUTE_PT --num-envs 1 --out NEW_RENDER`. renderer는mean이며sampled로라벨하지않는다. run은공식scripts/tab2body.py를통해nativeGym을Torch보다먼저로드한다. 외부PYTHONUTF8없음.

집계: `PYTHONPATH=. python -X utf8 docs/2026-11-02/손가락전환실험/도구/analyze.py ABS_EVAL`(도구경로는이연구하위절대경로사용). CPU검사: tests/test_pair_runtime.py,tests/test_study_safety.py. 실제전체명령은각로그및도구/study.py에있다.

봉인드라이버는이미완료한출력·profile을재실행하지않는다. 동일study에profile선택문턱을바꿔넣거나옛checkpointmetadata를새값으로수정하지말것. Python-O/PYTHONOPTIMIZE검사를끄지말것. 새소스/GPU/입력이라면새연구기준군필요.
