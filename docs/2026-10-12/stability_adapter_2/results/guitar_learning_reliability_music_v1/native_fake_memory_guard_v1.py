"""Exercise native recovery with a fake low-RAM observation, never host pressure."""
from pathlib import Path

if __name__=='__main__':
    import guitar_learning.train_parallel as training
    from guitar_learning.monitoring import Monitor,available_memory_bytes
    class FakeLowMemoryMonitor(Monitor):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.resource_interval_seconds=.1
            self.memory_probe=lambda:3*1024**3 if self.context['ticks']>=4 else available_memory_bytes()
    training.Monitor=FakeLowMemoryMonitor
    training.main()
