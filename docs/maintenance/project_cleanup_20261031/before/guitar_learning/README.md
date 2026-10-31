# 기타 학습: 기본 왼손 finger-skill

현재 기본 학습은 **finger-skill v3, GPU 왼손 J33 공동 학습 전용**이다. `--learning-family finger-skill`을 생략해도 같은 설정과 실행 경로를 사용한다. R/F 단계, 자동 단계 전환, 단계별 정책 이전, F 행동 유지와 숙련도 gate는 제거했다. 기존 song·오른손·CPU 실행은 별도 도구로 유지한다.

## 현재 실행과 보관 범위

기본 J 학습·평가·영상, 기존 song·CPU·오른손 실행, 곡 입력 도구와 현재 손가락 진단을 유지한다. [short_finger_learning](tool/experiments/short_finger_learning/README.md)과 이후 추가된 명시적 비교 도구는 별도 실행한다. 자연스러운 압현 준비의 E0~E4 비교는 [natural_press v3 안내](../docs/2026-11-02/압현성공/experiments/natural_press_v3/README.md)를 따른다. 손별 단계·모방·타이밍·정책 준비·단음 음악 품질과 과거 전문 실험8개는 보관했다.

보관 내용은 [보관 안내](archive/20261028_before_legacy_retirement_v1/ARCHIVE_INDEX.md), 원문 경로·SHA는 [manifest](archive/20261028_before_legacy_retirement_v1/manifest.json), 활성에서 제거한 목록은 [retired_files](archive/20261028_before_legacy_retirement_v1/retired_files.json)에서 확인한다. 이번에 Python193개(구현123개·검사/보조70개)와 전문 매뉴얼6개를 보관했다. 공용 압현·타현 측정과 CPU의 0초 준비·지속 세션은 현재 라이브러리로 유지하며, 보관 코드를 현재 실행에서 import하지 않는다.


## 프로젝트 이동·공유 실행

[이식성 안내](../docs/PORTABILITY.md)의 로컬 실행기를 사용한다. `scripts/tab2body.py`는 각 PC의 활성 Python과 로컬 Isaac Gym·Torch 캐시를 사용하고 프로젝트 소스·데이터는 공유 경로에 남긴다. 출력 경로는 두 PC에서 서로 다르게 지정한다. 상대 CLI 경로는 호출한 작업 디렉토리를 기준으로 하므로, 다른 디렉토리에서는 실행기·출력·checkpoint에 절대 경로를 명시한다.

이번 변경 이후 checkpoint는 `finger_skill_resume.v4`이며, `project://` 입력 경로·설정 snapshot·소스/자산 SHA·정책/물리 계약을 검증한다. 실행 디렉토리를 다른 프로젝트 루트로 복사해 재개·평가·영상에 사용할 수 있다. `portable_checkpoint_ref`는 현재 보고서 디렉토리 기준 참조다. 감사용 원래 실행 절대 경로는 남기되 입력 탐색에 사용하지 않는다. 이전 절대 경로 checkpoint는 명확한 오류로 거부하며 원래 소스 트리에서만 사용한다.

## 실행

Isaac Gym Preview4가 설치된 `rl38` 환경에서 프로젝트 루트로 이동한다.

```bash
conda activate tab2body-rl38
# 프로젝트 루트에서 실행. PC별 로컬 런타임을 먼저 준비한다.
python scripts/tab2body.py prepare

python scripts/tab2body.py run -m guitar_learning.train \
  --size large --num-envs 1024 --horizon 32 --updates 3000 \
  --checkpoint-every 250 --seed 7 \
  --out runs/left_finger_skill_default_01
```

위 명령은 실행 예시이며 이번 정리에서 새 학습을 진행했다는 뜻은 아니다. 출력은 아직 없는 새 디렉토리여야 한다. `--hand left`, `--device cuda:0`, `--learning-family finger-skill`은 기본값이라 생략할 수 있다. 물리 옵션은 기본 `auto`이며 이 경로에서는 GPU를 선택한다. `--physics gpu`로 명시해도 같다. 기본 곡은 `05_BN2-131-B_solo`의 67음이다. 곡 변경은 `--song SONG_ID`를 사용한다.

크기·환경 수·반복을 생략하면 medium·128환경·100업데이트이고, 수집 길이는 H32, checkpoint 간격은 250, seed는 7이다. GPU가 없으면 오류로 종료하며 CPU로 자동 대체하지 않는다. 기본 진입점은 왼손 GPU만 지원한다.

## 손가락 직접 제어

GPU 왼손 손가락21축은 목표각을 직접 지정하는 `position` 방식만 사용한다. 행동0은v9 초기 자세의 유지 목표, -1/+1은각관절의native하한/상한 요청이다. 같은 행동을 계속 주면 같은 각도를 요청하며 행동값을 목표에 계속 더하지 않는다. 목표각 변화는4rad/s로 제한되고 전체 가동범위·PD/힘·손가락 움직임 비용0은 유지한다. B 대기 자세로 자동 복귀시키는 기능은 아니다.

변경 전 누적 제어 구현·검사·문서는 [원문 보관 manifest](archive/20261029_before_direct_finger_control_v1/manifest.json)에 보존했다. 구형 누적 설정과 checkpoint는 현재 직접 제어로 재개하지 않는다. [전환 검증 기록](../docs/2026-10-29/direct_finger_control_v1/README.md)을 따른다.

## 학습 흐름

`train.py` → `training/launch.py` → `training/finger_skill_runner.py`가 기본 경로다. 설정은 `launch.py`, 환경 진행·수집은 `rollout.py`, 정책은 `policy.py`, 최적화는 `ppo.py`, 저장·로그·운영은 `training_log_io.py`에서 함께 읽을 수 있다.

기본 경로의 주요 구현에는 한글 역할 설명·주석을 작성했다. [코드 읽는 순서](docs/CODE_STRUCTURE.md)에서 주요 여섯 파일부터 따라갈 수 있다.

1. 검수된 곡·초기 자세·자산·소스의 입력 계약을 확인하고 새 정책을 만든다. 기존 전문가·BC를 요구하지 않고 J 모델을 새로 만든다.
2. 각 환경의 시작에서 손가락을 벌리고 손목을 올린 v9 초기 자세를 복원하고 첫 tick부터 왼팔·손목·손가락 33축을 함께 학습한다(J33). 비활성 오른손 6축 행동은 0이다.
3. 물리 240Hz, 정책 60Hz, 결정 유지 K1로 진행한다. H32마다 PPO를 갱신하며 진행 중인 에피소드의 장면·시계·원장·종료 타이머는 이어간다.
4. 초기에는 곡의 선택 구간을 학습한다. 원래 계획 전이 예산 `updates × horizon × num_envs`의 25%를 반영한 뒤, 이후 초기화되는 환경부터 전곡으로 바뀐다. 진행 중인 구간을 강제로 끊지 않으므로 실제 구간/전곡 비율이 정확히 25/75는 아니다.
5. 정상 끝 또는 물리·손목 실패 때 해당 환경만 초기화한다. 반복별 항목 보상·종료 통계와 모델을 저장한다.

상태는 **557차원(기반 552 + 남은 로컬 시간 1 + 손목 종료 관측 4)**이다. R/F/J 구분 3열과 계획 결정 길이 1열은 제거했다. 환경 계약은 `finger_skill.v3`, 정책은 `finger_skill_policy.v2`, 실행 보고서는 `finger_skill_run.v2`, 재개 메타데이터는 `finger_skill_resume.v4`를 사용한다. PPO는 reward/cost를 결합한 advantage와 고정 cost weight 1을 사용한다. 자유 기타·중력 ON·스트랩 OFF, Root 고정·하체 유한 제어, LH21 전체 native 가동범위·4rad/s·기존 PD/힘 상한과 손가락 움직임 비용 0을 유지한다.

기본 학습에는 손가락 명령·추종·접촉 진단 로그가 자동으로 남는다. `J/finger_control_trace.jsonl.gz`는 대표 환경의 최초600 tick 상세 기록이고, 종료 에피소드에는 전체 환경의 관절별 요약을 남긴다. [기록 항목과 해석](docs/LOGGING.md#손가락-제어압현-진단-2026-10-29-추가)을 참고한다.

## 보상과 종료

현재 보상 명칭과 로그 키는 아래 9개다. 항별 계산과 변경 이력은 [보상 상세](../docs/2026-10-26/왼손보상구조/12_v25보상단순화와종료.md)를 따른다.

| 보상항 | 로그 키 |
| --- | --- |
| 목표 패드 접근 | `song_left_approach` |
| 최초 접촉 | `song_left_contact` |
| 압현 유지 | `song_clean_hold` |
| 압현 달성 | `song_left_success` |
| 오압현 | `song_wrong_press` |
| 음 수행 부족 | `song_performance_deficit` |
| 대기 자세 | `song_finger_standby` |
| 엄지 안내 | `song_thumb_support` |
| 행동 변화 | `action_change` |

손목 안내와 물리 실패는 별도의 보상항 대신 종료 조건으로 사용한다. 손목 종료v2는 안내 영역 밖 추가3cm 초과 시간을 누적해1.5초가 되면 종료한다. 활성 상태에서 추가2~3cm로 복귀하면 누적 시간을 초당1초씩 줄이고,2cm 이내로 돌아오면 상태·시간을 초기화한다. 초기 3초 유예가 있으며, 심각 이탈 10cm 이상이 0.10초 지속되는 조건은 유예 중에도 적용한다. 물리 실패 문턱은 기존 기준을 유지한다.

오압현 출처 판정은 `wrong_press_sources.v3`이다. 같은 손가락의 유효 끝마디 패드라도 같은 줄의 더 높은 프렛에 닿으면 낮은 목표를 차단한다. 낮은 프렛 접촉이 남는 것 자체는 높은 목표의 실패 조건이 아니다. 변경 전 두 프렛 동시 성공을 인정한 저장본은 현행 판정으로 strict 재개하지 않는다. [보정과 전환 검증](../docs/2026-11-02/압현성공/experiments/target_transition_v2/PLAN.md)을 따른다. 이 판정은 기하·몸체 하중 후보이며 실제 현 압력·음향 측정을 대신하지 않는다.

엄지 후면 안내는 `gpu_thumb_rear_support.v3`를 사용한다. 실제 face가 참조하는 연주용 neck1의 유한 뒷면을 기준으로 하며, 사용되지 않는 OBJ 꼭짓점과 headstock 전이면을 제외한다. 최대0.02/초 예산과 기존 거리·방향·부하 조건은 유지한다. 현곡의 모든 안내 범위가 이 면 안에 있음을 검사한다. 변경 전 소스는 [보관 manifest](archive/20261027_before_thumb_rear_surface_v3/manifest.json)에 보존했으며, 이전 저장본을 수정 후 소스에서 strict resume/평가하지 않는다. 실제 검증 상태는 [수정 기록](../docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/thumb_rear_surface_v3/PLAN.md)을 따른다.

실패 비용은 한 번만 `5 + 2 × 남은 로컬 시간(초) + 남은 미관측 음 감점 예산`으로 부과한다. 손목·물리 실패가 겹쳐도 중복 부과하지 않는다. [보상·종료 상세](../docs/2026-10-26/왼손보상구조/12_v25보상단순화와종료.md)를 따른다.

GPU 왼손의 초기 자세는 `assets/prepared_reset_v1/left_standby_v9.json`이다. 에피소드 경계에서 한 번 복원하며 학습·평가·영상이 같은 자산을 사용한다. 원본035/v14와 오른손·CPU 과거 경로는 보존한다. 대기 B 권고는 MCP 중심±30도, PIP/DIP 중심±15도 안에서 같은 최대품질을 주고 바깥에서 부드럽게 줄어든다. 벌림은 보상 대상이 아니며 준비·압현 중 해당 손가락의 대기 보상을 끄는 기존 gate를 유지한다. 초기 v9와 B 대기 권고는 서로 다른 역할이다. 변경 전 checkpoint는 현재 입력·보상 계약으로 strict resume하지 않는다.

## 저장·재개·평가

실제 학습 저장본과 로그는 **`--out` 아래 `J/`**에 저장된다. 최상위 `report.json`의 `final_checkpoint`에서도 최종 모델 경로를 확인한다.

| 출력 | 내용 |
| --- | --- |
| `settings.json`, `report.json` | 전체 실행 설정·완료 여부·최종 checkpoint·전이 수 |
| `J/initial.pt`, `J/checkpoint_*.pt`, `J/final.pt` | 시작·주기·최종 모델, optimizer·RNG·학습 진행 상태 |
| `J/failure_last_valid.pt` | 오류 시 저장 가능한 유효 상태가 있을 때만 생성하는 복구본 |
| `J/learning_metrics.jsonl` | 반복별 PPO·보상/비용·9항목 평균·실제 구간/전곡 노출 수 |
| `J/episodes.jsonl`, `J/episode_metadata.json` | 종료 에피소드·항목별 누적 보상·종료 비용·음별 원장·공통 메타데이터 |
| `J/transitions.jsonl.gz`, `J/decisions.jsonl.gz` | 제어 전이·정책 결정과 학습 반영 여부. 매 시점의 9항목 분해는 저장하지 않음 |
| `J/checkpoint_manifest.jsonl` | 저장본 크기·SHA·저장 시점 |
| `J/inputs_before.json`, `J/training_contract.json` | 실행 입력 SHA와 실제 환경·정책 계약 |
| `J/status.json`, `J/resources.jsonl`, `J/events.jsonl` | 진행·자원·운영 사건 |
| `J/report.json`, `J/gpu_scene_initial.json`, `J/gpu_scene_final.json` | 실제 학습·종료·GPU 장면 감사 |

재개는 동일 소스·자산·정책·보상·물리 계약의 checkpoint를 사용한다. 예를 들어 위 명령의 모델 생성 뒤 다음과 같이 추가 500회를 실행한다.

```bash
python scripts/tab2body.py run -m guitar_learning.train \
  --size large --num-envs 1024 --horizon 32 --updates 500 \
  --checkpoint-every 250 --seed 7 \
  --resume runs/left_finger_skill_default_01/J/final.pt \
  --out runs/left_finger_skill_default_resume_01
```

모델·두 optimizer·난수·구간 선택기·누적 노출을 복원하며, 처음 계획한 25% 문턱은 추가 반복 수로 다시 계산하지 않는다. 물리 장면은 초기 자세의 새 에피소드에서 시작한다. **이전 finger-skill v1/v2 checkpoint는 현재 v3에서 재개·평가·렌더할 수 없다.** 상태·정책·재개 계약이 변경되었으며 자동 이전과 호환 분기는 제거했다. 현재 v3에서 동일 소스·자산·계약으로 만든 저장본만 엄격 재개한다.

평가·영상은 학습과 별도 명령이며, 현재 소스로 만든 모델에 다음 도구를 사용한다.

```bash
python scripts/tab2body.py run -m guitar_learning.tool.evaluation.evaluate_finger_skill \
  runs/left_finger_skill_default_01/J/final.pt \
  --scope full_song --num-envs 128 \
  --out runs/left_finger_skill_default_eval_01

python scripts/tab2body.py run -m guitar_learning.tool.demonstration.render_finger_skill \
  --checkpoint runs/left_finger_skill_default_01/J/final.pt \
  --scope full_song --num-envs 16 \
  --out runs/left_finger_skill_default_video_01
```

렌더는 환경 0의 첫 에피소드를 실제 물리에서 실행해 `hand.mp4`, `fullbody.mp4`, 자세·종료 기록을 남긴다. 실패로 끝난 영상도 그대로 기록한다. 접촉 후보는 실제 현 압력·음향 성공 인증이 아니며 `completed`는 실행 완료를 뜻한다. 이전 v25 짧은 검증의 전곡 평가 16개는 모두 손목 종료·평균 달성 0/67이었다. 기본 구조 채택을 연주 성능 검증으로 해석하지 않는다. [당시 봉인 결과](../docs/2026-10-26/guitar_learning_reward_simplification_v25/VERIFICATION.md)는 그대로 보존한다.

## 이전 구현과 문서

기존 song·오른손·CPU는 `python scripts/tab2body.py run -m guitar_learning.tool.training.train_legacy`로 실행한다. R/F/J v24 실행 옵션은 제거했으며 이전 원문은 [J 전용 전환 전 보관본](archive/20261028_before_joint_only_v3/manifest.json)에 보존했다. [도구 안내](tool/README.md)에 명령이 있다. 현재 코드가 사용하는 공용 설정·환경·정책·기록 모듈은 활성 라이브러리로 남기며, 보관본을 import하지 않는다.

변경 전 소스·문서는 [보관 manifest](archive/20261026_before_finger_skill_default/manifest.json)와 [이전 README](archive/20261026_before_finger_skill_default/guitar_learning/README.md)에 보존했다. 이전 버전의 장황한 변경 이력·명령은 보관 문서에서 확인한다. [코드 배치](docs/CODE_STRUCTURE.md) · [상세 학습 흐름](../docs/2026-11-02/코드해설/00_전체흐름과읽는방법.md).

## 코드와 변경 이력

현재 파일의 역할과 읽는 순서는 [코드 지도](docs/CODE_STRUCTURE.md), 함수별 설명은 [코드 해설](../docs/2026-11-02/코드해설/README.md)에 모았다. 정적 의존성·활성 파일 수는 해당 문서의 조사 시점을 따른다. 과거 통합 당시 파일 수를 현재 실행 파일 수로 해석하지 않는다.

이 문서에 중복되던 통합·J 전용 전환·가독성 정리·진단 제어의 상세 이력은 [정리 전 README](../docs/archive/document_cleanup_20261030/before/guitar_learning/README.md)에 보존했다. 기존 checkpoint의 엄격한 소스·입력 검증은 문서 정리와 무관하게 유지한다.
