# 진입 회전 여유 사전 검수

판정: **PASS — 문제없음**. 현재 Critical / Warning / Suggestion 없음. native 실행은 하지 않았으며 실제 PLAY 전환·종료·영상은 후속 검수 대상이다.

- [회전 helper](/home/ajou/yigyu/3/stability_adapter_2/strike_entry_rotation_margin.py:8)는 위치 box를 유지하고, 원래 Euler bounds 안에 찾은 reference와 native quaternion의 SO(3) 거리가 0.1° 이하일 때 추가 진입을 허용한다. 저장된 v1 step480 자세에서 reference bounds와 거리 **0.028953971651982085°**를 독립 재계산했다. 위치 밖·큰 회전 이탈 거절도 순수 함수 AST 실행으로 확인했다. 두 seed의 bounded 최적화는 찾은 reference에 대한 증거이며 전역 최근접 보장은 아니다.
- [runner 변경](/home/ajou/yigyu/3/stability_adapter_2/run_strike_two_second_episode_v2.py:279)은 PREPARE이고 물리 시간 2초 이상일 때 진입용 판정만 추가한다. 기존 strict 판정 row·위치·손 조건·25mm 준비 거리·2/10초 시간·원본 source clock/성공/실패 기준은 유지한다. `advance` / `integrate` / `sample` / `left_target` / `submit`의 AST는 v1과 동일하다. wrapper는 새 모듈 선택만 바뀌며 보존·입력 봉인 방식은 같다.
- [계획](/home/ajou/yigyu/3/stability_adapter_2/STRIKE_TWO_SECOND_BOUNDARY_MARGIN_PLAN.md:5)과 main PLAN/README 추가 절은 실제 범위를 넓히는 실험임을 명시하고, 수치 오류 수정·전역 최근접·물리 성공으로 과장하지 않는다. 초기값·PD·기타 힘/pose 제어 변경은 없다.
- [분석기 v2](/home/ajou/yigyu/3/stability_adapter_2/analyze_strike_episode_v2.py:26)는 요청 actor 행과 info가 있는 완료 행을 분리하고 pulse를 완료 행에서 합산한다. 실제 분리 AST에 요청 2개/완료 1개의 부분 자료를 넣어 이전 Warning의 해당 경계 해소를 확인했다. 초기화 전에 실패해 필수 raw 자체가 없는 경우까지 요약하는 분석기는 아니다.

Python 3.8 AST 문법 통과. 검수 전·후 아래 코드/계획과 보존 v1 runner 등 6개 입력 SHA가 동일했다. [root preflight](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strike_two_second_episode_v2/boundary_margin_preflight.json)의 소스 SHA와도 일치한다.

| 파일 | 검수 SHA256 |
|---|---|
| 회전 helper | `3dd77ecc5f71c920dd5f8f7fd5ef4f4ffbdd8baa05cce5adebf5de30654d7f20` |
| v2 runner | `d727a9ddb61b09424b59c9e1d2ccefecfec0a76acf158bf30fe0a6aba2d79383` |
| v2 wrapper | `f42294c7c760bc2d94e29a96069e2e114e06202e7b2a49c5e8ebb2283ea8aafe` |
| v2 계획 | `5068773efdb92d0ef3996a0377f6b63c607a39328cbd475b369a88594c6db937` |
| v2 분석기 | `980e22c6be9ed666d2cf808fa2eb2b6499ff557818a33629201a38fe8206f2da` |

검수의 native 초기화·물리 실행·다른 파일 변경은 0이다. 기존 v1 준비 timeout 자료는 새 진입 여유의 실행 결과와 구분해 보존해야 하며, 실제 성공 여부는 아직 미검증이다.
