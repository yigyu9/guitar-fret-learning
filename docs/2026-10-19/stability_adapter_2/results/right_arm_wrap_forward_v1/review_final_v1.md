# 오른 전완·손 전방 이동 최종 검수

요약 판정: 문제없음. 최신 문서·산출물과 봉인 코드 사전검수가 통과했다. source/native/원자료를 수정하거나 새 물리 실행을 하지 않았다.

Critical: 0

Warning: 0

Suggestion: 1

- [build_upper_timeline_v4.py:44](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/build_upper_timeline_v4.py:44): hash 불일치 에러메시지의 `step`은 정의되지 않아 그 실패분기에서 NameError가 난다. 검사 자체는 중단되므로 현재 성공 산출물/봉인에는 영향 없다. **소비본을 보존하고 다음 producer 버전에서 `physics_step`으로 정정한다.**

확인 근거:

- [완료 문서:7](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_ARM_WRAP_FORWARD_COMPLETION_V1.md:7), [결과 README:17](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/README.md:17): Elbow3만 초기변경·고정78각과 support/G39/reference exact를 world 전완·손 위치불변과 혼동하지 않는다. 실제 초기palm9.941820mm/5초8.562639mm, native Elbow원점59.605nm와1µm허용치, G추가동시각1.323156mm/0.555192° 및 절대drift가 canonical과 일치한다. native 초기Gfront 벡터의 source/native float32차이도 지적 후 actual vector로 정정됐다. endcap·왼손 기여·실제 부분실행과 지지범위가 명시돼 있다.
- [최신 그림 설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/README_V3.md), [최신 영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_forward_v1/INDEX_V3.md): 왼손/넥 카메라 그림을 오른손 이동 증거로 쓰지 않고, 같은 전신native ROI의 새 오른팔 비교를 제공한다. 새 오른팔 그림을 직접 열어 분홍색 오른손/상완/앞판과9.94mm 라벨을 확인했다. 모든 사진영역은 native 원본의 명시된 crop/resize픽셀과 일치한다.
- [정상비율 producer:19](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/build_upper_timeline_v4.py:19): 기존540×430→360×371 비균일resize 그림은 보존하고, 새360×287 타임라인으로 대체한다. 원native frame0/60/150·physics0/480/1200과 pixel변환을 독립 대조했다. 반올림 비율오차0.116%가provenance와맞고 새그림의caption/장면을 직접 확인했다. 최신 설명은 과거비율오류·원crop·원전신자료를 안내한다. 기존산출물을 덮어쓰지 않았다.
- [provenance_v3.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/provenance_v3.json)의 직접입력40개와 producer5개, [오른팔 provenance](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/provenance_right_arm_v1.json) 및 [새타임라인 provenance](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/provenance_upper_v4.json)의 각6입력 before/after SHA가 현재파일과일치한다. 기준MP4와폰트도명시적 before핀에포함한다. baseline은이전sealed inventory/native영상SHA로도대조됐다. 실패builder1/2와원래출력·설명은보존하고 새결과와구분한다.
- [manifest_v3.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_forward_v1/manifest_v3.json):6개MP4의 실제ffprobe를 다시실행해metadata와exact확인했다. 원본/사본SHA·크기는같고1280×720/30fps, 기준/선정은151frame/5.033333s, partial은20frame/0.666667s다. 물리5초 및0.633333초와 초기frame포함재생시간을구분한다. 재인코딩·부분영상늘림은없다.
- [navigation 기록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/navigation_update_v1.json):세main의before/afterSHA와byte-exactprefix 및 실제heading1244/2334/167을확인했다. 결과README/변경색인은latestREADME_V3/INDEX_V3로안내하고 최종JSON미생성 링크는예정으로명시한다. 표header/구분행이연속이며 절대경로·실제줄 링크가맞다.
- [봉인 코드:17](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/seal_outputs_v1.py:17): root경로와 이전B보존chain/currentsource·nativeattempt·네analysis입력map·append snapshot예외·PNG/manifest/additionalprovenance schema·links/AST가맞다. save를메모리로우회하고 미생성review존재검사만제외한 read-only확인에서52277입력version/123링크/342rawPNG 및 canonical현재값 조건이통과했다. source8조건/기하수락5/거절3과metadata3개/추가solver0, native1352physics/338control/1완전+1부분,6영상/10파생PNG집계가정확하다.10PNG에는보존된과거비율오류그림도포함되고 현재안내는정정본을쓴다.

실제봉인과source_final/artifact_inventory/finalverification생성은root의다음단계다. 본검수에서는파일쓰기없는guard확인만했고 원본·산출물·봉인JSON을생성하거나바꾸지않았다. 봉인 producer는 exclusive생성으로기존최종파일을덮어쓰지않는다.

현재봉인 코드 SHA256: `f7131f9b4245bebcdd57bca0a8f894422d2e51fb2b3643efdb350dd61d6aa010`.


# 실패 산출물 producer 이력 제한 추가 — 최신 판정

요약 판정: 현재 native 수치·정상 산출물·봉인 입력 map 검증은 문제없음. 모든 실패 producer 원문이 보존됐다는 포괄적 주장은 하지 않는다.

Critical: 0

Warning: 1

- [ARTIFACT_HISTORY_LIMITATION_V1.md:3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/ARTIFACT_HISTORY_LIMITATION_V1.md:3): 최초 `build_upper_timeline_v4.py` 실행이 StopIteration으로 중단된 뒤 같은 파일을 수정했으며, 최초 실패 원문/디스크 beforeSHA가 저장되지 않았다. **그 실패 소비본의 byte-exact 보존과 실행 전 핀을 인증하지 않는다.** 현재 성공 producer/SHA로 과거 누락을 소급 채우지 않으며, 다음 재시도는 최초 실행 전 원문·SHA를 디스크에 보존하고 새 버전으로 수행한다. 이 제한은 작업 지침 위반 이력이며 현재물리검증 오류와 구분한다.

Suggestion: 1

앞선 성공producer의 에러메시지 `step` 변수 지적은 그대로다. 소비본을 다시 수정하지 않는다.

- 새 제한 문서 전체를 읽고 현재 README/변경색인의 절대링크와 실제1행을 확인했다. 문서는 실패 source 이력 미보존과 정상출력/native 원자료 검증을 구분하며 소급 beforeSHA를 주장하지 않는다.
- 정상 `provenance_upper_v4.json`의 실제6입력 before/after SHA와 출력SHA를 다시 현재파일로 확인했다. 앞선 native1352행·명령/시계·같은시점palm/G 비교와 실제PNG 픽셀 검증은 여전히 유효하다. 최초 실패 원문을 저장된 기록으로 복원·독립 인증할 수 있다는 주장은 하지 않는다.
- 최초 실패는 물리 재실행이 아니고 출력 이전 중단이라는 이력 설명이다. 현재의 source/native/config/원본state·PNG·MP4와 성공한산출물값을 변경해 해결한 것이 아니다. 모든 실패가 같은 방식으로 완전히 보존됐다는 표현은 이추가단락으로 제한한다.
- 봉인 코드 SHA는 `f7131f9b4245bebcdd57bca0a8f894422d2e51fb2b3643efdb350dd61d6aa010`으로 그대로이고 아직 최종JSON은 미생성이다. source_final은 실제 저장된 입력 map의 검증 범위, inventory는 이 새 제한 문서까지의 현재파일 집계를 인증한다. 이를 잃어버린 최초 실패 소스의 사전 보존 인증으로 해석하지 않는다.
