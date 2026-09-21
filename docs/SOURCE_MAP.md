# Source Map

Paths below are relative to `MGGD_source/`, the top directory in
`MGGD_source.zip`. The release accompanies *Multiscale Multi-Coil MRI
Reconstruction with Bending-Energy and Generalized Gaussian Priors* by
Jehyeok Rew and Minjung Kyung.

| Path | Purpose |
| --- | --- |
| `README.md` | Manuscript protocol and release overview |
| `run_protocol.py` | Dry-run command plan; explicit execution and resume |
| `verify_release.py` | Standard-library-only file integrity checks |
| `reproduce_tables.py` | Summary calculations from user-supplied local results |
| `configs/{brain,knee}_recorded_settings.json` | Recorded solver settings and selected regularization parameters |
| `configs/{brain,knee}_trained_prior.json` | Recorded multiscale statistical prior parameters, not network weights |
| `provenance/source_files_sha256.csv` | Recorded hashes of nine original scientific scripts |
| `scripts/run_synthetic_mggd_experiment.py` | Synthetic multi-coil problem, operators, masks, and reconstruction routines |
| `scripts/run_fastmri_subset_experiment.py` | Local fastMRI loading and subset reconstruction helpers |
| `scripts/run_fastmri_manuscript_protocol.py` | Prior estimation, validation selection, classical evaluation, and noise analysis |
| `scripts/run_grappa_baseline_from_protocol.py` | GRAPPA-style baseline from a local classical protocol run |
| `scripts/run_fastmri_noise_from_protocol.py` | Noise-only analysis from a local protocol run |
| `scripts/run_fastmri_deep_fullscale.py` | Full-scale U-Net and VarNet training/evaluation, including vendored-model wrappers |
| `scripts/run_fastmri_deep_benchmarks.py` | Compact deep baselines and shared helpers |
| `scripts/prepare_fastmri_30pct_manifests.py` | Local split generation from training and official validation partitions |
| `scripts/prepare_fastmri_internal_holdout_manifests.py` | Local split generation from a single training pool |
| `external/fastMRI_official/` | Vendored fastMRI package, project metadata, and original license |
| `requirements-analysis.txt`, `requirements-reconstruction.txt` | Analysis pins and reconstruction dependency inventory |
| `THIRD_PARTY_NOTICES.md` | Attribution and separate code/data terms |

The original-source hashes apply to the nine scientific scripts, not the
documentation, wrappers, configurations, or vendor tree. The validator also
parses Python source and configuration structure and checks vendored-file
presence; it does not certify historical execution or scientific validity.

No result CSVs, table-audit records, MRI data, per-case manifests, images,
checkpoints, or execution-progress histories belong in this source archive.
The SHA256 index is source metadata, not an experimental result. Locally
generated outputs stay separate.

## Attribution and License Status

The vendored fastMRI snapshot is recorded at upstream commit
`91f2df4711adbb6d643df1810f234e4abcf5881b`. Retain its copyright notices and
MIT license at `external/fastMRI_official/LICENSE.md` in the archive, together with
[Third-Party Notices](../THIRD_PARTY_NOTICES.md). That license applies to its
respective third-party files, not automatically to the authors' code. An
authors' code license remains pending author choice; this documentation grants
none. MRI data must be obtained separately under the applicable fastMRI terms.
