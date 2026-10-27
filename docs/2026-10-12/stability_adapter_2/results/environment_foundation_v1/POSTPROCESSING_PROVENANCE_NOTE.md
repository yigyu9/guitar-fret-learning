# 시각화 중간본 보존 누락 기록

확인 범위: 이번 phase의 설명용 몽타주 생성기·몽타주·producer manifest에 한정한다. 시뮬레이션 원자료, 초기값, 상태/관측/명령, native 프레임·영상, 기존 실험은 변경되지 않았다. 현재 최종 이미지·원본 프레임·manifest의 SHA 대조는 통과했다.

산출물 담당자는 최초 그림의 캡션 간격을 수정하면서 성공한 중간 생성기·그림·manifest를 별도 보존하지 않고 같은 작업 경로에서 재생성했다고 보고했다. 이는 프로젝트의 소비된 소스/출력 보존 지침을 지키지 못한 것이다. 이전 bytes가 없으므로 원본 보존이나 중간 실행의 독립 재현을 확인했다고 주장하지 않는다.

아래 중간 SHA는 담당자의 보고값이며, 보존된 원본과 독립 대조할 수 없다.

- 최초 PNG:2399×915, `b3a3006da3e298b69e17121a1f87949f69af0b46ed7cc8c9ac2a58982a8c032f`.
- 중간 generator:`63aab0bc342c8a775a6a777dabdbe415ba2e40c069b0e437626a9bd0eb3bf2f7`.
- 중간 manifest:`32021200624951dbc69e64e170fbb18b0f109a18e1297c93e77549f7ce544678`.

현재 보존된 최종 PNG는2399×945/SHA`ec3bba7ed3477421c815b6fca561e9dfcf1236f07c0332774043be60fb8066ec`, generator는`ce00f8dd142cc8bf07b526210e7fd755cc284313ac6be6f2d345521f754fe60c`, manifest는`80f3f38079034962a6d00499838751113c8e31a3b6b5ba4e6d6715679877b644`다. 캡션 간격과 감사 metadata 수정이며 native 렌더/물리 실행 결과를 새로 생성한 것은 아니다.

이후 시각화에서도 첫 실행부터 별도 attempt 디렉토리를 사용하고, 성공한 생성기·입출력·manifest를 보존한 뒤 새 경로로 수정한다. 현재 봉인된 파일은 수정하지 않는다. 기존 final_verification.json/artifact_inventory.json은 최초 마감 이력으로 보존하고, 보존 누락을 반영한 final_verification_v2.json/artifact_inventory_v2.json을 추가한다.
