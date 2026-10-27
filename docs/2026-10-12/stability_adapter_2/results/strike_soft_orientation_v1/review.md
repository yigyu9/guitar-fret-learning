# Soft orientation 최종 독립 검수

요약 판정: **문제없음 / 검수 PASS**. 실험은 **미채택**이다. 남은 Critical·Warning·Suggestion 없음.

- 실제 저장 자료는1,200 physics steps·300 controls·151 native trace/camera 표본이며21개 native 계약이 모두 true다. PREPARE/PLAY/HOLD는49/251/0, source motor phase는0만 관측했고 PD switch는0이다. Native POSITION과 fingers21 policy 제어를 유지하며 EFFORT 요청은 없다.
- 실제 비교 기준은 기존 POSITION timed-wait-rebase의 **policy+PI**이며 actual-angle POSITION geometry PI가 아니다. 변경은 PLAY IK의 actual pick/FK/Chest anchor 회전 soft cost5mm/rad와 기록 필드다. 위치·방향·관절규제의 공동 soft cost, 기존 bounds/rate 및 대기/RECOVER 목표 소유권은 사전 검수한 소스와 동일하다. README:3의 비교 기준 오기를 정정했고 이전 문서는 `doc_before_base_wording_review/`에 보존해 Warning을 해소했다.
- 기준과49개 PREPARE 전체 controls·25개 native-state prefix·첫 actor observation/action이 exact임을 독립 확인했다. Prefix 입력4 SHA가 일치한다. PLAY251개 orientation reference/weight 기록이 candidate와 맞고 저장 trace와 같은 시점인125개 actual pick 회전이 native body 회전과 일치한다. 사전100-case 회전 anchor 검사는 순수 수학 범위로 유지하며 실제 전체 FK 추적 인증으로 확대하지 않는다.
- Raw target/physical/accepted/release/wrong은0, miss10, READY success 및 running F1은0이다. 최소 PLAY policy pick-to-READY 거리0.0063794227004078915m가 성공 인증은 아니다. 기타 위치 max/end46.353646/31.995380mm 및 SO(3) 회전 max/end45.290342/43.959132°를 재계산했고 playable region52/300 control·6/251 policy 표본과 일치한다. Source terminal 없이5초 기록을 마쳤다.
- Native closure1,088개는 현재 파일1,086개와 exact `native/source_before` 사본2개로 해소된다. 별도 분석 입력7·회전검사 입력1 SHA가 일치한다. 두 MP4의 실제 SHA/ffprobe1280×720·151frames·30fps·5.033333초와151×2 frame SHA/step coverage를 확인하고 종료 손 PNG를 직접 검토했다. 최종 README·CHANGED_FILES·progress의 결과·원자료/영상 링크 및 접촉/readiness 해석 한계가 맞는다.

확인 SHA256: runner `54b393fb5cf610e2c79f1e99070499974a2d75f80a31ebd516d8da6640ac6978`, wrapper `d8f22a8c61b017707a86752611c6d10130c2a770598d0cfd8e456861b71b0bbf`, 분석 summary `4d8281f7179f2d49f452db12d4edc7ac5c21eb41506fadbb33dd365334756d44`.

검수 중 추가 native 초기화·물리 실행은0회다. 방향 항의 단독 인과효과·지속 접촉 지지·전곡 연주 성공·미관측 회전 미분/force duality·source/native CPU/GPU 동등성을 인증하지 않는다. 후속 body-rotation spring과 root 최종 보존 감사의 완료를 대신하지 않는다.
