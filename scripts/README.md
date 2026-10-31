# Tab2Body PC-local runtime launcher

`tab2body.py` uses only Python standard libraries. It discovers the project root
from its own location and launches with the same `sys.executable`; no username,
Conda installation prefix, mount point, or working directory is hardcoded.

## Project-local data and cache

For a project on a local disk, keep generated runtime/cache files inside the project:

```bash
python scripts/tab2body.py --cache-root .runtime/cache prepare
python scripts/tab2body.py --cache-root .runtime/cache run \
  -m guitar_learning.tool.validation.portable_inputs
```

The active training inputs must resolve inside the current project before any read.
Historical absolute labels map to verified internal copies; they are not external
file fallback locations. Python packages, GPU drivers and system libraries remain
installed per PC. The generic cache defaults below are unchanged; the explicit
project-local option is used for the self-contained verification. A project on
SSHFS still needs the PC-local cache described below.

See [current verification](../docs/maintenance/self_contained_20261031/REPORT.md)
and [teammate handoff](../docs/TEAM_HANDOFF.md).

## Environment

Target: Linux x86_64, Python 3.8, NVIDIA GPU with a working driver compatible with
the PyTorch CUDA 12.1 build, and the project's Isaac Gym **Preview4** payload.
Python 3.9+ cannot load the bundled `gym_38.so`. The following file pins versions
observed in the source PC's `rl38` environment; creating it on another PC still
requires package availability and that PC's NVIDIA driver, C++ compiler and system
libraries. The environment itself must be installed on each PC's local disk.
Do not copy a Conda prefix between PCs or run its binaries from SSHFS.

```bash
conda env create -f scripts/environment.rl38.yml
conda activate tab2body-rl38
python --version
nvidia-smi
command -v c++
```

Isaac Gym's native dependencies include the standard Linux C++/OpenGL runtime
libraries; see the bundled `isaacgym/docs/install.html` for NVIDIA's installation
requirements and `isaacgym/docs/release-notes.html` for Preview4. System library and
driver installation follows the target distribution. Video generation also needs
`ffmpeg` on `PATH` and the renderer/display dependencies of the selected video tool.
The core CUDA-only probe uses graphics device `-1` and creates no viewer.

No `pip install -e isaacgym/python`, manual `PYTHONPATH`, or hardcoded
`LD_LIBRARY_PATH` export is needed for the commands below. Do not import Torch
before Isaac Gym in custom scripts.

The launcher starts its child Python in UTF-8 mode (`-X utf8`). No external
`PYTHONUTF8` export is needed: Korean JSON remains readable even if native asset
loading resets the process character locale to `C`.

## Prepare, probe, and run

Commands assume the activated environment. `/local/cache/tab2body` below is an
example: choose an existing local disk on **each PC**, never the SSHFS mount.
Without `--cache-root`, the launcher uses `TAB2BODY_CACHE_ROOT`, otherwise
`$XDG_CACHE_HOME/tab2body`, otherwise `~/.cache/tab2body`. Remote defaults fail with
a clear error; use an explicit local directory in that case.

```bash
python scripts/tab2body.py --cache-root /local/cache/tab2body prepare
python scripts/tab2body.py --cache-root /local/cache/tab2body probe
python scripts/tab2body.py --cache-root /local/cache/tab2body run \
  -m guitar_learning.train --num-envs 2 --horizon 2 --updates 1 \
  --out runs/portability_train_01
python scripts/tab2body.py --cache-root /local/cache/tab2body run \
  -m guitar_learning.train --num-envs 2 --horizon 2 --updates 1 \
  --resume runs/portability_train_01/J/final.pt \
  --out runs/portability_resume_01
```

All arguments following `run` are Python arguments (`-m MODULE`, a script path,
`-c CODE`, etc.). The launcher preserves the caller's current directory, so
relative output/checkpoint paths retain ordinary CLI meaning. An absolute path to
this launcher works from any directory. Use absolute output/checkpoint paths when
launching from a different directory. Training outputs must be new directories.
For separate evaluation and video module names/arguments, see
`guitar_learning/README.md` and prefix their Python commands with
`python scripts/tab2body.py --cache-root /local/cache/tab2body run`.

The probe creates a real GPU PhysX scene, steps a free box 120 times at 240Hz,
checks a finite CUDA root-state tensor, and destroys the scene. Success is shown
only after those checks; import success alone does not validate GPU execution.

## What is cached and verified

Only `isaacgym/python/isaacgym` is copied (about 438 MiB in this checkout), including
native libraries, plugins, and GymTorch source. Source/data remain in the shared
project. The launcher records the vendor version and SHA of `isaacgym/python/setup.py`,
hashes every regular runtime file and every internal link,
rejects absolute/escaping/broken links, verifies copied bytes, and publishes the
copy atomically under its SHA-256. Every launch hashes the source and verifies the
cache again. A changed runtime selects a new directory; a corrupt cache fails
rather than loading unverified bytes. Remove the named corrupt entry and prepare
again to rebuild it. Old content-addressed entries may be removed when no running
process uses them. Python bytecode caches are excluded and disabled at execution.

Local `flock` serializes concurrent preparation. Each Python/Conda prefix, Python
ABI, Torch package version, runtime hash, and CUDA/compiler environment receives
its own `TORCH_EXTENSIONS_DIR`. A shared mount is rejected for both native runtime
and extension builds by Linux mount information. `PYTHONPATH` is replaced with the
verified local package and the project root; `PATH` and `LD_LIBRARY_PATH` are
prefixed using the active Python executable/prefix. Existing system library
paths remain available. Do not intentionally redirect compiler, CUDA, NVIDIA
shader caches, or the active Python environment to a remote filesystem.

Two PCs may run the same shared project concurrently, with their own local
Python environment and cache root and **distinct output directories**. Stop
writers before preparing or running: source/data consistency during simultaneous
edits is not a filesystem snapshot. The runtime copy checks for changes during
copy; the training runner separately verifies its pinned project inputs.

No SSHFS mount was available for an end-to-end mount test on the source PC.
Filesystem rejection is covered by a mocked `fuse.sshfs` mount-type test;
content integrity and concurrent copy behavior use real local files.
