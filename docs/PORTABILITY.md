# Tab2Body: 다른 PC와 SSHFS에서 실행

현행 대상은 GPU 왼손 finger-skill v3, J33, 손가락 LH21 position 직접 제어다.
이번 작업은 보상·물리·정책 연산·성공 판정을 변경하지 않는다.

## /3 내부 자료만 사용하는 현재 실행

프로젝트의 현재 위치를 기준으로 자산·곡·준비 자세·CAS 원본을 해석한다. 외장 저장소·다른 작업 폴더의 프로젝트 자료로 우회하지 않는다. 등록된 과거 절대 경로는 내부 복사본을 고르는 식별자로만 쓰고, 미등록 외부 경로·`..` 탈출·외부 심볼릭 링크는 파일을 읽기 전에 거부한다. 기존 docs 전체가 없어도 아래 최소 구성으로 실행할 수 있다.

`/3`이 로컬 디스크에 있을 때는 캐시와 출력도 프로젝트 내부로 지정한다. 아래 모든 명령은 프로젝트 루트에서 실행한다. Python 환경·표준/설치 패키지·GPU 드라이버·시스템 라이브러리·ffmpeg는 설치 환경이므로 프로젝트 데이터와 구분한다. 실행기의 일반 기본 캐시는 그대로지만 이 안내는 `--cache-root .runtime/cache`를 명시해 외부 캐시를 사용하지 않는다.

```bash
python scripts/tab2body.py --cache-root .runtime/cache prepare
python scripts/tab2body.py --cache-root .runtime/cache run \
  -m guitar_learning.tool.validation.portable_inputs
```

프로젝트 내부의 공백 포함 새 루트로 필요한 파일만 복사해 입력·GPU학습·strict재개·평가·렌더를 검증한다.

```bash
python scripts/smoke_portability.py \
  --out '.runtime/relocated project 01/runs/smoke' \
  --cache-root .runtime/cache \
  --relocate-to '.runtime/relocated project 01' --render
```

출력과 복사 경로는 기존에 없는 새 경로를 쓴다. SSHFS처럼 프로젝트 위치가 원격 파일시스템이면 native 빌드를 그 안에 둘 수 없으므로 뒤의 각 PC 로컬 캐시 방식을 사용한다. 공유 프로젝트 데이터의 외장 의존 제거와 native 바이너리의 각 PC 로컬 실행은 구분한다.

[팀원 요청 파일·현재 경로](TEAM_HANDOFF.md) · [변경·실제 검증](maintenance/self_contained_20261031/REPORT.md).

## 필요한 파일과 환경

프로젝트 전체를 복사하거나, `scripts/smoke_portability.py`의 최소 실행 복사 구성을 사용한다.
현행 실행에 필요한 구성은 `guitar_learning/`의 활성 Python 및 `assets/` 전체,
`data/song_bundles/<사용할 곡>/`, `isaacgym/python/`의 vendor 런타임과 setup.py,
`scripts/`다. `assets/runtime_inputs/.../archive/`는 실제 초기화 입력이므로 제외하면 안 된다.
`guitar_learning/archive/`의 과거 코드와 대량 과거 `docs/` 결과는 기본 학습 입력이 아니다.
Git으로 옮길 때는 이 구성의 실제 파일과 LFS 자산도 모두 받아야 한다.

준비 상태는 `assets/prepared_reset_v1/`의 내부 JSON을 사용한다. GPU 왼손은 `left_standby_v9.json`을 추가 적용하며 오른손·CPU 과거 경로는 원본035/v14를 유지한다.
원래 docs 외부 링크는 역사 기록으로 남아 있으나 현행 실행은 따라가지 않는다.
native manifest는 현재 위치를 프로젝트 상대 경로로 기록한다. 원본 절대 경로와
original SHA는 역사 식별자로 보존하고 현재 파일의 검증을 대체하지 않는다.

Linux x86_64의 각 PC 로컬 디스크에 Python/Conda 환경과 NVIDIA 드라이버를 설치한다.
[환경 파일](../scripts/environment.rl38.yml)은 원본 rl38의 Python3.8.20,
PyTorch2.4.1+cu121, NumPy1.23.5, SciPy1.10.1 등을 고정한다.
설치 전제와 vendor 라이브러리·컴파일러·영상 의존성은 [설치 안내](../scripts/README.md)를 따른다.
환경 파일은 드라이버나 Isaac Gym vendor payload를 다운로드하지 않는다.
프로젝트에 포함된 Preview4 배포물의 라이선스·재배포 조건을 그대로 따른다.

```bash
# 복사한 프로젝트 루트에서
conda env create -f scripts/environment.rl38.yml
conda activate tab2body-rl38
nvidia-smi
python scripts/tab2body.py --cache-root .runtime/cache prepare
python scripts/tab2body.py --cache-root .runtime/cache probe
```

`prepare`는 Isaac Gym native·플러그인·GymTorch 소스를 로컬 캐시에 복사하고
버전·전체 내용 SHA를 확인한다. `probe`는 실제 GPU PhysX·CUDA tensor120step과 종료를 검사한다.
캐시 기본 위치는 `TAB2BODY_CACHE_ROOT`, `$XDG_CACHE_HOME/tab2body`, `~/.cache/tab2body` 순이다.
해당 위치가 공유 파일시스템이면 `--cache-root /로컬디스크/캐시`로 명시한다.
Torch 빌드도 이 로컬 캐시 아래 Python·Torch·vendor 버전별 경로를 사용한다.

실행기는 자식 Python에 `-X utf8`을 적용하므로 `PYTHONUTF8`를 별도로 설정하지 않는다.
native 자산 로딩 후 문자 locale이 `C`가 되어도 한글 JSON을 UTF-8로 읽는다.
현행 GPU 기타의 비충돌 현 6개는 명시적 capsule 시각 메시를 사용한다. Preview4의
비충돌 capsule visual 로딩 오류를 피하며 기존 위치·회전·치수와89개 충돌 형상은 유지한다.
시각 메시 SHA도 자산 manifest와 새 checkpoint의 필수 입력 검증에 포함된다.

## 입력 검사와 짧은 학습·재개·평가

아래 상대 경로는 프로젝트 루트에서 호출하는 예다. 실행기는 호출한 CWD를 유지한다.
다른 CWD에서는 실행기와 출력·checkpoint 경로를 절대 경로로 지정한다.

```bash
python scripts/tab2body.py --cache-root .runtime/cache run -m guitar_learning.tool.validation.portable_inputs

python scripts/tab2body.py --cache-root .runtime/cache run -m guitar_learning.train \
  --size small --num-envs 2 --horizon 2 --updates 1 \
  --out runs/portable_train_01

python scripts/tab2body.py --cache-root .runtime/cache run -m guitar_learning.train \
  --size small --num-envs 2 --horizon 2 --updates 1 \
  --resume runs/portable_train_01/J/final.pt --out runs/portable_resume_01

python scripts/tab2body.py --cache-root .runtime/cache run -m guitar_learning.tool.evaluation.evaluate_finger_skill \
  runs/portable_train_01/J/final.pt --num-envs 2 --scope full_song \
  --out runs/portable_eval_01

python scripts/tab2body.py --cache-root .runtime/cache run -m guitar_learning.tool.demonstration.render_finger_skill \
  --checkpoint runs/portable_train_01/J/final.pt --num-envs 2 --scope full_song \
  --out runs/portable_video_01
```

출력 디렉토리는 매번 새 경로로 지정한다. 짧은 학습의 정상 실행은 음악 성공을 뜻하지 않는다.

## checkpoint를 다른 프로젝트 루트로 이동

이번 수정 이후 저장본은 `finger_skill_resume.v4`와 `guitar_learning.project_paths.v1`을 사용한다.
동일한 변경 후 소스·데이터·자산과 저장된 실행 디렉토리를 새 PC로 복사하고,
새 위치의 `J/final.pt`를 위 `--resume` 또는 평가 인자로 전달한다.

- 필수 입력은 `project://guitar_learning/...` 식별자로 저장하고 현 PC의 프로젝트 루트에서 찾는다.
- 소스·모델·mesh·곡 SHA와 관측·행동·물리·PPO 계약 검증을 유지한다.
- 실행 설정은 원문 바이트와 SHA를 checkpoint 안에도 포함하여 검증한다.
- 부모 checkpoint는 계보 SHA로 기록하지만 새 저장본 실행에 부모의 원래 절대 경로를 요구하지 않는다.
- 보고서의 `portable_checkpoint_ref.path`는 해당 보고서의 현재 디렉토리를 기준으로 해석한다.
- 실행 당시 절대 경로는 감사용으로 보존하며 새 입력을 찾는 위치와 구분한다.
- 모델·Adam·RNG·누적 노출·구간 선택기를 복원하고 물리 장면은 새 에피소드에서 시작한다.

기존 v3의 절대 경로 checkpoint와 이전 누적 제어·정책 계약은 암묵 변환하지 않는다.
명확한 불일치 오류로 거부하며, 필요하면 그 저장본과 동일한 보관 소스·환경에서 재현한다.
같은 portable 형식도 소스나 자산을 바꾸면 SHA 불일치로 거부한다.
CUDA RNG의 GPU 개수 구성 검사도 유지하므로 양쪽 PC의 가시 GPU 구성을 맞춰야 한다.

## SSHFS로 두 PC에서 사용

소스·데이터는 SSHFS에서 공유하고 Python 환경·native 런타임·빌드는 각 PC 로컬에 둔다.
실행기는 활성 Python의 `sys.executable`과 `sys.prefix`에서 실행 파일·라이브러리 경로를 계산한다.
특정 사용자 Conda 경로나 원래 프로젝트 위치를 시스템에 다시 만들 필요가 없다.
각 PC는 서로 다른 출력 디렉토리를 사용하고 학습 중 공유 소스·자산의 변경을 멈춘다.
같은 출력에 두 PC가 동시에 쓰지 않는다. SSHFS는 소스 일관성 snapshot을 제공하지 않는다.
checkpoint는 같은 디렉토리의 임시 파일과 hard link로 공개하므로,
출력 SSHFS가 hard link를 지원하지 않으면 로컬 출력에 저장하고 종료 후 실행 디렉토리를 복사한다.

## 자동 짧은 검증

```bash
python scripts/smoke_portability.py \
  --out '.runtime/relocated project 02/runs/smoke' \
  --cache-root .runtime/cache \
  --relocate-to '.runtime/relocated project 02' --render
```

필요한 구성을 다른 루트로 복사하고 다른 CWD에서 입력·GPU probe·최소 학습·strict resume·
별도 평가를 차례로 실행한다. 선행 단계가 실패한 후의 처리는 skip으로 기록한다.
`--render`는 영상 의존성이 갖춰진 PC에서 지정한다. `report.json`과 단계별 로그를 확인한다.

이식성 도입 당시의 실측과 당시 GPU 제약은 [검증 기록](2026-10-29/portability_v1/README.md)에 있다. 이후 GPU 실행·재개 확인 및 현재 v9 단음 학습의 검증 범위는 [현재 상태](../CURRENT_STATUS.md)를 따른다. 일반 GPU 실행 확인을 다른 PC·SSHFS 이동 검증의 통과로 대신하지 않는다.
