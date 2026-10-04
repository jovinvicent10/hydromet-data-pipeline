"""Execute lab evidence without overwriting established datasets or reports.

python -m src.labs.complete_labs --section all
PostgreSQL uses the isolated local cluster on 127.0.0.1:55433.
"""
import argparse
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import sys
import time

import duckdb
import pandas as pd
from src.quality.quarantine import partition_rows, write_quarantine
from src.quality.validate_hydromet import validate_hydromet, save_outputs
from src.serving.create_serving_layer import create_serving_layer, freshness_label
from src.serving.build_dashboard import build_dashboard
from src.ml import prepare_ml_data as ml
from src.database import load_duckdb as optimized

ROOT=Path(__file__).resolve().parents[2]
LOCAL=ROOT/'data/processed/lab_evidence'
EVIDENCE=ROOT/'outputs/evidence'
CSV=ROOT/'data/interim/nasa_power_tanzania_daily.csv'
PSQL=Path('C:/Program Files/PostgreSQL/18/bin/psql.exe')
PROTECTED=[CSV,ROOT/'metadata/ingestion_manifest.json',ROOT/'metadata/ml_split_metadata.json',
           ROOT/'outputs/quality/data_quality_report.json',ROOT/'notebooks/01_initial_data_profiling.ipynb']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(name, data):
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    (EVIDENCE/name).write_text(json.dumps(data,indent=2,default=str),encoding='utf-8')


def ingestion(directory, log):
    with Path(log).open('w',encoding='utf-8') as handle:
        subprocess.run([sys.executable,'-m','src.ingestion.ingest_nasa_power','--workspace',str(directory),'--offline'],cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT,check=True)
    return json.loads((directory/'reports/ingestion_run_summary.json').read_text())


def paired_ingestion():
    directory=LOCAL/'paired_ingestion'
    summaries=[]
    for i in (1,2):
        summary=ingestion(directory,EVIDENCE/f'ingestion_run_{i}.txt')
        summary['evidence_run_number']=i
        write(f'ingestion_run_{i}.json',summary)
        summaries.append(summary)
    assert summaries[0]['output_sha256']==summaries[1]['output_sha256']==sha(CSV)
    assert all(s['rows_read']==s['rows_loaded']==73048 and s['rows_rejected']==s['duplicate_keys']==0 for s in summaries)
    assert summaries[0]['run_id']!=summaries[1]['run_id']
    write('idempotency_proof.json',{'status':'PASS','mode':'cached_offline','sha256':sha(CSV),
          'run_ids':[s['run_id'] for s in summaries], 'rows_each_run':73048,
          'rejected_each_run':0,'duplicate_keys_each_run':0,'distinct_summaries_retained':True})


def bad_rows():
    directory=LOCAL/'bad_rows';directory.mkdir(parents=True,exist_ok=True)
    sample=pd.read_csv(CSV).iloc[:10].copy()
    # Keep an unusual but physically valid value; never reject just for magnitude.
    sample.loc[0,'PRECTOTCORR']=1000.0
    fixture=pd.concat([sample,sample.iloc[[1]]],ignore_index=True)
    fixture.loc[3,'RH2M']=120
    fixture.loc[4,'T2M']=None
    fixture.loc[5,'PRECTOTCORR']=-1
    fixture.loc[6,'date']='not-a-date'
    fixture.loc[7,'WS2M']=-999
    fixture.to_csv(directory/'bad_input.csv',index=False)
    accepted,rejected,accounting=partition_rows(fixture)
    write_quarantine(rejected,accounting,directory)
    accepted.to_csv(directory/'accepted_rows.csv',index=False)
    assert accounting['rows_read']==11 and accounting['rows_rejected']==7
    assert 1000 in accepted.PRECTOTCORR.values
    (EVIDENCE/'bad_row_demo.txt').write_text(json.dumps(accounting,indent=2),encoding='utf-8')
    with (EVIDENCE/'bad_row_quality_gate.txt').open('w',encoding='utf-8') as handle:
        result=subprocess.run([sys.executable,'-m','src.quality.validate_hydromet','--input',str(directory/'bad_input.csv'),
                               '--output-dir',str(directory/'quality_gate')],cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT)
    assert result.returncode==1
    gate=json.loads((directory/'quality_gate/data_quality_report.json').read_text())
    assert gate['overall_status']=='FAIL' and gate['row_accounting']['rows_rejected']==7
    write('quarantine_proof.json',{'status':'PASS',**accounting,'physically_valid_extreme_retained':True,
          'input_sha256':sha(directory/'bad_input.csv'),'baseline_sha256':sha(CSV),
          'isolated_artifacts':'data/processed/lab_evidence/bad_rows',
          'quality_gate_return_code':result.returncode,'quality_gate_status':gate['overall_status']})


def regression(log):
    with Path(log).open('w',encoding='utf-8') as handle:
        result=subprocess.run([sys.executable,'-m','pytest','-q','-p','no:cacheprovider'],cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT)
    if result.returncode:
        raise RuntimeError(f'Regression failed; see {log}')


def profile(label):
    directory=LOCAL/f'profile_{label}';directory.mkdir(parents=True,exist_ok=True)
    database=directory/'hydromet.duckdb'
    # Compare equivalent cached reloads of the same established database state.
    shutil.copy2(ROOT/'data/database/hydromet.duckdb',database)
    if label=='before':
        baseline=LOCAL/'baseline_load_duckdb.py'
        if not baseline.exists():
            original=subprocess.check_output(['git','show','df0a67cf875fa731a10de4ed8a61afd8188b3884:src/database/load_duckdb.py'],cwd=ROOT)
            baseline.write_bytes(original)
        spec=importlib.util.spec_from_file_location('baseline_load',baseline)
        loader=importlib.util.module_from_spec(spec);spec.loader.exec_module(loader)
    else:
        loader=optimized
    loader.DATA_PATH=directory/'ingest/interim/nasa_power_tanzania_daily.csv'
    loader.DATABASE_PATH=database
    stages=[]
    start=time.perf_counter()
    def stage(name,action):
        before=time.perf_counter()
        with (directory/f'{name}.log').open('w',encoding='utf-8') as stream, redirect_stdout(stream),redirect_stderr(stream):
            result=action()
        stages.append({'stage':name,'status':'SUCCESS','duration_seconds':time.perf_counter()-before})
        print(f'{label}: {name} completed in {stages[-1]["duration_seconds"]:.3f}s',flush=True)
        return result
    stage('ingestion',lambda:ingestion(directory/'ingest',directory/'ingestion_process.log'))
    def quality():
        report,summary=validate_hydromet(loader.DATA_PATH,strict_baseline=True)
        _,rejected,accounting=partition_rows(pd.read_csv(loader.DATA_PATH))
        assert report['overall_status']=='PASS' and not accounting['rows_rejected']
        save_outputs(report,summary,directory/'quality')
        write_quarantine(rejected,accounting,directory/'quality/quarantine')
    stage('data_quality',quality)
    def schema():
        with duckdb.connect(str(database)) as c:
            c.execute((ROOT/'sql/01_create_schema.sql').read_text())
            c.execute((ROOT/'sql/03_create_views.sql').read_text())
    stage('database_schema',schema)
    stage('database_load',loader.main)
    metadata_path=directory/'serving_refresh.json'
    stage('serving_layer',lambda:create_serving_layer(database,metadata_path))
    ml.DATABASE_PATH=database;ml.OUTPUT_DIR=directory/'ml';ml.METADATA_DIR=directory/'metadata'
    ml.FEATURES_PATH=ml.OUTPUT_DIR/'ml_weather_availability_features.parquet'
    ml.TRAIN_PATH=ml.OUTPUT_DIR/'ml_weather_availability_train.parquet'
    ml.VALIDATION_PATH=ml.OUTPUT_DIR/'ml_weather_availability_validation.parquet'
    ml.TEST_PATH=ml.OUTPUT_DIR/'ml_weather_availability_test.parquet'
    ml.METADATA_PATH=ml.METADATA_DIR/'ml_availability_metadata.json'
    stage('ml_preparation',ml.main)
    stage('consumer_dashboard',lambda:build_dashboard(database,metadata_path,EVIDENCE/f'dashboard_{label}.html'))
    stage('regression_tests',lambda:regression(EVIDENCE/f'tests_{label}.txt'))
    duration=time.perf_counter()-start
    with duckdb.connect(str(database),read_only=True) as c:
        values=c.execute('SELECT observation_date,location_name,source_name,variable_code,value FROM vw_weather_observations ORDER BY location_name,observation_date,source_name,variable_code').fetchdf()
        fact_hash=hashlib.sha256(values.to_csv(index=False).encode()).hexdigest()
        counts={name:c.execute('SELECT COUNT(*) FROM '+name).fetchone()[0] for name in ['fact_observation','mart_weather_daily','vw_monthly_climate_summary']}
    result={'status':'SUCCESS','profile':label,'mode':'cached_offline_ingestion_existing_database_reload',
            'cold_api_run':False,'duration_seconds':duration,'stages':stages,'counts':counts,
            'source_sha256':sha(CSV),'logical_fact_sha256':fact_hash,
            'baseline_code_revision':'df0a67cf875fa731a10de4ed8a61afd8188b3884',
            'python':sys.version,'duckdb':duckdb.__version__,'pandas':pd.__version__}
    write(f'pipeline_{label}.json',result)
    write('ml_availability_results.json',json.loads(ml.METADATA_PATH.read_text()))
    if label=='after' and (EVIDENCE/'pipeline_before.json').exists():
        earlier=json.loads((EVIDENCE/'pipeline_before.json').read_text())
        assert earlier['logical_fact_sha256']==fact_hash and earlier['counts']==counts
        write('pipeline_improvement.json',{'correctness':'PASS','same_logical_facts':True,
              'before_seconds':earlier['duration_seconds'],'after_seconds':duration,
              'speedup':earlier['duration_seconds']/duration,
              'time_reduction_percent':100*(1-duration/earlier['duration_seconds']),
              'method':'One paired cached full-workflow run; identical original database copied before each; only loader implementation differs (anti-join and native solar-unit label correction); measurement values unchanged',
              'cold_api_run':False,'repetitions':1})
    return directory


def failed_refresh():
    directory=LOCAL/'profile_after';database=directory/'hydromet.duckdb';metadata=directory/'serving_refresh.json'
    previous=json.loads(metadata.read_text())
    try:
        create_serving_layer(database,metadata,simulate_failure=True)
    except RuntimeError as error:
        assert str(error)=='DELIBERATE_REFRESH_FAILURE'
    else:
        raise AssertionError('Expected failure did not occur')
    failed=json.loads(metadata.read_text())
    assert failed['last_successful_refresh_at']==previous['last_successful_refresh_at']
    with duckdb.connect(str(database),read_only=True) as c:
        frame=c.execute('SELECT * FROM mart_weather_daily ORDER BY location_name,source_name,observation_date').fetchdf()
    current=hashlib.sha256(frame.to_csv(index=False).encode()).hexdigest()
    assert current==previous['logical_sha256']
    dashboard=build_dashboard(database,metadata,EVIDENCE/'dashboard_failed_refresh.html')
    write('failed_refresh_proof.json',{'status':'PASS','last_good_output_unchanged':True,
          'logical_sha256':current,'last_successful_refresh_at':failed['last_successful_refresh_at'],
          'failed_attempt_at':failed['last_attempt_at'],'freshness':freshness_label(failed),
          'dashboard':dashboard})
    # Leave the failed snapshot for presentation, then restore isolated normal state.
    create_serving_layer(database,metadata)
    build_dashboard(database,metadata,EVIDENCE/'hydromet_dashboard.html')


def psql(sql,database='hydromet_lab'):
    result=subprocess.run([str(PSQL),'-w','-h','127.0.0.1','-p','55433','-U','hydromet_lab','-d',database,'-X','--csv','-v','ON_ERROR_STOP=1','-c',sql],text=True,capture_output=True,check=True)
    return result.stdout


def benchmark():
    directory=LOCAL/'benchmark';directory.mkdir(parents=True,exist_ok=True)
    # A ready port alone is not proof that it belongs to our disposable cluster.
    actual_cluster=pd.read_csv(io.StringIO(psql('SHOW data_directory',database='postgres'))).iloc[0,0]
    if Path(actual_cluster).resolve() != (LOCAL/'postgres_cluster').resolve():
        raise RuntimeError('Refusing to benchmark against a different PostgreSQL cluster')
    parquet=directory/'weather.parquet'
    df=pd.read_csv(CSV);df.to_parquet(parquet,index=False)
    available=subprocess.run([str(PSQL),'-w','-h','127.0.0.1','-p','55433','-U','hydromet_lab','-d','postgres','-X','-t','-A','-c',"SELECT 1 FROM pg_database WHERE datname='hydromet_lab'"],capture_output=True,text=True,check=True).stdout.strip()
    if not available:
        psql('CREATE DATABASE hydromet_lab',database='postgres')
    types={'date':'DATE','location':'TEXT','source':'TEXT'}
    ddl=', '.join('"'+c+'" '+types.get(c,'DOUBLE PRECISION')+' NOT NULL' for c in df.columns)
    psql('DROP TABLE IF EXISTS weather; CREATE TABLE weather ('+ddl+', PRIMARY KEY(date,location,source))')
    safe_path=CSV.as_posix().replace("'","''")
    copy_start=time.perf_counter()
    psql("\\copy weather FROM '"+safe_path+"' WITH (FORMAT CSV, HEADER TRUE)")
    copy_seconds=time.perf_counter()-copy_start
    query='SELECT location, CAST(EXTRACT(YEAR FROM date) AS INTEGER) AS year, CAST(EXTRACT(MONTH FROM date) AS INTEGER) AS month, AVG("PRECTOTCORR") AS mean_daily_precipitation FROM weather GROUP BY location,year,month ORDER BY location,year,month'
    def csv_query():
        data=pd.read_csv(CSV,parse_dates=['date']);data['year']=data.date.dt.year;data['month']=data.date.dt.month
        return data.groupby(['location','year','month'],as_index=False).PRECTOTCORR.mean().rename(columns={'PRECTOTCORR':'mean_daily_precipitation'}).sort_values(['location','year','month']).reset_index(drop=True)
    def parquet_query():
        with duckdb.connect() as c:
            return c.execute(query.replace('FROM weather','FROM read_parquet(?)').replace('EXTRACT(YEAR FROM date)','EXTRACT(YEAR FROM CAST(date AS DATE))').replace('EXTRACT(MONTH FROM date)','EXTRACT(MONTH FROM CAST(date AS DATE))'),[str(parquet)]).fetchdf()
    def postgres_query():
        return pd.read_csv(io.StringIO(psql(query)))
    expected=csv_query();results=[]
    storage_pg=pd.read_csv(io.StringIO(psql("SELECT pg_total_relation_size('weather') AS bytes"))).bytes.iloc[0]
    for engine,action,size in [('CSV + pandas',csv_query,CSV.stat().st_size),('PostgreSQL',postgres_query,int(storage_pg)),('DuckDB over Parquet',parquet_query,parquet.stat().st_size)]:
        warm=action();pd.testing.assert_frame_equal(expected,warm,check_dtype=False,atol=1e-9,rtol=0)
        timings=[]
        for _ in range(5):
            begin=time.perf_counter();output=action();timings.append(time.perf_counter()-begin)
            pd.testing.assert_frame_equal(expected,output,check_dtype=False,atol=1e-9,rtol=0)
        results.append({'engine':engine,'storage_bytes':size,'storage_mib':size/1024**2,
                        'median_seconds':statistics.median(timings),'timings_seconds':timings,'groups':len(output)})
    expected.to_csv(directory/'expected_aggregate.csv',index=False)
    write('required_engine_benchmark.json',{'status':'PASS','dataset_sha256':sha(CSV),'rows':len(df),
          'aggregate':'Mean daily precipitation by location/year/month, full interval, NASA_POWER',
          'warmups':1,'repetitions':5,'cold_run':False,'absolute_tolerance':1e-9,
          'timing_boundary':'Client wall time including reading/query execution and result materialization. PostgreSQL includes psql process/connection/CSV parse; DuckDB includes fresh connection and fetchdf; pandas includes CSV parse.',
          'storage_definition':'CSV/Parquet file bytes; PostgreSQL pg_total_relation_size includes table, primary-key index and TOAST; cluster overhead excluded.',
          'postgres_load_seconds':copy_seconds,'results':results})
    pd.DataFrame([{k:v for k,v in r.items() if k!='timings_seconds'} for r in results]).to_csv(EVIDENCE/'required_engine_benchmark.csv',index=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--section',choices=['all','pair','bad','before','after','benchmark','failure'],default='all');args=parser.parse_args()
    LOCAL.mkdir(parents=True,exist_ok=True);EVIDENCE.mkdir(parents=True,exist_ok=True)
    protected={str(p.relative_to(ROOT)):sha(p) for p in PROTECTED}
    actions={'pair':paired_ingestion,'bad':bad_rows,'before':lambda:profile('before'),
             'after':lambda:profile('after'),'benchmark':benchmark,'failure':failed_refresh}
    selected=list(actions) if args.section=='all' else [args.section]
    for action in selected:
        print('Starting '+action,flush=True);actions[action]()
    after={str(p.relative_to(ROOT)):sha(p) for p in PROTECTED}
    assert protected==after, 'Established or unrelated artifact changed'
    write('preservation_check.json',{'status':'PASS','sha256':after})
    print('Protected datasets, manifest, original report and notebook remain unchanged.',flush=True)


if __name__=='__main__':
    main()
