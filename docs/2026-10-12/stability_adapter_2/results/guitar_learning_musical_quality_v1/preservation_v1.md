# 음악적 품질 버전: 보존 감사

최종 보존 검사 통과.

- 현 source148개·v1원형148사본·v2사본148개 모두 SHA 일치. snapshot v1→v2의 유일한 차이는 MUSICAL_QUALITY.md의 설치 환경 bin PATH 두 줄이다.
- 이전14개 보관본 모두 정확하다. 원본 위치에서는 README·AGENTS의 권장 경로 문서만 예상대로 갱신됐으며 이전 production Python/config/test는 유지됐다.
- PATH 교정 전 MUSICAL_QUALITY.md의 별도 archive SHA도 정확하고 source_v1 사본과 일치한다. 코드 변경으로 Ninja 실패를 덮지 않았다.
- 이전 actionable phase의 frozen learning Python115개와 최종 봉인 proof10개가 그대로다. 실제 import한 외부 native Python63개도 이전 입력 pin과 일치한다. 과거 수천 파일 전체 해시는 이번에 중복하지 않았다.
- 기존 실패 CPU 로그를 보존했으며 최종 CPU297개 통과 로그와 SHA를 별도로 기록했다.

## 보존한 시작 실패

left_native_train_v1은 gymtorch C++ extension import에서 `Ninja is required to load C++ extensions`로 실패했다. 전이0·native_current_step=None·headless_description=None이며 lifecycle 파일도 생성 전이어서 없다. 이 실패를 완료된 native scene으로 세지 않는다. PATH 보완 후 새 left_native_train_v2로 재시도했으며 원 실패 보고서·입력·로그는 보존했다.

| 새 실행 | 상태 | 입력 SHA | 종료 scene | scope |
|---|---|---|---|---|
| left_native_train_v2 | completed | 1661 | True | 완료는 보존/실행 종료이며 품질 성공과 구분 |
| right_native_train_v1 | completed | 1661 | True | 완료는 보존/실행 종료이며 품질 성공과 구분 |
| left_native_eval_v1 | completed | 1629 | True | 완료는 보존/실행 종료이며 품질 성공과 구분 |
| right_native_eval_v1 | completed | 1629 | True | 완료는 보존/실행 종료이며 품질 성공과 구분 |

현재 확인된 생성/종료 scene은 4/4개, PPO update2·전이840개·결정적 평가2회다. 실제 준비0초·관측563(기존536+quality27)·출력39, 양손 별도 비활성 action0을 검사한다. Reset 경계는 local step0이며 누적 native시각7초는 정상이다. Guard의 경계 상태복원·기존 물성·원래105/97/8은 원자료에서 가능한 범위로 확인했다.

실제 import 목록이 있는 학습에서는 archive import0과 금지 호출0을 확인했다. 평가 producer가 별도 runtime census를 제공하지 않으면 이를 실측0으로 꾸미지 않고 source_unchanged와 동일 builder 연결 증거로 구분한다.

모델 출처 checkpoint update1을 새 Actor 초기화로 이전했으며 새initial은0, final은1이다. 기존 source/model byte를 바꾸거나 출처 update를 누적하지 않았다.

이 감사는 소스·입력·기존 결과·native수명 보존에 관한 것이다. 새 품질 기준의 성공/실패·압력·음향·일반화는 별도 분석 범위다.
