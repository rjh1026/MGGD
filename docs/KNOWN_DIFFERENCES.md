# Manuscript Protocol and Collected Implementation

The [README](../README.md#experimental-protocol) describes the manuscript
protocol. This release preserves the scientific scripts collected on
2026-09-21 without correcting them. Recorded settings and prior parameters are
included; result values and execution histories are not. No reconstruction or
training rerun, validated runtime, or exact paper reproduction is claimed.

## FFT and Sampling Coordinates

In `scripts/run_synthetic_mggd_experiment.py`, `fft2c` and `ifft2c` use unshifted
NumPy FFTs, but `make_mask` places its contiguous block around the middle array
row. Zero frequency in unshifted ordering is at index zero, so that block is
not the low-frequency central region described by the manuscript. The CUDA
helpers in `scripts/run_fastmri_manuscript_protocol.py` are also unshifted;
the reference-image loader in `scripts/run_fastmri_subset_experiment.py` uses
centered transforms. This coordinate discrepancy remains unchanged. Changing
the convention requires new evaluation, not relabeling the archived code.

## VarNet Mask Interface

`OfficialVarNetWrapper.forward` in `scripts/run_fastmri_deep_fullscale.py` uses
`mask[:, :1, :]`. The generated mask varies across rows and is constant across
columns, so selecting its first row drops the row-varying sampling pattern
before passing it to VarNet. The network's centered Fourier convention also
needs to agree with the generated measurements. This unchanged implementation
does not establish the performance of a correctly matched official VarNet
baseline.

## Interpretation Limits

The collected code is distinct from the manuscript's intended protocol.
Original cohort manifests and a historical authors' revision/environment lock
are not supplied; matching counts and seeds alone cannot recover the exact
sample. Fresh runs estimate priors and select parameters using local training
and validation data rather than loading the recorded settings as fixed inputs.
See [Reproducing](REPRODUCING.md) and [Environment](ENVIRONMENT.md).

`verify_release.py` checks file integrity only (hashes, syntax, required fields,
and required files), not scientific validity or full execution. Its success
does not resolve either implementation issue above.
