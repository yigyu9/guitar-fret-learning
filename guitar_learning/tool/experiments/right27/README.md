# 오른손 전체 손가락을 포함하는 타현 정책

오른쪽 팔꿈치3 + 손목3 + 엄지5 + 검지·중지·약지·소지 각4 = 27축을 학습한다. 어깨·흉곽은 기존 지지 제어를 따른다. 오른손21축은 준비 기준각을 중심으로 native 관절 한계까지 직접 요청하며 목표각 변화는4rad/s로 제한한다.

```bash
python scripts/tab2body.py run -m guitar_learning.tool.experiments.right27 train \
  --size large --num-envs 1024 --horizon 32 --updates 100 \
  --out runs/right27_01
```

별도 `--song SONG_ID`가 없으면 기존 기본 곡을 사용한다. 동일 계약으로 재개할 때는 `--resume runs/right27_01/final.pt`와 새 `--out`을 지정한다. 기존 left/right6 체크포인트는 새 정책 identity와 맞지 않아 거부한다.

```bash
python scripts/tab2body.py run -m guitar_learning.tool.experiments.right27 probe \
  --num-envs 4 --size small --out runs/right27_probe_01
```

probe는60tick 동안 ±0.25 명령을 주어21축 모두의 목표각과 실제각 변화, tick당 속도 제한을 검사한다. 학습 성능 검사는 아니다. CPU 검사는 `python -m unittest guitar_learning.tests.test_right27_policy guitar_learning.tests.test_right27_control`이다.

읽는 순서: `__main__.py` → `runtime.py` → `pool.py` → `environment.py`·`control.py` → `policy.py`. 수집·PPO·로그·저장은 기존 공용 코드를 재사용한다.39칸 운반 배열에서0:12는 비활성,12:33은RH21,33:39는팔꿈치·손목6이다. 확률과 우도는 실제27축만 계산한다.

기존 왼손 장기 연구의 소스 봉인을 유지하기 위해 새 진입점을 사용한다. 기존 `train_legacy --hand right`와 다른 연구의 `right_strike`는 종전6축 경로 그대로다. 새 타현27 학습에는 반드시 위 명령을 사용한다.

타현 목표24열·피크 교차 판정·보상은 기존 값을 유지한다. 손가락 제어 범위 확장과 개별 손끝으로 줄을 튕기는 판정은 다른 작업이다. 현재 피크는 검지의 고정 자식이라 검지 움직임에 따라 함께 움직이며, 엄지와 검지 사이의 동적인 피크 파지는 모델링하지 않는다.

실제 검증 결과는 `/home/ajou/yigyu/3/docs/2026-11-09/오른손_27자유도_타현정책_v1/`에 저장한다.
