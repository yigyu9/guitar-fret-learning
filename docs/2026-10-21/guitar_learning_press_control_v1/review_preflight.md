# 실제 압현면·추종 보상 사전 검수

요약 판정: **문제없음**. 아래 초기 설계/helper 검수 후 최종435 Python 동결본의 통합 정적/CPU 검수까지 완료했다. GPU 검증을 막는 코드 blocker는 찾지 못했다. 실제 접촉·성능·전체CPU 결과는 별도 증거이며 이 기록에서 성공으로 간주하지 않는다. 활성 소스·봉인된 이전 phase를 수정하지 않았다.

## 승인 계획과 설계

현재음 우선으로 손가락별 목표를 하나 선택하고, 관측·접근 potential의 목표를 pin된 neck collision source 평면으로 바꾸며, 기존 contact/clean/success를 유지하는 설계는 일관된다. 새 rate는 실제 접근속도와 가까운 곳의 감속·유지, LH21 요청속도를 함께 평가하고0..4/s로 제한한다. 행동 deadzone·자동 자세 고정·PD/힘/관절 한계·PPO/std 변경은 포함하지 않는다. 누적 제어의 실제 안정화·학습 향상은 아직 가설이다.

특히 다음 두 조건이 중요하다.

1. 기존 현 중심선 기반 candidate/wrong/clean 판정과 새 press-plane 관측·보상 기하를 분리해야 한다. projected strings를 기존 판정 입력에 공유하면 기존 성공 기준 보존이 아니다. 작성 중 환경을 읽은 범위에서는 기존 positive/wrong 계산 후 별도로 press surface delta/velocity를 만들고 있다. 최종 동결본을 다시 검수해야 한다.
2. source neck top9.3mm는 현 중심12.3mm의 기존±3mm 허용영역 경계와 맞닿는다. source hull의 평면/footprint proof만으로 native cooked contact와 기존 하중·성공의 동시 만족을 인증하지 않는다. 접촉 오프셋·표면 표본·추종 때문에 실제 조건이 다를 수 있으므로 기준을 완화하지 않고 native에서 측정해야 한다.

## 두 helper 독립 검수

`gpu/press_surface.py`는 pin된 compound XML·두OBJ·manifest를 검증하고 scale/geom pose를 적용한 두 source convex hull의 공통 상향 평면을 추출한다. 안쪽2mm fret-cell과 finite string 교집합 선분의 양 끝이 같은 hull에 들어가는지 검사한다. 기본67음의134 endpoint는 plane[0,0,1,-0.0093]에 포함된다. 투영은 string x/y를 보존하며 Gz만 바꾸고, 실제 상대속도의 기존 정의를 바꾸지 않는다. source convex proof가 PhysX cooked 기하/압력 인증이 아님을 계약에 명시한다.

`gpu/finger_reward.py`는 audible 중 earliest end, 없으면 press−2..end 준비 목표 중 earliest onset을 고른다. 동률은 원래 순서다. 음이 끝나기 전까지 현재 목표를 유지하므로40% 달성 뒤에도 유지할 수 있다. 곡에 존재하는 손가락 수를 분모로 사용하며, 실제속도는 surface_velocity의 음수, 원하는속도는4e의 norm을0.1m/s로 제한하고 기존 candidate가 참이면0이다. 거리·속도오차와 엄지 포함 LH21 지속 요청의 제곱평균이 계획한 양성 보상식에 반영된다. helper는 rate만 반환하고 입력을 바꾸지 않는다.

CUDA_VISIBLE_DEVICES를 비운 rl38 Python3.8에서 기하5개+보상10개, 총15개를 독립 실행해 PASS(0.040초)했다. tilted/outside/nonplanar/SHA·실제134점·속도 유지, 현재/다음 목표·반전·준비/종료 경계·빈 목표·batch·rate bound·입력 불변을 포함한다. GPU/native/GL은 실행하지 않았다.

| 파일 | 검수 SHA256 |
|---|---|
| gpu/press_surface.py | 9d292f2c9ccb19f779f9726529df5b16374fd37ddf0bd51fd85d20cefcb314d7 |
| tests/test_gpu_press_surface.py | 06311359a5a94233c413d45bca7756ac17cb6d09f3eab839637e87e8c0ab5d6d |
| gpu/finger_reward.py | 22ef7e070cf9e3de5b8f85abd0f036e9c129e4d75d3387518caa8f097dd8227b |
| tests/test_gpu_finger_reward.py | 563a6e0f5baba2f80105c2515ac1d89e296e2e3502e12fa9a6ee69032905025e |

## 동결 후 확인할 범위

- 새 항을 실제240Hz dt=1/240으로 네 번 적분하고60Hz 끝에서 중복하지 않는지, 실패 tick의 새 양성 보상을 억제하는지 검사한다.
- LEFT 전용 reward v4/표면 observation v2와3331 curriculum 분기·새 strict 계약을 확인한다. 과거 checkpoint 거부와 fresh 초기화, 기존 CPU/right/PPO/control 경로 보존을 별도로 검사한다.
- 작은 native probe에서는 원래035/v14·자유 기타·동일 PD/성공/안전을 유지한 실제 행동 응답과 source-plane/원래 string-center 거리·geometry/loaded/candidate/clean을 가능한240Hz 표본으로 같이 남겨야 한다. 원래 후보와 새 목표의 동시 만족을 관측하지 못하면 미검증으로 기록하며, source 기하 통과를 압현 성공으로 채우지 않는다.
- 그 뒤100회 학습/고정0·100평가/재개/영상은 기능·초기학습 비교로 구분한다. 이전 성과 회귀·실패를 보존하고2000회나 수렴 성공을 상속하지 않는다.

## 최종435 동결본 통합 검수

수정 전430 Python과 전체 파일 집합/SHA를 직접 비교했다. 환경·curriculum_runtime·기존 surface 테스트3개 수정, helper2개/테스트3개 추가, 삭제0개이며 `source_change_scope.json`과 일치한다. 현재435개와 `training_source_manifest.json` 및 `source_training/` 전부 SHA가 정확히 같다. 제어/scene/PPO 및 나머지427개 기존 Python은 동일하다.

- `environment.py:342`: 기존 positive/wrong/contact_geometry/loaded_target는 기존 virtual string 기준으로 먼저 계산된다. 새 plane projection은 관측/PBRS/추가 추종항에만 연결하고 기존 clean/contact/success 판정은 보존한다.
- `environment.py:670`: 새 항은 원래240Hz substep에서 rate/240을 정확히 한 번 더한다. 제어 끝에서 같은 항을 다시 적분하지 않고 단계 approach 비중1로 집계한다. `environment.py:736`은 실패한 전체60Hz tick의 새 양성항을0으로 만든다. 기존 PBRS의 실제terminal0/H32연속과 음별clean/contact/success 비중·음수항/남은곡비용은 유지한다.
- 에피소드 및 수집창에16번째 `song_finger_tracking`을 포함한다. 선택reset은 해당 에피소드 누적만 지우며 H32 창 초기화와 다른 환경 누적은 분리된다. ledger v2는 press-plane 접근/원래 string-contact 기준 및 서로 다른 selected-body load 표본 범위를 명시한다.
- LEFT만 reward v4/표면 observation v2이며 차원512/39는 유지한다. source plane/pins·inward margin·추종 수식을 계약에 고정한다. curriculum coordinator는 v3/v4 모두3331 buffer를 사용하고 CPU27 분기는 유지한다. 같은3331 크기라도 구v3 계약은 strict identity에서 거부한다. 오른손500·원래 event scale/보상v1 계산은 새 helper를 호출하지 않는다.

신설 `test_gpu_press_learning`7개를 독립 CPU 실행해 PASS(1.274초)했다.4substep 적분과 실제원본 입력 불변, 동일q/힘/기하에서 지속명령의 반복 감소, 실패tick 억제, wire candidate와3mm plane 오차 분리, H32/부분reset, 오른손 원식,3331 모델/두Adam/hostRNG roundtrip과 동차원v3 거부의 무변경을 포함한다. 앞선 helper15개와 합쳐 이 검수자가 독립 실행한 관련 CPU 검사는22개다. 전체CPU/GDB는 root가 별도로 실행 중이며 여기서 통과를 선행 주장하지 않는다.

추가 동결 SHA256:

| 파일 | SHA256 |
|---|---|
| gpu/environment.py | e1a022cab8d0e7fc0b7cbbb066416e39f4436818320608b61fcf02b12b2bdbdb |
| song/curriculum_runtime.py | 2db9ba3a77ab99aa093999bd4633ebd038ac16a4e6582d6b722833ca13fe8786 |
| tests/test_gpu_surface_learning.py | 9df39c4aaf7ebf63003916442afed31accf8462a61e54939a156cf7c2b4a3204 |
| tests/test_gpu_press_learning.py | 4cc0c9bba6a9f453d553fb34a5db47d349cfe7bf547b75b45dd09fdd6ce3215e |

## Native probe 도구 사전 검수

`probe_press_contact.py`/`test_probe_press_contact.py`도 정적으로 읽고 CPU5개를 독립 실행해 PASS(0.002초)했다. CPU 경로에 Isaac/Torch/MuJoCo import가 없음을 포함한다. 원래 substep 실행 뒤 실제240Hz 시계·native raw force11개·지정 표면 sample/body 매핑·plane/wire 거리·q/target21을 고정 크기 배열에 기록한다. 첫 종료를 기록한 row는 다음 제어step 전에 선택reset하고 이후 filler 표본은 첫 에피소드에 포함하지 않는다.4×7876 표본 메모리는110MiB 미만이며 실제 없는 접촉/물리실패도 기록 결과로 남긴다.

해당 도구는 all-zero39이므로 준비 상태의 물리 반응과 기존 후보/새 plane의 관계를 관측한다. 네 손가락의 의도적 접근/감속·학습 성공을 검증하는 도구로 해석하지 않는다. candidate frame 수는 음창/연속 clean의 달성이 아니며 실제 압력·접촉 상대 인증도 아니다. 원장/시계와 함께 후속 실측에서 해석해야 한다.

- probe SHA: `76381fbc4417cc0e66423c853e09a45cc06d75da4e00f7cb583aff95edbd70df`
- probe test SHA: `7da11b3649bd52e603f4894adfd1c2e5034f55653aac01d09f88ed0158088182`

Critical/Warning: 없음. 이 검수에서는 새 preflight Markdown만 작성/갱신했으며 GPU/native/GL·전체 학습·렌더링은 실행하지 않았다.
