"""Train with one native simulator per worker for the lifetime of the run."""

def main():
    from unittest.mock import patch
    from . import parallel,train_parallel
    from .persistent_parallel import PersistentPool
    # Only this new entry point chooses persistent workers. Running jobs and the
    # original fresh-scene entry point keep their imported implementation.
    with patch.object(parallel,'Pool',PersistentPool):
        train_parallel.main()


if __name__=='__main__':main()
