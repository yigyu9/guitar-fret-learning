"""기존 진단의 기록 대상을16목표 전체로 확장하는 실행 전용 래퍼."""
import sys

def main():
    # 원본 진단 모듈의 GPU 진입 순서와 기록 검증을 유지한다.
    if len(sys.argv)>1 and sys.argv[1]=='replay':
        import isaacgym
    from guitar_learning.tool.validation import press_acquisition as probe
    probe.REPRESENTATIVE_ROWS=tuple(range(16))
    probe.main()

if __name__=='__main__':
    main()
