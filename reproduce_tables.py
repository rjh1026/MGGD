"""Recompute manuscript summaries from archived CSVs, without MRI reconstruction."""
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

METHODS = ['SENSE', 'Tikhonov', 'BE', 'WaveletL1', 'TV', 'GRAPPA', 'DL_UNet_full', 'DL_VarNet_full']
METRICS = ['NMSE', 'PSNR', 'SSIM']


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def holm(p):
    result = np.empty(len(p))
    running = 0.0
    for rank, idx in enumerate(np.argsort(p)):
        running = max(running, (len(p) - rank) * p[idx])
        result[idx] = min(1.0, running)
    return result


def summarize(root, out):
    means, comparisons, noises = [], [], []
    for dataset, dirname in [('brain', 'brain_interim'), ('knee', 'knee')]:
        base = root / dirname
        records = []
        for group, filename in [('classical', 'test_metrics_by_volume.csv'), ('grappa', 'grappa_test_metrics_by_volume.csv'), ('deep', 'fullscale_deep_test_metrics_by_volume.csv')]:
            records.extend(read_csv(base / group / filename))
        index = {}
        for row in records:
            key = (int(row['acceleration']), row['method'], row['case_id'])
            if key in index:
                raise ValueError(f'Duplicate observation: {key}')
            index[key] = row
        if len(index) != 1080:
            raise ValueError(f'{dataset}: expected 1080 volume/method/acceleration rows, found {len(index)}')
        for r in [2, 4, 6, 8]:
            ids = sorted(case for acc, method, case in index if acc == r and method == 'MGGD')
            if len(ids) != 30:
                raise ValueError('Expected exactly 30 evaluation volumes')
            for method in METHODS + ['MGGD']:
                if {case for acc, m, case in index if acc == r and m == method} != set(ids):
                    raise ValueError(f'Unmatched volume set: {dataset}, R={r}, {method}')
                for metric in METRICS:
                    values = np.array([float(index[r, method, case][metric]) for case in ids])
                    if not np.isfinite(values).all():
                        raise ValueError('Nonfinite metric')
                    means.append({'dataset': dataset, 'R': r, 'method': method, 'metric': metric, 'n': 30, 'mean': float(values.mean()), 'std': float(values.std(ddof=1))})
            for metric in METRICS:
                family = []
                proposed = np.array([float(index[r, 'MGGD', case][metric]) for case in ids])
                for method in METHODS:
                    comparator = np.array([float(index[r, method, case][metric]) for case in ids])
                    diff = comparator - proposed if metric == 'NMSE' else proposed - comparator
                    half = stats.t.ppf(0.975, 29) * stats.sem(diff)
                    p = 1.0 if np.allclose(diff, 0.0) else float(stats.wilcoxon(diff, zero_method='wilcox', alternative='two-sided').pvalue)
                    family.append({'dataset': dataset, 'R': r, 'comparator': method, 'metric': metric, 'n_pairs': 30, 'mean_difference': float(diff.mean()), 'ci95_low': float(diff.mean() - half), 'ci95_high': float(diff.mean() + half), 'win_rate': float(np.mean(diff > 0)), 'wilcoxon_p': p})
                for row, p in zip(family, holm([x['wilcoxon_p'] for x in family])):
                    row['p_holm'] = float(p)
                    comparisons.append(row)
        grouped = defaultdict(list)
        for row in read_csv(base / 'classical/test_noise_summary.csv'):
            grouped[row['method']].append(row)
        for method, rows in grouped.items():
            if len(rows) != 5 or {int(x['acceleration']) for x in rows} != {8}:
                raise ValueError('Expected five noise cases at R=8')
            var = np.array([float(x['median_variance']) for x in rows])
            snr = np.array([float(x['median_snr']) for x in rows])
            noises.append({'dataset': dataset, 'R': 8, 'method': method, 'n': 5, 'variance_mean': float(var.mean()), 'variance_median': float(np.median(var)), 'snr_mean': float(snr.mean()), 'snr_median': float(np.median(snr)), 'geff_ratio': float(np.mean([float(x['median_geff_ratio_vs_sense']) for x in rows]))})
    write_csv(out / 'metric_summary_recomputed.csv', means)
    write_csv(out / 'paired_statistics_recomputed.csv', comparisons)
    write_csv(out / 'noise_summary_recomputed.csv', noises)
    write_csv(out / 'table4_knee_BE_TV.csv', [x for x in comparisons if x['dataset'] == 'knee' and x['comparator'] in ['BE', 'TV']])
    write_csv(out / 'tableA1_brain_BE_TV_UNet.csv', [x for x in comparisons if x['dataset'] == 'brain' and x['comparator'] in ['BE', 'TV', 'DL_UNet_full']])
    print(f'Wrote {len(means)} means, {len(comparisons)} paired comparisons, {len(noises)} noise summaries to {out}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results-root', type=Path, required=True, help='Directory containing knee/ and brain_interim/')
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    summarize(args.results_root, args.out_dir)
