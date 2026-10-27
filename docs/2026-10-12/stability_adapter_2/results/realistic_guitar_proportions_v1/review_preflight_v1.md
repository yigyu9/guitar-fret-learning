# 현실적 기타 비율 자산 사전 독립 검수

요약 판정: **수정 권장 — 새 runner의 물성 계약 검증·차단 보완 필요.** 자산 source 치수·좌표 보존은 확인했으나 아래 사항을 해결하기 전 물성 계약을 강제·검증했다고 인증할 수 없습니다. 신규 native 결과와 음악 성능은 검토하지 않았습니다.

## Critical

- [run_realistic_guitar_trial_v1.py:63](/home/ajou/yigyu/3/stability_adapter_2/run_realistic_guitar_trial_v1.py:63): scene 생성 뒤 PropertyGym을 제거하며 기존 [InitializationGuard:10](/home/ajou/yigyu/3/stability_adapter_2/environment_guard_v2.py:10)은 rigid-body property setter를 차단하지 않습니다. 따라서 `set_actor_rigid_body_properties`는 초기화 완료 뒤에도 native에 전달될 수 있고, 55행의 `runtime_setter_calls=0`은 관측 카운터가 아닌 상수입니다. frozen 기존 guard를 수정하지 말고 새 runner의 전용 property guard를 유지하여 허가된 construction 시점·대상 외 setter를 거절하고 실제 호출을 기록해야 합니다.

## Warning

- [run_realistic_guitar_trial_v1.py:52](/home/ajou/yigyu/3/stability_adapter_2/run_realistic_guitar_trial_v1.py:52): setter 후 질량만 요청값과 비교하고 COM·관성은 finite/SPD 검사만 합니다. 질량은 맞아도 COM/관성이 요청과 다르면 현재 검사는 통과할 수 있습니다. importer COM 보존·질량비에 따른 관성 전체 행렬을 readback과 비교하고 `route_com`, LearningScene의 `com`, `guitar_mass` 캐시도 적용된 값과 대조하는 것을 권장합니다. setter→parent route cache→LearningScene COM cache의 생성 순서는 적절합니다.
- [run_realistic_guitar_trial_v1.py:67](/home/ajou/yigyu/3/stability_adapter_2/run_realistic_guitar_trial_v1.py:67): 추가 collision camera의 handle 실패 검사가 없습니다. 기존 camera 구현처럼 음수 handle을 즉시 거절하면 뒤의 이미지 query 실패를 명확히 기록할 수 있습니다. 성공한 camera/render 자체를 물리 형상 인증으로 해석하지 않아야 합니다.

## 확인 사항

- [Yamaha FS800 공식 사양](https://shop.sg.yamaha.com/fs800.html)의 바디497×380mm·깊이90–110mm·스케일634mm·전체1021mm를 대조했습니다. 기존 현 marker 평균 길이와 대응시킨 scale0.981682는 근사이며 실제 nut–saddle 길이와 같은 정의가 아닙니다. 새 바디 길이0.487896m·폭0.373039m·깊이0.088351–0.107985m·전체1.002298m와 휴머노이드 중립 source 높이1.7205m의 범위를 문서가 구분합니다.
- manifest8검사의 입력/자산 SHA를 대조했고 실제3OBJ를 CPU에서 읽어 convex·closed 형상을 확인했습니다. 두 bout mesh가 별개이며 headstock 끝은기존 neck tip보다 연장됩니다. XML body 이름/순서/frame 및 비바디 음악 geom은 직접 대조해 보존됐습니다. 기존 넥·현 mesh 좌표를 유지한 연구용 윤곽 근사이지 제품 정밀 복제나 중공 목재 질량 분포 인증이 아닙니다.
- [Scene:60](/home/ajou/yigyu/3/stability_adapter_2/run_realistic_guitar_trial_v1.py:60)은 새 자산과 버튼만 별도로 적용하고 원본 strap 길이·법칙은 유지합니다. 버튼·COM·초기 팔/기타 배치가 바뀌므로 old/new 결과를 형상만의 인과효과로 해석할 수 없습니다. 새 source audit은 실제 지정 자산 경로를 읽습니다.
- PropertyGym의 setter는 guitar create_actor 직후, prepare/초기화 전에 실행됩니다. 기존 GraphicsGym/InitializationGuard/StrapForceGuard 계층으로 돌아가는 경로와 neutral_action의 고정 q_ref 제출·5초/1200물리 step·151프레임 경로를 확인했습니다. 입력 SHA 검사는 scene 생성 전에 수행합니다.

## 검수 SHA·범위

[source_before_native_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/source_before_native_v1.json:1)의5파일 현재 SHA는 모두 일치했습니다. 검토 runner SHA256은 `e3325812aa9bd73c8bbf3e9071874ab88c789054b646c4e70897e1030834a2a9`, builder SHA256은 `abca87cbd512eaaf40437ee0fd7f2781d23bbc6a196a1feaf5074e4b96d0994e`, 자산 MJCF SHA256은 `fb9a5a35715059a8fb8638e491289751eeecda97744b5331d791fb5c47fb64bc`입니다. 이후 정정 runner는 이 수정 전 기록의 인증 대상이 아닙니다.

검수자는 이 새 리뷰만 작성했습니다. source 형상 확인용 읽기 전용 CPU 검사를 했으며 추가 native·물리·추론·학습과 기존 파일 수정은 하지 않았습니다.
