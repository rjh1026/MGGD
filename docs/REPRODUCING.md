# Using the Source Release

`MGGD_source.zip` extracts to `MGGD_source/`. It contains scientific code,
configurations, recorded prior parameters, and protocol documentation, not
results, table-audit records, MRI data, per-case manifests, images, checkpoints,
or execution-progress histories. The collected implementation is unchanged;
this is not a claim of exact paper reproduction. Read
[Known Differences](KNOWN_DIFFERENCES.md) before using it.

## Check the Files

```sh
python -m zipfile -e MGGD_source.zip .
cd MGGD_source
python verify_release.py
```

The standard-library-only validator checks recorded original-source SHA256
values, Python syntax, required configuration fields, and vendored code/license
presence. It checks file integrity only, not scientific validity or full
execution. It does not load MRI data or import scientific packages.

## Prepare Local Inputs

Obtain fastMRI data separately under its applicable terms. The
[README protocol](../README.md#experimental-protocol) describes the manuscript
design; the following are volume-disjoint training/validation/evaluation counts:

| Dataset | Acquisition | Training | Validation | Evaluation | Crop |
| --- | --- | ---: | ---: | ---: | --- |
| Brain | `AXT2` | 505 | 20 | 30 | 272 x 272 |
| Knee | `CORPDFS_FBK` | 147 | 20 | 30 | 320 x 320 |

Brain uses an internal holdout from the official training partition. Knee uses
the official training partition and separate subsets of the official validation
partition. Neither evaluation cohort is the target-hidden challenge test set.

Create local `train_manifest.csv`, `calibration_manifest.csv` (the validation
split), and `test_manifest.csv` (the evaluation split). Required columns are
`path` and `slice_idx`; slice indices are zero-based nonnegative integers.
Paths identify local HDF5 files and are absolute or relative to `--data-root`,
not the manifest directory. Preserve filenames, row order, slice indices, and
split membership when relocating an existing cohort; filenames affect seeds.
The wrapper checks file existence, counts, duplicates, and volume separation,
not HDF5 contents, patient identity, or agreement with the paper cohort.

The two manifest generators in [Source Map](SOURCE_MAP.md) can prepare new local
splits. Recorded preparation uses seed `20260709` and up to 8/1/3 central slices
per training/validation/evaluation volume. The brain generator requires exactly
555 usable `AXT2` volumes in its pool. The knee generator uses
`--train-fraction 1.0`, `--target-train-volumes 147`,
`--target-calibration-volumes 20`, and `--target-test-volumes 30`; it partitions
the available validation pool before selecting those counts. Matching counts
and seeds with a different pool does not recover the exact paper cohort.

## Preview and Run

Check [Environment](ENVIRONMENT.md) first. From the extracted source root:

```sh
python run_protocol.py --dataset brain --manifests-dir /local/manifests/brain --data-root /local/fastmri --out-dir /local/new-results/brain_interim
python run_protocol.py --dataset knee --manifests-dir /local/manifests/knee --data-root /local/fastmri --out-dir /local/new-results/knee
```

Replace example paths with local paths. These commands only print plans; they
do not validate inputs or execute experiments. After checking the environment
and plan, `--execute` launches classical reconstruction, GRAPPA, then deep
training/evaluation using the invoking Python. The data root uses
`brain_multicoil_train/`, `knee_multicoil_train/`, and `knee_multicoil_val/`;
explicit manifests determine the cases.

Protocol and parameter references:

- `configs/brain_recorded_settings.json` and
  `configs/knee_recorded_settings.json` in the source archive retain classical
  methods, R = 2/4/6/8, selected regularization, CUDA/float32, 15 IRLS iterations,
  CG maximum 150 and tolerance `1e-5`, wavelet settings, and seed `23`.
- `configs/brain_trained_prior.json` and
  `configs/knee_trained_prior.json` in the archive contain statistical prior
  estimates, not network checkpoints. A fresh run estimates priors from training
  inputs and selects parameters by validation SSIM; the wrapper does not load
  these recorded values as fixed inputs.
- `run_protocol.py` retains deep training at up to 50 epochs, batch size 1,
  zero loader workers, U-Net channels 32, VarNet channels 18 and 8 cascades,
  patience 7, one sample per volume per epoch, vendored models, and AMP.
  The inherited deep seed is `101`, distinct from the classical seed.
- The classical noise stage uses five evaluation volumes, one slice each,
  R = 8, 20 repeats, and noise standard deviation `0.01`, with signal, mask,
  and sensitivity maps fixed across repetitions. This is not a nine-method
  noise comparison. See the README for the manuscript measurement protocol.

Keep generated results, images, checkpoints, and run records outside the source
release. A nonempty output directory requires explicit `--execute --resume`
with the same wrapper plan and manifest hashes. Resume delegates to the
archival scripts; uninterrupted and resumed training are not guaranteed to
match bitwise.

## Optional Analysis of Your Local Results

`reproduce_tables.py` accepts user-supplied results; no result values are
packaged. With the analysis dependencies installed:

```sh
python reproduce_tables.py --results-root /local/results --out-dir /local/new-summaries
```

The input root must contain both `brain_interim/` and `knee/`, each with:

```text
classical/test_metrics_by_volume.csv
classical/test_noise_summary.csv
grappa/grappa_test_metrics_by_volume.csv
deep/fullscale_deep_test_metrics_by_volume.csv
```

Metric columns are `acceleration`, `method`, `case_id`, `NMSE`, `PSNR`, `SSIM`.
Each cohort needs 30 matched evaluation volumes for nine methods at each of
R = 2/4/6/8 (1,080 rows). Method names are `SENSE`, `Tikhonov`, `BE`,
`WaveletL1`, `TV`, `MGGD`, `GRAPPA`, `DL_UNet_full`, and `DL_VarNet_full`.
Noise inputs need five rows per included method at R = 8, with `method`,
`acceleration`, `median_variance`, `median_snr`, and `median_geff_ratio_vs_sense`.
The utility computes summaries and paired comparisons from those inputs only.
Use a new output directory because it overwrites its summary filenames; its
outputs do not establish reproduction of the manuscript tables or figures.
