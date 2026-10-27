# 오른쪽 10 mm 초기 위치 후보 — native 비교

이 비교는 기존 current neck-support 자세의 보존된 native 0초 전신 프레임과, 오른쪽으로 10 mm 이동한 후보의 실제 native 프레임을 나란히 기록합니다. 후보의 영상·정지 프레임은 모두 원본 native camera 파일의 바이트 그대로 복사했으며 재렌더·자르기·합성·색칠·주석을 하지 않았습니다. 기존 current baseline archive는 별도 경로에 계속 보존되어 있습니다.

## 비교 프레임

### 기준: 기존 current neck-support 자세 — 전신, native 0초

![기존 기준 자세 native 전신 0초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1/v2/before_current_baseline_t00_whole_body.png)

### 후보: 오른쪽 10 mm — 전신, native 0초

![오른쪽 10 mm 후보 native 전신 0초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1/v2/after_right10_t00_whole_body.png)

### 후보: 손, native 0초

![오른쪽 10 mm 후보 native 손 0초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1/v2/after_right10_t00_hands.png)

### 후보: 엄지 뒤, native 0초

![오른쪽 10 mm 후보 native 엄지 뒤 0초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1/v2/after_right10_t00_thumb_back.png)

### 후보: 전신, native 5초

![오른쪽 10 mm 후보 native 전신 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1/v2/after_right10_t05_whole_body.png)

## 초기 위치와 후보 선택

오른쪽 방향은 R_Hip−L_Hip 수평축으로 정의했습니다. 초기 actor/root 이동은 world 기준 (+9.99254, +0.38654, 0) mm이며 bounding-box 이동은 (+9.99254, +0.38655, +0.000179) mm입니다. 몸통 9개·머리 6개·손가락 42개, 합계 57개 초기 DOF 각도는 exact였습니다. 기타 39개 body의 quaternion/translation 초기 상태도 exact였고 FK를 검증했습니다. 초기 자세 조정은 팔 24개 DOF에 한정됐습니다.

Source screening에서는 V1 Thorax gate가 지나치게 좁아 두 후보를 기각했습니다. V2는 기존 Thorax gap 34.77 mm 대비 재검사해 10 mm 후보를 수락했고, 20 mm 후보는 negative Shoulder 값 −0.289로 기각했습니다. native 실행은 수락된 10 mm 조건 한 번입니다.

## 실제 5초 관측

native run은 5초(1200 physics step, 300 control step)를 완료했습니다. 기타는 free, strap OFF, root·하체 고정, self-collision ON이었고 human proximal support의 finite control은 유지됐습니다. 오른쪽 EW6만 타현 목표를 바꿨으며 다른 75개는 target 상태 유지이지 실제 움직임 고정이 아닙니다. checkpoint와 training은 0입니다.

| 관측값 | 오른쪽 10 mm 후보 | 기존 baseline |
|---|---:|---:|
| 기타 최대 body-center 이동 | 22.9101 mm | 10.0213 mm |
| 기타 최대 SO(3) 변화 | 5.00974° | 3.31719° |
| 마지막 body-center 이동 | 22.8857 mm | 7.6005 mm |
| 마지막 SO(3) 변화 | 3.07915° | 2.90298° |
| 2초 이후 최대 추가 위치/회전 | 0.383416 mm / 0.120637° | 0.372159 mm / 0.300022° |

5초 종료 bounding-box 위치는 기존 종료점 대비 (+27.716, −4.645, −12.292) mm였습니다. 이 한 번의 실행은 완전 passive equilibrium이나 반복된 robustness를 증명하지 않습니다.

## 접촉과 삼면 조건의 한계

초기 세 면 검사에는 통과했지만, 2초 이후 six-face strict gate의 동시 통과 비율은 0%였습니다. 그러므로 이를 완전한 grip 성공으로 해석하지 않습니다. 감사 로그의 contact-step 수는 right upper arm 1185, right hip/thigh 1187, left hand 1151 (thumb 858, index 224, pinky 191, palm 0)입니다. Thorax·forearm·trunk/guitar·right wrist/hand 기록은 0이며, 접촉 부분의 step 수는 서로 겹칠 수 있습니다.

분석은 virtual-pick down 6→1과 up 1→6 한 차례를 통과했습니다. 이는 virtual-pick detector 결과이지 learned checkpoint 기반 연주나 노래 성공이 아닙니다. 선택 collision facet 접촉은 해부학적 pad 위치·압력 또는 지속 grip 인증이 아닙니다.

## 전체 native 영상

### 전신

![오른쪽 10 mm native 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_shift_initial_v1/video_v2/native_right10_v1_whole_body.mp4)

### 손

![오른쪽 10 mm native 손 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_shift_initial_v1/video_v2/native_right10_v1_hands.mp4)

### 엄지 뒤

![오른쪽 10 mm native 엄지 뒤 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_shift_initial_v1/video_v2/native_right10_v1_thumb_back.mp4)

## 보관 위치와 입력

초기 패키징 v1은 5초 frame의 capture-step 검증에서 중단됐습니다. 부분 생성 파일은 보존했으며 납품용이 아닙니다. 아래 v2 복사본은 step별 캡처 해시와 전체 출력 SHA를 다시 검증했습니다.

- 후보의 별도 initial archive: [/home/ajou/yigyu/3/docs/2026-10-19/initial/right_shift10_comparison_v1/README.md](/home/ajou/yigyu/3/docs/2026-10-19/initial/right_shift10_comparison_v1/README.md:1)
- 이전 current baseline archive: [/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/README.md](/home/ajou/yigyu/3/docs/2026-10-19/initial/current_neck_support_v1/README.md:1)
- 설정·candidate·native·분석 사본은 initial archive의 README와 FILES 색인에 정리했습니다.
- 전후 copy SHA/ffprobe: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1/provenance_v2.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/artifacts_v1/provenance_v2.json:1)
- source 및 native 감사: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/comparison_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_shift_initial_v1/comparison_v1.json:1)
- 실행 및 추가 결과 색인: [/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_shift_initial_v1/INDEX.md](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_shift_initial_v1/INDEX.md:1)
- 오른쪽 위치 viewer 사용 안내: [/home/ajou/yigyu/3/stability_adapter_2/right_shift_pose_test_v1/README.md:1](/home/ajou/yigyu/3/stability_adapter_2/right_shift_pose_test_v1/README.md:1), [/home/ajou/yigyu/3/stability_adapter_2/right_shift_pose_test_v1/open.sh:1](/home/ajou/yigyu/3/stability_adapter_2/right_shift_pose_test_v1/open.sh:1)

Viewer GUI 조작 성공 여부는 이 native 결과와 분리해 다뤄야 합니다. 이 문서는 GUI 실측을 주장하지 않습니다.
