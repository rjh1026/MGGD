# Environment

There is no retained historical environment lock for the authors' experiments. The code was collected on 2026-09-21, not checked out from a retained historical authors' revision. A new installation must be treated as a candidate environment until independently checked. No bitwise end-to-end reproduction is verified.

## Wrapper Preview

`run_protocol.py` uses only the Python standard library and supports Python 3.9 or later. A dry run does not import reconstruction packages or probe CUDA. It always uses the invoking interpreter (`sys.executable`) for child commands; it neither creates an environment nor chooses another Python installation.

## Analysis Only

`requirements-analysis.txt` pins NumPy 2.0.2 and SciPy 1.13.1, the tested analysis versions recorded for this release. This narrow pair supports the separate CSV table-recalculation workflow; it is not a reconstruction environment lock or evidence of end-to-end reproducibility.

In a clean analysis environment, install:

```sh
python -m pip install -r requirements-analysis.txt
python reproduce_tables.py --help
```

No PyTorch, HDF5 reader, or MRI data is required for that utility. Its actual calculation needs the archived input CSVs described in [Reproducing](REPRODUCING.md). Do not infer reconstruction compatibility from a successful table calculation.

## Reconstruction: Candidate Environment Only

Use a separate clean environment with mutually compatible Python, NumPy, SciPy, pandas, h5py, PyWavelets, scikit-image, matplotlib, and CUDA-enabled PyTorch builds. `requirements-reconstruction.txt` lists the dependencies used by the local scripts and their vendored model import path. It deliberately does not pin a historical combination. Installing the newest resolved packages is not a validated recipe.

Treat this file as an inventory, not an instruction to install the newest PyTorch. In particular, do not assume PyTorch 2.x can run the unchanged code. Select and check the full dependency combination, CUDA runtime, and hardware before execution; no validated reconstruction version combination is prescribed here.

### FFT Compatibility Is Unresolved

The authors' CUDA protocol calls the legacy `torch.fft(x, 2, normalized=True)` and `torch.ifft(x, 2, normalized=True)` APIs. The copied deep helper also contains these calls. By contrast, the inspected vendored `fastmri/fftc.py` imports `torch.fft` and calls `torch.fft.fftn` and `torch.fft.ifftn` with `view_as_complex`/`view_as_real`; it is not a legacy FFT wrapper. Its package metadata declares `torch>=1.8`, but that declaration alone does not establish compatibility with the authors' legacy calls.

The current host's PyTorch 1.7.1+cu110 is not necessarily inappropriate for the authors' legacy CUDA code. The supplied host still has NumPy-related binary incompatibilities, and a working unchanged combination across both source trees has not been verified. A successful import is insufficient to settle the FFT issue. The wrapper neither replaces these calls nor installs a compatibility shim. Resolve and document this issue independently before executing the full protocol; do not silently modernize the archived scientific code.

The deep script prepends `external/fastMRI_official` to its import path and imports the vendored U-Net and VarNet implementations. Retain that directory and its `LICENSE.md`; do not replace it with an arbitrary installed fastMRI version. The recorded third-party clean commit is `91f2df4711adbb6d643df1810f234e4abcf5881b`. The reconstruction list covers this source-import workflow, not all optional upstream training-framework dependencies declared in fastMRI's packaging metadata.

Before a costly run, check imports in the intended environment without launching training or reading a dataset:

```sh
python -m pip check
python -c "import numpy, scipy, pandas, h5py, pywt, skimage, matplotlib, torch; print('Core imports passed'); print('CUDA available:', torch.cuda.is_available())"
python -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path('external/fastMRI_official').resolve())); from fastmri.models import Unet, VarNet; print('Vendored model imports passed')"
```

Run the last command from the repository root. These checks do not establish numerical correctness, CUDA kernel execution, or successful model training. If they fail, stop before the full protocol and repair the candidate environment without editing the archived scientific scripts. Any later compatibility changes must be tracked separately and disclosed in [Known Differences](KNOWN_DIFFERENCES.md).

For an independently validated environment, retain its exact Python/package versions, platform and accelerator details, and the result of each check alongside the new local run. Do not describe that new record as the missing historical lock.

## Current Host Is Not a Valid Recipe

The following host inventory was supplied for the archive. It has binary incompatibilities and must **not** be prescribed as a working reconstruction environment:

| Component | Reported version |
| --- | --- |
| Python | 3.9.13 |
| NumPy | 2.0.2 |
| SciPy | 1.13.1 |
| pandas | 2.3.3 |
| h5py | 3.7.0 |
| PyWavelets | 1.3.0 |
| scikit-image | 0.19.2 |
| matplotlib | 3.9.4 |
| PyTorch | 1.7.1+cu110 |

Only the invoking Python version was checked during wrapper preparation; the supplied host inventory is not a new successful import or reconstruction test. Do not copy it into a reconstruction lock file. In particular, the tested analysis pair does not validate older compiled HDF5, wavelet, image-processing, or PyTorch extensions in the same environment. The exact historical revision of the authors' code is unavailable, so the collected code cannot establish which historical FFT implementation or environment was used end to end.

## Runtime Settings

The wrapper sets `OMP_NUM_THREADS=4`, `MKL_NUM_THREADS=4`, `OPENBLAS_NUM_THREADS=4`, and `NUMEXPR_NUM_THREADS=4` before starting each child. It preserves classical CUDA/float32 and the deep script's AMP option. These requested thread settings are not measured limits on total CPU use, RAM, or GPU memory. Availability of a compatible CUDA environment remains a prerequisite for the classical stage; a successful dry run does not establish it.
