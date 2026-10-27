"""CPU-only integrity and media checks for the three predeclared captures."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIDEOS = ROOT / "03_short_learning/native_videos_seed7"


def sha(path):
    with Path(path).open("rb") as stream:
        digest = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify():
    results = []
    for case in ("incremental_best_50", "incremental_final_300", "position_final_300"):
        directory = VIDEOS / case
        report = json.loads((directory / "report.json").read_text())
        launcher = json.loads((VIDEOS / (case + "_launcher.json")).read_text())
        before = json.loads((directory / "inputs_before.json").read_text())
        after = json.loads((directory / "inputs_after.json").read_text())
        assert launcher["returncode"] == 0
        assert after["verified"] and not after["changed_paths"]
        assert not after["unpinned_project_sources"]
        assert before == after["input_pins"]
        assert all(sha(path) == digest for path, digest in before.items())
        assert sha(report["checkpoint"]) == report["checkpoint_sha256"]
        for key in ("completed", "checkpoint_unchanged", "policy_unchanged",
                    "native_pixels", "trace_finite", "physics_clock_contiguous",
                    "source_pins_unchanged", "checkpoint_pins_validated",
                    "scene_closed", "lifecycle_verified"):
            assert report[key], (case, key)
        assert not report["failure"] and not report["cleanup_errors"]
        assert report["recorded_environment"] == 0 and report["first_episode_only"]
        assert report["training_updates"] == 0
        assert report["gpu_scene"]["diagnostic_guitar_mode"] == "fixed"
        assert report["gpu_scene"]["num_envs"] == 128
        assert report["gpu_scene"]["physics_steps"] == 872
        media = {}
        for camera in ("hand", "fullbody"):
            path = directory / (camera + ".mp4")
            probe = json.loads(subprocess.check_output([
                "ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate,nb_read_frames:format=duration",
                "-of", "json", str(path)], text=True))
            stream = probe["streams"][0]
            assert (stream["width"], stream["height"], stream["r_frame_rate"],
                    stream["nb_read_frames"]) == (1280, 720, "30/1", "109")
            assert abs(float(probe["format"]["duration"]) - 109 / 30) < .002
            assert report["encoding_exit_codes"][camera] == 0
            media[camera] = {"probe": probe, "sha256": sha(path)}
        artifacts = {str(path.relative_to(VIDEOS)): sha(path)
                     for path in directory.iterdir() if path.is_file()}
        artifacts[case + "_launcher.json"] = sha(VIDEOS / (case + "_launcher.json"))
        results.append({"case": case, "current_input_pins_checked": len(before),
                        "achieved": report["episode_summary"]["achieved"],
                        "clean_fraction": report["episode_summary"]["clean_fraction"],
                        "media": media, "artifacts": artifacts})
    return {"passed": True, "cases": results,
            "visual_qa": "Root inspected each 3s hand/fullbody frame: upright; full body includes head and feet. This does not certify naturalness or successful pressing.",
            "script_sha256": sha(__file__)}


if __name__ == "__main__":
    result = verify()
    (VIDEOS / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "cases": len(result["cases"])}))
