# GPU 재확인·정오 마감 시험 학습

**GPU 정상, 사용자가 수행할 재설치·재부팅은 없다.** 격리 실행에서 GPU 장치가 숨겨졌던 것이 최초 드라이버 통신 실패의 원인이다. GPU 접근 실행에서 RTX4070Ti12GB/580.178.04, PyTorch CUDA 실제 연산, 독립 Isaac GPU PhysX step을 확인했다. [진단](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/GPU_DIAGNOSIS.md:1).

## 실제 실행 상태

2026-10-12 한국시간04:16:45에 장기 실행 PID3721851을 시작했다.04:19경실제PPO1회/256transition을 확인했다. native물리는CPUPhysX,정책·최적화는CUDA다. 상체81/관측820/512→256 Actor·Critic,등록된Fret035000과Strike010000 동결목표를 하나의PD제출자가합친다. 기타자유/스트랩OFF/root·하체고정/self-collision을유지한다.

- [진행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/live_progress.jsonl:1)
- [장기 학습 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/long_run_v3/training.jsonl:1)
- [프로세스 출력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/long_run_v3.log:1)
- 체크포인트: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/long_run_v3/checkpoints/`
- 평가 영상: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/long_run_v3/evaluations/<checkpoint명>/native/episode_0001/media/whole_body.mp4` 및 `hands.mp4`.

첫영상과1회갱신평가를추가확인하고,이후벽시계30분간격으로완료rollout뒤저장·평가한다. 평가동안학습은대기한다. 매평가준비2초부터곡전체16.3667초를기록하며 MP4는492frame/16.4초다.11:40이후새제어진입을차단해마지막영상시간을확보한다. 스케줄과중단의정확한범위는[실행계획](/home/ajou/yigyu/3/stability_adapter_2/DEADLINE_EXECUTION_V3.md:13)에명시했다. OS/native호출내부의강제순간중단이나정오성공을인증한것은아니다.

## 마친 연결 검증

v2에서 GPU PPO실제1회/256transition과 학습전·후각16.3667초전체평가를완료했다.각42event성공0/accepted0이며−397.140450→−397.744697은품질개선근거가아니다.시험보상은정식v4/v5인증이아니며,현재연주·안정화성공을선언하지않는다.

[실제Isaac이미지·4영상·비교그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/artifacts_smoke_v2/README.md:19) · [검증기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/smoke_verification_v1.json:1) · [독립검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/review_v1.md:1) · [변경파일·실제줄](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/CHANGED_FILES.md:1).

v1 Python3.8오류와회전v1/v2실패는원본과로그를보존했다. 장기v3는새소스ABI에맞춰새정책으로시작하며v2checkpoint를계약무시로복사하지않았다. main4원문prefix와실행입력SHA를검증했고,실행동안main4와A소스를추가편집하지않는다. 실행결과가계속생성되므로이번phase전체의최종봉인은아직하지않았다.
