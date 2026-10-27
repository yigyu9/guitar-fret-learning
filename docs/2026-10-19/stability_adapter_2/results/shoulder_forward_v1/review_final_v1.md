# 최종 검수 — 오른 어깨의 작은 전방 배치

요약 판정: **문제없음.** Critical 0 / Warning 2 / Suggestion 0. 추천1cm 초기 후보의5초 **정지** 결과와 문서·미디어 정리를 한정 승인한다. 새팔 자세의 동작·연주·장시간·반복 성공 인증은 아니다.

- [native 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/review_native_v1.md:1)의 두 실행·2400행 수식·600 control state/readback·고정78 및 전체기타 초기state 대조가 최종 결과와 일치한다. [root README:13](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/README.md:13)은20mm gate 실패와10mm 정지 gate 통과를 구분한다. source1 실패/metadata 상속 오류와 source2의 새 전방projection 정의를 보존했다.
- [canonical artifactV3:15](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1/README_V3.md:15)은 실제 Shoulder3 변경/other78 초기고정과 가상 motor점 요청 cap10N→human Jᵀ torque를 정확히 구분한다. V1/V2의 잘못된81각 동일·상완 effort cap 표현은 보관본이며 정식 탐색은 V3다. 10N을 실제 접촉힘 또는 Nm 관절 한계로 설명하지 않는다.
- [artifactV3:20](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1/README_V3.md:20)의 초기Elbow+9.893081mm/5초 동일시각+10.710865mm, Palm 초기+1.720963mm/5초+2.570061mm와 실제3D 변위를 확인했다. 두 PNG를 열어 이전/추천 초기·5초 timeline 및 같은 native 원본 crop의 캡션·글자·배치를 확인했다. 새카메라·물리 관통 인증으로 설명하지 않는다.
- provenance1/2/3의 flat producer·inputs before/after·outputs SHA가 모두 일치했다. 기준2+신규4의 영상6개는 서로 다른 목적지의 byte-exact 사본이고 실제ffprobe151frames/30fps다. 별도 side-by-side 파생 재인코딩과 원영상 사본을 구분한다. 물리5.0초와 영상5.033333초는 다른 기간이다.
- [navigation](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/navigation_update_v1.json:1)의 main3 원prefix/before-after SHA 및 실제 heading PLAN1164/A README2256/D README89를 대조했다. 검토 문서72개 절대링크·줄을 확인했다. [봉인:52](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/seal_outputs_v1.py:52)의 actual provenance schema, [봉인:68](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/seal_outputs_v1.py:68)의6영상 SHA/프레임 및2native·review gate·exclusive 최종출력 순서를 읽기 검토했고 AST도 통과했다. 이phase에 없는 invalid probe1을 parse하지 않는다. 봉인은 실행하지 않았다.

Warning 1 — [root README:17](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/README.md:17): 추천10mm 최종BB9.425103mm/SO3 2.887575°와 최대10.455249mm/3.343712°는 다른 양이다. 전기간10mm/3° 이내 유지로 확대하지 않아야 한다. 이전19°의 팔꿈치 동작 시험을 이번 shoulder 초기값의 인증으로 재사용할 수 없다.

Warning 2 — [artifactV3:28](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/shoulder_forward_v1/artifacts_v1/README_V3.md:28): 지정35%+상부영역presence1062/1200·positive237/1200은 전체상완1173/1162와 별개이며 이전1117/1113보다 지정영역 positive가 줄었다. 접촉분포 tradeoff를 숨기지 않고 raw 양lambda 관측으로만 해석한다. ‘힘수반’ 표현도 N단위 지지력·각부위 힘/모멘트 기여·해부학적 겨드랑이 지지의 증거가 아니다. endpoint 표본 역시 연속시간 접촉 인증은 아니다. 최신 문서의 제한 문구를 확인했다.

추가 native/학습/소스·기존자료 수정0. 이전전체 inventory와 입력버전 전수 보존 재감사 및 source_final/inventory/final_verification 생성은 root 후속 봉인 범위다. 예정 출력이 아직 없는 상태에서 미래 감사 완료를 주장하지 않는다.

검수 SHA256:

- root README: `b3511a50dddd359baae5d8190062b986af816fef5205b8123016e8c4fff7944a`
- canonical artifact README_V3: `456a5f428ba2dca8b0fb30dbf2a35a9a2025ef1f5d5b7a9d7cfc1c81c0bbd76e`
- 변경 색인: `87e2ec667734bcb5885d09b8b0399658b2c8b2d9de7249a19474ae5480005d59`
- 봉인 source: `fca5340a3579c634103dc748716881aab0ff1131ae403b338fedc0fdf52729bb`
- 실제 shoulder crop PNG: `b41c2f67b96b80d7b95266f6c9094c3c29327b2b37c08c40821cd8b0ad75063a`
- 실제 whole-body timeline PNG: `97e6d390c4ec448ac1a459567c42063c3b3411d1563ab32ec0dcabcf8c04cf78`
