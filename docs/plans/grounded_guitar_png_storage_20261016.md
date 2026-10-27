# 완료된 동일 PNG의 저장 공간 공유

추가 실제 시험과 보존 봉인에 필요한 공간이 부족하다. 읽기 전용 조사에서 현재 phase의 완료 native 영상 PNG에는 약1.70GB의 동일 내용 중복 저장이 있다. 다른5개 sealed phase·코드·설정·raw는 건드리지 않고 현재 phase의 완료 native 영상 프레임만 같은 내용의 파일끼리 hardlink로 저장 공간을 공유한다. 모든 논리 경로·PNG bytes·SHA는 그대로 유지한다. 새 실제 렌더를 생략하거나 다른 실험 프레임으로 대신하는 작업이 아니다.

1. 완료 report·support_wrapper가 존재하는 현재 phase native 디렉토리의 media/frames 및 media/strap/frames만 대상으로 한다. capture.json에 이미 기록된 SHA와 실제 bytes/길이를 확인한다. 진행 중 출력·symlink·다른 device는 제외한다.
2. 사전 입력 map과 원 inode/nlink/mtime/bytes를 기록한 뒤 실제 bytes가 같은 쌍만 새 임시 hardlink→atomic replace한다. 모든 논리 경로의 사후 SHA/bytes와 inode/nlink 및 실제 가용 공간 변화를 다시 기록한다. 고유 내용을 삭제하지 않으며 원 raw/code/config는 변경하지 않는다.
3. inode·mtime 보존은 주장하지 않는다. 동일 inode의 alias를 하나라도 제자리 수정하면 모두 바뀔 수 있으므로 이후 해당 PNG는 절대 덮어쓰지 않고 후속 실행은 새 디렉토리만 사용한다. 원 mtime/inode는 별도 저장 기록에 남긴다. 최종 consumed SHA·기존5개 inventory 보존·phase artifact inventory 검사는 그대로 유지한다.
