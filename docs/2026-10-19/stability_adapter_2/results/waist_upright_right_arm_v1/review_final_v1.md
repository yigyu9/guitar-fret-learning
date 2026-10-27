# 최종 문서·native 산출물·봉인 스크립트 검수 V1

요약 판정: **문제없음**. 현재 수정본 기준 **Critical: 0 / Warning: 0 / Suggestion: 0**.

검수 범위: phase README·CHANGED_FILES·artifact brief·완료 문서, main PLAN1219행/README2311행/날짜 README144행부터의 추가 부분, Luna `artifacts_v1`·영상 폴더, 새 `seal_outputs_v1.py`. 검수자는 다른 담당자 파일을 수정하지 않았고 이 기록만 생성했다.

## Critical / Warning / Suggestion

없음. 검수 중 지적한 완료 문서의2° 기울기 비교 표현·머리6 초기각 변경 누락 및 산출물 README의 분석 링크 라벨은 root의 수정 후 확인했다.

## 확인 근거

- [WAIST_UPRIGHT_RIGHT_ARM_COMPLETION_V1.md:5](/home/ajou/yigyu/3/stability_adapter_2/WAIST_UPRIGHT_RIGHT_ARM_COMPLETION_V1.md:5): 현재는 “완화량이 더 작은2°”로 올바르게 비교한다.18행은 body9·양팔24·머리6 초기각 재맞춤과 head world 목표 보존을 함께 설명한다.4° 후보의14.545mm/8.013°가 기존 waist11.831mm/6.095°보다 커 안정성 향상·학습 기준 교체로 채택하지 않는다고 명시한다. 실제 초기 요청8mm/달성3.119mm·scalar/상대 회전·Chest proxy/임상 각도·raw lambda/N·Thorax 후기0/왼손 지지 제한도 원자료와 일치한다.
- [CHANGED_FILES_v1.md:8](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/CHANGED_FILES_v1.md:8): 새 문서 및 추가 부분의 링크70개가 절대 경로·실재 파일·유효 줄번호다.1219/2311/144행은 실제 새 heading이다.3개 navigation before snapshot과 현재 문서는 exact prefix이며 `navigation_update_v1.json`의 before/after SHA·heading도 일치한다. 기존 main 문서의 변경 전 부분은 검수 범위에서 제외했다.
- [artifacts_v1/README.md:11](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/artifacts_v1/README.md:11): 같은 전신 카메라에서 같은 픽셀 crop을 비교한다고 정확히 설명한다. baseline/4° 전신 view/projection은 exact, 손 카메라 view는 다르며 표시와 metadata가 일치한다.6개 PNG를 열어 caption이 프레임 밖에 있고 조건·0/2/5초 표기가 맞음을 확인했다. 원native PNG의 동일 resize/crop으로 각 이미지 패널의 픽셀을 독립 재현해 exact함을 확인했다.2초 장면이 주기 시작2.5초 전이라는 설명도 명확하다.
- [manifest_v1.json:1](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/waist_upright_right_arm_v1/manifest_v1.json:1): 영상6개는 원native MP4와 byte-exact이며 SHA·크기·실제 ffprobe가 manifest와 일치한다. 각1280×720/30fps/151frames/5.033333초이며 물리5.0초와 구분한다.20개 source input·2개 producer의 before/after/current SHA,6개 PNG SHA, provenance의 output manifest SHA도 모두 일치한다. 산출물 생성에 따른 원자료/실행 소스 변경 증거가 없다.
- 최종 `posture_final_v1.json` SHA `274bf2881d450addcd04e2e62c3f0eec3005a741b12780049e5dc6786d606eec`, `analysis_final_v1/analysis.json` SHA `5aa490d730399f7a7c48975070d5baf6efb05e857773283438a48b39f137d5f8`은 독립 native 검수 시점과 exact하다. 현재 문서·그림 설명의 주요 수치가 이 결과와 같다.
- [seal_outputs_v1.py:50](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/waist_upright_right_arm_v1/seal_outputs_v1.py:50): expected SHA별 입력 버전을 검사하고 승인된 append의 exact prefix snapshot으로만 차이를 해소한다. 이전 phase/current source·native·analysis·provenance·906raw PNG·6영상·203복원 dependency를 대조하고 새 closure 파일은 exclusive 생성한다. navigation 실제값·단계 수치/제한·링크 검증과 AST도 확인했다. 봉인 스크립트의 SHA는 `0c3634ea867292a8b3a0c94c5d6aefd446de2aa23e606c923d19cf9d7ccd6da1`이며 AST 통과했다.

## 검수 시점

봉인 **실행 전** 사전 검수다. `source_final_v1.json`·`artifact_inventory_v1.json`·`final_verification_v1.json`의 실제 생성·최종 실행 통과는 root의 봉인 단계에서 확인한다. 이 기록은 이전 독립 native 검수의3600physics/900control·명령/waist/영상 검증을 대체하거나 물리 성공 범위를 넓히지 않는다.
