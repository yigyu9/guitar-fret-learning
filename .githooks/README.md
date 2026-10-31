# GitHub file policy

The included directories are data, docs, guitar_learning, isaacgym, paper, tab2fingermapping and scripts. Root documentation and .githooks remain eligible.

Checkpoint/model-weight files and checkpoint folders, videos/animated GIFs, process logs/log folders, docs JSONL streams (including JSONL manifests), diagnostic NPZ files under docs, archive directories and related_work directories stay local. The exception is `guitar_learning/assets/**`: archives there are required training inputs, not disposable experiment outputs. JSON settings, compact JSON reports/manifests, Markdown, PDF and still figures remain eligible. Raw JSONL/NPZ datasets and test fixtures outside docs remain eligible.

External-storage symlinks stay local. Run the following before adding files after an offload operation:

```sh
python3 .githooks/storage_policy.py
```

This refreshes a managed section in .git/info/exclude and records paths in .git/external-storage-links.json. It leaves symlinks and their targets untouched. Directories currently containing only external links may be grouped into one local exclude rule; refresh scans those directories again so newly added real files can become eligible. Keep these machine-specific paths out of the shared .gitignore. Internal library symlinks remain eligible.

The pre-commit hook rejects ignored staged paths and external-storage link targets, including when force-added. It reads staged link blobs rather than trusting the working tree. It also blocks generated logs/reports above 10 MiB, ordinary Git blobs above 50 MiB, archives outside `guitar_learning/assets`, out-of-scope paths and accidental embedded repositories. JSONL streams under docs are not converted into required summary artifacts; commit a compact JSON/Markdown summary instead.

Other required large inputs (audio, FBX, non-diagnostic arrays, shared libraries) use the remaining LFS attributes. Existing model/video LFS attributes retain historical file handling but do not override ignore rules.

After cloning, install Git LFS and enable the shared hooks; commit .githooks files together:

```sh
git lfs install --local
git config --local core.hooksPath .githooks
python3 .githooks/storage_policy.py
```

.gitignore does not remove already tracked paths or rewrite history. Changing these patterns alone never removes local content or changes the index. Review tracked paths separately before any explicit index cleanup. Existing Git/LFS history remains. This policy does not automatically commit or push.
