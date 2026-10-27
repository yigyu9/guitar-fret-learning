# 왼손 넥 아래 지지 목표 독립 검수

검수 범위는 새 [좌표 helper](/home/ajou/yigyu/3/stability_adapter_2/underneck_contact_targets.py:10), 테스트·검증기 v1/v2, [최신 계획](/home/ajou/yigyu/3/stability_adapter_2/LEFT_UNDERNECK_CONTACT_PLAN.md:1), 저장 검증 결과와 main PLAN/README 변경분이다. 다른 담당자 파일은 수정하지 않았다. 검수자는 테스트·검증기·렌더·물리·학습 본체를 실행하지 않고 AST/SHA와 저장 좌표의 독립 수학 대조만 수행했다.

## 코드·수치·계획

- [helper:22](/home/ajou/yigyu/3/stability_adapter_2/underneck_contact_targets.py:22)는 세 점 외적으로 설명용 면 법선을 구하고 정규화한 후 선택된 G local +X/-Z/+Z 방향으로 부호를 맞춘다. `R*polygon+p`, `R*normal`, 반대 방향 손 목표 계산은 rigid transform과 일치한다. 이것은 해부학적 손 패드나 실제 cooked 표면 법선의 보정이 아니다.
- 저장 네 점의 평면성·수직성·world 좌표를 독립 재계산했다. 현재 수평 q에서 palm outward `[-0.016313732854892453,0,-0.9998669222053198]`, desired hand Z `0.9998669222053198`; thumb/front outward는 각각 world -Y/+Y다. 테이퍼 아래면을 정확한 world -Z 평면으로 잘못 취급하지 않는다.
- 테스트는 독립 직사각형 fixture, rigid motion/inverse, q/-q 동치, taper 법선, 잘못된 pose/퇴화 영역의 5개다. 저장 v1/v2 테스트 로그 모두 5개 OK이며 4개 소스의 Python3.8 AST를 독립 확인했다. 테스트나 실제 접촉 검증을 재실행하지 않았다.
- 검증기 v1은 NumPy bool JSON 직렬화에서 실패했다. [failure.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_underneck_contact_v1/verification/failure.json)과 원 소스·테스트 로그가 보존되어 있다. v2는 checks 값에 Python bool 변환 한 줄만 추가했다. [verification_v2/verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_underneck_contact_v1/verification_v2/verification.json)의 6개 입력 SHA와 현재 파일을 독립 대조했고 6개 저장 판정·새 native/physics 0·새 손 자세/controller false가 정합한다.
- PLAN 보존본 대비 변경은 최신 사용자 무스트랩 힘/표시 OFF, 넥 수평·앞판 정면, 오른손 비접촉, 왼손 초기 아래/뒤/앞 목표 및 움직이는 G 상대 목표에 대응한다. root/하체 고정·몸통9 유지 목표·66 주제어·단일 PD 합성·자유 기타·부착/상태 덮어쓰기 금지와 모델 한계는 유지된다. 기존 스트랩 길이는 이력이며 새 기본 조건이 아니다.
- 초기 네 손가락 전면 접촉 목표와 연주 중 음악 목표에 따른 개폐를 구별한다. 위쪽 반구와 지지면 방향이 충돌하면 후보 재검토, 도달 범위/변화율/마찰 밖 보장 금지가 명시되어 있다. 설명용 source 영역은 실제 접촉/지지력/PhysX 면 인증이 아니다. 현재 helper는 위치·방향 계산만 하며 상대 속도 오차·관절 보정·새 초기각·실접촉·5초 지지는 후속 미구현/미검증이다.
- main README의 기존 바이트 prefix는 보존본과 일치한다. 최신 append도 기존 자세의 결과를 새 수평·무스트랩 자세에 전이하지 않는다.

## 그림의 관측 범위

첫 `artifacts/contact_regions.png`에서 아래 축/캡션 겹침과 낮은 대비를 확인했다. 기존 producer/PNG/manifest는 별도 보존되어 있다. v2 및 최종 설명도는 세 영역·목표 법선 화살표·world m 축·별도 설명/범례로 정리되어 캡션 겹침이 해결되었다. 실제 PNG를 보았으며 저장 world 좌표와 범위를 대조했다. 손/실제 접촉/PhysX 형상을 나타내는 그림으로 확대하지 않는다. producer 세 버전과 대응 manifest/PNG SHA가 각각 보존 소스 및 현재 소스와 일치한다.

요약 판정: 현재 완료한 CPU 영역 변환·검증과 계획 범위는 문제없음. 최종 결과 문서와 root 보존 기록은 준비 후 별도 delta 확인한다.

## 최종 문서·보존 대조

[README.md:17](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_underneck_contact_v1/README.md:17)의 판정 개수는 6개와 단위 테스트 5개로 정정되었다. 변경 색인은 메인 README 원문 백업, PLAN의 CPU 완료 104행과 실제 초기 배치 대기 106행, v1 직렬화 실패 기록을 구별한다. 모든 최종 문서 링크와 지정 행이 존재한다. 기존 native 기준 이미지는 과거 수평 후보이며 새 손 접촉 결과가 아님을 명시하고, 개념도도 실제 native/접촉/지지력으로 설명하지 않는다.

[preservation_checks.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_underneck_contact_v1/preservation_checks.json)의 현재 소스 11개 SHA와 source_final의 대응 사본을 바이트 단위로 독립 대조했다. main PLAN 전 원문은 직전 보존 계획과 exact이며 main README 원문 prefix도 유지된다. v1 실패 producer와 6개 입력 SHA 역시 원본과 일치한다. 이 기록은 직접 소단계 입력 보존 범위이며 기존 거대한 ancestry나 실제 PhysX 접촉을 새로 인증하지 않는다. 최종 감사/인벤토리는 root 후속 기록이며 검수자가 생성하거나 실행하지 않았다.

최종 요약 판정: 문제없음. 미해결 Critical/Warning 없음. 완료 범위는 설명용 상대 영역·법선 변환, CPU 검사와 최신 계획/설명도다. 새 인간 초기각, 오른손 비접촉·왼손 다중 실접촉, 상대 속도 기반 제어, 무스트랩 자유 기타의 5초 지지는 여전히 미검증이다.

최종 판정: PASS
