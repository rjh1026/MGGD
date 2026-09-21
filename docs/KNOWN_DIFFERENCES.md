# Submitted manuscript and archived implementation

This release preserves the code snapshot and saved outputs available on 2026-09-21. It does not silently repair the implementation or replace submitted results with new experiments. The submitted manuscript is **Multiscale Multi-Coil MRI Reconstruction with Bending-Energy and Generalized Gaussian Priors**, initial submission generated on 2026-09-20.

## Numerical table check

All 504 printed numerical entries in Tables 1-5 and Appendix Table A1 were compared with summaries recalculated from saved experiment CSV files. 499 match at the printed precision. The remaining five entries are in Table 3:

| Knee PSNR | Submitted | Saved mean, rounded |
|---|---:|---:|
| BE, R=2 | 39.43 | 39.42 |
| BE, R=6 | 33.79 | 33.78 |
| TV, R=8 | 32.56 | 32.55 |
| U-Net, R=6 | 24.79 | 24.78 |
| Proposed, R=6 | 34.13 | 34.12 |

Both versions are retained in `results/submission_numeric_audit.csv`. The table checks verify aggregation of existing results, not end-to-end reconstruction reproducibility or scientific validity of every comparison.

## FFT and sampling coordinates

The archived `fft2c` and `ifft2c` functions in `scripts/run_synthetic_mggd_experiment.py` use unshifted NumPy FFTs. The sampling mask allocates its contiguous block around the middle array row. In unshifted FFT ordering, zero frequency is at index zero, not the middle row. The CUDA implementation in `scripts/run_fastmri_manuscript_protocol.py` also uses unshifted FFTs, whereas the HDF5 reference-image loader uses centered transforms.

This is a discrepancy with the submitted description of a fully sampled low-frequency central region. The functions are archived unchanged. A corrected coordinate convention requires new evaluation and must not be presented as the code that produced the existing tables.

## VarNet mask interface

The archived `OfficialVarNetWrapper.forward` constructs the network mask using `mask[:, :1, :]`. The generated two-dimensional masks vary along rows and are constant along columns. Selecting their first row therefore does not preserve the full line-selection pattern for the official VarNet interface. The centered Fourier convention expected by the upstream network also needs to be reconciled with the generated measurements.

Consequently, the archived VarNet scores describe this specific implementation and do not establish the performance of a correctly matched official VarNet baseline. The wrapper is not changed in this archival release.

## Objective and covariance interpretation

The saved BE and MGGD coefficients multiply terms in the implemented normal operator. For unit data-fidelity scaling, objective coefficients are half the corresponding normal-operator coefficients; the MGGD weight additionally contains the global multiplier and the IRLS factor. A numerical ridge is also present. Do not substitute the stored coefficients into a differently scaled theoretical objective without conversion.

The noise experiments measure variance across magnitude reconstructions with repeated simulated noise and fixed sensitivity maps. They do not calculate the inverse Hessian in manuscript Equation 24. For a fixed linear quadratic estimator, repeated-measurement covariance has the sandwich form `H^-1 B H^-H`, where `B = A^H Sigma_y^-1 A`; an inverse surrogate Hessian is a different uncertainty quantity. No covariance-matrix or condition-number validation is included in these saved outputs.

## Scope of reproduction

- The local result archive contains exact submitted figure page excerpts and extracted embedded images. The older editable Figure 1 candidate is not certified as the final submitted layout.
- Brain evaluation uses a separate 30-volume subset of the available official training data, not the official challenge test set. Knee evaluation uses 30 volumes from the official validation set.
- Classical methods and GRAPPA share measurement draws; the deep methods use another base seed. BE and proposed methods use different BE strengths. These are not matched single-component ablations.
- The own-code historical experimental Git revision and full historical environment lock were not retained. This release's Git SHA identifies the archived release, not a retrospectively recovered execution-time commit.
- Full training and reconstruction have not been rerun for this release. Checkpoints, case-level results and MRI-derived images remain in the local archive. Exact-cohort reconstruction requires independently authorized fastMRI access and the original cohort manifests.

These items should be resolved with the authors before describing the release as a fully verified reproduction of the submitted physical acquisition protocol.
