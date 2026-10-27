# V13: 상완 normal preload 감소와 읽기 전용 접촉력 관측

V12는 실제5초를 완료했고18 gate 중 가슴·상완 동시접촉95%만 실패했다. 기타 회전 최대1.493°/body 이동5.956mm/Spine4.860°와 양발은 통과했다. 마지막1초 Chest source gap 평균은 V11 0.0822084mm에서 V12 0.0661187mm로0.0160897mm 줄었다. paired240표본은 모두 개선됐지만 동시접촉 유지에는 부족하다.

## 원인 진단과 선택

오른상완의 실제 material point는 수정 목표 방향으로 평균98.9% 추종했다. 따라서 이를 인체 제어의 처짐으로 설명하거나 접선 목표를18배 늘리는 방법을 채택하지 않는다. 기하 query와 달리 접선 이동이 기타 pose로 강체 전달되지 않았다. 캡슐 접촉 패치의 구름·미끄럼 가능성은 아직 가설이다.

실제 V12 마지막 오른 task의 **인체 가상 요청**은 W=[−2.16965,+2.01224,−6.74592]N, source normal 성분−7.0318N/tangent2.1950N이다. 이것을 실제 기타 접촉력으로 부르지 않는다. 기타 전체 applied39 body 질량은4.64871573kg(중량45.6039N)이며 imported root 한 body의5.43N과 구분한다. 이번에는 오른상완의4mm human preload를2mm로 줄여 하향 요청을 줄이는 단일 제어 비교를 한다. 같은 상태의 계산상 하향 요청은 약2.779N이지만 실제 새 평형은 별도 시험한다.

초기 source4/상체 target2/오른팔 affine correction과 palm·material IK 목표/Chest7→9mm/모든gain·cap·rate/유한 하체·발/Root·cube/Gfree·gravityON·strapOFF를 그대로 유지한다. task goal만 `material + .5*(taskgoal−material)`로 바꾼다. 기타 직접힘·고정·부착·매step 상태 쓰기는0이다. 상완 접촉이 약해질 위험이 있으므로 가슴뿐 아니라 기존 전체 조건을 모두 요구한다.

## 관측과 판정

새 read-only native net-contact-force tensor를240Hz 기록한다. 원 body 인덱스 DOMAIN_SIM과 이름을 닫고, 원 CC_LAST_SUBSTEP/substeps 설정을 바꾸지 않는다. tensor는 제어에 사용하지 않는다. 원 raw contact λ는 계속 단위변환하지 않는다. 전체G39 body의 applied 질량과 COM 속도 차분으로 `ΣFcontact + Mg − ΣmΔv/dt`의 시점·world·SI 정합을 진단한다. 마지막1초 residual RMS≤2N을 관측 유효성 기준으로 미리 둔다. 초과하면 관측 제한을 공개하고 이 센서로 하중 결론을 확정하지 않는다. 이를 기존 동적 성공 기준의 완화에 쓰지 않는다.

1. 새 runtime/run/analyzer v15와 `static5_v13.json`을 검수한다. 실제 native12 schema를 바탕으로 CPU 사전 검사를 한다.
2. `native_static_v13`에서5초를 검사한다. 기존17개 실제 기준과 human 목표 연결 검사를 유지하고2mm preload·센서 map/finite/step 정합을 별도로 확인한다.
3. V12 대비 실제G·Chest/상완/Spine/Rhip·하체·접촉력을 비교하여 normal 하중 분배의 효과와 한계를 기록한다.
4. 전체 통과 시 동일 재현 후 압현·타현, 이어 왼손 해제15초를 검사한다. PPO는 시작하지 않는다.

- [ ] 신규 코드/입력·사전 검사/독립 검수
- [ ] 실제5초 전체 판정과 센서 유효성
- [ ] 하중 분배·접촉 전환의 실제 비교 기록
- [ ] 통과 재현→압현/타현→왼손 해제

소비한 leaf·입력·실패·결과는 수정하지 않고 다음 기록을 새 파일로 남긴다.
