# 현재 waist 자세 추가 완화 사전 검수 V1

요약 판정: **문제없음**. Critical: 0 / Warning: 0 / Suggestion: 0.

새 `WAIST_STRAIGHTEN_PLAN_V1.md`와 `search_waist_straighten_v1.py`의 기존 consumed 검색V3 대비 변경을 검수했다. 검색/native는 미실행이며 검수자는 지정된 이 기록만 생성했다.

## 확인 근거

- [search_waist_straighten_v1.py:18](/home/ajou/yigyu/3/stability_adapter_2/search_waist_straighten_v1.py:18): 기준 config는 이전 수락4° source, 실제 FK 기준은 `native_relief4_static` 초기 상태다. 이름 순서·81개 source 초기각/native 초기각이 exact하다. 현재 Chest localZ 전방 투영은61.412311100°다.
- [search_waist_straighten_v1.py:62](/home/ajou/yigyu/3/stability_adapter_2/search_waist_straighten_v1.py:62): world 휴머노이드 오른 수평축 양의 회전으로 뒤로 펴는 부호가 맞다. 추가4°/8° 목표의 Chest 투영은57.412311100°/53.412311100°이며 현재 대비4°/8° 감소한다. 누적 Torso/Spine/Chest 비율 .4/.75/1과 계획이 일치한다. body9 FK fit을 먼저 끝낸 후 body를 고정해 양팔/head만 맞춘다.
- [search_waist_straighten_v1.py:82](/home/ajou/yigyu/3/stability_adapter_2/search_waist_straighten_v1.py:82): Thorax0.3mm 강제 선호 잔차는 제거됐고 비겹침 최소 gap 잔차만 남는다. `inward_m=0`으로76행의 elbow 목표는 현재 origin이다.86행의 잔차는 현재 위치 선호이며 의무적인 기타쪽 접근 목표가 아니다.
- [search_waist_straighten_v1.py:114](/home/ajou/yigyu/3/stability_adapter_2/search_waist_straighten_v1.py:114): Thorax 최대3mm 및 elbow 축투영/거리감소 의무 수락 gate가 모두 제거됐다. 해당 측정값은115행의 기록으로만 남아 고아 코드가 아니다. body 방향/기울기·전체 source clear·모든 capsule 최소 gap·상완 근위 gap·전완 >12mm·waist·왼손목·head 방향·natural elbow·finger42·native limits 조건은 유지된다.
- [search_waist_straighten_v1.py:26](/home/ajou/yigyu/3/stability_adapter_2/search_waist_straighten_v1.py:26): anchor와 guitar XML의 발견 전 SHA, 발견값 재대조, 전체 SHA 저장 후 contract/FK/형상 helper 구축, 종료 전체 SHA 재검사가 유지된다. 동일 규칙으로 수집한 고유751개 입력 경로는 모두 존재하며 human37개·guitar XML69개·XML/manifest union70개 mesh를 포함한다.
- 초기 guitar p/q는 현재 native 기준으로 고정하고 lower/hip pose·finger42는 변경하지 않는다. body±.15/양팔±.4/head±.35rad의 모델 한계 교집합 및 elbow ±5° 여유를 유지한다. 수락 후보의 새 config는 기존 controller/PD/cap을 승계하고 elbow amplitude0을 사용한다. 후보는2개뿐이며 native 비교는 최대2회 정지5초다. 새 파동/학습/연주/기타 힘/부착/runtime pose 덮어쓰기 로직은 없다.

## 검증과 제한

Python AST 통과. 검수 시 `search_v1` 출력 폴더가 없었다. 이전 consumed source V3 SHA `290170c4e66041d0f75e0ede20a86f813224a641f85165854e2b23eba68ae1d5`는 이전 검수/실행과 exact하다.

기울기·입력 경로·기준 초기각 검산만 수행했고 source optimizer/전체 겹침 audit/native는 실행하지 않았다. 목표가 관절 범위 안에서 가능한지 및 실제 초기/5초 자세가 유지되는지는 후속 결과로 확인한다. 기존 Thorax 가상점 controller는 그대로이므로 CPU Thorax 근접 gate 제거가 실제 Thorax task 제거를 뜻하지 않는다. Source clear는 cooked 비관통·지속 지지를 인증하지 않는다.

검수 SHA256:

- 새 source: `484d0f54843a1303be325030739b338486bb9d46fa3828910676111e6ff7b251`
- 새 plan: `8a45f7c34753d6b95c9939eb38b8bfa049b62d8e2d656603750f56ccfd22ee08`

다른 담당자의 파일은 수정하거나 되돌리지 않았다.
