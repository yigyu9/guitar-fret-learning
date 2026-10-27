**중단: 원본은308회부근SIGFPE로끝났고원래후속workflow도중단됐다. 실제재개와작업상태는../guitar_learning_surface_training_recovery_v1을따른다. 원본세션을재실행하지않는다.**

# 실행 상태와 재진입 메모

사용자 요청: 새 학습을 진행하고 결과/로그를 분석하며 마지막 또는 최고 checkpoint의 전신 영상을 남긴다. 현재 선택은 최종 checkpoint다.

- 본 학습: fresh left/large1024/H32/seed7,2000 updates,checkpoint50. `train1024_large_2000/`와 같은 이름의 `.log`. 실제 host PID854545/starttime65077459. Root tool session14411.
- 현재427개 활성Python은 이전 surface_fretting_v1과 SHA가 같고 source_training/에 동결했다. 본학습/후속GPU평가가 끝날 때까지 활성 코드와 자산을 변경하지 않는다.
- 후속 workflow는 **이미 실행 중**이다. Root tool session92788. `finish_workflow.py`가 main PID의 종료를 기다린 뒤 report/song_report.completed와 closed를 확인하고 순서대로 실행한다: `verify_training.py`→`analyze_training.py`→`evaluate_checkpoints.py`→`render_video.py`. 중복 실행하지 않는다. 상태는 `workflow_status.json`, 각 단계 로그는 `<scriptstem>.log`다.
- workflow_inputs.json에 후속4스크립트/자신/소스manifest SHA를 묶었다. worker 두 명의 최종도구·CPU회귀·독립검수와 workflow race 보완 검수를 통과했다. 현재 활성 학습 코드 수정은 없다.
- 실제GPU평가는 initial/final1024환경의 첫 종료만 채점한다. 자체3331단계는 restore후고정,학습/승급없다. final의사전env0..7 실제60Hz endpoint·t0를캡처한다. 영상은그중안전완주최저ID(없으면최장첫episode/동률최저ID)이며최고음악점수선택이아니다.
- 영상은GPU실측worldpose를MuJoCo OSMesa로정적재생한다(새물리/정책없음). final_video/final_fullbody_60fps.mp4,preview_*.png,pose_audit.json,report.json과SHA를남긴다.

남은 작업:

1. 학습 중 progress.py와periodicprefix분석으로 진행/자원을 확인한다. 최초 prefix100, 이후250/500/1000/1500/최종을 권장한다. `analyze_training.py --prefix N`은 `analysis_prefix_000NNN` 새경로를생성하므로 중복호출하지 않는다.
2. main report 정상종료 및 workflow 단계 성공을 실제 확인한다. native crash/입력 SHA변경/자원하한 실패는 완료로 보고하지 않는다. 실패자료는보존하고원인을탐색한다.
3. analysis_final/analysis.json과checkpoint_evaluation.json,first_episodes.jsonl의초기/최종을독립교차분석한다. 학습 중 정책 수집과 고정평가·음향성공을섞지 않는다.
4. final_video 미디어를ffprobe/poseaudit/preview 전신구도로직접확인하고 영상embed를최종응답에넣는다. PNG뷰는functions.view_image로읽을수있다.
5. change-reviewer 최종증거검수,README/계획완료/결과SHA manifest를남긴다. 현재phase는실행중이며아직봉인하지않았다. 과거봉인phase는절대수정하지않는다.

Root가수행한현행소스의기존검증: 이전turn전체CPU823/실제GPU64+resume1/3331 replay 통과. 새2000회완료/성능향상은아직주장하지않는다. 디스크시작여유36GiB,RTX4070Ti12GiB,소요예상약6시간이다.
