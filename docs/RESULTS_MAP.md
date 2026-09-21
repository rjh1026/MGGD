# Manuscript results map

`results/` contains numeric summaries only. `reproduce_tables.py` recomputes them from case-level experiment CSVs obtained through the locally retained archive or a separately authorized experiment run.

| Submitted item | Numeric output or source | Aggregation |
|---|---|---|
| Table 1, brain fidelity | `results/stored_metric_summary.csv`, brain rows | Three slices per volume, then 30 volume means for each R and method |
| Table 2, brain noise | `results/stored_noise_summary.csv`, brain rows | Foreground median per case, then mean/median over five cases at R=8 |
| Table 3, knee fidelity | `results/stored_metric_summary.csv`, knee rows | Same volume-level procedure as Table 1 |
| Table 4, knee tests | `results/recomputed/table4_knee_BE_TV.csv` | Paired Wilcoxon; Holm across eight comparators per dataset/R/metric |
| Table 5, knee noise | `results/stored_noise_summary.csv`, knee rows | Same noise procedure as Table 2 |
| Table A1, brain tests | `results/recomputed/tableA1_brain_BE_TV_UNet.csv` | Paired mean differences, unadjusted t intervals, win rates, Holm-adjusted Wilcoxon |
| Figure 1, framework | Manuscript schematic; exact image retained locally | Not a reconstruction result |
| Figure 2, brain images | Local brain set 03 and exact submitted figure extraction | Approximate median proposed-method volume SSIM, R=2/4/6/8 |
| Figure 3, knee paired differences | Knee BE/TV rows in `results/recomputed/paired_statistics_recomputed.csv` | Unadjusted 95% t intervals for mean paired differences |
| Figure 4, knee images | Local knee sets 03/04 and exact submitted figure extraction | Cases nearest proposed-method SSIM quantiles 0.50/0.70 |

Original experiment directory names are `knee` and `brain_interim`. Each contains `classical`, `grappa`, `deep`, and `manifests`. Classical, GRAPPA, and deep volume-metric files are respectively `test_metrics_by_volume.csv`, `grappa_test_metrics_by_volume.csv`, and `fullscale_deep_test_metrics_by_volume.csv`. Noise cases are in `classical/test_noise_summary.csv`.

Positive paired differences mean comparator minus proposed for NMSE, and proposed minus comparator for PSNR/SSIM. Confidence intervals are for mean differences; Wilcoxon tests concern the paired difference distributions. The original protocol's all-pairs Holm family differs from the manuscript's eight-comparator family. Use the release analysis script for the manuscript family.

No raw MRI, reconstructed MRI, per-case data files or network weights are distributed here. Dataset access is through [fastMRI](https://fastmri.med.nyu.edu/), subject to its terms. Aggregate CSVs do not by themselves allow independent recalculation of per-volume tests; the analysis script requires the local case-level inputs.
