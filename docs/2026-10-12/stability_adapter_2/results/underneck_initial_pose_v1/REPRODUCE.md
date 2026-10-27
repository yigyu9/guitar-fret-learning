# 선택 초기 배치 재실행

선택 초기값과 팔24 목표 유지 PI를 같은 조건으로 실행하는 명령이다. 아래 새 결과 경로가 이미 있으면 실행을 중단하므로 마지막 폴더명만 새로운 이름으로 바꾼다. 기존 결과를 덮어쓰지 않는다. 실행은1200 physics step/5초이며 전신·손151프레임 영상과 실제 초기각·PD·접촉·trace를 저장한다. 이 명령은 초기 후보의 재현이며 fret/strike 학습 또는 모든 손가락의 접촉 유지 성공을 뜻하지 않는다.

```bash
cd /home/ajou/yigyu/3
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
MUJOCO_GL=disable MPLBACKEND=Agg \
VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.x86_64.json \
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib \
/home/ajou/miniconda3/envs/rl38/bin/python \
-m stability_adapter_2.underneck_pose_trial_v5 \
--candidate /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_initial_pose_v1/refine/candidate_w10000.json \
--out /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/underneck_replay_001 \
--dynamic --hold
```

이때 source 전체를 바꿔 기타를 고정하거나 PD값을 변경할 필요가 없다. 다른 관절 후보는 새로운 입력JSON과 새 결과 경로로 실행한다. 실제 사용 모델은 하체고정 파생자산이고 양팔·손/몸통의 기존 self-collision exclusion 정책을 사용한다. CPU PhysX/Mesa renderer 조건이며 GPU 학습 자원은 별도 확인한다.
