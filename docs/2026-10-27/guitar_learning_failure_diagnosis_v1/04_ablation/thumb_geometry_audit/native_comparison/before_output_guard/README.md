# 엄지 후면의 고정 기타 native 기하 A/B 준비

상위 [source 감사](../README.md)의 좌표 단서를 실제 접촉으로 확인하기 위한 **새 진단**이다. 구현·CPU 검증만 진행했으며 GPU는 아직 실행하지 않았다. active Python·OBJ·물리 자산·기존 결과는 수정하지 않는다.

| 조건 | 제어·판정이 보는 안내면 | 공통 native 물리 |
| --- | --- | --- |
| A `current_all_vertices` | 기존 모든 OBJ vertex 기반 긴 후면 | 같은035·fixed guitar compound asset·중력·PD·힘 상한·엄지5축 |
| B `face_only_playing_neck1` | face 참조 vertex만 사용한 physical neck1 후면 | A와 동일 |

B는 source geometry 입력과 candidate 계약이 바뀐 진단이다. 원래 보상 학습 성과로 보고하지 않는다. 원래128개 엄지 점·normal·geom offset·local frame과 rate/거리·방향·하중 문턱은 그대로다. 두 mesh 공통 plane 가정은 docs helper에서만 사용하지 않고, neck1의 실제 끝 bounds를 유지한다. 네이티브 충돌 파일은 A/B 모두 같은 원본이다. 과거 thumb 두 probe는 자유 기타였으므로 새 fixed A/B와 같은 조건으로 합치지 않는다.

`guitar_learning.tool.validation.thumb_contact_probe`를 그대로 실행하며, 이전 `run_thumb_deeper.py`의 wrapper 방식·source를 참고하고 봉인한다. **−0.9mm override는 실행하지 않는다.** 양쪽 모두 원래−0.3mm 스케줄·900제어틱(15초/3600physics)·±15°·제어 요청당0.5°·4rad/s codec·2N 접근 보호·원래 물리 이탈 기준과 접촉→유지→해제→재접촉 판정을 사용한다. 추가 힘이나 상태 덮어쓰기·범위 확대·문턱 완화가 없다. 기타의 fixed 옵션만 양쪽에 같은 값으로 요청하며, scene의 prepared boundary reset 이외 상태 setter를 추가하지 않는다.

## 저장과 검증

- base helper의 primary 측정·선택을 바꾸지 않고, 그 **동일 실제 selected point·normal·thumb3 force**를 현재 면과 face-only 면으로 각각 추가 판독한다. 두 gap·region excess·normal cosine·rear-normal load·candidate·quality가 원래240Hz trace에 함께 저장된다. 추가 계측은 primary 제어·선택 키를 덮어쓰지 않는다.
- 같은 sample selection 알고리즘도 안내면이 바뀌면 선택 점·제어 witness와 궤적이 달라질 수 있다. 원래 sample ID·fixed witness ID·stage와 실제 힘을 보존한다. thumb1/2 접촉힘도 원래 full native force trace에 남지만 thumb3 candidate에 합산하지 않는다.
- 원래 raw report는 새 출력의 `base_probe_report.json`에 보존한다. wrapper의 `report.json`은 fixed scope를 명시하고 그 base report를 포함한다. `completed`는 실행·검산 완료이며 접촉 프로토콜 성공과 별개다. 실제 접촉 판정·해제 판정은 `base_probe.protocol_passed`를 본다.
- 원래 codec 오차·physical failure와 함께 native target limit 초과, ±15° 체류, 제어당 target 변화, 실제 qd, 기타 drift, 실제3600physics와 scene close를 검사한다. 실제 저장 point·force에서 두 gap·normal load를 독립 재계산한다.
- A/B의 물리 asset SHA·fixed/gravity 옵션·shape 속성 readback SHA와 의미 있는 PD 필드 SHA가 같아야 한다. 모델·asset 원래 manifest 검사는 그대로 먼저 실행한다. runtime wrapper는 원래 함수 연결을 종료 때 복구한다.
- 자체 script/helper와 상위 감사640개 입력을 포함해 실행 전후 SHA를 봉인한다. parent는30초마다 감시한다. 변경·실행 실패가 나면 중단하고 원자료를 남기며 예산을 늘려 재시도하지 않는다.

## 실행

아래는 기본적으로 계획만 출력한다. **root의 GPU 인계 전에는 `--execute`를 사용하지 않는다.** 현재 queue의 앞 작업이 모두 장면을 닫은 뒤 root가 직렬 실행한다.

```bash
taskset -c 0-13 /home/ajou/miniconda3/envs/rl38/bin/python \
  /home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/thumb_geometry_audit/native_comparison/support/run_pair.py \
  --out /home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/thumb_geometry_audit/native_comparison/run_v1
```

GPU 승인 후 동일 명령에 `--execute`를 붙인다. 두 별도 프로세스와 별도 새 디렉토리에서 native 영상과 trace를 생성한다. 첫 조건이 실행·봉인·종료 검증에 실패하면 자동으로 다음 조건이나 재학습을 시작하지 않는다. 원래 probe의 candidate 프로토콜 실패만으로 실행을 실패 처리하지는 않는다.

## CPU 확인 범위

`cpu_self_test.json`은 A/B의 패드 점·normal·valid 동일, face-only plane `(0,0,−1,−.008)`·유한 bounds, primary 측정의 정확한 보존, 같은 합성 점·힘에 대한 두 기하 판독과 zero-load candidate 차단, 원래 깊이 스케줄·경로·구문을 확인한다. **CPU의 합성 힘은 오직 판정 산술 시험**이며 실제 native 접촉이나 압력 증거가 아니다. GPU 실행 후 실제 힘과 정상 후면 기하·프로토콜을 함께 확인해야 한다.
