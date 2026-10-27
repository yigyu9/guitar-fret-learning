# 준비 관문 없는 왼손 동시 학습 v25

실행 당시035/v14 준비 상태에서 팔·손목·엄지17축과 네 손가락16축을 처음부터 함께 학습한다. support/finger 인코더와 출력부는 분리하며 활성33축 모두 PPO에 포함한다. R 통과 평가나 R32회 소진에 따른 전체 실행 중단은 없다. 기존 기본 진입점은 보존했으므로 **아래 v25 명령으로 명시적으로 실행**한다.

```bash
python -m guitar_learning.tool.experiments.active_press_v25.run train \
  --size large --num-envs 1024 --updates 1000 --max-wall-seconds 3600 \
  --out /home/ajou/yigyu/3/runs/active_press_v25_run01
```

Isaac Gym용rl38 환경에서 프로젝트 루트를 작업 위치로 사용한다. PATH와LD_LIBRARY_PATH는 기존 guitar_learning README의 환경 설정을 따른다. 출력 경로는 새 경로여야 한다. 업데이트1000은 상한이며 전체 실행시간3600초를 먼저 사용하면 업데이트 경계에서 저장하고 종료한다. 정리 시간 때문에 소폭 초과할 수 있다.50회마다 추가 저장하며 초기/최종 저장본도 남긴다.

## 변경 계약

- **559상태**: 기존 v24의557상태에 손목 연속 이탈 시간과 남은 유예 시간을 추가한다. support와 critic 모두 타이머를 본다.
- **원곡 연속 구간 학습**: 기존 균등구간 sampler·음 ID·타이밍·선택 분모 유지. 고정 전곡 평가는 별도로 원래67음을 사용한다.
- **최대3tick의 공동 결정**: 모든 활성 명령을 함께 유지한다. press/onset/end의 전후60Hz 경계·H32·실패에서 짧게 확정한다. 실제 지속 d에 맞는 discount/GAE/PPO를 적용한다. 물리240Hz·제어60Hz는 그대로다.
- **팔 탐색**: 위치 제어를 유지하며 초기 latent std는 .10（기존 약.05）이다. .25 첫 후보는 기타 이탈이 많아 채택하지 않았다. 탐색 크기와 공동 학습의 장기 효과는 아직 입증하지 않았다.
- **엄지5축**: 준비 참조각에서 native 전체 범위의 부호별 위치 요청.0은 참조 자세 요청이며 동일 명령이 계속 누적되지 않는다.4rad/s·기존 PD/힘 상한 유지. 관절 고정이나 넥 강제 부착은 없다.
- **나머지16축**: 기존4rad/s 누적 제어·native 전체 범위·움직임/속도/행동변화 비용0 유지.0은 이전 목표 유지다.
- **손목**: 안내 관측과 진단은 유지하고 연속 손목 보상은0이다. 기존 안내 상자를 각축3cm 확대한 영역 밖에 .75초 연속 머물면 `wrist_region_exit`로 에피소드를 종료한다. 초기3초와 안내 중심이1cm 이상 이동한 뒤 .35초 유예를 둔다. 안내 영역에서 각축10cm 넘게 벗어난 심각한 이탈은 초기3초 이후 즉시 종료한다. 재진입하면 연속 이탈 타이머를 지운다.
- **실패**: 원래 물리 기준과 새로운 손목 종료 이유를 구분한다. true terminal bootstrap0·실패tick 양성 억제·잔여구간 실패 비용을 재사용한다. 미관측 꼬리의 목표 음을 분모에서 빼지 않는다.
- **초기 상태/물리**: 자유 기타·중력ON·스트랩OFF·root/의자 고정·기존 하체 유한 제어·105/97/8·48POSITION/57EFFORT 유지. 새 상태 주입이나 기타 직접 힘을 추가하지 않는다.

같은 v25 설정의 저장본은 `train --resume /absolute/path/to/J/final.pt --updates N --out NEW`로 추가N회 엄격 재개한다. v24나 .25 탐색 후보 저장본을 현행 계약으로 재해석하지 않는다.

```bash
python -m guitar_learning.tool.experiments.active_press_v25.run evaluate \
  --checkpoint /absolute/path/to/J/final.pt --num-envs 16 --out /absolute/path/to/new_evaluation
python -m guitar_learning.tool.experiments.active_press_v25.run render \
  --checkpoint /absolute/path/to/J/final.pt --num-envs 16 --out /absolute/path/to/new_render
```

과거 family의 수집/PPO/저장 원장 형식을 재사용한다. 실행 설정의 `active_press`, 정책 architecture schema, 실제 control/termination 계약이 새 버전을 식별하며 엄격 로드에서 비교된다. 기존 소스를 디스크에서 고치지 않고, 단일 실행 프로세스 안에서만 새 클래스들을 연결하고 종료 시 원복한다.

[구현·검증 결과](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_active_press_v25/README.md) · [다각도 목표 영상](/home/ajou/yigyu/3/docs/2026-10-26/시각화/wrist_targets_multiview_v25/README.md)
