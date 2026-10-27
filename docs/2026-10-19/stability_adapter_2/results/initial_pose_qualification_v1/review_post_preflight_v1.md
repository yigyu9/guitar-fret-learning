# 초기 자세 시험 배치·후처리 사전 검수

요약 판정: **수정 권장**. Critical 0건, Warning 3건. 진행 중인 native 제어 자체의 오류는 발견하지 않았다. 아래는 검수 시점 V1 소스 기준이며, 수정 후 소비 여부와 해결 증거는 후속 버전에서 구분해야 한다.

## Warning

1. [run_initial_pose_qualification_batch_v1.py:34](/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_qualification_batch_v1.py:34): 후속 두 실행을 기다리는 `proc.poll()` 루프에는 제한 시간이 없다. 처음 baseline/static 대기의30분 제한과 달리 자식이 멈추면 무기한 대기한다. 그룹별 monotonic deadline과 timeout 시 자식 종료·로그 닫기를 추가하거나, 별도 supervisor의 실제 제한을 명시해야 한다.
2. [run_initial_pose_qualification_batch_v1.py:27](/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_qualification_batch_v1.py:27): 최초 두 보고서의 `exists()`만 확인한 뒤 즉시 JSON을 읽는다. 공통 save는 `open('x')` 뒤 json.dump를 사용하므로 파일 생성과 전체 쓰기 사이 짧은 구간에 reader가 들어가면 JSONDecodeError로 배치가 중단될 수 있다. 최초 보고서 readiness를 parse 가능할 때까지 제한 시간 안에서 재시도하도록 하는 것이 맞다. 이미 소비한 V1 소스는 수정하지 않고 새 버전을 사용한다.
3. [render_initial_pose_qualification_v1.py:16](/home/ajou/yigyu/3/stability_adapter_2/render_initial_pose_qualification_v1.py:16): 8줄에서 직접 import해 사용하는 read/save/sha의 `initial_pose_noise_v1.py`가 후처리 before/after paths에 없다. 직접 소비 helper를 목록에 추가해야 한다. 다른 단계에서의 native pin은 이번 후처리의 현재 helper 불변 검사를 대신하지 않는다.

## 확인한 정상 범위

- 두 신규 Python 파일의 AST 문법 검사는 통과했다.
- batch는 한 그룹에2개 subprocess만 띄우고 해당 그룹이 종료된 뒤 다음 그룹으로 넘어간다. 서로 다른 config/output/log 경로를 사용하며 subprocess shell 문자열 주입 경로는 없다. baseline/static가 incomplete면 후속을 생략하고, 분석 invariant 실패도 check=True로 드러난다.
- native runner V2의 contact_frames.json과 media/capture.json을 읽고 30fps 길이·physics_step 정렬·상태 보존 플래그를 확인한다. 소비 PNG의 실제 경로는 media/frames/{native_key}/NNNNN.png로 native StringTrialRecording이 기록한 image_sha256과 맞다. OM_appearance는 보조카메라이며 이번 세 시점 후처리 대상이 아니다.
- 개별 native camera matrix와 실제 world contact feature를 기존 검증된 draw에 전달한다. front/right_side/top의1280×720 원본 영역과220px footer, 3840×940 snapshot,1920×470 합본 구성이 기존 함수와 맞는다. 영상 프레임 수는 조건별 count를 사용하며 encode/ffprobe가 count와30fps 표시 길이를 검증한다.
- 표식 색·양의 lambda 채움/0 빈 원·고정 크기·X-ray·동일 그룹2mm voxel 표시 병합은 기존 의미를 유지한다. 힘N·접촉 면적·압력으로 해석하지 않는다. static/EW6 타현 제목을 patch.dict로 추가하며 왼손 cycle의 기존 stage 이름도 맞다.
- native 출력·물리·제어를 바꾸는 새 코드는 없다. post output은 새 디렉터리, save는 exclusive create, 영상 인코더는 -n을 사용한다. 원래 기록을 덮어쓰는 경로는 발견하지 않았다.

검수자는 지정한 이 보고서만 작성했다. 구현·native 결과·기존 검수 보고서는 수정하지 않았다.

## 검수 시점 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_qualification_batch_v1.py`: `efa492d44774e9cfbab49350d29ad0554affca171689357b2fbbcc18a29d28ca`
- `/home/ajou/yigyu/3/stability_adapter_2/render_initial_pose_qualification_v1.py`: `7ab8080a8a7480b1d7290cdc0515d79b549bbbdefa7fc374b63389cc88ae2c89`
