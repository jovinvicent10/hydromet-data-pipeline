"""Behavior tests for Phase 2 safeguards; historical artifact tests remain separate."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import duckdb
import pandas as pd
import pytest
from src.quality.quarantine import partition_rows
from src.ml.prepare_ml_data import create_features, remove_incomplete_feature_rows, temporal_split, validate_temporal_split, PREDICTORS
from src.serving.create_serving_layer import freshness_label, create_serving_layer
from src.database.load_duckdb import load_fact_observation, transform_to_long, load_dim_date, load_dim_location, load_dim_variable, load_dim_source

ROOT=Path(__file__).resolve().parents[1]


def test_quarantine_preserves_extreme_and_accounts_for_multiple_reasons():
    frame=pd.read_csv(ROOT/'data/interim/nasa_power_tanzania_daily.csv').iloc[:4].copy()
    frame.loc[0,'PRECTOTCORR']=1000
    frame.loc[1,'RH2M']=120
    frame.loc[1,'WS2M']=-999
    accepted,rejected,report=partition_rows(frame)
    assert report['rows_read']==report['rows_loaded']+report['rows_rejected']==4
    assert report['rows_rejected']==1
    assert 'HUMIDITY_RANGE' in rejected.reason_codes.iloc[0]
    assert 'PROVIDER_FILL_WS2M' in rejected.reason_codes.iloc[0]
    assert 1000 in accepted.PRECTOTCORR.values


def test_duplicate_conflicts_reject_both_original_rows():
    frame=pd.read_csv(ROOT/'data/interim/nasa_power_tanzania_daily.csv').iloc[:2].copy()
    frame=pd.concat([frame,frame.iloc[[0]]],ignore_index=True)
    frame.loc[2,'T2M']=frame.loc[0,'T2M']+1
    accepted,rejected,report=partition_rows(frame)
    assert len(rejected)==2 and len(accepted)==1
    assert rejected.reason_codes.str.contains('DUPLICATE_KEY').all()


def test_non_numeric_and_bad_date_are_rejected_without_mutating_input():
    frame=pd.read_csv(ROOT/'data/interim/nasa_power_tanzania_daily.csv').iloc[:2].astype(object)
    frame.loc[0,'T2M']='broken';frame.loc[1,'date']='broken'
    original=frame.copy(deep=True)
    accepted,rejected,report=partition_rows(frame)
    pd.testing.assert_frame_equal(frame,original)
    assert len(accepted)==0 and len(rejected)==2


def weather_series():
    dates=pd.date_range('2018-10-01','2022-02-01')
    return pd.DataFrame({'observation_date':dates,'location_name':'Example','source_name':'NASA_POWER',
                         'latitude':-3.,'longitude':36.,'prectotcorr':range(len(dates)),
                         't2m':20.,'rh2m':70.,'t2m_min':10.,'t2m_max':30.,'ws2m':2.,'allsky_sfc_sw_dwn':20.})


def test_future_values_cannot_change_current_features_and_recent_weather_is_excluded():
    original=weather_series();modified=original.copy()
    issue=pd.Timestamp('2019-01-10')
    modified.loc[modified.observation_date>issue-pd.Timedelta(days=8),'prectotcorr']=99999
    a=create_features(original);b=create_features(modified)
    pd.testing.assert_series_equal(a.loc[a.observation_date==issue,PREDICTORS].iloc[0], b.loc[b.observation_date==issue,PREDICTORS].iloc[0])
    assert not set(['t2m','rh2m','prectotcorr','allsky_sfc_sw_dwn','target_precip_next_day']) & set(PREDICTORS)
    assert 'prectotcorr' not in a.columns
    actual=a.loc[a.observation_date==issue,'precip_mean_7d_available'].iloc[0]
    expected=original.loc[original.observation_date.between(issue-pd.Timedelta(days=14),issue-pd.Timedelta(days=8)),'prectotcorr'].mean()
    assert actual==expected


def test_target_dates_do_not_cross_holdout_boundary():
    clean=remove_incomplete_feature_rows(create_features(weather_series()))
    train,validation,test=temporal_split(clean)
    validate_temporal_split(train,validation,test)
    assert train.target_date.max()<=pd.Timestamp('2018-12-31')
    assert validation.target_date.max()<=pd.Timestamp('2021-12-31')
    assert not clean.observation_date.isin([pd.Timestamp('2018-12-31'),pd.Timestamp('2021-12-31')]).any()
    assert len(clean)==len(train)+len(validation)+len(test)


def test_missing_day_prevents_row_lag_from_impersonating_calendar_day():
    with pytest.raises(ValueError,match='continuous'):
        create_features(weather_series().drop(index=50))


def test_freshness_distinguishes_archive_coverage_and_refresh_age():
    now=datetime.now(timezone.utc)
    metadata={'last_successful_refresh_at':(now-timedelta(hours=25)).isoformat(),
              'last_attempt_status':'SUCCESS','observation_coverage_end':'2025-12-31'}
    assert freshness_label(metadata,now)['label']=='STALE'
    metadata['last_attempt_status']='FAILED'
    assert freshness_label(metadata,now)['label']=='FAILED_REFRESH'
    assert freshness_label(metadata,now)['observation_coverage_end']=='2025-12-31'
    assert freshness_label({},now)['label']=='UNKNOWN'


def test_failed_refresh_rolls_back_replaced_curated_table(tmp_path,monkeypatch):
    from src.serving import create_serving_layer as serving
    database=tmp_path/'test.duckdb';metadata=tmp_path/'refresh.json';sql=tmp_path/'refresh.sql'
    sql.write_text("CREATE OR REPLACE TABLE mart_weather_daily AS SELECT DATE '2020-01-01' observation_date, 'changed' location_name, 'NASA_POWER' source_name; CREATE OR REPLACE VIEW vw_monthly_climate_summary AS SELECT * FROM mart_weather_daily")
    with duckdb.connect(str(database)) as c:
        c.execute("CREATE TABLE mart_weather_daily AS SELECT DATE '2020-01-01' observation_date, 'original' location_name, 'NASA_POWER' source_name")
    previous={'last_successful_refresh_at':'2020-01-01T00:00:00+00:00','logical_sha256':'prior'}
    metadata.write_text(json.dumps(previous))
    monkeypatch.setattr(serving,'SQL_PATH',sql);monkeypatch.setattr(serving,'EXPECTED_DAILY_ROWS',1);monkeypatch.setattr(serving,'EXPECTED_MONTHLY_ROWS',1)
    # Existing validation requires eight points: this deliberate count failure
    # still happens after replacing the table inside a transaction.
    with pytest.raises(ValueError,match='Unexpected serving'):
        serving.create_serving_layer(database,metadata)
    with duckdb.connect(str(database),read_only=True) as c:
        assert c.execute('SELECT location_name FROM mart_weather_daily').fetchone()[0]=='original'
    after=json.loads(metadata.read_text())
    assert after['last_attempt_status']=='FAILED' and after['last_successful_refresh_at']==previous['last_successful_refresh_at']


def test_loader_reload_preserves_keys_values_and_partial_new_fact(tmp_path):
    database=tmp_path/'test.duckdb'
    frame=pd.read_csv(ROOT/'data/interim/nasa_power_tanzania_daily.csv',parse_dates=['date']).iloc[:3]
    with duckdb.connect(str(database)) as c:
        c.execute((ROOT/'sql/01_create_schema.sql').read_text())
        load_dim_location(c,frame);load_dim_date(c,frame);load_dim_variable(c);load_dim_source(c)
        long=transform_to_long(frame)
        load_fact_observation(c,long.iloc[:-1]);before=c.execute('SELECT observation_id,value FROM fact_observation ORDER BY observation_id').fetchall()
        load_fact_observation(c,long)
        assert c.execute('SELECT COUNT(*) FROM fact_observation').fetchone()[0]==21
        assert c.execute('SELECT observation_id,value FROM fact_observation WHERE observation_id<=20 ORDER BY observation_id').fetchall()==before
        load_fact_observation(c,long)
        assert c.execute('SELECT COUNT(*) FROM fact_observation').fetchone()[0]==21
        assert c.execute("SELECT unit FROM dim_variable WHERE variable_code='ALLSKY_SFC_SW_DWN'").fetchone()[0]=='MJ/m2/day'


def test_benchmark_refuses_a_different_postgresql_cluster(tmp_path,monkeypatch):
    from src.labs import complete_labs as labs
    monkeypatch.setattr(labs,'LOCAL',tmp_path/'isolated')
    calls=[]
    def other_cluster(sql,database='hydromet_lab'):
        calls.append(sql)
        return 'data_directory\n' + str(tmp_path/'unrelated_cluster') + '\n'
    monkeypatch.setattr(labs,'psql',other_cluster)
    with pytest.raises(RuntimeError,match='different PostgreSQL cluster'):
        labs.benchmark()
    assert calls==['SHOW data_directory']
