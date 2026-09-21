"""Preview the archival MRI commands; only --execute launches experiments."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path, PureWindowsPath
import subprocess
import sys


THREAD_LIMITS = {
    "OMP_NUM_THREADS": "4",
    "MKL_NUM_THREADS": "4",
    "OPENBLAS_NUM_THREADS": "4",
    "NUMEXPR_NUM_THREADS": "4",
}
DATASETS = {
    "brain": ("brain_AXT2_internal_holdout", "AXT2", 272, (505, 20, 30)),
    "knee": ("knee_CORPDFS_FBK", "CORPDFS_FBK", 320, (147, 20, 30)),
}
MANIFEST_NAMES = (
    "train_manifest.csv", "calibration_manifest.csv", "test_manifest.csv"
)
CLASSICAL_METHODS = ("SENSE", "Tikhonov", "BE", "WaveletL1", "TV", "MGGD")
RECORD_NAME = "run_protocol_record.json"
BRAIN_COMPLETE = {
    "classical": (
        "run_summary.json", "test_metric_summary_by_volume.csv",
        "test_noise_summary.csv", "test_pairwise_significance_by_volume.csv",
    ),
    "grappa": ("run_summary.json", "grappa_test_metric_summary_by_volume.csv"),
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, choices=DATASETS)
    parser.add_argument("--manifests-dir", "--manifest-dir", required=True, type=Path)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--out-dir", "--output-dir", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--execute", action="store_true", help="Launch the printed commands.")
    parser.add_argument("--resume", action="store_true", help="Reuse a matching wrapper-created run.")
    args = parser.parse_args(argv)
    for name in ("manifests_dir", "data_root", "out_dir", "repo_root"):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    return args


def check_output(out_dir, resume):
    if out_dir.exists():
        if not out_dir.is_dir():
            raise ValueError(f"Output path is not a directory: {out_dir}")
        if any(out_dir.iterdir()) and not resume:
            raise ValueError("Output directory is nonempty; use a new directory or explicit --resume.")


def build_commands(args):
    label, acquisition, crop, _ = DATASETS[args.dataset]
    scripts = args.repo_root / "scripts"
    manifests = []
    for flag, name in zip(
        ("--train-manifest", "--val-manifest", "--test-manifest"), MANIFEST_NAMES
    ):
        manifests.extend([flag, str(args.manifests_dir / name)])
    classical_dir = args.out_dir / "classical"
    shared = ["--acquisition", acquisition, "--crop-size", str(crop), "--coils", "0"]
    accelerations = ["--accelerations", "2", "4", "6", "8"]
    classical = [
        sys.executable, str(scripts / "run_fastmri_manuscript_protocol.py"),
        "--dataset-name", label, *manifests, "--out-dir", str(classical_dir),
        *shared, *accelerations, "--methods", *CLASSICAL_METHODS,
        "--noise-repeats", "20", "--noise-max-volumes", "5",
        "--noise-accelerations", "8", "--irls-iters", "15", "--cg-maxiter", "150",
        "--solver-device", "cuda", "--gpu-dtype", "float32",
        "--cpu-core-limit", "4", "--low-priority",
    ]
    grappa = [
        sys.executable, str(scripts / "run_grappa_baseline_from_protocol.py"),
        "--source-run", str(classical_dir), "--out-dir", str(args.out_dir / "grappa"),
        "--save-figures",
    ]
    train_dir = args.data_root / f"{args.dataset}_multicoil_train"
    val_dir = train_dir if args.dataset == "brain" else args.data_root / "knee_multicoil_val"
    deep = [
        sys.executable, str(scripts / "run_fastmri_deep_fullscale.py"),
        "--train-dir", str(train_dir), "--val-dir", str(val_dir), "--test-dir", str(val_dir),
        *manifests, "--out-dir", str(args.out_dir / "deep"), *shared, *accelerations,
        "--epochs", "50", "--batch-size", "1", "--num-workers", "0",
        "--unet-chans", "32", "--varnet-chans", "18", "--varnet-cascades", "8",
        "--early-stopping-patience", "7", "--one-sample-per-volume-per-epoch",
        "--official-models", "--save-figures", "--amp",
    ]
    if args.resume:
        classical.append("--resume")
        deep.append("--resume")
    return [("classical", classical), ("grappa", grappa), ("deep", deep)]


def validate_manifests(args):
    """Check local CSV metadata without opening any referenced MRI file."""
    hashes = {}
    previous_volumes = set()
    previous_ids = set()
    for name, expected in zip(MANIFEST_NAMES, DATASETS[args.dataset][3]):
        manifest = args.manifests_dir / name
        raw = manifest.read_bytes()
        hashes[name] = hashlib.sha256(raw).hexdigest()
        table = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
        if not {"path", "slice_idx"}.issubset(table.fieldnames or []):
            raise ValueError(f"{name} requires path and slice_idx columns.")
        volumes, observations, identifiers = set(), set(), {}
        for row_number, row in enumerate(table, 2):
            path_text = row.get("path") or ""
            slice_text = row.get("slice_idx") or ""
            if not path_text or path_text != path_text.strip():
                raise ValueError(f"{name}:{row_number}: missing path or surrounding whitespace.")
            if not slice_text.isascii() or not slice_text.isdigit():
                raise ValueError(f"{name}:{row_number}: slice_idx must be a nonnegative integer.")
            if os.name != "nt" and (PureWindowsPath(path_text).drive or "\\" in path_text):
                raise ValueError(f"{name}:{row_number}: use paths valid on this host with forward slashes.")
            path = Path(path_text)
            resolved = (path if path.is_absolute() else args.data_root / path).resolve()
            if not resolved.is_file():
                raise ValueError(f"{name}:{row_number}: referenced local file is missing: {resolved}")
            observation = (resolved, int(slice_text))
            if observation in observations:
                raise ValueError(f"{name}:{row_number}: duplicate path/slice_idx observation.")
            volume_id = path.stem
            if volume_id in identifiers and identifiers[volume_id] != resolved:
                raise ValueError(f"{name}:{row_number}: different paths share a volume identifier.")
            identifiers[volume_id] = resolved
            volumes.add(resolved)
            observations.add(observation)
        if len(volumes) != expected:
            raise ValueError(f"{name}: expected {expected} volumes, found {len(volumes)}.")
        if volumes & previous_volumes or set(identifiers) & previous_ids:
            raise ValueError(f"{name}: volume overlap or repeated volume identifier across splits.")
        previous_volumes.update(volumes)
        previous_ids.update(identifiers)
    return hashes


def run_record(args, commands, hashes):
    return {
        "schema_version": 1,
        "dataset": args.dataset,
        "cwd": str(args.data_root),
        "thread_limits": THREAD_LIMITS,
        "commands": [
            {"stage": stage, "argv": [arg for arg in argv if arg != "--resume"]}
            for stage, argv in commands
        ],
        "manifest_sha256": hashes,
    }


def completed_brain_stage(args, stage):
    if args.dataset != "brain" or not args.resume or stage not in BRAIN_COMPLETE:
        return False
    return all(
        (args.out_dir / stage / name).is_file()
        and (args.out_dir / stage / name).stat().st_size > 0
        for name in BRAIN_COMPLETE[stage]
    )


def execute(args, commands):
    if not args.data_root.is_dir():
        raise ValueError(f"Data root is not a local directory: {args.data_root}")
    for _, argv in commands:
        if not Path(argv[1]).is_file():
            raise ValueError(f"Missing archival script: {argv[1]}; check --repo-root.")
    vendor = args.repo_root / "external" / "fastMRI_official"
    if not (vendor / "fastmri" / "models" / "varnet.py").is_file() or not (vendor / "LICENSE.md").is_file():
        raise ValueError("The vendored fastMRI models and LICENSE.md must remain in the release.")
    hashes = validate_manifests(args)
    check_output(args.out_dir, args.resume)
    record = run_record(args, commands, hashes)
    record_path = args.out_dir / RECORD_NAME
    if args.out_dir.exists() and any(args.out_dir.iterdir()):
        if not record_path.is_file():
            raise ValueError("Nonempty output has no wrapper record; choose a new output directory.")
        if json.loads(record_path.read_text(encoding="utf-8")) != record:
            raise ValueError("Resume plan or manifest hashes differ; choose a new output directory.")
    else:
        args.out_dir.mkdir(parents=True, exist_ok=True)
        with record_path.open("x", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2)
            handle.write("\n")
    env = os.environ.copy()
    env.update(THREAD_LIMITS)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for stage, argv in commands:
        if completed_brain_stage(args, stage):
            print(f"resume=skip completed brain {stage} artifacts", flush=True)
            continue
        print(f"Starting {stage}", flush=True)
        subprocess.run(argv, cwd=str(args.data_root), env=env, check=True)
    return 0


def main(argv=None):
    args = parse_args(argv)
    try:
        check_output(args.out_dir, args.resume)
        commands = build_commands(args)
        print(json.dumps({
            "mode": "execute" if args.execute else "dry-run",
            "dataset": args.dataset,
            "expected_volumes_train_calibration_evaluation": DATASETS[args.dataset][3],
            "cwd": str(args.data_root),
            "thread_limits": THREAD_LIMITS,
            "resume": args.resume,
            "commands": [{"stage": stage, "argv": command} for stage, command in commands],
        }, indent=2), flush=True)
        if not args.execute:
            print("Dry run only: no input validation, output creation, or experiment execution.")
            return 0
        return execute(args, commands)
    except (OSError, ValueError, csv.Error) as exc:
        print(f"Refused: {exc}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as exc:
        print(f"Stage failed with exit code {exc.returncode}; outputs retained.", file=sys.stderr)
        return exc.returncode if 0 < exc.returncode < 256 else 1
    except KeyboardInterrupt:
        print("Interrupted; outputs retained for an explicit resume.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
