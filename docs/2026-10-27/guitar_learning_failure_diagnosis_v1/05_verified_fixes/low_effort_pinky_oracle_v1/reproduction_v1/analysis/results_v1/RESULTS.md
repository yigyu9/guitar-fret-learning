# 소지121 새4시도 재현

기존grid의1시도와분리한새4첫시도(실패포함)이다. 원acceptance는 **PASS** 이다.

| 달성/4 | 평균 clean/wrong | 물리/손목실패 |
|---:|---:|---:|
| 4/4 | 1.000000/0.000000 | 0/0 |

env0 음중 actual4°: 87.3995, -7.8693, 25.1211, -2.7320; target4°: 87.9429, -5.3658, 25.3122, -2.6526; 세마디순힘평균N: 0.0000, 0.0000, 1.1254; 손목mm/°: 8.9781, 1.2782.

candidate/wrong·CPU6gate/오현·오프렛·arm actionbound 요약은 comparison.json에기록했다. 다른3환경상세힘/nativeqd는없으며추정하지않았다. 원240Hz음원장/9보상을60Hz기하로재지급하지않았다.

| env0 LH body | 음중표본 | 평균/p95/최대 N |
|---|---:|---:|
| human/LH:palm | 17 | 0.0000, 0.0000, 0.0000 |
| human/LH:thumb1 | 17 | 0.0000, 0.0000, 0.0000 |
| human/LH:thumb2 | 17 | 0.0000, 0.0000, 0.0000 |
| human/LH:thumb3 | 17 | 4.7352, 5.2315, 5.2569 |
| human/LH:thumb_pad | 17 | 0.0000, 0.0000, 0.0000 |
| human/LH:thumb_top | 17 | 0.0000, 0.0000, 0.0000 |
| human/LH:index1 | 17 | 0.0000, 0.0000, 0.0000 |
| human/LH:index2 | 17 | 1.9230, 1.9381, 1.9385 |
| human/LH:index3 | 17 | 1.8497, 1.8734, 1.8764 |
| human/LH:index_top | 17 | 0.0000, 0.0000, 0.0000 |
| human/LH:middle1 | 17 | 0.0000, 0.0000, 0.0000 |
| human/LH:middle2 | 17 | 0.0000, 0.0000, 0.0000 |
| human/LH:middle3 | 17 | 0.0000, 0.0000, 0.0000 |
| human/LH:middle_top | 17 | 0.0000, 0.0000, 0.0000 |
| human/LH:ring1 | 17 | 0.0000, 0.0000, 0.0000 |
| human/LH:ring2 | 17 | 0.0000, 0.0000, 0.0000 |
| human/LH:ring3 | 17 | 0.0000, 0.0000, 0.0000 |
| human/LH:ring_top | 17 | 0.0000, 0.0000, 0.0000 |
| human/LH:pinky1 | 17 | 0.0000, 0.0000, 0.0000 |
| human/LH:pinky2 | 17 | 0.0000, 0.0000, 0.0000 |
| human/LH:pinky3 | 17 | 1.1254, 1.3275, 1.3408 |
| human/LH:pinky_top | 17 | 0.0000, 0.0000, 0.0000 |

기존소지reference4/zero4·gridbaseline112·gridselected121은별도출처로보존했다. 같은seed7의4환경이지4seed가아니다. 새reference는sourceactual이아닌선정유한목표이며zero명령에서는사용하지않는다. body순힘은접촉쌍/현압력/모터토크가아니며고정기타/noNN재현을정책학습·자유기타·생산채택성과로확대하지않는다.
