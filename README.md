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

## Experimental Protocol

Sections 3.2-3.4 of the submitted manuscript describe the following experimental design. The knee analysis uses 147 coronal PD-FS training volumes and a separate subset of 50 official validation volumes, divided into 20 validation and 30 evaluation volumes. The brain analysis uses 555 axial T2-weighted volumes from the official training set, divided into 505 training, 20 validation, and 30 evaluation volumes. The training, validation, and evaluation subsets are used for prior estimation and network training, parameter and model selection, and final performance assessment, respectively.

Reconstruction quality is evaluated at acceleration factors R = 2, 4, 6, and 8 using NMSE, PSNR, and SSIM. Regularization parameters are selected separately for the knee and brain datasets by maximizing mean validation SSIM and are fixed during evaluation. Slice-level metrics are averaged within each volume, giving 30 paired observations per dataset at each acceleration factor.

The noise analysis uses five evaluation volumes from each dataset at R = 8, with one slice per volume. Each case is reconstructed 20 times with independently generated circular complex Gaussian noise of standard deviation 0.01 added at sampled locations. The underlying signal, sampling mask, and sensitivity maps remain fixed across repetitions. Noise performance is summarized using magnitude variance, SNR, and the empirical effective geometry-factor ratio relative to SENSE.

The source archive provides reconstruction and analysis scripts, recorded settings, prior estimates, and aggregate numerical results. Execution instructions and environment requirements are provided in [Reproducing](docs/REPRODUCING.md) and [Environment](docs/ENVIRONMENT.md). MRI data must be obtained separately through [fastMRI](https://fastmri.med.nyu.edu/) under its applicable terms. Documented differences between the archived implementation and the manuscript, together with table-level comparisons, are retained in [Implementation and results notes](docs/KNOWN_DIFFERENCES.md).

## Attribution and License Status

The vendored fastMRI source is recorded at clean commit `91f2df4711adbb6d643df1810f234e4abcf5881b`; its license is retained at `external/fastMRI_official/LICENSE.md` inside the source archive. A license for the authors' source code is pending author choice. This documentation grants no new license and does not extend the third-party license to the authors' code.
