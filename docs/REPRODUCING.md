# Reproducing the Archived Protocol

This guide separates recalculation of stored measurements from a new MRI reconstruction run. Neither is a verified bitwise reproduction of the submitted manuscript. Read [Known Differences](KNOWN_DIFFERENCES.md) when comparing outputs with submitted numbers.

Commands below assume the release layout contains `run_protocol.py`, `reproduce_tables.py`, `scripts/`, `configs/`, and `external/fastMRI_official/` at the repository root. All example input and output paths are placeholders for local paths. Keep new results separate from the archive.

## 1. Recalculate Tables Without Reconstruction

Use the analysis-only dependencies described in [Environment](ENVIRONMENT.md). The supplied `reproduce_tables.py` consumes previously computed CSV measurements; it does not load MRI images or train a model. It does read volume-level measurements, so retain these inputs locally if they are not part of the distributed archive.

```sh
python reproduce_tables.py --results-root /local/archived-results --out-dir /local/new-table-calculation
```

The results root must contain both `brain_interim/` and `knee/`, each with:

```text
classical/test_metrics_by_volume.csv
classical/test_noise_summary.csv
grappa/grappa_test_metrics_by_volume.csv
deep/fullscale_deep_test_metrics_by_volume.csv
```

For each cohort the utility requires 30 matched evaluation volumes for every method at each R, totaling 1,080 volume/method/acceleration rows. Its metric summaries use NMSE, PSNR, and SSIM with sample standard deviations. Paired differences are oriented so a positive value favors MGGD. It calculates t-based confidence intervals and two-sided Wilcoxon comparisons, with Holm adjustment over eight comparators within each cohort/R/metric family. Noise summaries require five cases per included method at R = 8. These describe the utility's calculations, not new findings.

The utility writes:

- `metric_summary_recomputed.csv`
- `paired_statistics_recomputed.csv`
- `noise_summary_recomputed.csv`
- `table4_knee_BE_TV.csv`
- `tableA1_brain_BE_TV_UNet.csv`

Label these as **recalculated**, even when a filename refers to a manuscript table. Do not replace or relabel the submitted numbers automatically. Use a new output directory: unlike `run_protocol.py`, this utility has no nonempty-directory refusal. It does not recreate manuscript layouts or establish reproduction of all figures.

The completed table audit reported by the release team checked 504 cells: 499 matched and five PSNR cells differed by 0.01. No other differences were reported within those audited cells. This documentation preparation did not rerun that audit; see [Known Differences](KNOWN_DIFFERENCES.md) for the cell-level account.

## 2. Obtain Data and Prepare Local Manifests

Obtain fastMRI data independently under the fastMRI terms. This release does not supply data, exact cohort manifests, reconstructed images, or trained neural-network weights. The prior estimates in `configs/*_trained_prior.json` are recorded statistical estimates, not neural-network weights.

The manuscript protocol uses the following volume-disjoint partitions:

| Wrapper dataset | Acquisition | Training | Calibration | Evaluation | Source partitions |
| --- | --- | ---: | ---: | ---: | --- |
| `brain` | `AXT2` | 505 | 20 | 30 | Internal holdout from the official training partition only |
| `knee` | `CORPDFS_FBK` | 147 | 20 | 30 | Official training partition; separate calibration/evaluation subsets of the official validation partition |

Neither evaluation set is the target-hidden official challenge test set. The brain run retains the script label `brain_AXT2_internal_holdout` and the knee run uses `knee_CORPDFS_FBK`.

Supply a directory containing `train_manifest.csv`, `calibration_manifest.csv`, and `test_manifest.csv`. Each CSV must have at least:

```csv
path,slice_idx
brain_multicoil_train/example_volume.h5,12
```

This row illustrates syntax only. `slice_idx` is a zero-based nonnegative integer. Paths must identify local HDF5 files; use forward slashes for portable relative paths. Absolute paths must be valid on the machine running the experiment. Relative paths are interpreted against `--data-root`, **not** the manifest directory. Preserve original volume filenames, row order, slice indices, and split membership when relocating the same cohort: the archival scripts derive identifiers and random seeds from filenames. The wrapper does not rewrite manifests or remap unavailable absolute paths.

The source generators request up to eight central training slices, one central calibration slice, and three central evaluation slices per volume. Deep training then uses the existing one-sample-per-volume-per-epoch option. The wrapper checks the CSV schema, duplicate observations, volume counts, and path/volume-identifier separation across splits before execution. It checks that referenced files exist, but does not inspect HDF5 contents, acquisition metadata, slice bounds, or patient identity. These checks do not establish that a supplied cohort matches the paper sample.

### Equivalent Split Generation

The archived generators can prepare local manifests from independently available data. These commands are optional data preparation, not part of the wrapper, and read HDF5 data. They must use new manifest directories.

Brain, with a pool containing **exactly 555 usable AX T2 volumes** from the training partition:

```sh
python scripts/prepare_fastmri_internal_holdout_manifests.py --dataset-name brain_AXT2_internal_holdout --pool-dir /local/fastmri/brain_multicoil_train --out-dir /local/manifests/brain --acquisition AXT2 --train-volumes 505 --calibration-volumes 20 --test-volumes 30 --train-slices-per-volume 8 --calibration-slices-per-volume 1 --test-slices-per-volume 3 --seed 20260709
```

The brain generator requires the discovered pool size to equal the requested total. It does not automatically choose 555 from a larger collection. Define and document a suitable local pool separately.

Knee, with enough matching volumes for the requested partitions:

```sh
python scripts/prepare_fastmri_30pct_manifests.py --dataset-name knee_CORPDFS_FBK --train-dir /local/fastmri/knee_multicoil_train --source-val-dir /local/fastmri/knee_multicoil_val --out-dir /local/manifests/knee --acquisition CORPDFS_FBK --train-fraction 1.0 --target-train-volumes 147 --target-calibration-volumes 20 --target-test-volumes 30 --train-slices-per-volume 8 --calibration-slices-per-volume 1 --test-slices-per-volume 3 --seed 20260709
```

The knee generator partitions the available validation pool before selecting the requested calibration and evaluation counts and refuses insufficient partitions. Identical seeds and counts with a different available pool do **not** reproduce the exact paper sample. Report such outputs as a new cohort run, not recovered submitted results.

## 3. Preview or Execute the Protocol

Use a clean, separately checked reconstruction environment; the current archival host package combination is not valid. See [Environment](ENVIRONMENT.md).

```sh
python run_protocol.py --dataset brain --manifests-dir /local/manifests/brain --data-root /local/fastmri --out-dir /local/new-results/brain_interim
python run_protocol.py --dataset knee --manifests-dir /local/manifests/knee --data-root /local/fastmri --out-dir /local/new-results/knee
```

These commands only print a JSON plan. They do not create directories, read manifest contents or MRI files, import scientific packages, or start subprocesses. A successful preview is not an environment or data validation. `--repo-root /local/MGGD` optionally selects the release root when the wrapper is staged elsewhere.

After checking the plan, add `--execute` to launch the three stages sequentially. Each stage uses `sys.executable`, so run the wrapper with the intended environment's Python. The child working directory is `--data-root`; scripts and manifest arguments use absolute paths. Use the conventional subdirectories `brain_multicoil_train`, `knee_multicoil_train`, and `knee_multicoil_val` under that root. Explicit manifests determine the actual cases; the directory arguments do not select additional data when manifests are supplied.

| Stage | Archival script | Methods |
| --- | --- | --- |
| Classical | `scripts/run_fastmri_manuscript_protocol.py` | SENSE, Tikhonov, BE, WaveletL1, TV, MGGD |
| GRAPPA | `scripts/run_grappa_baseline_from_protocol.py` | GRAPPA |
| Deep | `scripts/run_fastmri_deep_fullscale.py` | `DL_UNet_full`, `DL_VarNet_full` using vendored fastMRI models |

All nine methods use R = 2, 4, 6, 8. The wrapper preserves the launcher options and remaining archival defaults:

- Brain crop 272; knee crop 320; `--coils 0` in both classical and deep stages.
- Classical solver: CUDA, float32, 15 IRLS iterations, CG maximum 150; inherited CG relative tolerance `1e-5`, noise sigma `0.01`, and seed `23`.
- Classical noise experiment: 20 repeats, up to five evaluation volumes, R = 8 only. This is not a nine-method noise experiment.
- GRAPPA uses the classical run summary and inherits its accelerations; its original calibration and numerical implementation are unchanged.
- Deep: 50 maximum epochs, batch size 1, zero loader workers, U-Net channels 32, VarNet channels 18 and 8 cascades, patience 7, one sample per volume per epoch, official models, saved figures, and AMP. Its inherited seed is `101`, not the classical seed.
- Child environment: `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, and `NUMEXPR_NUM_THREADS` are each set to `4`. The classical launcher also retains its four-core resource option and low-priority option. These are configured limits, not measured resource guarantees.

The wrapper changes orchestration only. It does not replace kernels, refit rules, validation grids, losses, precision choices, or metrics. In particular, it does not substitute CPU/float64 for the classical CUDA/float32 path or replace the deep AMP path with float32-only training.

### Recorded Settings Are Not Fresh-Run Inputs

`configs/brain_recorded_settings.json` and `configs/knee_recorded_settings.json` record settings and selected parameters. The corresponding `*_trained_prior.json` files record earlier estimates. On a fresh run, the original classical script estimates a prior from the supplied training manifest and tunes parameters on the supplied calibration manifest. The wrapper does not copy the recorded estimates into a run or force the earlier selected parameters. Values can differ on a new cohort or environment.

## 4. Outputs and Resume

The wrapper writes `run_protocol_record.json` and stage subdirectories `classical/`, `grappa/`, and `deep/` inside the selected output directory. Important stage summaries include:

- `classical/test_metric_summary_by_volume.csv`
- `classical/test_noise_summary.csv`
- `grappa/grappa_test_metric_summary_by_volume.csv`
- `deep/fullscale_deep_test_metric_summary_by_volume.csv`

The scientific scripts also write local per-case measurements, images, and deep checkpoints. Their presence is not a claim that all submitted figures or numbers have been reproduced. Keep these new outputs local and separate from the public release.

A nonempty output directory is refused unless `--resume` is explicit. To continue a wrapper-created run, repeat the same command with both `--execute --resume`. The wrapper compares its recorded command plan and manifest hashes; changed inputs or a missing wrapper record require a new output directory. The record does not establish unchanged data contents, installed packages, or archival source contents. Do not modify them while resuming, and do not run concurrent executions into the same directory.

Resume delegates to the original implementations. Classical prior/validation caches and deep checkpoints can be reused. For brain, the wrapper also retains the original launcher's completed-artifact checks for the classical and GRAPPA stages. For knee, GRAPPA runs again because its script has no resume flag. Existing derived summaries may be regenerated during an explicitly resumed run. Deep checkpoints do not store all random-generator states; resumed training is not guaranteed to match an uninterrupted run bitwise. A failed child stops subsequent stages and leaves existing outputs in place.

## Archival Boundaries

Collection date: 2026-09-21. A historical authors' code revision and environment lock were not retained. The vendored fastMRI tree is recorded at clean commit `91f2df4711adbb6d643df1810f234e4abcf5881b`, with its [license](../external/fastMRI_official/LICENSE.md). This identifies the third-party snapshot, not a historical revision for the authors' code. No end-to-end reconstruction experiment was run to prepare this wrapper and documentation. No new scientific result or blanket figure-reproduction claim is made.
