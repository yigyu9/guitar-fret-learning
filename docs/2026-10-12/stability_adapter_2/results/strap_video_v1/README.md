# 실제 스트랩 경로를 함께 표시한 Isaac Gym 영상

사용자 요청에 따라 앞으로 만드는 결과영상에 수동 스트랩의 실제 경로를 표시한다. 매프레임 기타 버튼과 몸통/어깨guide의 실제world13지점/12구간을 조회해 native camera 위에 주황선으로 투영한다. Native depth 기준으로 보이는 구간은 굵은 실선, 몸·기타에 가려진 구간은 옅은 점선이다. 절대rest length도 화면에 표시한다. 새 물리 actor/충돌shape/힘/천 처짐을 추가한 것이 아니며 경로를 보는 시각화다.

## 실제 0~5초 결과

직전 근접진단 original_targets와 같은 초기81각/목표/기타p·q/LA/PD/solver로 새1회1200step을 실행했다. 각카메라151frame,30fps,5.033333초 영상이다. states/trace/tasks/contacts/controls의 원자료5배열과 raw native PNG302개가 직전실행과exact 같다. 이는 관측된 재현성이지 성공을 강제하는 통과gate가 아니다. 기타최대이동25.779645mm/최대회전7.800837°, 종료22.034643mm/7.092339°로물리결과는동일하다. 기타안정화·세면grip의성공은아니다.

![스트랩포함 실제Gym 손근접5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/native/hands.mp4)

![스트랩포함 실제Gym 전신5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/native/whole_body.mp4)

## 초기와 종료 이미지 설명

![초기손근접스트랩표시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/native/frames/hands/00000.png)

기타에서 어깨/몸통으로 이어지는 주황선은 실제 경로다. 기타·팔·가슴에가려진 부분도 위치를 확인할수있도록 옅은 점선으로 보여준다. 점선이 몸표면 위에 보인다고 물리접촉/관통을 인증하는 것은 아니다. LA1.1018469719600776m는 절대rest length이며 현재경로길이나 천의처짐길이와구분한다.

![5초손근접스트랩표시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/native/frames/hands/00150.png)

기타와상체가움직여실제route가바뀌면같은프레임에서주황경로가갱신된다. 저장trace의13route지점과151프레임모두exact일치했다. 선두께는화면식별용픽셀폭이며 실제strap너비가아니다.

![초기전신스트랩표시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/native/frames/whole_body/00000.png)

전신카메라에서도동일route를같은카메라행렬로투영했다. 모든route지점이두카메라화면안/전방에있었고151프레임모두보이는/가려진구간을표시했다. 가림허용오차는depth축2mm이다. Depth분기는합성장면에서검사했고실제PNG는직접열어원본카메라/route와대조했다.

## 기록과 재사용

- [실제초기값/관절각·목표·LA·physics](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/native/initial_values.json:1)
- [물리/영상15검사·원자료exact관측](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/verification.json:1)
- [각프레임route/camera행렬/raw·표시SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/native/capture.json:1)
- [보존raw camera 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/native/raw/capture.json:1)
- [원실행·시간·입력SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/execution.json:1)

원nativePNG는native/raw/frames, 표시PNG는native/frames에분리보존했다. 기존frozen helper/camera/runner/영상은수정하지않았고새녹화 helper/entry를작성했다. 이번 actual 검증은 run_strap_recorded_diagnostic으로수행했다. 일반상수trial용 run_strap_recorded_trial은기존1200step loop AST동일/문법을검사했고이번단위에서그entry의별도physics실행은0이다.

앞으로새상수trial은 `python -m stability_adapter_2.run_strap_recorded_trial --trial <입력절대경로> --out <새출력절대경로>`로기록한다. 근접/FK진단은 `python -m stability_adapter_2.run_strap_recorded_diagnostic --trial <입력> --proposal <봉인proposal> --out <새출력>`이다. 새feedback runner도 StrapTrialRecording을사용하며 과거frozen entry는재현용으로보존한다.

Luna/독립검수는agent thread limit오류로실행되지못했고root가문서와실제PNG QA/원자료검증을수행했다. 독립최종승인을완료한것으로표현하지않는다. PhysX CPU 및기존SDK경고는native.log에보존했다. 다음물리실험은손바닥옆면우선초기배치계획을계속따르며영상에는이스트랩표시를기본사용한다.
