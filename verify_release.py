"""Verify archived source bytes and numerical-audit completeness without MRI data."""
from __future__ import annotations

import ast
import csv
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def rows(relative):
    with (ROOT / relative).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def main():
    sources = rows('provenance/source_files_sha256.csv')
    for row in sources:
        data = (ROOT / row['path']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == row['sha256'], row['path']
        ast.parse(data.decode('utf-8-sig'), filename=row['path'])
    a = rows('results/submission_numeric_audit.csv')
    b = rows('results/submitted_tables_2_4_5_A1_audit.csv')
    assert len(a) == 216 and len(b) == 288
    mismatches = [x for x in a + b if x['matches_printed'] != 'True']
    assert len(mismatches) == 5
    assert all(x['table'] == '3' and x['metric'] == 'PSNR' for x in mismatches)
    expected = {('BE', '2'), ('BE', '6'), ('TV', '8'), ('U-Net', '6'), ('Proposed', '6')}
    assert {(x['method'], x['R']) for x in mismatches} == expected
    assert len(rows('results/recomputed/paired_statistics_recomputed.csv')) == 192
    assert len(rows('results/stored_noise_summary.csv')) == 12
    print(f'Verified {len(sources)} unchanged source files and 504 table audit entries.')
    print('499 printed numbers match; 5 documented Table 3 PSNR differences remain.')
    print('This check does not rerun MRI reconstruction, training, or certify the scientific protocol.')


if __name__ == '__main__':
    main()
