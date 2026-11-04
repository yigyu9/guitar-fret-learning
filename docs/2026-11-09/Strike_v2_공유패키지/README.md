# 과거 Strike-v2 — 공유용 코드와 해설

고정된 기타를 가상 피크로 타현하는 과거 강화학습 코드의 검토용 사본이다. **관측 303차원 → 블록별 인코딩 합계 552차원 → 오른팔·손 30축 행동**을 사용한다. 단일 타현, 스트럼, 회복과 곡 내 목표 전환을 다룬다.

원본은 `archive/legacy_guitar_20261019/tab2body`, 이 사본의 기준은 `archive/strike_v2_20261104`이다. 공유본에서는 불필요한 압현·양손 결합 코드를 제외하고 입력 검증과 타이밍 경계를 보완했다. 현재 `guitar_learning`의 27축 타현 정책과는 별도 구현이다. 원본·활성 학습 코드는 수정하지 않았다.

작성일은 2026-11-04이며, 상위 디렉토리의 `2026-11-09`는 요청된 저장 위치의 이름이다.

## 처음 읽는 순서

1. [구조·입력·출력·신경망](docs/01_구조와입출력.md)
2. [판정·보상·학습 단계](docs/02_판정과보상.md)
3. [실행 방법·검증 범위](docs/03_실행과검증.md)
4. [원본 대비 변경·남은 개선점](docs/04_검토와변경.md)
5. [현재 guitar_learning의 타현 구조·파일별 읽는 위치](docs/05_현재_guitar_learning_타현구조.md)

현재 프로젝트의 타현 작업을 이어받는 연구원은 5번 문서를 함께 읽는다. **이 패키지의 과거30축 코드와 현재 자유 기타27축 코드는 별도 구현**이며, 5번 문서에서 입력·신경망·판정·보상·제어·학습 실행의 대응 위치를 정리했다. 현행 `guitar_learning` 소스와 자산은 이 공유 패키지에 복사하지 않았으므로 현재 코드를 실행하려면 해당 프로젝트도 필요하다.

| 질문 | 먼저 볼 코드 |
| --- | --- |
| 실행 옵션과 전체 학습 흐름 | [train_strike.py](tab2body/train_strike.py) |
| 학습률·보상 계수·단계 기준 | [strike_cfg.py](tab2body/strike_cfg.py) |
| 관측 항목과 인코더 크기 | [strike_v2_contract.py](tab2body/strike_v2_contract.py) |
| actor·critic 신경망 | [strike_v2_model.py](tab2body/learning/strike_v2_model.py) |
| 관측 조립·행동·사건 진행·종료 | [task_strike.py](tab2body/env/tasks/task_strike.py) |
| 피크 교차 검출 / 사건 판정 | [strike_detector.py](tab2body/env/strike_detector.py) / [strike_events.py](tab2body/env/strike_events.py) |
| 보상 / PPO 업데이트 | [strike.py](tab2body/env/rewards/strike.py) / [ppo.py](tab2body/learning/ppo.py) |
| 목표 컴파일 / 목표 로딩 | [strike_goal_compiler.py](tab2body/env/strike_goal_compiler.py) / [strike_goals.py](tab2body/env/strike_goals.py) |

## 들어 있는 것

```text
tab2body/       과거 타현 코드·공통 의존 코드·검사·합성 입력 3개
tools/         공유본의 CPU 검증 도구
docs/          구조·보상·실행·검토 설명
verification/  CPU 결과·로그·출처·변경 내역·독립 검수 기록
requirements-cpu.txt
FILES.sha256   배포 시점의 파일 해시 목록
```

원래 `tab2body` 내부 구조를 유지해 import와 코드 지문 검증 경로를 보존했다. 대형 환경 파일을 임의로 쪼개거나 공용 PPO 내부를 정리하지 않았다.

## CPU에서 먼저 확인

압축을 푼 패키지 디렉토리에서 실행한다. 아래 검사는 GPU와 Isaac Gym을 사용하지 않는다.

```bash
python -m pip install -r requirements-cpu.txt
python -B tools/verify_cpu.py
```

검사 결과는 [cpu_report.json](verification/cpu_report.json)에 저장된다. 원래 검사들은 `main()`과 `assert`를 사용하는 스크립트이므로 일반 테스트 탐색의 “0개 통과”를 검증 결과로 사용하지 않는다.

**이 패키지만으로 물리 학습을 바로 실행할 수는 없다.** 인체·기타 자산, 초기 자세·PD 설정, 파지 기준, 학습용 악보, Isaac Gym 실행 환경은 포함하지 않았다. [필수 외부 항목과 실행 순서](docs/03_실행과검증.md)를 먼저 확인한다. CPU 통과는 물리 연주·학습 수렴·음향 성공을 의미하지 않는다.
