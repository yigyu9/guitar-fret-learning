# Tab2Body — 자유 기타 연주 제어 연구

오디오에서 구성한 연주 목표를 휴머노이드와 자유 기타의 물리적 상호작용으로 실행하는 연구다. 논문 작업 제목은 **From Audio to Full-Body Guitar Performance with a Freely Moving Instrument**다.

**현재 상태는 [CURRENT_STATUS](/home/ajou/yigyu/3/CURRENT_STATUS.md), 신규 학습은 [현행 학습 안내](/home/ajou/yigyu/3/guitar_learning/README.md)를 먼저 읽는다.**

## 현재 조건과 확인된 결과

Root만 고정하고 하체는 유한한 자세 유지 제어를 사용한다. 기타는 자유 강체·중력ON·스트랩OFF다. 105개 모델 입력 채널과97개 비영 가동범위 축,8개 원 영범위 축을 구분한다. 정책 출력은 왼팔·왼손33개와 오른팔꿈치·손목6개이며 전신105축을 모두 학습하는 구조는 아니다.

현행 기본은 GPU 왼손 finger-skill v3의 J33 공동 학습이다. 상태557·K1·기본128환경/H32를 사용한다. 기본 흐름은 구현24개와 초기화8개로 연결되며 활성 Python은281개다. CPU·오른손 song과 현행 진단·영상·로그 도구는 유지한다.

과거 손별 초기 정책은 각각4/4 품질 평가를 통과했다. 단음joint는 같은 장면에서 두 손을 제어하고 실제840전이·PPO1업데이트·저장 모델 재평가까지 확인했다. 안전하게 완주했으나 공동 음악 성공은0회였다. 당시 전곡song은4096전이·8업데이트와 안전 전곡2회 완주를 확인했으며 음악적 전곡 성공은0/2다. 이 과거 성과를 현행 J 전용 학습의 성과로 상속하지 않는다.

## 코드와 문서

| 위치 | 역할 |
|---|---|
| [guitar_learning 현행 안내](/home/ajou/yigyu/3/guitar_learning/README.md) | 신규 자유 기타 환경·측정·학습과 버전 구분 |
| [과거 joint](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_legacy_retirement_v1/guitar_learning/tool/experiments/joint/README.md) | 보관한 단음 공동 실행·PPO·평가의 원문 |
| [과거 song 계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_full_song_20261019.md) | 당시 전곡67음·500상태·1969tick 확장 기록 |
| [paper](/home/ajou/yigyu/3/paper/README.md) | 논문 본문·근거·작성 원칙 |
| [학습 기준 초기 자세](/home/ajou/yigyu/3/paper/initial_pose/current_v3/README.md) | 기존035/v14의 값·영상·개별 시험 |
| [tab2fingermapping](/home/ajou/yigyu/3/tab2fingermapping/README.md) | 오디오·탭·코드·운지 전처리 |
| [압현·타현](/home/ajou/yigyu/3/guitar_learning/README.md) | 현재 환경·측정·학습 진입점 |
| [과거 양손·전곡](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_legacy_retirement_v1/guitar_learning/tool/experiments/song/README.md) | 보관한 양손 실행·공통 시간축·공동 판정 |
| [도구](/home/ajou/yigyu/3/guitar_learning/tool/README.md) | 곡 번들 등록·데이터·타현 계획·입력 감사·타임라인 |
| [구형 코드 보관](/home/ajou/yigyu/3/archive/legacy_guitar_20261019/README.md) | fret/full/strike/stability_adapter/stability_adapter_2/tab2body 원본과 과거 실행 계보 |
| [전문 실험·구형 실행기 보관](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_legacy_retirement_v1/ARCHIVE_INDEX.md) | 과거8실험·전문 환경·CLI·검사 등220파일(193 Python)의 원문과 SHA |
| [문서 색인](/home/ajou/yigyu/3/docs/DOCUMENT_INDEX.md) | 목적별 현재 문서와 실험 근거 |

## 실행 환경

물리 학습은 Isaac Gym Preview4가 설치된 `rl38` 환경을 사용한다. 기본 `python -m guitar_learning.train --out NEW`는 왼손 finger-skill v3(J 전용)의 GPU PhysX·GPU tensor pipeline 학습을 실행한다. `--learning-family finger-skill`은 생략할 수 있다. 설정·보상·종료·저장 명령은 [현행 안내](/home/ajou/yigyu/3/guitar_learning/README.md)를 따른다. 별도 song·오른손·CPU 실행은 [도구 안내](/home/ajou/yigyu/3/guitar_learning/tool/README.md)의 `python -m guitar_learning.tool.training.train_legacy`를 사용한다. v24와 과거 전문 실험 명령은 보관본의 역사 기록이다. 오디오 전처리는 별도 `tab2fm` 환경을 사용한다.

```bash
cd /home/ajou/yigyu/3
conda activate rl38
export PYTHONPATH="$PWD/isaacgym/python:$PWD${PYTHONPATH:+:$PYTHONPATH}"
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib:${LD_LIBRARY_PATH:-}
```

Native Python 진입점은 NumPy·Torch보다 Isaac Gym을 먼저 불러온다. 출력 경로는 새 디렉토리를 사용하고, 경로별 설정과 checkpoint 계약을 혼용하지 않는다. 과거 [단음 검증 근거](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_joint_v1/README.md), [전곡 실험 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1)는 당시 계약의 기록이다.

Stage1은 [설치 안내](/home/ajou/yigyu/3/tab2fingermapping/SETUP.md)에 따라 다음과 같이 실행한다.

```bash
conda activate tab2fm
cd /home/ajou/yigyu/3/tab2fingermapping
python pipeline.py /path/to/audio.wav --bpm 117
```

생성한 목표를 검수한 뒤 곡 번들에 등록한다. 현재 물리 실험의 성능을 자동 오디오 전사의 정확도로 해석하지 않는다.
