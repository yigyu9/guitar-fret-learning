# 오른 허벅지 waist source2 사전 검수

판정: **문제없음 — CPU 탐색 차단 없음.** 현재 Critical 0건, Warning 3건, Suggestion 0건.

[source2:38](/home/ajou/yigyu/3/stability_adapter_2/search_right_thigh_waist_v2.py:38)은 humanoid compiler.meshdir 기준 실제37개 mesh, config.json/원 기타 XML 및 거절 seed85 audit를 SHA 목록에 포함한다. source1 원본을 보존하며 이 seed는 숫자 시작점으로만 사용하고 모든 최종 gate를 재검사한다. source1의 완전 입력 봉인 미달을 소급해서 해결했다고 설명하지 않는다.

새3개 right/front 배치의 brent 구간 [−20,+120]mm에서 minHipgap−0.3mm 부호 전환을 순수 형상 산술로 확인했다. waist profile 최소 반폭+5mm 구간과 positive Gx 조건, RHip0.05~4mm, 최종6caps≥0.05mm/전체 LP, Thorax<6mm·근위0~30% Shoulder<4mm·forearm>12mm, 자연 형상·왼 wrist<5mm/Head·wrist 방향<1°, frozen42·모델 한계 및 Elbow_y ±5° 여유가 유지된다. 초기 body/right/left/head 범위 확대는 모델과 교차한다. 기타 회전은 원 seed 값을 유지하고 새 p·전체 predicted guitar states와 genuine human FK를 갱신하며 기존 helper witness 키도 유지한다. AST 검사를 통과했다. native runner 검수와 실제 후보 수락은 별도 단계다.

## Warning

- [source2:46](/home/ajou/yigyu/3/stability_adapter_2/search_right_thigh_waist_v2.py:46): 앞30/50mm 추가분은 **world +Y**다. 실제 수평 앞축 cross(up,right)≈[−.03865,.99925,0]와 약2.2° 차이가 있으므로 순수 humanoid-forward 이동으로 확대하지 말고 전체 world delta를 제시한다.
- [source2:84](/home/ajou/yigyu/3/stability_adapter_2/search_right_thigh_waist_v2.py:84): waist neck-axis 구간·positive Gx와 full Hip 최근접점은 source 배치 proxy다. min 양 Hip0.3mm/RHip<4mm만으로 오목한 waist가 cooked 허벅지에 안정적으로 걸쳤다는 뜻이 아니다. 실제 접촉점·기타 변화·왼손 기여를 후속 native에서 확인한다.
- [source2:89](/home/ajou/yigyu/3/stability_adapter_2/search_right_thigh_waist_v2.py:89): 초기 body/right와 보상 각도까지 바꾸므로 위치 하나의 인과효과나 runtime body .08rad 유지 인증으로 해석하지 않는다. 상속된 `left_neck_near` 등 과거 seed 측정은 역사 정보이며 새 실제 면 거리 측정으로 재사용하지 않는다. 새 q/p와 예측·source gate가 권위다.

검수 SHA-256: source2 `682596925b334fbff69bf20480c2551c4cf71258da58609f3df250fdc8e3322d`, PLAN_V2 `a717925a70e67a2d4de94f4842606fbfc830c7df156ab68dc454fa3e81cf28b9`.

다른 소스·원자료·기존 결과/리뷰를 수정하지 않았고 새 탐색·물리·정책 추론/학습은 수행하지 않았다. 결과 수락·실제 cooked 상태·최종 보존 봉인을 선인증하지 않는다.
