# Minimal finger-base pose diagnostics proposal

제어 효과가 입증되지 않으면 최소 개선은 **GPU left 종료 episode의 기존 finger-motion 로그에 실제 기저 회전을 보강**하는 것이다. 새 helper 모듈 없이 `guitar_learning/gpu/environment.py`의 기존 `_record_finger_motion()`/`_finger_motion_episode()`를 확장한다. 정책 입력512/event24·행동39·기존 q/action 통계·보상·48POSITION/57EFFORT·gain/힘 한계·PPO/H32·준비자세·body 수·공통 asset은 바꾸지 않는다. 이는 설계 문서이며 active435나 기존 봉인 자료를 수정하지 않았다.

## 가장 작은 코드 경로

- GPU left init에서 body 이름 `human/LH:palm`, `human/LH:{index,middle,ring,pinky}1` 및 각 native `{finger}1_x/{finger}1_z`를 metadata 이름으로 찾고 존재·유일성을 검사한다. 손가락 순서는 index/middle/ring/pinky다. 이름/indices는 새 진단 계약에 명시한다. 임의 body 번호를 하드코딩하지 않는다.
- 현재 pinned source XML은 이 네 base가 palm의 직계 자식이고 body 회전 offset이 없으며 hinge axes는 x/z다(`assets/tab2body/assets/smpl_mpl_hands_body.xml`의 해당 body). source435와 asset pin을 그대로 사용한다. 다른 rig에 일반화하거나 MJCF importer를 새로 만들지 않는다. source identity frame 가정은 계약에 명시하고 source/body 매핑을 CPU 검사한다.
- 매 completed60Hz endpoint에서 `Ractual=inverse(Rpalm)*Rfinger1`을 실제 `body_state` quaternion으로 계산한다. `actual_y=Log(Ractual).y`를 얻는다. `Rcommand=Exp([target_x,0,target_z])`와 `error_local=Log(inverse(Ractual)*Rcommand)`를 만든다. 그 x/z norm과 full3D norm도 계산한다. 기존 geometry의 quaternion 함수들을 사용하고, Exp의 짧은 sinc 식만 이 경로에서 계산한다. control→geometry import나 기존 제어 함수 이동은 하지 않는다.
- **zero-y command는 진단 참조모형이다.** SDK의 내부 target/locked-frame 동작을 완전히 읽은 것이라고 주장하지 않는다. 실제 body 상대회전의 y도 물리 drift 전부를 직접 인증하는 값이 아니다. 초기 준비 pose로 rest offset을 매 reset 재추정하면 초기 미보고 성분을 숨길 수 있으므로 그렇게 하지 않는다. 현재 source body-rest가 identity인 점을 사용하고 초기 수십 µrad 성분도 남긴다. `inertial.quat`는 COM 주관성축이므로 body-rest에 사용하지 않는다.

## 통계·분모·출력

기존 `finger_motion` dict에 float64 `[N,4]` accumulator6개(sum-square3개, max3개)만 추가한다. 기존 reset의 value별 selected-row0 루프가 이 shape도 처리한다. 기존21축 range/action/error fields와 그 계산은 보존한다.

`FINGER_MOTION_CONTRACT`를 `guitar_learning.gpu_left_finger_motion.v2`로 올리고, 종료 episode의 `left_finger_motion.base_rotation`에 다음을 출력한다.

```
finger_names: [index, middle, ring, pinky]
sampling_hz: 60
endpoint_samples: steps
actual_rotvec_y_rms_rad: [4 floats]
actual_rotvec_y_max_abs_rad: [4 floats]
command_so3_xz_rms_rad: [4 floats]
command_so3_xz_max_rad: [4 floats]
command_so3_full_rms_rad: [4 floats]
command_so3_full_max_rad: [4 floats]
```

`command_so3_xz`의 샘플은 `sqrt(ex²+ez²)`이고 RMS는 `sqrt(sum(ex²+ez²)/steps)`다. 두 축의 평균으로 나누지 않는다. full은 세 성분을 같은 방식으로 사용한다. actual_y RMS는 `sqrt(sum(y²)/steps)`, max는 `max(abs(y))`다. denominator0은1로 보호해0을 반환한다. source frame/정의/scope는 부모 finger-motion 계약 안에 넣고 같은 정의를 중복 복사하는 구조를 늘리지 않는다.

reset t0은 통계에서 제외한다. 물리 terminal tick을 포함해 completed60Hz endpoint당 한 번만 계산한다. 기존 `steps` 증가 직전 `_record_finger_motion()` 호출을 그대로 사용하므로 episode `endpoint_samples=steps`와 맞는다. 240Hz extrema·한 곡 완료·압현 성공을 뜻하지 않는다. partial reset은 지정 행의 새 통계만0으로 만들고 다른 행 통계와 고정 mapping을 보존한다. 원자료 시계열을 늘려 저장하지 않는다.

해석은 명확히 제한한다: q-target scalar RMS와 다른 pose 진단이며, full3D오차와 구동축투영 norm은 다르다. actual_y가 새 action축이라는 뜻이 아니고, 접촉 pair·압력·정확한 내부 SDK drive torque·원인/학습효과를 인증하지 않는다. x/z norm이 작아도 full residual은 클 수 있으며, 모든 진단이 작아도 올바른 음의 압현을 의미하지 않는다.

## CPU 검사와 호환성

새 `guitar_learning/tests/test_gpu_finger_pose.py` 또는 기존 GPU환경 검사에 작은 fixture를 추가한다. 별도 범용 기하 helper가 없으므로 테스트용 abstraction도 늘리지 않는다.

1. q/target는 고정하고 actual base quaternion만 바꿔 기존 q오차0과 새 y/full오차 양수가 동시에 나오는지 검사한다. 두 개 endpoint의 sum-square/max와 분모를 직접 재계산한다.
2. actual=zero-y command이면 오차0이며, quaternion q↔−q와 0각에서 finite하다. palm/body를 동일 world회전으로 바꿔도 상대 진단은 같다.
3. 알려진 full residual이 있지만 local x/z투영은0인 fixture로 두 지표 구분을 검사한다. 값은 독립 scalar SciPy oracle 또는 명시 quaternion fixture와 대조한다.
4. selected reset이 다른 행의 N×4통계에 영향을 주지 않고, right에는 이 진단이 생기지 않는지 확인한다. 이름/4sourcebase/palm/axis 가정도 현재 XML과 대조한다.
5. 변경 전 fixture와 같은 action/snapshot을 주어 observation/event/reward/cost/termination/기존 motion 값이 동일한지 비교한다. H32는 그대로이며 수집 endpoint 수만 검사한다. 240Hz를 측정한다고 주장하지 않는다.

계약의 diagnostics schema가 바뀌므로 **현 strict checkpoint identity는 old v1의 직접 resume를 거부**한다. 차원/물리/보상이 동일하다는 이유로 호환을 주장하거나 source SHA 차이만의 거부로 설명하지 않는다. loader 예외/마이그레이션은 이번 최소 개선에 넣지 않는다. CPU/right와 공통 원본 asset은 별도 SHA/계약 대조로 보존한다.

CPU/기존 환경 회귀·독립 검수 뒤 root의 짧은 실제 수집에서 raw body quaternion 재계산, endpoint 수, selected reset, close/pins를 확인하면 진단 보강의 완료 기준을 충족한다. 추종/곡 학습 성능의 개선 검증으로 확대하지 않는다. solver 비교 전에는 활성 코드 편집을 시작하지 않는다.
