# Thumb2 단일 hinge source 검색 사전 검수

요약 판정: **문제없음(PASS)**. 실행을 막는 Critical 사항은 찾지 못했다. 소유 파일은 이 review.md뿐이며 검색/geometry/native/분석/렌더 main은 실행하지 않았다. 다른 작업자의 파일과 이전 봉인 자료를 수정하지 않았다.

- [검색 기준](/home/ajou/yigyu/3/stability_adapter_2/search_thumb2_clearance.py:35)은 실제 거절 native 초기 상태를 읽고 이전 inventory의 해당 SHA를 확인한다. CoupledSnapshot에는 같은 실제 상태를 state0/state로 전달하며, 새 finger1 변화에 이전18축 인증을 확대하지 않는다. [Zero identity](/home/ajou/yigyu/3/stability_adapter_2/search_thumb2_clearance.py:48)와 비변경 body pose 검사를 강제하고 delta18의 thumb2 한 성분만 바꾼다.
- [형상 범위](/home/ajou/yigyu/3/stability_adapter_2/search_thumb2_clearance.py:54)는 전체human–G/cross-hands, graph>2의 native허용 또는same-left self1188쌍을 포함한다. 연결 graph≤2는 제외한다. [이동 geom assertion](/home/ajou/yigyu/3/stability_adapter_2/search_thumb2_clearance.py:74)은 thumb2/3 두 body만 포함하고 thumb_top은 pose chain에만 있다. Rear patch는 기존 G-local polygon을 실제 저장 기타 pose로 world 변환하며 certified_distance의 upper/lower/gap/feasible witness 기록을 유지한다. LP 교차와 source 거리의 cooked contact/force 인증은 하지 않는다.
- [7조건 및 선택](/home/ajou/yigyu/3/stability_adapter_2/search_thumb2_clearance.py:84)은 float32 양자화 뒤 실제 delta로 검색·최소절대delta 우선/동률thumb3 patch upper-distance 순으로 한 후보를 고른다. 실제q81과 초기PD81 exact, 원 native initial의 sealed SHA를 독립 대조했다. Thumb2 시작0.3384127914905548rad와 유효범위0..1.1171258687973022rad가 계획과 같으며 일곱 양자화 각도0.13841278851032257..0.5384128093719482rad는 모두 범위 안이다. 검수에서 source solver/FK/mesh screen은 호출하지 않았다.
- [후보 조립](/home/ajou/yigyu/3/stability_adapter_2/search_thumb2_clearance.py:118)은 기존 trial을 읽어 thumb2 초기=held 및 offset0만 바꾼다. 다른80 target은 기존 target 배열을 보존하고 무clipping compose와 전체81 source/native-effective 범위를 검사한다. clear 후보가 없으면 proposal/native를 만들지 않는다. 새 proposal도 fresh direct native gate를 면제하지 않으며 기존 source-support false를 유지한다.
- [wrapper 입력](/home/ajou/yigyu/3/stability_adapter_2/run_thumb2_clearance_phase.py:25)은 source 실행의 직접 자료·XML/mesh·canonical helper closure를 측정 전에 SHA/사본으로 보존한다. Native만 frozen runner가 실제 소비하는 이전 closure를 추가하고 frozen runtime/inner runner SHA를 강제한다. [실행 기록](/home/ajou/yigyu/3/stability_adapter_2/run_thumb2_clearance_phase.py:65)은 전후SHA·로그·exit를 보존하며 fresh gate 거절은0step report로만 허용한다. 과거 nested snapshot의 재귀 복사를 요구하지 않는다. Native 실제 결과/후속 문서·미디어는 아직 이번 사전 판정에 포함되지 않는다.

Warning(설명만): [search scope:136](/home/ajou/yigyu/3/stability_adapter_2/search_thumb2_clearance.py:136)의 “thumb2/3/top meshes transformed”는 top geom이 없어 정확하지 않다. 실제 코드는 위 assertion으로 두 geom만 변환한다. Root에 전달했고 source 실행이 이미 시작돼 소비본을 보존하며 후속 ROOTnotes/README에서 “thumb2/3 두 geom, thumb_top은 pose만”으로 정정하기로 회신받았다. 동작 blocker는 아니다.

Python3.8 AST 통과와 사전 확인 SHA-256:

- search_thumb2_clearance.py: `898fe338f0f01820e36718c97b0a88b1a2bb07acc058225fcae87eef419c853f`
- run_thumb2_clearance_phase.py: `9c65de4a06bcb92dd65e6db9391109d88ea3921a6e334dbf0f5578083ef30c38`

검색 실행 완료/조건별 LP 결과와 native 승격 여부는 저장 결과가 나온 뒤 별도로 검수한다. 이번 판정은 코드·작은 수치 계약·입력 보존 설계에 한정된다.


## 실제 첫 실행 실패 추가 기록

실제 source 실행은 **exit1 / terminal error**로 종료됐다. [원 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb2_clearance_v1/search.log:1)는 [other_pose_identity assertion:100](/home/ajou/yigyu/3/stability_adapter_2/search_thumb2_clearance.py:100) 실패를 보존한다. XML의 thumb2 하위 body는 thumb2/3/thumb_pad/thumb_top 네 개인데 기존 moving_names에 thumb_pad가 빠져, thumb2 delta를 따라 정상 이동한 자식 pose를 고정 대상으로 잘못 검사했다. 사전 검수에서 이 누락을 잡지 못했으며 위 사전 PASS를 실행 완료/정확성 인증으로 사용하면 안 된다. 원 검수 기록은 삭제하지 않고 실제 실패로 보완한다.

검색 원본67입력/67사본·전후/현재 SHA·로그 SHA/exit1 보존을 직접 확인했다. Search 결과/proposal/native는 생성되지 않았고 이 실패를7조건 형상 해소불가로 해석할 수 없다. 소비 소스·로그·입출력을 수정하지 않았다. 수정은 별도 source_hand_thumb2_clearance_v2에서 검토한다.
