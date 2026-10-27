# 다른 면 받침 source 탐색 사전 검수

요약 판정: **CPU 후보 탐색은 문제없음. 기존 native 연결은 수정 필요.** Critical 1건(기존 helper 재사용 시), Warning 2건, Suggestion 0건. 탐색 결과와 native 실행은 이 검수 시점에 미검증이다.

## Critical

- [search_right_block_cradle_v4.py:100](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v4.py:100), [right_block_effort_v6.py:24](/home/ajou/yigyu/3/stability_adapter_2/right_block_effort_v6.py:24): 새 후보 row는 중간 35~65% witness를 `upper_arm_support_witness`/`proximal_upper_arm65_witness`에 저장하지만 기존 native helper는 없는 `proximal_upper_arm30_witness` 키를 직접 읽는다. 그대로 연결하면 초기 기록기 구성에서 KeyError가 발생한다. CPU 탐색에는 영향이 없으며, native 연결 전에 새 helper에서 실제 중간 witness와 구간을 명시적으로 선택해야 한다. 소비된 기존 helper나 30% 의미를 덮어쓰지 않는다.

## 확인한 정확성

[부분 캡슐 구성과 fraction 변환](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v4.py:28)은 원래 축의 35~65%로 끝점만 줄이고 반지름을 유지한다. 반환 fraction을 `.35+.3*t`로 원래 축 좌표에 복원하며, 최종 `.36<f<.64` 조건은 잘린 끝점의 구면을 full capsule 표면으로 오인하는 경우를 배제한다. 동시에 full R_Shoulder와 나머지 명시된 5개 analytic capsule 간격 및 전체 mesh LP 감사를 통과해야 한다.

[최종 float32 gate](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v4.py:80)는 법선 Gz(T≤−.4/U≥.3)·각도≥55°, Thorax≤6mm/중간 상완≤4mm, 전완≥12mm, 자연 팔 형상·Head/왼 wrist 회전≤1°·왼 wrist 위치<5mm, 모델 한계·손가락42 exact를 확인한다. 기타 p/q는 원 seed 배열을 보존하고 genuine calibrated FK로 predicted poses를 생성한다. source 입력 before/after SHA 검사와 새 출력 디렉터리의 배타 생성도 유지된다. 새 Python AST 검사를 통과했다. 새 실험·소스 수정은 하지 않았다.

## Warning

- [계획:5](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_BLOCK_CRADLE_FACE_WRAP_SOURCE_PLAN_V1.md:5): rear/front corner 및 axis 목표는 source 가설이다. 최종 법선과 구간 gate를 통과해도 actual cooked 접촉·지지력·force closure·팔꿈치 동작 유지가 인증되지는 않는다. 후보가 수락되면 native 초기 형상과 실제 접촉 위치를 별도로 확인해야 한다.
- [search_right_block_cradle_v4.py:66](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v4.py:66), [같은 파일:73](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v4.py:73), [같은 파일:79](/home/ajou/yigyu/3/stability_adapter_2/search_right_block_cradle_v4.py:79): `max_nfev=90`은 주 fit의 solver 평가 제한이며 numerical Jacobian 호출과 별도의 왼팔80/Head90 평가를 포함한 전체 실행 시간 상한이 아니다. CPU 작업량 설명과 실제 완료/중단 기록을 구분한다.

## 검수 SHA-256

| 파일 | SHA-256 |
|---|---|
| search_right_block_cradle_v4.py | 954c2338130b1ee79e0d6f46f4600edd837224063e358e43f21016260aea701f |
| RIGHT_BLOCK_CRADLE_FACE_WRAP_SOURCE_PLAN_V1.md | d0f618e7c64dbd00b3210f9a46874eabc0c517e6082f74de378ad4594fb5941d |

검수 범위는 새 계획·source 코드·부분 캡슐 query 및 현재 native helper의 witness 계약이다. 광범위한 과거 데이터 재감사·최종 보존 봉인은 수행하지 않았다.
