# 작업용 초기 자세 채택 독립 검수

요약 판정: **문제없음**. Critical 없음, Warning 없음, Suggestion 없음. 지정한 등록 파일·채택 문서·메인 마지막 append와 입력 검증만 검토했다. 새 물리·학습은 실행하지 않았고 이 검수 보고서만 작성했다.

- [manifest](/home/ajou/yigyu/3/stability_adapter_2/working_initial_pose_v1/manifest.json:1)의 정지/15초 타현 config 두 사본이 기존 검증본과 바이트·SHA가 동일하다. 두 쌍의 EnvironmentContract를 직접 비교하여 81관절 순서/qref/candidate/PD reference/rates/유효 body bounds의 동등성을 확인했다.
- manifest의 81개 목표와 실제 초기각은 기존 native 초기값과 정확히 같다. 기타 actor-root·정규화 회전·BB 중심을 기존 native 초기 pose와 SciPy 변환으로 재대조해 일치했다. 6개 사전 입력 및 evidence SHA 모두 현재 파일과 같다. [verification_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/working_initial_pose_adoption_v1/verification_v1.json:1)의 동등성 결과를 확인했다.
- [채택 범위 12–16행](/home/ajou/yigyu/3/stability_adapter_2/WORKING_INITIAL_POSE.md:12)은 기존 유한 지지제어/모델·root/하체 고정 조건의 초기 배치를 작업용 기준으로 삼는다. 15초 최대 5.116mm/2.203° 근거는 이전 검수 결과와 일치한다. 왼손 접촉·해제/재파지 미확보를 유지하며, 105채널 이식/최종 제어권/학습 설정이 자동 변경됐다고 주장하지 않는다.
- [재현 안내 24행](/home/ajou/yigyu/3/stability_adapter_2/WORKING_INITIAL_POSE.md:24)은 새 config 경로와 기존 runner의 audit 추론 경로가 맞지 않는 제한을 명시하고 기존 검증 config 경로를 사용하도록 안내한다. 이번 사본을 곧바로 실행 가능한 새 native 진입점으로 오인하게 하지 않는다.
- 메인 README/PLAN은 해당 main_before 사본을 정확히 prefix로 보존하고 각 709byte만 append했다. 채택 문서/결과 README의 절대 링크 10개와 지정 줄 번호도 모두 유효하다. 기존 결과/소스 변경 없이 좁은 채택 기록의 목적을 충족한다.
