# MGGD

Archival code and aggregate results accompanying the manuscript **Multiscale Multi-Coil MRI Reconstruction with Bending-Energy and Generalized Gaussian Priors**, by Jehyeok Rew and Minjung Kyung, submitted to Magnetic Resonance in Medicine.

Repository destination: [github.com/rjh1026/MGGD](https://github.com/rjh1026/MGGD).

The release contains reconstruction scripts, recorded settings and prior estimates, and a separate table-recalculation utility. It covers nine methods at acceleration factors R = 2, 4, 6, and 8: SENSE, Tikhonov, BE, WaveletL1, TV, MGGD, GRAPPA, fastMRI U-Net, and fastMRI VarNet.

| Cohort | Training / calibration / evaluation volumes | Crop |
| --- | --- | --- |
| Brain AX T2 (`AXT2`), internal holdout from the training partition | 505 / 20 / 30 | 272 x 272 |
| Knee (`CORPDFS_FBK`), training partition and held-out validation subsets | 147 / 20 / 30 | 320 x 320 |

## Use

The **complete source and aggregate-results tree** is distributed as [MGGD_source_results.zip](MGGD_source_results.zip). The top-level scripts and `docs/` are also displayed for convenient inspection. Download the archive and extract it before running commands; it includes all scientific scripts, vendored model code and its license, configurations, and CSV results. The archive contains no MRI images, case-level data, or trained network checkpoints.

```sh
python -m zipfile -e MGGD_source_results.zip .
cd MGGD_source_results
python verify_release.py
```

See [Reproducing](docs/REPRODUCING.md) for table recalculation, local manifests, and reconstruction commands, and [Environment](docs/ENVIRONMENT.md) before installing dependencies. A command preview requires only Python:

```sh
python run_protocol.py --dataset brain --manifests-dir /local/manifests/brain --data-root /local/fastmri --out-dir /local/new-results/brain_interim
```

The wrapper is dry-run by default. Only `--execute` starts reconstruction and training; `--resume` explicitly permits reuse of an existing nonempty run directory.

## Reproducibility Limits

**Scientific implementation differences are documented, not corrected in this archive.** Inspection found a mismatch between the FFT coordinate convention and the central sampling-mask placement, and a VarNet mask-handling mismatch. These affect interpretation of the stated sampling protocol and the VarNet comparison, beyond ordinary environment or rounding uncertainty. Read [Known Differences](docs/KNOWN_DIFFERENCES.md) before using these archived scores as evidence of the intended protocol or a correctly matched official VarNet baseline.

Code was collected on **2026-09-21**. The historical revision of the authors' code and a historical environment lock were not retained. Bitwise end-to-end reproduction has not been verified. The current host has binary-incompatible packages and is not a validated reconstruction environment.

Obtain data independently under the fastMRI terms. Exact cohort manifests, images, and trained neural-network weights remain local-only. Generating an equivalent split from another available cohort does not recover the exact paper sample. Recalculated summaries are distinct from submitted numbers; this release does not claim that all manuscript figures have been reproduced. See [Known Differences](docs/KNOWN_DIFFERENCES.md).

The reported table audit matched 499 of 504 checked cells; five PSNR cells differed by 0.01, with no other differences among the audited cells. This is a table check, not an end-to-end reconstruction result.

## Attribution and License Status

The vendored fastMRI source is recorded at clean commit `91f2df4711adbb6d643df1810f234e4abcf5881b`; its license is retained at `external/fastMRI_official/LICENSE.md` inside the source archive. A license for the authors' source code is pending author choice. This documentation grants no new license and does not extend the third-party license to the authors' code.
