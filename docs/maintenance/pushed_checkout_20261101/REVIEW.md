# push 파일 단독 실행 검증기 독립 검수

요약 판정: **검증 결과 문제없음**. 초기 Warning 2개의 수정 후 재검수했다. 원격 체크아웃이나 GPU 작업을 실행·수정하지 않고 검증기와 12개 mock 테스트, 원격 체크아웃의 smoke·입력 감사 코드를 읽었다. 12개 테스트는 통과했다. 최종 CPU 증거와 LFS 실체도 아래 범위에서 독립 대조했다. **실제 GPU 학습·저장·strict재개·평가가 완료되었음을 후속 대조했다.**

## 최종 CPU 증거 대조

- `CPU_AUDIT.json`이 지정한 증거 3개의 SHA 및 checkout 봉인 파일 3,488개의 크기·SHA를 `cpu_gate`로 직접 재검증했다. `tracked_identity`도 통과했다. index tree 전후 및 원격 tree가 동일하다는 `GIT_IDENTITY.json` 기록과 일치한다.
- 원격 LFS 목록과 검증 목록 121개의 경로·OID·크기가 일치하며, 별도 checkout의 각 파일을 직접 읽어 SHA-256·크기를 전부 다시 확인했다. 합계 407,829,993바이트다. 원격 다운로드 경위와 원본 캐시 미사용은 생성된 기록을 검토했으며, 다운로드를 독립적으로 다시 수행하지 않았다.
- `INPUT_AUDIT.json`은 입력 214개·67음·준비 상태 105축·11,389,398바이트이며 외부·누락 입력이 없다. `CPU_FILE_ACCESS.json`은 성공 접근 1,328회·파일 666개, 기존 프로젝트·미등록 외부·미해석 성공 접근 모두 0이다.
- 현재 6→8 fresh 학습에 필요한 미push 파일 11개의 `origin/main` 부재를 원격 checkout의 Git 객체에서 직접 확인했다. 기본 학습 가능성과 현재 실험 재현 가능성을 구분한 `REPORT.md`의 결론은 이 증거에 부합한다.
- 초기 CPU 검수 당시 GPU 검증은 대기 상태였으며, 이후 아래 실제 GPU 실행까지 완료되었다.

## Critical

현재 확인된 항목 없음.

## Warning

프로젝트 입력의 외부 의존은 발견하지 않았다. 감사 도구에는 다음 해석 제한이 있다.

- `trace_access`가 역사적 `/proc/self` 경로를 현재 감사 프로세스의 `Path.resolve()`로 해석한다. 따라서 다른 Python으로 재분석하면 `/proc/self/exe`가 그 Python을 가리켜 미등록 외부 파일로 오분류될 수 있다. 이는 실제 GPU 실행의 외부 프로젝트 데이터 의존을 발견한 것이 아니다. 원본 보고·실행 script SHA를 보존하고, 향후 도구에서는 커널 가상 경로를 당시 trace 문자열에 근거해 분류하는 것이 적절하다.

초기 지적은 다음과 같이 해결되었다.

- 외부 성공 파일 접근 전체를 수집하고 fresh checkout·설치 환경·기존 프로젝트·알 수 없는 외부 파일로 분류한다. 알 수 없는 `/tmp`·다른 사용자 홈의 파일 접근도 실패 처리하며 이를 확인하는 회귀 테스트가 추가됐다. XDG·임시파일·CUDA 캐시도 fresh checkout 안에 생성한다.
- `cleanup_group`은 직접 자식의 종료 여부와 관계없이 자신의 프로세스 그룹에 최종 SIGKILL을 보낸다. 이미 종료한 직접 자식과 사라진 그룹에 대한 mock 테스트가 추가됐다. 다른 연구의 프로세스 그룹은 대상으로 삼지 않는다.

## 확인된 보호 장치

- CPU 감사의 완료·성공, 원격 SHA, checkout 경로, 파일 크기·SHA, 증거 파일 SHA를 요구한다.
- 현재 연구가 종료 상태이며 GPU compute PID가 없을 때만 실행하고, 실행 직전 다시 검사한다.
- 새 checkout 내부 캐시를 명시하며 PYTHONPATH/PYTHONHOME을 제거한다. 로컬 실행기는 Torch 확장 캐시도 checkout 안에 만든다.
- GPU subprocess가 성공해야 하고, train/resume/evaluation이 실제 실행·통과해야 최종 성공으로 표시한다. 미실행이나 단순 CPU 감사 통과는 GPU 성공으로 간주하지 않는다.
- 원격 checkout의 Git SHA·tracked 변경 여부와 입력 실체를 실행 전후 다시 확인한다.
- 기본 곡 학습과 아직 push되지 않은 6→8 연구의 구분은 DEPENDENCY_REVIEW.md에 명시되어 있다.

CPU mock 검증 명령: `python -m unittest discover -s docs/maintenance/pushed_checkout_20261101 -p 'test_verify_gpu_when_idle.py' -v`.

## 실제 GPU 실행 최종 대조

기존 연구가 종료된 뒤 감시기가 원격 checkout에서 실제 실행을 시작했다. train·resume·evaluation 모두 완료되었다. 최종 보고는 `status=completed`, `actual_gpu_verification=true`, subprocess returncode 0이다.

- 두 학습 보고서 모두 `device=cuda:0`, `physx_use_gpu=true`, `use_gpu_pipeline=true` 및 관측·접촉·Jacobian 등의 CUDA tensor를 기록했다. 각 실행에서 실제 physics 8 step, 경험 4개가 기록됐다.
- train의 optimizer update 1에서 resume의 2로 이어졌다. 각 실행의 initial/final 체크포인트 총 4개의 실제 크기·SHA가 manifest와 일치했다.
- 저장본을 CPU로 읽어 model·Adam optimizer·RNG·identity·`finger_skill_resume.v4` 메타데이터 존재를 확인했다. resume의 입력 계약 lineage에 기록된 원본 final.pt SHA는 실제 train final.pt SHA `f18974ded5b8d0035062ac15b87e0b6da08ee213fe70cabbde2ff1d5579f2901`과 일치한다.
- 원격 코드의 `restore_checkpoint`는 schema·설정·입력 pin 검증을 거쳐 복원한다. 두 실제 보고서의 lifecycle은 true이며 changed_inputs·missing_import_pins·cleanup_errors는 전부 빈 목록이다.
- 평가는 실제 2개 episode·3,940개 simulated transitions를 완료했고 checkpoint SHA는 위 train final SHA와 일치한다. 평가 lifecycle도 true이며 changed_inputs·missing_import_pins·cleanup_errors는 전부 빈 목록이다.
- GPU 파일 접근은 성공 32,879회·파일 8,520개이며 기존 프로젝트·미등록 외부·미해석 성공 접근은 0이다. 실행에 사용된 rl38 Python으로 trace를 독립 재분석해 같은 통과·카운트·분류 결과를 얻었다. `/proc/self`의 현재 PID 해석 문자열만 달라 원본 JSON과 바이트 단위 일치는 주장하지 않는다. 다른 Python에서는 위 Warning의 오분류가 재현되었다.
- 실행 후 CPU 증거·checkout 전체 봉인·Git tracked identity를 다시 검증했고 통과했다. 감시기 script SHA도 실행 당시 보고와 일치한다.
- 이 짧은 실행은 기본 구성의 GPU 학습·저장·재개·평가 실행 가능성 확인이다. 압현 성능이나 장기 학습 수렴 성공, 현재 미push 6→8 실험의 재현 성공을 뜻하지 않는다.
