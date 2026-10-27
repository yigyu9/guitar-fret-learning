# 하체 PD 원인 분리: 독립 hip fixture

사용자가 승인한 하체 초기각 유지·PD/solver 진단의 후속이다. 기존 14조건에서
안정 자세를 찾지 못했고, 외부 접촉 없는 humanoid-only에서도 held target 이탈이 있었다.
기타 초기 Z 변경 확인을 기다리는 동안 실제 환경 조건을 바꾸지 않는 진단을 수행한다.

1. 공용 XML의 L_Hip 관절 3개·형상·armature 정의만 읽어 독립 fixed-root fixture를
   만든다. 중력/ground/chair/guitar는 없다. 실제 humanoid나 공용 자산은 변경하지 않는다.
2. x 단일 hinge와 x/y/z 3 hinge를 비교한다. 진단 fixture의 초기 x는 0 또는 기존
   L_Hip 값 −π/2, 나머지 0이다. 기존 scalar range와 넓은 ±180° range를 대조한다.
   kp=300/kd=75/effort=300, baseline TGS4/2·240Hz·substeps1 POS를 사용한다.
3. native joint type/초기 q·목표·gain·armature readback과 24-step q/vel/body pose/contact를
   기록한다. → 무접촉·유한값·초기 상태 일치 확인, 변형별 raw target 편차 비교.
4. Sol이 해석하고 Luna가 표/그림/설명을 결과 문서에 누적한다. 별도 검수한다.

- [ ] fixture 및 native readback 확인
- [ ] 원인 분리 실행·raw 결과 분석
- [ ] 그림·설명·별도 검수

fixture의 넓은 range/0 초기각은 원인 분리용이다. 실제 humanoid의 하체 한계나 초기각을
바꾸도록 승인받은 것이 아니며, 이런 변경을 환경에 적용하지 않는다. 다중 hinge의 차이가
보여도 전체 모델의 불안정 원인으로 바로 확정하지 않는다. 기본 환경과 이전 결과를 보존한다.
fixture XML은 고유 결과 폴더에 기록하고 실제 시뮬레이션 소스 hash·원시 로그를 보존한다.
