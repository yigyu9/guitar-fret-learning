# UTF-8 자동 적용과 기타 현 시각 로딩 수정 — 2026-10-29

공식 `scripts/tab2body.py` 실행기는 자식 Python을 `-X utf8`로 시작한다.
외부 `PYTHONUTF8` 설정 없이 native 자산 로딩 이후에도 한글 JSON을 읽는다.

## visual geom 오류 원인과 변경

실제 native 최소 사례에서 `contype=conaffinity=0`인 capsule은
`Could not load visual geom`을 출력했다. 충돌 capsule과 비충돌 box는 정상 로딩됐다.
원래 GPU compound 기타의 비충돌 capsule 현6개가 여기에 해당했다.
이를 동일 반지름·중앙 원통 길이·위치·회전·색의 명시적 OBJ 시각 메시로 교체했다.
16각 원주와 반구당4개 링으로 원 capsule 표면을 표본화한다.

geom101개·충돌89개와 물리 manifest의 질량/COM/관성·준비 상태·원본 SHA는 동일하다.
원본 연구 자산·역사 기록은 변경하지 않았다. 시각 메시의 SHA를 manifest에서
검증하고, 새 checkpoint의 project:// 필수 입력에도 포함한다.
소스/자산 SHA가 달라진 이전 checkpoint는 기존 strict 규칙대로 현재 코드에서 거부한다.

## 검증

현재 PC `yigyu`, 로컬 `rl38`, RTX4070 Ti SUPER에서 검증한다.
소스·데이터는 SSHFS, native·Torch 빌드·학습 출력은 로컬 ext4를 사용한다.
모든 GPU 종단 명령은 `env -u PYTHONUTF8`로 실행한다.
관련 CPU31개 검사와 다른 루트·checkpoint 변조 거부 검사가 통과했다.
실제 결과는 [verification.json](verification.json)에 기록했다.

| 항목 | 결과 |
| --- | --- |
| 입력 감사 |213개·외부/누락0, native provenance193개 SHA 통과 |
| 신규 GPU 학습 | medium·8환경·H32·8업데이트·2048전이, 초기/중간/최종 저장 |
| strict resume | 추가2업데이트·512전이, 누적10업데이트·2560전이 |
| 복원 | 모델·두Adam·Python/NumPy/Torch/CUDA RNG·노출 일정 정확 일치 |
| 저장본 |5개 SHA/크기 검산, 새시각메시6개를442필수 project:// 입력에 포함 |
| GPU 물리 | 기타1강체·89충돌, native68/logical106몸체,145 aggregate shape 유지·속성 readback 통과 |
| visual geom 오류 | 학습·재개·완료한 구간 렌더 모두0건 |
| 구간 영상 | 손/전신 각1280×720·30fps·109프레임·3.633초, 두 encoder 종료0 |
| 영상 검사 | 전프레임 디코딩·육안 확인,219개 native pose 유한, 정책/입력 불변·장면 정상 정리 |

[손 영상](hand.mp4) · [전신 영상](fullbody.mp4) · [손 프레임](hand_frame.png) ·
[렌더 보고서](render_report.json) · [원인 재현](diagnose_visual.log) ·
[물리 불변 비교](physics_invariance.json) · [CPU 검사](cpu_tests.log)

전체곡 렌더의 첫 시도는 외부300초 제한으로 중단됐다(부분영상750프레임/25초).
이 시도는 완료로 주장하지 않으며 [로그](render_full_song_timeout.log)를 보존했다.
완료 검증 영상은 `--scope phrases --num-envs 1`의 첫 구간 에피소드 전체다.
선택2음의 달성은0/2이며 안전하게 구간이 끝났다. 실행·인코딩 통과와 연주 성공은 구분한다.
ffmpeg의 Conda ncurses/tinfo 버전 경고는 남지만 두 encoder 종료0·전체 디코딩을 확인했다.

## 재현 명령

`rl38` 환경에서 프로젝트 루트로 이동하고, 매 출력은 새 디렉토리를 사용한다.
외부 `PYTHONUTF8`를 지워도 아래 공식 실행기만으로 동작한다.

```bash
conda activate rl38
unset PYTHONUTF8
python scripts/tab2body.py run -m guitar_learning.train \
  --size medium --num-envs 8 --horizon 32 --updates 8 \
  --checkpoint-every 4 --seed 7 --out runs/utf8_visual_train_NEW
python scripts/tab2body.py run -m guitar_learning.train \
  --size medium --num-envs 8 --horizon 32 --updates 2 \
  --checkpoint-every 4 --seed 7 \
  --resume runs/utf8_visual_train_NEW/J/final.pt --out runs/utf8_visual_resume_NEW
python scripts/tab2body.py run -m guitar_learning.tool.demonstration.render_finger_skill \
  --checkpoint runs/utf8_visual_resume_NEW/J/final.pt --scope phrases --num-envs 1 \
  --out runs/utf8_visual_video_NEW
```

실측에서는 출력을 현재PC 로컬 `/home/yigyu/local-runs/utf8_visual_fix_20261029_JU0cWB/`에 저장했다.
SSHFS 출력의 hard-link 제약은 기존 [이식성 안내](../../PORTABILITY.md)를 따른다.

원문은 `guitar_learning/archive/20261029_before_utf8_visual_load_v1/manifest.json`에 보존한다.
짧은 구동 검증은 연주 숙련이나 장기 수렴을 입증하지 않는다.
