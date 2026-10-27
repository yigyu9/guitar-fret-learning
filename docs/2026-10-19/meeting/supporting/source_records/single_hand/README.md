# 최신 손별 정책 결과 영상

최신 BC 정책의 실제 검증 기록을 재생한 정면 영상이다. 새 학습이나 물리 시뮬레이션은 실행하지 않았다. 기존2시간 PPO의 영상이나 교사 보조 제어의 영상이 아니다.

- [정면 상체 확대 합본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_local_skills_v1/front_video_v2/front_upper_body_60fps.mp4)
- [정면 전신 합본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_local_skills_v1/front_video_v2/front_combined_60fps.mp4)
- [왼손 단독7초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_local_skills_v1/front_video_v2/front_left_60fps.mp4)
- [오른손 단독7초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_local_skills_v1/front_video_v2/front_right_60fps.mp4)

합본은 왼손7초 → 별도 시험 전환 카드1초 → 오른손7초다. 양손을 동시에 연주한 결과가 아니며 무음이다. 초록색이 왼손, 자홍색이 오른손이다. 왼손의 해제는 목표 현의 압현 접촉 해제이며 왼손 전체를 넥에서 완전히 떼는 시험과 다르다.

## 어떤 결과인가

기존2시간 PPO는 손별384episode 중 전체 품질 성공0이었다. 이후 성공한 국소 동작을 모방학습한 새 Actor는 같은 단음의 손별 결정적 평가에서 각각4/4 품질·안전을 통과했다. 두 실험은 평가 방식과 분모가 다르므로 직접적인 학습 성공률 비교로 해석하지 않는다. 새 Actor를 초기값으로 하는 추가 PPO는 아직 실행하지 않았다.

영상은 사전에 정한 평가 episode0만 재생한다. 왼손은 음 구간 clean 접촉 비율1.0과 이후 압현 해제를, 오른손은 인정 타현1회·추가/오방향 타현0·최종 분리를 확인한 기록이다. 손별 품질의 오방향 타현 지표와 합주 MusicLedger의 wrong_crossings는 서로 다른 값이다.

성공 기준은 현재 stage1±0.5초다. 오른손 영상의 첫 시험 타현 오차는+50.178669ms였으며, 나머지 세 시험은 각각+108.706248ms였다. 인정 타현 시각만의100ms 이내는1/4이고, 양손 합주 MusicLedger matched50/matched100은 손별 시험 모두0이다. 왼손의 grace 이후 해제 지연 적분량도0.179050초로0이 아니다. 전곡·정밀 타이밍·양손 합주·실제 압력이나 음향 성공으로 확대하지 않는다.

[학습 및 검증 상세](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_local_skills_v1/README.md)

## 영상 검증

원본240Hz 기록 중 각60Hz 제어 tick의 마지막 실제 몸체 world pose를 사용했다. 각 손은 첫 끝점(정책1/60초·물리step4)부터 마지막(7초·step1680)까지420프레임이다. 임의 보간이나 관절 FK로 동작을 다시 만들지 않았다. 원본 source visual mesh를 표시하며 MuJoCo는 자세 표시만 수행한다.

- 손별 영상420프레임·7초, 합본900프레임·15초, 모두1280×720·60fps.
- 모든840개 동작 프레임의 몸체 위치 readback 최대오차0m, 회전 최대오차 약6.67e-16rad. 새 물리step0.
- 모델·형상·평가 기록·렌더러·폰트 등126개 입력SHA 불변.
- [프레임·입력·미디어 보고서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_local_skills_v1/front_video_v2/report.json)
- [독립 검수: 문제없음](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_local_skills_v1/front_video_v2/review_v1.md)
- [렌더링 코드](/home/ajou/yigyu/3/guitar_learning/local_skills/render.py)

첫 시도의 상체 카메라가 후면을 향해 정면270도로 교정했다. 첫 소스는 guitar_learning/archive/20261019_before_local_video_front_camera_fix에, 첫 출력과 로그는 상위archive/front_video_back_camera_v1에 보존했다. 기존 학습 코드·모델·평가 자료는 수정하지 않았다.
