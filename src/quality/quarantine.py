"""Row-level hard failures; statistical extremes are never rejected here."""
from collections import Counter
import json
from pathlib import Path

import numpy as np
import pandas as pd

VARIABLES = ['T2M', 'T2M_MIN', 'T2M_MAX', 'RH2M', 'PRECTOTCORR', 'WS2M', 'ALLSKY_SFC_SW_DWN']
REQUIRED = ['date', 'location', 'latitude', 'longitude', 'source', *VARIABLES]


def partition_rows(df):
    """Return accepted rows, original rejected rows with codes, and accounting.

    All occurrences of a duplicate natural key are rejected: selecting one
    arbitrarily would conceal contradictory source measurements.
    """
    missing = set(REQUIRED) - set(df.columns)
    if missing:
        raise ValueError(f'Missing required columns: {sorted(missing)}')
    original = df.reset_index(drop=True).copy()
    clean = original.copy()
    codes = [[] for _ in range(len(clean))]

    def mark(mask, code):
        for i in np.flatnonzero(np.asarray(mask.fillna(False), dtype=bool)):
            codes[i].append(code)

    parsed = pd.to_datetime(clean['date'], errors='coerce')
    mark(parsed.isna(), 'INVALID_DATE')
    clean['date'] = parsed
    mark(original[REQUIRED].isna().any(axis=1), 'MISSING_REQUIRED')
    for field in ['location', 'source']:
        mark(original[field].astype('string').str.strip().eq(''), 'EMPTY_' + field.upper())
    for field in ['latitude', 'longitude', *VARIABLES]:
        numeric = pd.to_numeric(clean[field], errors='coerce')
        mark(numeric.isna() | ~np.isfinite(numeric), 'INVALID_NUMERIC_' + field)
        if field in VARIABLES:
            mark(numeric.eq(-999), 'PROVIDER_FILL_' + field)
        clean[field] = numeric
    mark(~clean.latitude.between(-90, 90), 'LATITUDE_RANGE')
    mark(~clean.longitude.between(-180, 180), 'LONGITUDE_RANGE')
    mark(~clean.RH2M.between(0, 100), 'HUMIDITY_RANGE')
    for field in ['PRECTOTCORR', 'WS2M', 'ALLSKY_SFC_SW_DWN']:
        mark(clean[field].lt(0), 'NEGATIVE_' + field)
    mark((clean.T2M_MIN > clean.T2M) | (clean.T2M > clean.T2M_MAX), 'TEMPERATURE_ORDER')
    mark(clean.source.ne('NASA_POWER'), 'UNSUPPORTED_SOURCE')
    mark(clean.duplicated(['location', 'date', 'source'], keep=False), 'DUPLICATE_KEY')
    rejected_mask = pd.Series([bool(c) for c in codes], dtype=bool)
    rejected = original.loc[rejected_mask].copy()
    rejected.insert(0, 'input_row_number', rejected.index + 2)
    rejected['reason_codes'] = ['|'.join(codes[i]) for i in rejected.index]
    accepted = clean.loc[~rejected_mask].reset_index(drop=True)
    counts = dict(sorted(Counter(code for row in codes for code in row).items()))
    report = {'rows_read': len(original), 'rows_loaded': len(accepted),
              'rows_rejected': len(rejected), 'rejection_reason_counts': counts}
    assert report['rows_read'] == report['rows_loaded'] + report['rows_rejected']
    return accepted, rejected.reset_index(drop=True), report


def write_quarantine(rejected, report, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    rejected.to_csv(directory / 'rejected_rows.csv', index=False)
    (directory / 'row_accounting.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
