#!/usr/bin/env python3
"""Prepare or run the pinned Cloth-fit solver, without bundling its assets."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
REVISION = "123e2440f46720b5f993c91d1705aff838aa55fb"
OFFICIAL = ("foxgirl_skirt", "Goblin_Jacket", "Goblin_Jumpsuit", "Trex_Jacket")
STRUCTURED = ("FoxGirl", "Goblin")
STRUCTURED_INPUTS = {
    "garment_mesh_path": "garment.obj",
    "source_skeleton_path": "source_skeleton.obj",
    "no_fit_spec_path": "no-fit.txt",
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def real_path(path):
    if not path.is_file():
        raise ValueError(f"Missing input: {path}")
    return str(path.resolve())


def config_for(case, repo, source, threads):
    library = repo / "garment-data"
    if case in OFFICIAL:
        original = library / case / "setup.json"
        config = read_json(original)
        for key, value in config.items():
            if key.endswith("_path") and isinstance(value, str) and value:
                path = original.parent / value
                # Some pinned examples reference optional metadata not provided
                # by upstream. Preserve the absolute paths and upstream fallbacks.
                if key in {"avatar_skin_weights_path", "no_fit_spec_path"}:
                    config[key] = str(path.resolve())
                else:
                    config[key] = real_path(path)
    else:
        if source is None:
            raise ValueError("V4 requires --structured-source (local approved assets, not bundled).")
        config = read_json(ROOT / "configs" / f"structured_{case}.json")
        for key, name in STRUCTURED_INPUTS.items():
            config[key] = real_path(source / name)
        for key in ("avatar_mesh_path", "target_skeleton_path", "avatar_skin_weights_path"):
            if config.get(key):
                config[key] = real_path(library / config[key])
    config["solver"]["max_threads"] = threads
    config["output"]["skip_frame"] = 1
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=OFFICIAL + STRUCTURED)
    parser.add_argument("--repo", type=Path, default=ROOT / "cloth-fit")
    parser.add_argument("--solver", type=Path, help="Optional explicit PolyFEM_bin path")
    parser.add_argument("--structured-source", type=Path)
    parser.add_argument("--out", type=Path, help="New run directory (must not exist)")
    parser.add_argument("--threads", type=int)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    threads = (4 if args.case in STRUCTURED else 8) if args.threads is None else args.threads
    if threads < 1:
        parser.error("--threads must be positive")
    repo = args.repo.resolve()
    try:
        actual_revision = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], text=True,
            stderr=subprocess.PIPE,
        ).strip()
        if actual_revision != REVISION:
            raise ValueError(f"Expected Cloth-fit at {REVISION}; found {actual_revision}")
        config = config_for(args.case, repo, args.structured_source, threads)
        solver = (args.solver or repo / "build" / "PolyFEM_bin").resolve()
        if not args.prepare_only and not (solver.is_file() and os.access(solver, os.X_OK)):
            raise ValueError(f"Solver not executable: {solver}; run tools/bootstrap.sh")
        out = (args.out or (ROOT / "runs" / args.case)).resolve()
        if out.exists():
            raise ValueError(f"Output already exists; choose a new --out: {out}")
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))
    out.mkdir(parents=True, exist_ok=False)
    settings = out / "setup.json"
    settings.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    if args.prepare_only:
        print(settings)
        return 0
    mesh_dir = out / "output"
    mesh_dir.mkdir()
    command = [str(solver), "-j", str(settings), "--max_threads", str(threads), "-o", str(mesh_dir)]
    start = time.monotonic()
    with (out / "run.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        _, status, usage = os.wait4(process.pid, 0)
        process.returncode = os.waitstatus_to_exitcode(status)
    elapsed = time.monotonic() - start
    with (out / "run.log").open(encoding="utf-8", errors="replace") as log:
        success_marker = "Garment retargeting succeeded!" in log.read()
    snapshots = {
        int(path.stem.removeprefix("step_garment_")): path
        for path in mesh_dir.glob("step_garment_*.obj")
        if path.stem.removeprefix("step_garment_").isdigit()
    }
    latest = max(snapshots, default=None)
    succeeded = process.returncode == 0 and success_marker and latest is not None
    metrics = {
        "case": args.case, "solver_commit": actual_revision, "threads": threads,
        "returncode": process.returncode, "wall_seconds": round(elapsed, 3),
        "peak_rss_kib_linux": usage.ru_maxrss, "solver_reported_success": success_marker,
        "latest_saved_step": latest,
        "latest_mesh": str(snapshots[latest].relative_to(out)) if latest is not None else None,
        "run_succeeded": succeeded,
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    return 0 if succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
