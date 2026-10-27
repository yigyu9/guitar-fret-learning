# 최종 문서·산출물·봉인 코드 검수

요약 판정: 문제없음. 현재 문서와 산출물은 native 독립 검수 결과의 범위와 일치한다. 봉인 코드 사전검수 통과. 검수 대상 원본을 수정하거나 새 물리 실행을 하지 않았다.

Critical: 0

Warning: 1

- [산출물 builder:17](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/artifacts_v1/build_artifacts_v1.py:17): 기준 두 MP4와 NanumGothic 폰트는 이번 builder의 before-pin 목록에 없다. **이전 sealed inventory/native SHA로 기준 영상 동일성을 확인한 근거와 폰트 사전SHA 미인증 범위를 유지한다.** [README V2:37](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/artifacts_v1/README_V2.md:37) 및 [봉인 scope:114](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/seal_outputs_v1.py:114)에 제한이 명시돼 있으며 소급 before 근거로 쓰지 않는다.

Suggestion: 1

- [영상 색인:55](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/INDEX.md:55): 현재 마지막 이미지설명 링크는 보존된 README V1을 가리킨다. 최신 raw축부분집합/fullbody 및 before-pin 설명이 있는 README_V2.md로 안내하면 탐색 일관성이 좋아진다. 원 V1은 그대로 보존한다.

확인 근거:

- [완료 문서:9](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_ARM_WRAP_UPRIGHT_COMPLETION_V1.md:9), [결과 README:19](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/README.md:19): 실제 localZ proxy13/17/20° 완화와 부모상대13/4/3°, 초기 기타25mm/+1.03mm, static BB최대34.001mm/SO3최대16.503°,2→5초7.342mm/3.344°, wave추가0.458126mm/0.200994°가 canonical posture/timeline과 일치한다. 몸통 기댐0, 전체상완1196과 raw축0~1부분집합181, waist1198, 왼팔·손1189 및 endcap·left 기여·정착drift가 명시돼 있다. 학습기본 교체·왼손 없는 수동유지·일반 연주 성공을 주장하지 않는다.
- [영상 manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/manifest_v1.json): MP416개 원본/사본 SHA·크기 및 실제 ffprobe의1280×720/30fps/프레임수/재생시간을 독립 대조했다. 기준과 두 완전사례는151frame/5.033333s이며, 다섯 partial은54/17/20/30/24frame 원길이다. 물리 시간과 영상의 초기프레임 포함 재생시간을 구분한다.
- [builder:31](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/artifacts_v1/build_artifacts_v1.py:31): derivedPNG13개의 사진·crop 영역을 실제 native원본의 동일resize/crop 픽셀로 독립 재계산해 exact 확인했다. frame0/60/150의 실제시점0/2/5초도 capture metadata와 일치한다. 전신 비교 카메라행렬은exact이고 side는 달라 그 한계가 캡션과 V2에 명시됐다. 초기비교·상체crop·손타임라인 PNG를 직접 열어 라벨/장면/읽힘을 확인했다.
- [navigation 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/navigation_update_v1.json): 세 main문서의 before snapshot/after SHA와 byte-exact prefix, 실제heading1237/2327/160을 확인했다. 새 결과 표의 header/delimiter 빈 줄 및 봉인JSON의 생성예정 표기는 지적 후 수정됐다. source/root/공용자산 변경과 새 문서추가를 구분한다.
- [봉인 코드:17](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/seal_outputs_v1.py:17): root경로·실제provenance schema/native_source_inputs·manifest/copy_sha256·이전 B보존체인·현재7source입력map/7nativeattempt/3analysis입력map·PNG SHA·prefix예외·링크 실제줄·AST가 맞다. save를 메모리로 우회하고 아직없는 review파일 검사만 제외한 read-only guard확인에서51371입력version,106링크,894rawPNG가 통과했다. source21행/4수락/17거절, native3512physics/878control/2완전+5partial,16영상/13derived집계도 일치한다. 447capture×2PNG=894이며1094가 아니다.
- 봉인 producer는 기존파일을 덮어쓰지 않는 exclusive생성으로 source_final/artifact_inventory/finalverification만 마지막에 작성한다. 실제 봉인 실행과 최종JSON 생성은 root의 후속 단계다. 이 검수에서는 저장을 우회했으며 원본/산출물/봉인JSON을 생성하거나 바꾸지 않았다.

봉인 코드 SHA256: `3663c7fe95a19e5fae1db225549ed5bc2860e61bbac4419af85757b30d98b495`.
