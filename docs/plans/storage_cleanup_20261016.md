# docs·Git 저장공간 정리

사용자가 docs와.git의 불필요한 파일을 모두 제거하도록 명시 승인했다. 현재 자세 교정 작업의 저장공간 장애를 해결한다. 삭제 대상은 근거를 갖고 판정하며 기존 수정/삭제/미추적 작업은 되돌리지 않는다. 감사는 docs/storage_cleanup_20261016_v1에 남긴다.

1. Git: 기존 HEAD/index/refs/status·fsck와 disk usage를 기록한다. Git이 garbage로 보고하는 오래된 tmp_pack/tmp_obj 중 잠금·활성 Git 작업·열린 파일이 없는 명시 목록을 SHA와 함께 기록하고 제거한다. 정상 pack/idx와 commit/ref·reflog는 직접 삭제하지 않는다.
2. Git: reflog 만료와 unreachable pruning을 하지 않는 공식 gc로 중복 저장을 압축한다. LFS는 dry-run을 기록하고 공식 --verify-remote 정리를 검토한다. 유일한 과거 데이터를 잃지 않도록 원격 검증 불가/로컬단독 후보는 보존한다. 외부 .git 대체·전체폴더삭제·reset/clean/force prune/히스토리재작성은 사용하지 않는다.
3. docs: 유일한 실험 원자료·소비 소스·설정·증거·과거버전을 삭제하지 않는다. 내용이 완전히 동일하고 불변인 데이터/보존사본은 SHA와 실제bytes를 대조해 같은 inode로 통합하여 중복 디스크 저장만 없앤다. 경로/bytes/SHA를 유지하고 inode·mtime변화를 기록한다. 외부 가변 원본과 링크하지 않는다. 열린파일·활성출력·symlink·작업audit폴더를 제외한다. 잠재적으로 소비된33개 pyc는 용량이 작고 보존근거가 불명확하므로 남긴다.
4. 각 구현/대상 목록을 독립 검수한 뒤 실행한다. 완료 후 Git 무결성/논리refs/index/작업상태와 docs 대상의 전체 bytes/SHA,기존 하체·기타 봉인 input/inventory의 보존을 검사한다. 삭제파일/통합경로·확보공간·잔여용량·제외 이유를 기록한다.

Git LFS 후보는 로컬dry-run만으로 원격 보존이 확인됐다고 주장하지 않는다. GC의 임시 peak사용을 고려해15GB 임시파일부터 정리한다. docs의 hardlink alias를 제자리 수정하지 않고 후속 실험은 새 경로를 쓴다. 기존 paper/초기자세·학습결과·공유자산은 쓰기대상이 아니다.

- [ ] before/명시Git임시목록/코드검수
- [ ] 오래된Gitgarbage 제거와공식gc
- [ ] LFS 필요여부·검증·정리/보존
- [ ] docs 중복내용통합과전수검증
- [ ] after/무결성·보존·용량·최종검수
