# 왼손 OFF 최종 문서·산출물·봉인 사전검수

요약 판정: 문제없음. 증거무결성 검증통과와실제5초기타유지실패를명확히분리한다. 원본/산출물을변경하거나추가물리실행을하지않았다.

Critical: 0

Warning: 3

- [산출물 이력 제한:7](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/artifacts_v1/ARTIFACT_HISTORY_LIMITATION_V1.md:7): V2가원provenance_v1을덮어썼고현재파일은같은producer로재생성된기록이다. **최초V1provenance바이트·historicalbefore동일성을인증하지않는다.** producerV1복원은사전SHA로확인되지만provenance원문복원과다르다. 현재V3성공산출물과native원자료를보증하고이력을소급채우지않는scope가적절하다.
- [소비PLAN_V3:1](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_OFF_CURRENT_PLAN_V3.md:1): V2제목/search_v2잔류를원본으로보존했다. [완료문서:14](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_OFF_CURRENT_COMPLETION_V1.md:14)와결과README는실제V3/search_v3를명시해현재실행과구분한다. 현재판단을그잔류경로로안내하지않는다.
- [분석기:11](/home/ajou/yigyu/3/stability_adapter_2/analyze_left_hand_off_current_v1.py:11): 두새분석기의독립map에직접없는helper를native/timeline의원SHA와현재exact로합성검증했다. [native검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/review_native_v1.md)의범위를유지하고새before기록을소급완성한것으로취급하지않는다.

Suggestion: 0

- [완료문서:8](/home/ajou/yigyu/3/stability_adapter_2/LEFT_HAND_OFF_CURRENT_COMPLETION_V1.md:8), [결과README:3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/README.md:3): .933333초/224physics/56control 중단,BB77.452mm/SO335.625°/actorroot208.335mm,LEFTcontact/request0,upper185/마지막.7875초,hip222 및57같은시각BB차55.547mm가canonical/raw와일치한다. t0away·activePDgravity/R현재G제어와연속release/passive평형을구분하고질량배치의인과한계도명시한다. maintained_for_5s=false이며2~5초/후기값을만들지않았다.
- [현재아티팩트 설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/artifacts_v1/README_V3.md), [현재색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_hand_off_current_v1/INDEX_V3.md): 실제시작과224step종료native원프레임을표시하고현재V3provenance/디스크beforepin을사용한다. MP4는원nativeSHA와byte-exact,1280×720/30fps/29frame/.966667초다. 물리.933333초와초기프레임포함재생시간을구분한다. 잘못된과거레이아웃·재생성이력을현재정상V3와구분하고5초/유지성공으로설명하지않는다.
- [navigation 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/navigation_update_v1.json): 승인된3mainappend의before/afterSHA·byte-exactprefix가봉인검사에서통과했고실제heading1251/2341/174와최신문서의절대경로/줄을확인했다. source/native원byte변경과append를혼동하지않는다.
- [봉인 코드:15](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_hand_off_current_v1/seal_outputs_v1.py:15): 이전Bchain·현재source/native/analysis maps·capturePNG·현재V3provenance/원본-영상사본SHA·히스토리한계·링크/AST범위가맞다. save를메모리로우회하고미생성review검사만제외한read-onlyguard에서52689입력version/41링크가통과했다. source6/2수락, native1·224/56·5초실패,현재58nativePNG집계가맞다. `verification passed; physical maintenance failed`로무결성과물리결과를분리한다.

실제봉인과최종JSON생성은root의다음단계다. 본검수에서는저장을우회했고source_final/artifact_inventory/finalverification을생성하거나수정하지않았다.

현재봉인 코드 SHA256: `ee89728eeca85defbb081d9e4a6cafca24f68a540f19733961f703e6d639586d`.
