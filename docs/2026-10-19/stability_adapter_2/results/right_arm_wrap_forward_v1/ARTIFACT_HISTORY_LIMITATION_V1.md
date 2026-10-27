# 그림 후처리 실패 이력의 보존 범위

산출물 담당자가 build_upper_timeline_v4.py 첫 실행에서 capture 조회의 StopIteration으로 중단한 뒤 같은 파일을 수정해 성공 실행했다. 첫 실패 당시 producer 원문과 before SHA는 저장되지 않았다. 따라서 그 실패 소스가 보존됐거나 사전 입력 봉인이 완전하다고 주장할 수 없다. 실행 소비본을 새 버전으로 보존하는 작업 지침을 어긴 후처리 이력이다.

이 실패는 PNG/provenance 출력 이전이며 물리 시뮬레이션 실행이 아니다. 실제 Isaac Gym source/config/초기·경과 상태/원본 PNG/영상은 그대로 보존됐고, 정상 완료한 현재 producer와 해당 원프레임·capture·font 입력의 before/after SHA 및 출력 SHA는 provenance_upper_v4.json에서 검증했다. 이 정상 실행 기록으로 첫 실패의 누락을 소급 채우지 않는다.

수치 결과와 현재 정상 비율 이미지의 검증, 첫 실패 소스 이력의 미보존을 구분한다. 다음 산출물 재시도에는 실패 단계라도 최초 실행 전에 producer 원문·SHA를 디스크에 보존하고 새 버전으로 실행한다.
