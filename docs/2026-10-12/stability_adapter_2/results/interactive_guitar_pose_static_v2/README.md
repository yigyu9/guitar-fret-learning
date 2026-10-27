# 물리 없는 정적 기타 초기 배치 편집기 v2

사용자가 화면에서 기타 배치를 살펴보고 시각적으로 자연스러운 후보를 고를 수 있도록, 물리 상호작용을 제거한 별도 Isaac Gym native viewer 도구를 만들었다. 기존 v1은 물리 preview를 포함한 과거 재현 도구로 보존한다. v2는 초기화부터 중력이 0이고, `simulate`, `fetch_results`, 외력 제출, environment step을 차단한다. 따라서 접촉 반응, PD에 의한 자세 이동, 스트랩 힘이 발생하지 않는다. 후보는 정적 화면에서 고른 pose이며 실제 지지·접촉·clearance를 증명하지 않는다.

새 도구의 최종 실행법은 [정적 편집기 entry 안내](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_POSE_STATIC_ENTRY.md:1), 조작법은 [정적 편집기 가이드](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_POSE_STATIC_GUIDE.md:1), 구현 범위와 검증 단계는 [정적 편집 계획](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_POSE_STATIC_PLAN.md:1)에 있다. 기존 물리 preview가 필요한 과거 기록은 [v1 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_v1/README.md:1)에서 확인한다. 자연스러운 배치 후보를 새로 고를 때에는 이 문서의 static launcher를 사용한다.

## 실행과 조작

그래픽 화면에 연결된 터미널에서 실행한다.

```bash
bash /home/ajou/yigyu/3/stability_adapter_2/open_guitar_pose_static.sh
```

처음부터 스트랩 참고 경로를 숨기려면 `--no-strap`을 추가한다. 저장 후보를 다시 열 때는 `--candidate /absolute/path/pose.json`을 지정한다. 이전 v1 후보도 읽을 수 있으며 스트랩 ON/OFF는 힘이 아니라 표시 상태로만 해석한다. 불러온 후보의 `strap_visible`이 launcher option보다 우선한다.

F1–F3은 이동 X/Y/Z축, F4–F6은 회전 X/Y/Z축을 선택한다. J/L은 선택 축을 음/양 방향으로 조절한다. 기본 increment는 이동 2 mm·회전 1°이고 F로 정밀 모드를 선택하면 이동 0.5 mm·회전 0.25°다. Tab은 world/local 축, Z는 undo, R은 기준 기타 배치 복원, C는 전체/손 camera, G는 시각/충돌 형상 보기, T는 스트랩 참고 경로 표시만 전환, S는 후보 JSON과 두 camera 이미지를 저장한다. H는 도움말, Esc는 종료다. Space와 E는 물리를 시작하지 않고 inert 처리된다. 회전 중심은 기타 actor root 원점이다. 화면은 정지 상태이며 마우스 조작은 Gym 시점 변경에 쓴다.

## 정적 검증 결과

[실제 검증 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/native/verification.json:1)은 18개 검사 모두 `true`, `physics_steps=0`, `physics_trials=0`을 기록한다. 실제 native X11 키 입력 F3/L/SPACE/E를 확인했고, 편집·렌더 중 전체 humanoid state가 바뀌지 않았으며 Space/E가 inert임을 검사했다. 중력 zero, `simulate`/`fetch_results`/외력/step 차단, 차단 호출 뒤 state 불변, 시간 0, 저장 JSON의 `physics_enabled=false`·`simulation_steps=0`, 표시 전용 T, 저장 후보 reload, preview methods 부재도 확인했다. 이 기록은 native 정적 상호작용과 의도적으로 차단된 API 호출만 다룬다. `strap_toggle_is_display_only`는 표시 상태 전환과 physics step 0만 검사한다. 이 18개 항목은 raw image의 선 잔류 여부를 검사하지 않는다. 별도 [snapshot 검사 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/snapshot_verified/verification.json:1)의 4개 검사는 같은 event batch의 T/S 입력 후 whole-body와 hands PNG의 주황 debug pixel 0, 모든 상태 불변, physics step 0, strap 표시 OFF를 확인했다. 이 검증도 정적 화면 캡처에 한정되며 물리 trial·영상은 새로 실행하지 않았다.

## 실제 native 정지 이미지

아래는 1280×720 Isaac Gym native camera에서 편집 기능 검증 중 physics step 0에 저장한 이미지다. `candidate_000` 전체 장면과 손 장면에는 주황색 13-point strap-route 참고 overlay가 보인다. 선은 정적 표시일 뿐 cloth, 접촉, 장력 또는 물리 경로 반응을 뜻하지 않는다. `candidate_001`은 같은 편집 위치를 저장하면서 표시를 OFF로 둔 후보지만, harness가 T 전환 후 draw 없이 저장해 원본 viewer snapshot에는 debug route 선이 남아 있다. 해당 원본과 이전 `clean_static_capture`는 보존한다. 실제 UI에서도 T/S가 같은 event batch에 들어오면 선 잔류가 가능함을 확인해 최종 entry를 보완했다. 아래 OFF 장면은 새 entry가 저장 직전 viewer debug line을 지우고 capture한 `snapshot_verified` 이미지이며, 별도 검사에서 두 camera 모두 주황 debug pixel 0 및 physics step 0이다. 두 후보 모두 기능 검증을 위한 임의의 6축 편집값이며, 자연스러운 최종 자세로 선택된 후보가 아니다.

![candidate_000 정적 native 전체 장면, 참고 strap route 표시 ON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/native/session/candidate_000/images/frames/whole_body/00000.png)

![candidate_000 정적 native 손 장면, 참고 strap route 표시 ON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/native/session/candidate_000/images/frames/hands/00000.png)

![최종 static entry가 T/S 같은 batch에서 저장한 실제 정적 native 전체 장면, strap OFF](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/snapshot_verified/candidate_000/images/frames/whole_body/00000.png)

후보의 world position, xyzw orientation, 기준 대비 pose delta, static 플래그와 route 표시 상태는 [candidate_000](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/native/session/candidate_000/pose.json:1)과 [candidate_001](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/native/session/candidate_001/pose.json:1)에 기록돼 있다. 두 JSON 모두 `strap_enabled=false`, `physics_enabled=false`, `simulation_steps=0`이다. 차이는 `strap_visible=true`와 `false`뿐이다. 이전 OFF harness snapshot에서 보인 잔류 주황 선은 T 후 draw 없이 저장했을 때 남은 viewer debug route다. 이는 접촉, 힘, 시간 진행을 나타내지 않는다. 일반 draw는 route를 clear하지만 실제 UI에서도 같은 event batch에 T/S가 연속되면 잔류할 수 있다. 최종 권장 entry는 후보 저장 전 line clear, native capture 후 화면 draw 복원을 수행한다. 새 [snapshot verification](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/interactive_guitar_pose_static_v2/snapshot_verified/verification.json:1)은 같은 batch T/S 저장의 whole-body/hands 모두 orange debug pixel 0 및 상태 불변/시간 0을 기록한다. 영상이나 physical preview는 만들지 않았다.

## 이전 단계와의 경계

이 정적 도구는 이전 사용자 배치 도구를 대체해 과거 물리 기록을 다시 쓰지 않는다. [v1 launcher](/home/ajou/yigyu/3/stability_adapter_2/open_guitar_pose_editor.sh:1), v1 소스·로그·영상은 과거 물리 preview 재현을 위해 그대로 보존한다. 새 자연스러움 판단은 [최종 권장 launcher](/home/ajou/yigyu/3/stability_adapter_2/open_guitar_pose_static.sh:1)와 [capture 보정 entry](/home/ajou/yigyu/3/stability_adapter_2/guitar_pose_static.py:1)에서 수행하며 자동 물리 실험은 계속 중단 상태다. 기존 static core와 이전 launcher는 보존한다. 정적 충돌 형상 보기는 화면상의 기하 확인일 뿐 접촉 반응이나 clearance 인증이 아니다.
