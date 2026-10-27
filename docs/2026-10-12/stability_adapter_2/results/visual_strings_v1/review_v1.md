# 물리 없는 6현 표시 독립 검수

판정: **문제없음 — 지정된 오버레이 구현과 완료된 5초 녹화를 승인한다.** 미결 Critical 0건, Warning 1건, Suggestion 0건. 봉인 초안의 Critical 1건은 새 v2에서 해결됐다. 리뷰어는 추가 native·학습 실행이나 원본 수정 없이 읽기 전용 대조와 저장 자료 재계산을 수행했다.

확인 범위:

- [선택 진입점](/home/ajou/yigyu/3/stability_adapter_2/run_visual_strings_trial_v1.py:8)은 기존 OM runner의 녹화기 선택만 patch한다. [wrapper](/home/ajou/yigyu/3/stability_adapter_2/string_trial_recording_v1.py:30)는 미리 가져온 원 녹화기 alias를 호출하므로 재귀 없이 raw·strap·6현 표시 단계를 각각 보존한다. 새로운 물리 geometry나 setter는 추가하지 않는다.
- [끝점·가림 처리](/home/ajou/yigyu/3/stability_adapter_2/string_trial_recording_v1.py:14)는 실제 native G:string1..6와 대응 end 위치를 매 녹화 시점 읽는다. 기존 투영 함수의 음수 camera-Z 규약으로 depth를 비교하고 가려진 표본 구간은 숨긴다. 2px 선·2mm depth 여유·현당 2,049개 표본은 이번 카메라 조건의 시각 근사이며 실물 현 굵기·진동·장력이나 완벽한 픽셀 가림 인증이 아니다. 카메라 크기는 전신/손 1280×720, 초기 외관 1280×960에 맞춰 고정되어 있다.
- [검증 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/verification_v1.json:1)의 입력 1,698개 SHA가 현재와 일치한다. trace·contacts·initial_values·native_shapes·native_properties·property_cache_checks 6개 JSON을 직전 OM native_v2와 직접 비교해 exact 일치를 확인했다. 따라서 이번 표시 추가로 저장된 물리 궤적·물성·접촉이 바뀌지 않았다.
- native 1회는 1,200 physics/300 control로 완료됐다. 각 카메라 151frame이며 세 단계 PNG 906개의 SHA와 렌더 전후 상태 동일 검사가 검증 입력에 포함된다. 151개 녹화 시점의 실제 6×2 끝점을 XML 로컬 위치와 기타 root pose로 독립 재계산했고 최대 오차 `2.024472051×10⁻⁷m`가 보고서와 일치했다. 초기→5초 위치 변화 `113.199839mm`, SO3 회전 `4.857745°`는 기존 결과 그대로이며 초기 유지·연주 성공은 아니다.
- 초기·0/2/5초 전신·손·최종 비교 PNG 4개를 직접 열었다. [v2 비교 그림](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/artifacts_v2/hands_sameframe_strap_vs_sixline_v2.png)의 좌우 패널은 각각 동일 초기 strap-only/strings 원자료와 픽셀 exact로 대조했다. 손에 가려진 구간과 현 표시 차이를 확인했다. 모든 artifact provenance 입력 전후·출력 SHA가 일치하고 보관 MP4 2개도 원본/복사본 SHA가 동일하다. 물리 5초와 151frame/30fps MP4 약 5.033초를 구분한다. 전체 영상 디코딩 인증은 수행하지 않았다.
- 최종 README·변경 색인·v2 정정 설명의 절대 링크/실제 줄 번호 및 main4 완료 append의 prefix·SHA를 확인했다. [봉인 v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/seal_v2.py:35)는 검증 입력·이전 inventory·main append chain·provenance·영상 복사·리뷰 존재를 확인한 후 별도 출력 경로를 만든다. 실제 봉인 실행과 최종 inventory는 root의 후속 확인 범위다.

Critical 해결 기록:

- [미실행 봉인 v1:37](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/seal_v1.py:37)은 실제 영상 manifest에 없는 `sha256_source/sha256_copy`를 읽어 KeyError가 발생하는 초안이었다. 원본을 보존한 [v2:37](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/seal_v2.py:37)에서 실제 `source_sha256/copy_sha256`으로 두 키만 정정한 것을 확인했다. 지정 영상 2개의 실제 SHA 대조도 통과했다.

Warning 1건:

- [보존 artifact README v1:15](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/artifacts_v1/README.md:15)는 raw 패널에 strap이 있다는 잘못된 설명을 포함한다. [README_V2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/visual_strings_v1/artifacts_v2/README_V2.md:3)가 오류와 원본 보존을 공개하고 양쪽 strap이 동일한 비교를 제공한다. 최종 설명에는 v2 비교를 사용하고 소비된 v1을 수정하지 않는다. 정정본 검수는 통과했다.

Suggestion: 없음.

검수 SHA256: verification `7874dcb7ef2f8eb8f7e554feff86820f7dbabc59cbea1c844baa8e0a0d9f7d43`; wrapper `ef20b949a2954710828b9cfc64408d1a8a40159c6dd98073f030ff0ae88514ff`; 선택 진입점 `97ca1cf3837c30d0788ab3e1c65f13b085c700626a669d863be5b2f7e1cae8a8`. 지정 리뷰 외 파일은 생성·수정하지 않았다.
