"""Draw the saved, static PD actuation-path audit; does not initialize a simulator."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


EXPECTED_CHECKS = 6
EXPECTED_INPUTS = 101


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def add_box(ax, x, y, w, h, text, *, fc="#f4f6f8", ec="#506070", fontsize=9, dashed=False):
    patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.02",
                           facecolor=fc, edgecolor=ec, linewidth=1.2,
                           linestyle="--" if dashed else "-")
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize)
    return (x, y, w, h)


def arrow(ax, start, end, *, color="#596b7a", style="-", rad=0):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=12,
                                 linewidth=1.2, color=color, linestyle=style,
                                 connectionstyle=f"arc3,rad={rad}"))


def grouped_ranges(audit):
    rows = {row["joint"]: row for row in audit["nominal_rows"]}
    tasks = {name: set(names) for name, names in audit["task_policy_names"].items()}
    fret, strike = tasks["Fret"], tasks["Strike"]
    main, torso = set(audit["main66_names"]), set(audit["torso9_names"])
    task_union = fret | strike
    groups = [
        ("Fret policy", fret),
        ("Strike policy", strike),
        ("Main66 beyond task names", main - task_union),
        ("Torso9 PD-hold names", torso),
        ("Other native DOFs", set(rows) - main - torso),
    ]
    table = []
    for label, names in groups:
        values = [rows[name] for name in names]
        table.append((label, len(names),
                      min(v["kp"] for v in values), max(v["kp"] for v in values),
                      min(v["kd"] for v in values), max(v["kd"] for v in values),
                      min(v["explicit_cap"] for v in values), max(v["explicit_cap"] for v in values)))
    return table, (fret, strike, main, torso)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True, help="read-only audit result directory")
    parser.add_argument("--out", type=Path, required=True, help="new PNG output path")
    args = parser.parse_args()
    manifest_path = args.out.with_suffix(".manifest.json")
    if args.out.exists() or manifest_path.exists():
        raise FileExistsError(f"preserve existing output or manifest: {args.out}")

    audit_path = args.run / "audit.json"
    execution_path = args.run / "audit_execution.json"
    audit = json.loads(audit_path.read_text())
    execution = json.loads(execution_path.read_text())
    checks = audit.get("checks", {})
    inputs = audit.get("input_sha256", {})
    if len(checks) != EXPECTED_CHECKS or not all(checks.values()):
        raise ValueError("audit contract checks are not all true")
    if len(inputs) != EXPECTED_INPUTS:
        raise ValueError(f"expected {EXPECTED_INPUTS} input hashes, got {len(inputs)}")
    if execution.get("returncode") != 0 or execution.get("native_initializations") != 0 or execution.get("physics_steps") != 0:
        raise ValueError("static audit execution provenance does not show exit 0 / native 0 / steps 0")
    for path_text, expected in inputs.items():
        source = Path(path_text)
        if not source.is_file() or sha256(source) != expected:
            raise ValueError(f"stale or missing audit source: {source}")

    rows = audit.get("nominal_rows", [])
    if len(rows) != 105 or len({row.get("joint") for row in rows}) != 105:
        raise ValueError("expected 105 unique named DOF nominal rows")
    groups, (fret, strike, main_names, torso) = grouped_ranges(audit)
    all_names = {row["joint"] for row in rows}
    if (len(fret) != 30 or len(strike) != 30 or fret & strike or
            len(main_names) != 66 or len(torso) != 9 or not (fret | strike) <= main_names or
            torso & main_names or sum(item[1] for item in groups) != 105 or all_names != set(audit["main66_names"]) | set(audit["torso9_names"]) | (all_names - set(audit["main66_names"]) - set(audit["torso9_names"]))):
        raise ValueError("unexpected task-policy/main66/torso9 name-set relationship")

    fig = plt.figure(figsize=(14.5, 10.0), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, height_ratios=(1.45, 1.0))
    original = fig.add_subplot(grid[0, 0])
    current = fig.add_subplot(grid[0, 1])
    table_ax = fig.add_subplot(grid[1, :])
    for ax, title in ((original, "Original tab2body path"), (current, "Current stability_adapter_2 path")):
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off"); ax.set_title(title, fontsize=12, pad=8)

    add_box(original, .06, .84, .42, .11, "Fret policy targets\n30 names: 9 arm + 21 fingers", fc="#e9f1fb", fontsize=8.5)
    add_box(original, .52, .84, .42, .11, "Strike policy targets\n30 names: 9 arm + 21 fingers", fc="#fff1e3", fontsize=8.5)
    add_box(original, .23, .66, .54, .10, "PD target vector (target, q)", fc="#f4f6f8")
    arrow(original, (.27, .84), (.43, .76)); arrow(original, (.73, .84), (.57, .76))
    add_box(original, .23, .49, .54, .11, "Explicit stiffness torque\nτ = kp × (target − q)", fc="#fff8df")
    arrow(original, (.5, .66), (.5, .60))
    add_box(original, .23, .32, .54, .11, "Symmetric explicit cap\nclamp(τ, −cap, +cap)", fc="#fff8df")
    arrow(original, (.5, .49), (.5, .43))
    add_box(original, .12, .11, .76, .14, "gym.set_dof_actuation_force_tensor\nDOCS: actuation forces apply only to DOF_MODE_EFFORT\nRuntime effect of the original POS + force-tensor path is unverified",
            fc="#fff0ef", ec="#ad4a43", fontsize=8.1)
    arrow(original, (.5, .32), (.5, .25), color="#ad4a43")
    add_box(original, .62, .64, .34, .12, "Native DOF properties\nPOS · stiffness=0 · damping=kd", fc="#f0f0f0", ec="#77808a", fontsize=8, dashed=True)
    original.text(.5, .035, "Static source path; no runtime API response measured", ha="center", fontsize=8, color="#7d302d")

    add_box(current, .08, .80, .84, .15,
            "Task-name interfaces: Fret 30 + Strike 30 (60 names)\nMain66 includes those 60 plus 6 names; Torso9 is separate PD-hold interface\nThese are audited interfaces, not a new learning-dimension decision",
            fc="#e9f3ec", fontsize=8.4)
    add_box(current, .19, .60, .62, .11, "set_actor_dof_position_targets", fc="#e9f1fb")
    arrow(current, (.5, .80), (.5, .71), color="#3c7651")
    add_box(current, .13, .39, .74, .14,
            "DOF_MODE_POS · stiffness=kp · damping=kd\nnominal effort property carries the numeric cap values",
            fc="#f0f7f1", ec="#3c7651", fontsize=8.3)
    arrow(current, (.5, .60), (.5, .53), color="#3c7651")
    add_box(current, .19, .18, .62, .13, "CPU PhysX solver position-target drive\n(no custom arm torque submission in this path)",
            fc="#f0f7f1", ec="#3c7651", fontsize=8.3)
    arrow(current, (.5, .39), (.5, .31), color="#3c7651")
    current.text(.5, .07, "Stored property numbers can match without actuator equivalence",
                 ha="center", fontsize=8, color="#335e42")

    table_ax.axis("off")
    table_ax.set_title("105 named DOFs: nominal values read from audit.json", fontsize=11, pad=5)
    cell_text = [[label, str(count), f"{kp0:g}–{kp1:g}", f"{kd0:g}–{kd1:g}", f"{cap0:g}–{cap1:g} Nm"]
                 for label, count, kp0, kp1, kd0, kd1, cap0, cap1 in groups]
    table = table_ax.table(cellText=cell_text,
                           colLabels=["Name group", "DOFs", "kp range", "kd range", "Explicit cap range"],
                           cellLoc="center", colLoc="center", loc="center",
                           colWidths=[.38, .1, .16, .16, .2])
    table.auto_set_font_size(False); table.set_fontsize(8.5); table.scale(1, 1.35)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor("#dfe6ed"); cell.set_text_props(weight="bold")
        elif row % 2:
            cell.set_facecolor("#f6f8fa")
    fig.suptitle("Static PD actuation-path audit — code/data diagram, not a physics result", fontsize=14)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=180)
    plt.close(fig)

    source_paths = [
        Path("tab2body/env/base.py"), Path("tab2body/env/safety.py"),
        Path("tab2body/env/tasks/task_fret.py"), Path("tab2body/env/tasks/task_strike.py"),
        Path("stability_adapter_2/environment.py"),
        Path("isaacgym/docs/programming/tensors.html"),
    ]
    manifest = {
        "purpose": "Static source/data path diagram; no native initialization or physics steps",
        "audit_json_sha256": sha256(audit_path),
        "audit_execution_sha256": sha256(execution_path),
        "audit_checks": checks,
        "audit_input_sha256_count": len(inputs),
        "audit_input_sha256": inputs,
        "additional_code_and_document_sha256": {str(p.resolve()): sha256(p) for p in source_paths},
        "plotter_sha256": sha256(Path(__file__).resolve()),
        "output_png": str(args.out.resolve()),
        "output_png_sha256": sha256(args.out),
        "grouped_values_source": "audit.nominal_rows; ranges are numeric values, not claims of actuator equivalence",
        "official_document_anchor": "isaacgym/docs/programming/tensors.html:384",
        "native_initializations": 0,
        "physics_steps": 0,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "manifest": str(manifest_path),
                      "output_sha256": manifest["output_png_sha256"], "input_sha_count": len(inputs),
                      "native_initializations": 0, "physics_steps": 0}, indent=2))


if __name__ == "__main__":
    main()
