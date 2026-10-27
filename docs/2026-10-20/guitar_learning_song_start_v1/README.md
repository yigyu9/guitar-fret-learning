# 기본 손별 학습을 곡 단위로 전환

2026-10-20. 기본 실행은 합의035/v14 초기 자세에서 선택한 손으로 검수된 곡 전체를 학습한다. 이전 BC·전문가 모델·성공평가 gate를 새 기본 실행 전제로 요구하지 않는다.

```bash
python -m guitar_learning.train --hand left --song 05_BN2-131-B_solo --out /absolute/new_left_song
python -m guitar_learning.train --hand right --song 05_BN2-131-B_solo --out /absolute/new_right_song
```

실행 환경은 [학습 안내](/home/ajou/yigyu/3/guitar_learning/README.md)를 따른다. 기본67음 전부·500상태·39행동·1969tick/32.8167초이며 원오디오29.3064초+정책준비3초+말미0.5초를60Hz 경계로 올린다. native 대기는0초다.

기본 rollout은 한 곡 길이이며 --horizon을 줄여도 PPO 업데이트 사이에 같은 장면·곡 시계·음별 원장을 유지한다. 곡 종료/물리 실패 때만 reset한다. 왼손과 오른손은 각각 자기 손의 보상/전곡 성공으로 학습하고, 양손협응·strict50/100ms는 별도 진단이다. 이전563 단음 checkpoint는 새500 전곡 strict resume에서 거부한다.

[전곡 공용 코드](/home/ajou/yigyu/3/guitar_learning/song/README.md), [공용6모듈 이동표](move_map.json), [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261020_before_song_start/manifest.json)를 확인할 수 있다. task.py·music_task.py·song/__init__.py는 원문/경로를 보존했다. 기존 전문 도구의 gate·이전·joint 계약은 유지한다.

## 실행과 학습 계약

`train.py → training/start.py → training/runner.py`로 예산·선택 곡 입력·기존 PPO를 연결하고 `song/runtime.py`의 독립 native worker가 `HandSongEnvironment`를 만든다. 기본 설정은2환경·100업데이트·seed7·medium·자동 장치 선택이다. 설정을 영구 출력 경로에 저장하고 선택한 곡의 실제 파일 전부와 현재 소스를 pin한 뒤 native 작업자를 시작한다.

왼손 보상은 clean 유지·압현 달성·발음 중 오압현/미압현·접근·놓친 음이다. 오른손은 실제 기하 타현 달성·놓친 음·잘못된/반복 crossing·60Hz potential 차이 보상을 사용한다. 공통 행동 변화/실패 보상과 실제240Hz 안전 비용은 그대로다. 선택하지 않은 손의 보상은 학습에 넣지 않으며 비활성 손의 정책 행동은 물리 실행 전에 정확히0인지 검사한다. 손별 전곡 성공은 전곡 종료·안전과 선택한 손의 전체 음 달성을 요구한다. 양손 협응 성공과 원strict50/100ms는 진단으로 유지한다.

같은 프로세스의 짧은 rollout은 곡 중간에서 이어진다. 새 프로세스의 --resume은 모델·optimizer·부모 RNG를 복원하고 초기 자세에서 새 곡 에피소드를 시작한다. 저장하지 않은 native 중간 장면을 복원했다고 주장하지 않는다.

## 검사 결과

[CPU 관련 검사25개](targeted_tests_final.log), [모듈별122개/702검사](module_tests_final.json), [도구 도움말54개](cli_help.json)가 통과했다. 모듈마다 별도 프로세스로 검사했으며 단일 프로세스 discover 전체 통과와 구분한다. 기존 JSON/float 표현 SIGFPE의 원인 해결을 주장하지 않는다. 초기 progress 집계 helper는 `Ran 1 test` 단수형2개를 합계에서 빠뜨렸으며, 최종 결과는 실제 각 로그의 단·복수형을 모두 읽어702개로 검증했다. 검사 실패나 검증 조건 변경은 없었다.

[등록곡 입력 감사](song_inputs.json)에서 지원5곡의 모든 원음표 coverage와 관측64슬롯 용량을 확인했다. 미지원3곡은 이유를 기록했다. 현재 측정이 지원하는 등록된 fretted 곡만 지원하고 개방현/unsupported gesture나 입력 누락을 자동 생략하지 않는다. [입력/보관 검증](preservation_verified.json)과 [현재 소스](source_manifest_final.json), [공용 의존 관계](dependencies.json)를 기록했다. 기본 학습은 tool을 import하지 않는다.

새 손별 환경 검사는500상태·67음·1969tick·native0·반대 손0·선택 성공의 독립성·보상/episode 합·실패 양성 억제/비용1회·rollout 시계 지속·예외 후 재적분 차단을 확인한다. 기본 실행 검사는 다른42음 곡의 선택과 실제 입력 pin, 자동 길이1074tick, 지원되지 않는 입력 거부,563 단음 모델의500 전곡 strict load 거부와 대상 Tensor 무변경을 확인한다.

## 실제 native 결과

rl38·CPU정책·small모델·1환경으로 실행했다. 모든 실행은 입력 변경0·물리 조건 오류0·persistent 감사 통과·모델 저장을 확인했다. 아래는 실행 연결/완주 증거이며 음악 수렴은 아니다.

| 실행 | 수집 길이·업데이트 | 전이 | 최종 PPO 업데이트 | 전곡 안전 완주 | 손별 전곡 성공 |
|---|---|---:|---:|---:|---:|
| [왼손](native_left_v1/report.json) |512tick×4|2048|4|1|0|
| [오른손](native_right_v1/report.json) |기본1969tick×1|1969|1|1|0|
| [왼손 재개](native_resume_v1/report.json) |20tick×1추가|20|5|0|0|

[실제 시계 검증](native_timelines.json): 왼손512→513에서8.5333→8.55초,1024→1025에서17.0667→17.0833초,1536→1537에서25.6→25.6167초로 연속 진행했다. 좌우 각각1969tick/32.8167초에서 timeline_complete로 전곡을 마쳤고 종료 episode의 per_note에67개 목표가 모두 있다. 왼손의 남은79전이는 초기 자세에서 새 에피소드를 시작한 부분 구간으로 완주에 추가하지 않았다.

[재개 비교](resume_parity.json): 기존 전곡 final.pt와 재개 initial.pt는 metadata를 제외한 전체 payload가 정확히 같다. identity·model·양 optimizer·cost_weight·업데이트 수·Torch/NumPy/Python/CUDA RNG가 보존되고 이후 업데이트4→5를 확인했다. 새 프로세스의 물리 시계는0에서 시작하며20전이를 전곡 완주로 세지 않는다.

## 보관과 검수

변경 전459개 원문을 원경로/SHA로 보관하고 CAS에 등록했다. 기존2,483개 version/default metadata를 유지했고 현재2,593개 object와2,737개 버전의 참조/바이트를 확인했다. 공용6모듈은 이동과 import만 바뀌었으며 task.py·music_task.py·song/__init__.py 원문과 기존 전문 경로의 gate/Actor 이전은 유지한다. native190개 provenance 원문은 그대로이고 tool18개의 현재 안내 SHA를 갱신하면서 원본 SHA를 유지했다.

[종합 검증](verification.json)은 현재396개 소스 집합·SHA, 선택 곡/보상/시계와 세 실제 실행을 검사한다. [독립 검수](review.md) 결과도 함께 기록한다. 과거 입력 증거·실행 결과·checkpoint는 수정하지 않았다.
