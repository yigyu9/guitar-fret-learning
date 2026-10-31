# 손가락 직접 위치 제어 전환 완료

GPU 왼손 손가락21축은 **목표각 직접 지정(position)**만 사용한다. 행동0은035/v14 준비 기준각, -1/+1은각 관절의native하한/상한 요청이다. 같은 행동을 반복하면 같은 목표각을 요청하며 행동값을 목표각에 계속 더하지 않는다. 이전 목표각은4rad/s의 변화 제한에만 사용한다. 전체 가동범위·PD·힘 상한·보상9개·손가락 움직임 비용0은 유지했다.

누적 제어 분기·전용 계약·누적 역변환·선택 옵션과 전용 검사는 활성 경로에서 제거했다. 변경 전281개 Python과문서를 합친310개 원문은 [보관 안내](/home/ajou/yigyu/3/guitar_learning/archive/20261029_before_direct_finger_control_v1/ARCHIVE_INDEX.md)와SHA manifest에 보존했다. 팔/손목 DLS 보정·발 IK·로그와 보상의 증분 집계는 별도 기능이므로 유지한다. 과거 봉인된 docs 진단 자료와checkpoint는 원문을 바꾸지 않았다.

## 검증

| 확인 항목 | 실제 결과 |
| --- | --- |
| 관련 CPU 검사 | 62개 통과 |
| 전체 CPU 검사 | 917개, 신규 회귀0. 변경 전부터 있던24개 실패는남아 있음 |
| GPU 직접 제어 | 8환경·960제어tick(16초)·환경별3840물리step, 유지/반전/B 자세·초기화 통과 |
| GPU 목표각 검산 | 직접 위치 요청식과 최대오차0rad |
| 기본 학습 | large·128환경·H32·8업데이트·32768전이, 정상 종료·저장 |
| 저장본 재개 | 같은 계약으로2업데이트 추가·8192전이, 누적40960전이 |
| 별도 저장본 평가 | 4환경·4에피소드·phrases, 정상 종료 |
| 입력 보존 | GPU검증 전후 현재281개 Python SHA 변경0, 보관310개 SHA 일치 |

[검수](REVIEW.md) · [검증 요약과 근거 SHA](verification.json) · [전체검사 전후 실패 비교](cpu_comparison.json)

전체 기준 검사는 변경 전923개에서1 failure/24 error였다. 현재917개에서1 failure/23 error이며 구형codec거부 검사를 현행계약으로 정리하면서 기존1개 error가 해소됐다. 남은 실패는 대부분구형thumb관측계약 fixture, 정리된 역사자료3개, 과거진단schema 기대값이다. 현재정책/계약검사를 완화하거나 해당검사를 숨기지 않았다. 상세는cpu_before.log/cpu_after_final.log에 남겼다.

이 검증은 제어·학습 실행·저장·재개의 정상 작동 확인이다. 압현 성공률이나 자연스러움의 장기 개선을 입증한 학습은 아직 하지 않았다.

## 실행

기본 명령은 그대로이며 직접 제어가 자동 적용된다.

```bash
python -m guitar_learning.train --size large --num-envs 128 --horizon 32 --updates 100 --out NEW
```

단음 도구는short_finger_learning.v3/short_finger_policy.v3이고position·초기std0.01이 기본이다. teacher/reference.v2는 원래 형식을 유지한다. 구형 누적 설정과checkpoint는 현재 직접 제어로 재개하지 않는다.
