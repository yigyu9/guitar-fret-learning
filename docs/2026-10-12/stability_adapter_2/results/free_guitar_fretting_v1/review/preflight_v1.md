# 압현 접촉 후보 측정 사전 검수

**판정: 문제없음.** `fretting_v1.py`, `fretting_environment_v1.py`, `run_fretting_probe_v2.py`의 제한된 native 측정 실행을 진행할 수 있다. 실제 측정 결과나 압현·음악 성공을 미리 인증하는 판정은 아니다.

원 `run_fretting_probe_v1.py`의 영상 helper import는 과거 native expected map에 없는 의존성을 원 runtime으로 분류하여 물리 실행 전 실패할 수 있었다. 두 원 manifest 모두 해당 영상 파일이 없음을 직접 확인했다. v2는 이 import를 제거하고 원 attempt/wrapper SHA 병합·충돌 검사를 자체 수행한다. 원 runtime/assets의 expected SHA 및 새 의존성의 전후 pin은 유지된다.

측정은 지정 손가락의 실제2/3 body와 허용 기타 root/해당 fret body, raw lambda 양성, 양측 feature 일치, 현재 기타 좌표의 목표 현 lane·높이·유한현·프렛구간을 함께 검사한다. COM을 접촉 feature 좌표에 더하지 않는다. 현은 비평행·비균등이므로 실제 feature y에서 각 현 위치를 평가하며 동률 lane은 거부한다. 프렛선 접촉 허용 구역과 중점 접근 proxy를 구별한다. distal origin을 pad로 부르지 않고 실제 현 압력·음향 성공을 주장하지 않는다.

시간 추적은 연속 양성 표본 사이의 구간만 누적한다. N개 표본의 dwell은 `(N−1)/240`이며 fractional note 경계를 격자에 반올림하지 않는다. 누락·중복/역순·목표 변경·접촉 소실을 구분한다. 50ms dwell 획득과 짧은 note의 관측 hold 비율은 별도 지표다. 후자는 표본 사이 관측 구간의 지표이며 solver 내부의 연속 접촉을 직접 측정한 것으로 해석하지 않는다.

adapter는 실제 post-fetch 상태와 raw contact를 같은 step에 읽고 조회 전후 상태 불변을 검사한다. 내부 last-substep feature의 정확한 생성 시각은 미인증이라고 표시한다. 원 제어·준비 절차를 변경하지 않는다.

독립 CPU 검증: `PYTHONDONTWRITEBYTECODE=1 /home/ajou/miniconda3/envs/rl38/bin/python -m unittest stability_adapter_2.free_guitar_learning_v1.test_fretting_v1 stability_adapter_2.free_guitar_learning_v1.test_fretting_environment_v1 -v` → **12 tests, OK**. 기존 stage1 테스트나 물리 실행은 반복하지 않았다.

| 파일 | SHA256 |
| --- | --- |
| fretting_v1.py | `bcd9d050e61627501a54cc8d13221af8b4198bd2441645907c12602e2fe8ec04` |
| test_fretting_v1.py | `18ffe870dba4ef019be18cfc843a77aac37468a3b10b86f873a8ab3d9002cf05` |
| fretting_environment_v1.py | `f17e505f145d65842834068fa00496f2bf309c9d62011dfc52dcc32c701f3321` |
| test_fretting_environment_v1.py | `e4dde3752578ca5000db79aa5e1dd4891a86f8cbd7e9cf6d7b017585b75ddc67` |
| run_fretting_probe_v2.py | `45ef2436506537075cb7af237002986b48868f0b46b59374d629af79b62f5a43` |

선택한 string1/fret5/index는 기존 준비 접촉에서 고른 진단 대상이다. 고정 임계값과 해당 접촉을 검증하는 제한된 시험이며 다른 프렛 도달성, 악곡 수행, 일반적 압현 성공 또는 PPO 결과로 확대하지 않는다.
