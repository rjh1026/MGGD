"""Check source-release file integrity only, not scientific validity or execution."""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import sys


SOURCE_NAMES = (
    "run_synthetic_mggd_experiment.py",
    "run_fastmri_subset_experiment.py",
    "run_fastmri_manuscript_protocol.py",
    "run_grappa_baseline_from_protocol.py",
    "run_fastmri_noise_from_protocol.py",
    "run_fastmri_deep_fullscale.py",
    "run_fastmri_deep_benchmarks.py",
    "prepare_fastmri_30pct_manifests.py",
    "prepare_fastmri_internal_holdout_manifests.py",
)
ROOT_SOURCES = ("verify_release.py", "run_protocol.py", "reproduce_tables.py")
VENDOR = "external/fastMRI_official"
VENDOR_FILES = (
    "LICENSE.md", "README.md", "setup.py", "setup.cfg", "pyproject.toml",
    "fastmri/__init__.py", "fastmri/coil_combine.py", "fastmri/evaluate.py",
    "fastmri/fftc.py", "fastmri/losses.py", "fastmri/math.py", "fastmri/utils.py",
    "fastmri/data/__init__.py", "fastmri/data/mri_data.py",
    "fastmri/data/subsample.py", "fastmri/data/transforms.py",
    "fastmri/data/volume_sampler.py", "fastmri/models/__init__.py",
    "fastmri/models/adaptive_varnet.py", "fastmri/models/policy.py",
    "fastmri/models/unet.py", "fastmri/models/varnet.py",
    "fastmri/pl_modules/__init__.py", "fastmri/pl_modules/data_module.py",
    "fastmri/pl_modules/mri_module.py", "fastmri/pl_modules/unet_module.py",
    "fastmri/pl_modules/varnet_module.py",
)
PARAMETERS = {
    "SENSE": ("ridge",),
    "Tikhonov": ("ridge", "tikhonov"),
    "BE": ("ridge", "bending"),
    "WaveletL1": ("ridge", "wavelet_l1"),
    "TV": ("ridge", "tv"),
    "MGGD": ("ridge", "bending", "mggd_scale"),
}
LIMITS = (
    "File integrity only: hashes, syntax, required fields, and required files. "
    "Not scientific validity or full execution; no reconstruction, training, "
    "dependency imports, or result calculations are performed."
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_bytes(root, relative):
    data = (root / relative).read_bytes()
    require(data.strip(), f"{relative}: empty file")
    return data


def parse_source(data, relative):
    tree = ast.parse(data, filename=relative)
    compile(tree, relative, "exec")


def verify_sources(root):
    relative = "provenance/source_files_sha256.csv"
    reader = csv.DictReader(io.StringIO(
        read_bytes(root, relative).decode("utf-8-sig"), newline=""
    ), strict=True)
    require(reader.fieldnames == ["path", "sha256", "copy_verified"],
            f"{relative}: expected path,sha256,copy_verified header")
    expected = {f"scripts/{name}" for name in SOURCE_NAMES}
    seen = set()
    for row in reader:
        path, digest = row.get("path"), row.get("sha256")
        require(None not in row and all(value is not None for value in row.values()),
                f"{relative}:{reader.line_num}: malformed row")
        require(path in expected, f"{relative}: unexpected source path {path!r}")
        require(path not in seen, f"{relative}: duplicate source path {path}")
        require(len(digest) == 64 and all(c in "0123456789abcdef" for c in digest),
                f"{path}: invalid recorded SHA256")
        require(row["copy_verified"] == "True", f"{path}: copy_verified is not True")
        data = read_bytes(root, path)
        require(hashlib.sha256(data).hexdigest() == digest, f"{path}: SHA256 mismatch")
        parse_source(data, path)
        seen.add(path)
    require(seen == expected, f"{relative}: missing sources: {sorted(expected - seen)}")
    return seen


def object_fields(value, keys, label):
    require(isinstance(value, dict), f"{label}: expected an object")
    missing = set(keys) - value.keys()
    require(not missing, f"{label}: missing fields {sorted(missing)}")


def number(value, label, *, integer=False, positive=True):
    valid_type = type(value) is int if integer else type(value) in (int, float)
    require(valid_type, f"{label}: expected {'integer' if integer else 'number'}")
    require(not isinstance(value, float) or math.isfinite(value),
            f"{label}: expected a finite number")
    require(value > 0 if positive else value >= 0,
            f"{label}: expected {'positive' if positive else 'nonnegative'} value")


def json_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON field {key!r}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"nonfinite JSON constant {value}")


def load_json(root, relative):
    try:
        return json.loads(read_bytes(root, relative).decode("utf-8-sig"),
                          object_pairs_hook=json_object, parse_constant=reject_constant)
    except ValueError as exc:
        raise ValueError(f"{relative}: {exc}") from exc


def verify_settings(value, label, image_size):
    object_fields(value, ("config", "accelerations", "methods", "selected_params",
                          "solver_device", "gpu_dtype"), label)
    config = value["config"]
    integers = ("image_size", "cg_maxiter", "irls_iters", "wavelet_level")
    positives = ("cg_rtol", "irls_eps")
    object_fields(config, integers + positives + ("coils", "seed", "noise_sigma", "wavelet"),
                  f"{label}.config")
    for key in integers + ("coils", "seed"):
        number(config[key], f"{label}.config.{key}", integer=True,
               positive=key not in ("coils", "seed"))
    for key in positives + ("noise_sigma",):
        number(config[key], f"{label}.config.{key}", positive=key != "noise_sigma")
    require(isinstance(config["wavelet"], str) and config["wavelet"].strip(),
            f"{label}.config.wavelet: expected a nonempty name")
    require(config["image_size"] == image_size, f"{label}: unexpected image_size")
    require(config["wavelet_level"] == 3, f"{label}: expected three prior levels")
    accelerations = value["accelerations"]
    require(isinstance(accelerations, list) and
            all(type(item) is int for item in accelerations) and
            accelerations == [2, 4, 6, 8], f"{label}: expected accelerations [2, 4, 6, 8]")
    methods = value["methods"]
    require(isinstance(methods, list) and all(isinstance(item, str) for item in methods)
            and len(methods) == len(PARAMETERS) and set(methods) == set(PARAMETERS),
            f"{label}: expected the six classical methods")
    require(value["solver_device"] == "cuda", f"{label}: expected recorded solver_device cuda")
    require(value["gpu_dtype"] == "float32", f"{label}: expected recorded gpu_dtype float32")
    selected = value["selected_params"]
    object_fields(selected, PARAMETERS, f"{label}.selected_params")
    for method, keys in PARAMETERS.items():
        field = f"{label}.selected_params.{method}"
        object_fields(selected[method], keys, field)
        for key in keys:
            number(selected[method][key], f"{field}.{key}", positive=False)


def verify_prior(value, label):
    bands = [f"L{level}_{band}" for level in (1, 2, 3) for band in ("ad", "da", "dd")]
    object_fields(value, bands, label)
    for band in bands:
        field = f"{label}.{band}"
        object_fields(value[band], ("alpha", "p", "lambda_base", "n"), field)
        for key in ("alpha", "p", "lambda_base", "n"):
            number(value[band][key], f"{field}.{key}", integer=key == "n")


def verify_release(root):
    parsed = verify_sources(root)
    for relative in ("THIRD_PARTY_NOTICES.md", "requirements-analysis.txt",
                     "requirements-reconstruction.txt"):
        read_bytes(root, relative)
    for name in VENDOR_FILES:
        relative = f"{VENDOR}/{name}"
        data = read_bytes(root, relative)
        if relative.endswith(".py"):
            parse_source(data, relative)
            parsed.add(relative)
    for relative in ROOT_SOURCES:
        parse_source(read_bytes(root, relative), relative)
        parsed.add(relative)
    # Parse additional source files without importing packages or writing bytecode.
    for directory in ("scripts", VENDOR):
        for path in sorted((root / directory).rglob("*.py")):
            relative = path.relative_to(root).as_posix()
            if relative not in parsed:
                parse_source(read_bytes(root, relative), relative)
                parsed.add(relative)
    for dataset, size in (("brain", 272), ("knee", 320)):
        settings = f"configs/{dataset}_recorded_settings.json"
        prior = f"configs/{dataset}_trained_prior.json"
        verify_settings(load_json(root, settings), settings, size)
        verify_prior(load_json(root, prior), prior)
    return {"original_sources": len(SOURCE_NAMES), "python_files": len(parsed),
            "configurations": 4, "vendored_files": len(VENDOR_FILES)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent,
                        help="Extracted MGGD_source directory (default: this script's directory)")
    args = parser.parse_args(argv)
    print(LIMITS, flush=True)
    try:
        counts = verify_release(args.root.expanduser().resolve())
    except (OSError, ValueError, SyntaxError, csv.Error) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(f"PASS: {counts['original_sources']} original-source SHA256 matches; "
          f"{counts['python_files']} Python files parsed; "
          f"{counts['configurations']} configuration files checked; "
          f"{counts['vendored_files']} vendored files present, including the license.")
    print("Hashes cover only the recorded original scripts, not configs, wrappers, or vendor bytes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
