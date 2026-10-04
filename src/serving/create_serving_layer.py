"""Transactional curated refresh with last-good metadata and failure tracking."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = PROJECT_ROOT / 'data/database/hydromet.duckdb'
SQL_PATH = PROJECT_ROOT / 'sql/05_create_serving_layer.sql'
METADATA_PATH = PROJECT_ROOT / 'metadata/serving_refresh.json'
EXPECTED_DAILY_ROWS = 73048
EXPECTED_MONTHLY_ROWS = 2400


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.json.tmp')
    temp.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temp.replace(path)


def freshness_label(metadata, now=None, threshold_hours=24):
    now = now or datetime.now(timezone.utc)
    last_good = metadata.get('last_successful_refresh_at')
    age = None if not last_good else (now - datetime.fromisoformat(last_good)).total_seconds() / 3600
    if metadata.get('last_attempt_status') == 'FAILED':
        label = 'FAILED_REFRESH'
    elif age is None:
        label = 'UNKNOWN'
    else:
        label = 'FRESH' if age <= threshold_hours else 'STALE'
    return {'label': label, 'refresh_age_hours': age, 'threshold_hours': threshold_hours,
            'observation_coverage_end': metadata.get('observation_coverage_end')}


def create_serving_layer(database_path=None, metadata_path=None, simulate_failure=False):
    database_path = Path(database_path or DATABASE_PATH)
    metadata_path = Path(metadata_path or METADATA_PATH)
    metadata = json.loads(metadata_path.read_text(encoding='utf-8-sig')) if metadata_path.exists() else {}
    metadata.update({'output_name':'mart_weather_daily', 'last_attempt_at':utc_now(), 'last_attempt_status':'RUNNING'})
    atomic_json(metadata_path, metadata)
    connection = None
    try:
        if not database_path.exists():
            raise FileNotFoundError(database_path)
        connection = duckdb.connect(str(database_path))
        connection.execute('BEGIN TRANSACTION')
        connection.execute(SQL_PATH.read_text(encoding='utf-8'))
        rows, locations, duplicates = connection.execute('''SELECT COUNT(*), COUNT(DISTINCT location_name),
            COUNT(*)-COUNT(DISTINCT (observation_date,location_name,source_name)) FROM mart_weather_daily''').fetchone()
        monthly = connection.execute('SELECT COUNT(*) FROM vw_monthly_climate_summary').fetchone()[0]
        if (rows,locations,duplicates,monthly) != (EXPECTED_DAILY_ROWS,8,0,EXPECTED_MONTHLY_ROWS):
            raise ValueError(f'Unexpected serving counts {(rows,locations,duplicates,monthly)}')
        frame = connection.execute('SELECT * FROM mart_weather_daily ORDER BY location_name,source_name,observation_date').fetchdf()
        fingerprint = hashlib.sha256(frame.to_csv(index=False).encode()).hexdigest()
        if simulate_failure:
            # Fail AFTER replacing the table within the transaction, proving rollback.
            raise RuntimeError('DELIBERATE_REFRESH_FAILURE')
        finished = utc_now()
        connection.execute('CREATE TABLE IF NOT EXISTS serving_refresh_metadata (output_name VARCHAR PRIMARY KEY, refreshed_at TIMESTAMPTZ, logical_sha256 VARCHAR)')
        connection.execute('INSERT OR REPLACE INTO serving_refresh_metadata VALUES (?,?,?)', ['mart_weather_daily',finished,fingerprint])
        connection.execute('COMMIT')
        metadata.update({'last_attempt_status':'SUCCESS', 'last_successful_refresh_at':finished,
                         'logical_sha256':fingerprint, 'rows':rows,
                         'observation_coverage_start':str(frame.observation_date.min().date()),
                         'observation_coverage_end':str(frame.observation_date.max().date()),
                         'last_error':None})
        atomic_json(metadata_path, metadata)
        print(f'Serving refreshed: {rows} daily rows; {monthly} monthly groups')
        return metadata
    except Exception as error:
        if connection is not None:
            try:
                connection.execute('ROLLBACK')
            except duckdb.Error:
                pass
        metadata.update({'last_attempt_status':'FAILED', 'last_attempt_finished_at':utc_now(), 'last_error':str(error)})
        atomic_json(metadata_path, metadata)
        raise
    finally:
        if connection is not None:
            connection.close()


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--database', type=Path, default=DATABASE_PATH)
    parser.add_argument('--metadata', type=Path, default=METADATA_PATH)
    parser.add_argument('--simulate-failure', action='store_true')
    args=parser.parse_args()
    create_serving_layer(args.database,args.metadata,args.simulate_failure)
