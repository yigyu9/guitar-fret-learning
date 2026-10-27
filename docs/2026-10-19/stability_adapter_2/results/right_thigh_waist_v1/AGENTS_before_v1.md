# StabilityAdapter 2 추가 작업 지침

프로젝트 공통 지침과 README.md·EXPERIMENT_WORKFLOW.md 및 최신 사용자 지시를 함께 따른다. 사용자는 2026-10-07부터 필요한 실험 결정을 별도 승인 요청 없이 진행하도록 변경했다.

- GPT-6.1 Sol은 물리 해석·후속 후보·구현과 실행을 맡고, GPT-6 Luna는 확정 brief에 따른 산출물만 맡는다. 작업별 파일 소유권을 명시하고 다른 담당자의 파일을 수정하지 않는다.
- 산출물 담당자는 **review.md·final_verification.json·source_final·artifact_inventory.json을 생성하거나 수정하지 않는다.** 아직 없는 파일의 문서 링크는 예정 경로로 표시한다. 링크를 존재하게 만들기 위해 임시 검수·감사 파일을 생성하지 않는다. 검수 기록은 change-reviewer, 최종 보존 감사와 봉인은 root 담당이다.
- 결과 README와 변경 파일 색인은 한국어로 작성한다. 로컬 파일·이미지·영상 링크는 절대 경로를 사용하고, MP4 표시는 `![설명](/절대/경로.mp4)`를 사용한다. Raw HTML video는 사용하지 않는다.
- 그림 생성 전 캡션 폭과 범례가 실제 데이터 표본을 가리지 않는지 확인한다. 생성 후 실제 PNG와 원자료·native 프레임을 대조한다. 원본 소스 그림을 Isaac Gym 렌더로 설명하지 않는다.
- 실행에 소비된 소스·leaf 계획·입력·출력은 수정하지 않는다. 재시도는 예상 SHA와 실행 기록을 대조하고 원본을 보존한 뒤 새 파일/경로로 진행한다. 성공한 후처리도 배치 수정 전에 소스·wrapper·metadata·로그·입출력을 보존한다.
- 계획·진행 기록은 기존 main PLAN/README에 추가한다. 결과·로그·미디어는 사용자가 지정한 `docs/2026-10-12/stability_adapter_2/` 아래 새 phase에 저장한다. 기존 stability_adapter/·공용 자산·이전 실험은 보존한다.

- POSITION(stiffness=0)를 POS0로 설명할 때 토크 명령 0과 혼동하지 않는다. driveMode·stiffness·damping과 requested OFF0/ON10Nm를 별도로 기록하고 명령을 측정 토크로 부르지 않는다.

- 산출물 담당자는 A(stability_adapter_2)의 main PLAN/README를 포함한 어떤 파일도 수정하지 않는다. 진행 요약도 D(docs/2026-10-12/stability_adapter_2)의 지정한 progress 파일에만 쓴다. A 문서 갱신이 필요하면 root에게 보고하며 다른 경로로 대체 기록하지 않는다.

- native DOF scalar q 변화 표와 부모–자식 body 상대 회전 차이 표를 구분한다. R_Shoulder_x/y/z 같은 DOF 이름의 suffix를 world 회전축으로 설명하지 않는다. `q_delta_rad`와 `shoulder_relative_rotation_delta_from_OFF_rad`는 다른 양이다. 표의 행·열 정의와 단위를 실제 raw field에 맞춘다.
