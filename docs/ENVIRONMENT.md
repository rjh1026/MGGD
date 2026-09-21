# Environment

The release provides dependency information, not a validated reconstruction
environment or a historical environment lock.

## File Checks and Preview

Use Python 3.9 or later for `verify_release.py` and `run_protocol.py` previews.
Both use only the standard library. The validator parses code without importing
it, and a preview does not probe scientific dependencies or CUDA.

## Local Result Analysis

`requirements-analysis.txt` pins NumPy `2.0.2` and SciPy `1.13.1` for the separate
table utility, not reconstruction.

```sh
python -m pip install -r requirements-analysis.txt
python reproduce_tables.py --help
```

Actual analysis requires the user's local CSV inputs described in
[Reproducing](REPRODUCING.md); no measurements are bundled.

## Reconstruction Dependencies

`requirements-reconstruction.txt` is an unpinned dependency inventory, not a
tested installation recipe. It lists NumPy, SciPy, pandas, h5py, PyWavelets,
scikit-image, matplotlib, PyTorch, requests, PyYAML, and tqdm. A candidate
environment needs mutually compatible builds and CUDA for the classical
launcher settings. The wrapper preserves CUDA/float32 and deep AMP; it does
not install packages or change numerical implementations.

**FFT API compatibility remains unresolved.** The authors' CUDA helpers call
legacy `torch.fft(x, 2, normalized=True)` and
`torch.ifft(x, 2, normalized=True)`. The vendored `fastmri/fftc.py` uses
`torch.fft.fftn`/`ifftn` and `view_as_complex`/`view_as_real`. A working unchanged
combination across both code trees has not been verified. Neither the newest
PyTorch nor a successful import alone establishes compatibility.

The deep runner imports from `external/fastMRI_official/`. Retain that source
and its `LICENSE.md`, rather than substituting an installed fastMRI version.
The recorded upstream commit is `91f2df4711adbb6d643df1810f234e4abcf5881b`.
The dependency inventory covers the source-import workflow, not every optional
upstream training-framework feature.

Before execution, check package imports, both FFT paths, CUDA operations, and
model execution in the intended environment. Record exact versions and hardware
for that run. This release does not include compatibility corrections.

The wrapper uses its invoking Python for children and sets `OMP_NUM_THREADS`,
`MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, and `NUMEXPR_NUM_THREADS` to `4`.
These are requested settings, not measured CPU, RAM, or GPU-memory guarantees.
