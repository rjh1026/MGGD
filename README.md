# MGGD

Source code, recorded settings, and the experimental protocol for **Multiscale Multi-Coil MRI Reconstruction with Bending-Energy and Generalized Gaussian Priors**, by Jehyeok Rew and Minjung Kyung, submitted to Magnetic Resonance in Medicine.

This code-only release includes reconstruction and analysis scripts, prior parameters, and the required fastMRI model source. Experiment results, table-audit records, execution logs, MRI images, exact cohort manifests, and trained network weights are not included.

## Source Code

Download [MGGD_source.zip](MGGD_source.zip) for the complete source tree. The top-level utilities and documentation are also available directly in this repository.

```sh
python -m zipfile -e MGGD_source.zip .
cd MGGD_source
python verify_release.py
```

The verification utility checks source-file integrity and configuration structure. It does not run an MRI experiment or certify agreement with the manuscript's results. See [Source map](docs/SOURCE_MAP.md), [Usage](docs/REPRODUCING.md), and [Environment](docs/ENVIRONMENT.md).

## Experimental Protocol

The following summarizes the manuscript protocol. Training data are used for prior estimation and network training, validation data for parameter and checkpoint selection, and evaluation data for final assessment. The three subsets are disjoint at the volume level.

| Dataset | Data source | Training / validation / evaluation volumes | Image matrix |
| --- | --- | --- | --- |
| Brain axial T2, AXT2 | 555 volumes from the official fastMRI training partition | 505 / 20 / 30 | 272 x 272 |
| Knee coronal PD-FS, CORPDFS_FBK | 147 training volumes and 50 volumes from the official validation partition | 147 / 20 / 30 | 320 x 320 |

All receiver channels are retained. Each slice is normalized by the 99th percentile of its k-space magnitude. Sensitivity maps for SENSE and the regularized methods are derived from fully sampled coil images and remain fixed during reconstruction. VarNet estimates sensitivities internally.

The manuscript specifies variable-density Cartesian sampling at R = 2, 4, 6, and 8, a fully sampled central low-frequency region, and circular complex Gaussian noise with standard deviation 0.01 at sampled locations. The archived implementation differences affecting this specification and the VarNet input are stated below.

| Reconstruction setting | Value |
| --- | --- |
| Wavelet transform | Daubechies-4, three levels, periodization |
| GGD shape-parameter search interval | 0.25 to 4.0 |
| IRLS iterations | 15 |
| Conjugate-gradient limit / relative residual tolerance | 150 / 1e-5 |
| IRLS smoothing / numerical ridge | 1e-6 / 1e-6 |
| Tikhonov and BE coefficients | 8e-3 |
| Wavelet L1 and TV coefficients | 1.6e-3 |
| Proposed BE coefficient / global MGGD scale | 2e-3 / 3.2e-5 |

The coefficients above follow the archived normal-operator convention. The complete recorded settings and prior parameters are in `configs/` inside the archive. Regularization selection uses mean validation SSIM over 20 volumes and four acceleration factors, with the selected settings fixed during evaluation.

U-Net uses 32 initial channels, four pooling levels, and no dropout. VarNet uses eight cascades, 18 regularizer channels, and eight sensitivity-estimation channels, with four pooling levels in both subnetworks. Training uses random initialization, Adam with learning rate 2e-4 and weight decay 1e-6, batch size one, mixed precision, and MAE plus 0.25 times MSE. The maximum is 50 epochs, with an SSIM improvement threshold of 1e-4 and early-stopping patience of seven epochs.

GRAPPA uses up to four source phase-encoding lines, five readout samples per line, a maximum phase-encoding offset of 16, and ridge coefficient 1e-3. Kernel calibration uses the central sampled region.

Evaluation uses NMSE, PSNR, and SSIM averaged within each of 30 volumes. Paired comparisons use Student-t confidence intervals and two-sided Wilcoxon tests with Holm adjustment across eight comparators for each dataset, acceleration factor, and metric. The noise protocol uses five evaluation volumes per dataset at R = 8 and 20 noise repetitions per case, summarized using magnitude variance, SNR, and the empirical noise ratio relative to SENSE.

## Implementation Notes

The supplied code is an unchanged collected implementation, not a verified end-to-end reproduction of the manuscript protocol. Its FFT ordering and central-mask placement use different frequency coordinates, and its VarNet wrapper does not preserve the row-varying sampling mask. See [Implementation notes](docs/KNOWN_DIFFERENCES.md) before using these components; this release does not include corrected experiment results.

## Data and Attribution

Obtain MRI data separately through [fastMRI](https://fastmri.med.nyu.edu/) under its applicable terms. The package does not provide the original cohort identifiers or network checkpoints.

The vendored fastMRI source is recorded at commit `91f2df4711adbb6d643df1810f234e4abcf5881b`. Its license is retained at `external/fastMRI_official/LICENSE.md` in the archive. A license for the authors' source code is pending author choice; the third-party license does not apply automatically to the authors' code.
