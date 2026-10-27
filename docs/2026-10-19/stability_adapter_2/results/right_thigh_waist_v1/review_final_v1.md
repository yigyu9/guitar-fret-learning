# 최종 독립 검수

요약 판정: **문제없음 — 현재 문서·미디어·봉인 준비 범위에서 승인**. Critical 0 / Warning 3 / Suggestion 0. 소비된 원본이나 다른 담당자의 파일을 수정하지 않았고 새 물리·학습 실행은 하지 않았다.

## 확인 범위

- [실제 실행 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/review_native_v1.md:1)의 정지·팔꿈치 raw 결과와 완료 설명이 일치한다. 두 완료 실행은 각각 5초/1,200 physics step/300 control tick이며, 동일 초기 상태·첫 2.5초 궤적을 보존했다. 실제 팔꿈치 범위 10.095744°, 정지 대비 추가 기타 변화 0.154754mm/0.148812°, waist endpoint presence/positive 1,198개 및 후기 120개가 문서에 맞게 반영됐다. 부분 중단 4.783333초와 영상 4.833333초도 구분했다.
- 최종 [V3 도식](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/artifacts_v1/waist_profile_contacts_v3.png)을 직접 확인했다. t→G_Y 방향과 core/flank 구간이 명시되고, V3의 source 윤곽 mask로 band가 내부에 제한된다. V1/V2 오류 이력은 남아 있다. native 전신 0/3/5초 및 초기 측면 비교도 확인했으며 측면은 카메라 행렬 동등성 인증으로 제시하지 않는다.
- provenance V1/V2/V3의 입력 before/after·출력·producer SHA를 현재 파일과 대조했다. 원본/사본 영상 6개의 SHA가 모두 같고 저장된 ffprobe 정보는 완료 151frame/30fps/5.033333초, 중단 145frame/30fps/4.833333초다. 전체 영상 decode 검증은 하지 않았다.
- main PLAN:1201, A README:2293, D README:126, AGENTS:19의 before snapshot SHA·현재 after SHA·원문 prefix·추가 heading을 확인했다. 완료 문서·V3 README·변경 색인의 현재 링크 61개가 존재하고 지정 줄이 유효하다. 최종 리뷰 링크는 이 파일 생성으로 충족된다.
- [seal_outputs_v1.py](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/seal_outputs_v1.py:30)의 구문과 논리를 읽었다. 이전 입력/목록과 허가된 append snapshot, 중첩 support 입력, provenance, 3 native/2 완료/1 중단, 9 CPU 후보/2 수락, 영상 6개를 검사하고 최종 파일을 배타 생성한다. 기능상 실행 차단은 발견하지 않았다. **봉인은 아직 미실행**이며 과거 전체 inventory 재계산·최종 봉인 결과 인증은 root의 후속 범위다.

## Warning

1. [완료 설명:41](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_THIGH_WAIST_COMPLETION_V1.md:41)의 “후기 지지”는 관측된 오른 허벅지·상완·왼손 손가락 접촉으로 한정한다. 힘·모멘트 기여는 분리 측정하지 않았다. 실제 왼 부위는 middle2/index2/pinky3이고 Thorax 후기 접촉은 0이므로, 무왼손·오른 두 블록만의 유지나 수동 집게 성공으로 확대하지 않는다. root는 최종 안내도 이 범위로 제한하기로 했다.
2. [완료 설명:55](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_THIGH_WAIST_COMPLETION_V1.md:55)의 source1 손 STL35개 사전 핀 누락 한계는 유지한다. 후속 37개 핀과 실제 초기 감사가 소급 완전 봉인을 뜻하지 않는다. +15mm flank 표본 및 작은 한 주기는 좁은 core 접촉·접촉력 N·연속시간·장기·임의 운동·연주 인증이 아니다.
3. [V3 README:1](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/artifacts_v1/README_V3.md:1)의 표제 V2와 :47–48의 V1 provenance/producer 링크는 이전 설명을 상속한 minor 표기다. 현재 도식의 근거는 [provenance_v3.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/artifacts_v1/provenance_v3.json:1) 및 [producer V3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/artifacts_v1/build_artifacts_v3.py:64)다. 최종 안내에서는 V3 및 최신 변경 색인을 사용하고 소비 문서는 보존한다.

## 확인 SHA-256

- 최종 V3 PNG: `b395e46135e470946f344e3afb28eac8430f9081ea7df726599ee0673fd55d91`
- V3 README: `1b1ebf8fbfa7922c93c0332c3fe6acea1391469c1a68d6de8a634e9bb0009f41`
- V3 provenance: `c4509f7cf7f867b4283ff3bb256c26583a0fa2f925dfaf9184dfd2e9b061b903`
- 봉인 실행 예정 소스: `c4bb4aaa5f5f758cd2fbedee9981e0938cb7cd197f79ad053cfec1ec9a23064a`
