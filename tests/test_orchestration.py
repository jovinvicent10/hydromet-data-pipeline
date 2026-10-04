"""Orchestrator behavior tested without executing or overwriting the live pipeline.

Historical run evidence is retained separately under outputs/orchestration.
"""
import json
from pathlib import Path
import pytest
from src.orchestration import run_pipeline as pipeline


@pytest.fixture
def isolated_pipeline(tmp_path,monkeypatch):
    monkeypatch.setattr(pipeline,'OUTPUT_DIR',tmp_path/'outputs')
    monkeypatch.setattr(pipeline,'LOG_DIR',tmp_path/'logs')
    monkeypatch.setattr(pipeline,'RUN_SUMMARY_PATH',tmp_path/'outputs/summary.json')
    calls=[]
    def execute(stage):
        calls.append(stage['name'])
        return {'stage':stage['name'],'status':'SUCCESS','return_code':0,
                'duration_seconds':0.1,'started_at':pipeline.utc_now(),
                'finished_at':pipeline.utc_now(),'log_file':str(tmp_path/'logs'/stage['name'])}
    monkeypatch.setattr(pipeline,'run_stage',execute)
    return calls


def summary():
    return json.loads(pipeline.RUN_SUMMARY_PATH.read_text())


def test_default_pipeline_includes_ingestion_dashboard_and_tests(isolated_pipeline):
    assert pipeline.execute_pipeline()==0
    assert isolated_pipeline==[s['name'] for s in pipeline.PIPELINE_STAGES]
    assert 'ingestion' in isolated_pipeline and 'consumer_dashboard' in isolated_pipeline and 'regression_tests' in isolated_pipeline
    assert summary()['status']=='SUCCESS'


def test_skip_ingestion_is_explicit_and_other_stages_remain(isolated_pipeline):
    assert pipeline.execute_pipeline(skip_ingestion=True)==0
    assert 'ingestion' not in isolated_pipeline
    assert summary()['skip_ingestion'] is True
    assert isolated_pipeline==[s['name'] for s in pipeline.PIPELINE_STAGES if s['name']!='ingestion']


def test_skip_tests_is_explicit(isolated_pipeline):
    pipeline.execute_pipeline(skip_tests=True)
    assert 'regression_tests' not in isolated_pipeline and 'ingestion' in isolated_pipeline
    assert summary()['skip_tests'] is True


def test_failure_stops_downstream_and_records_partial_run(isolated_pipeline,monkeypatch):
    def fail(stage):
        isolated_pipeline.append(stage['name'])
        return {'stage':stage['name'],'status':'FAILED','return_code':1,
                'duration_seconds':0.2,'log_file':'isolated-failure.log'}
    monkeypatch.setattr(pipeline,'run_stage',fail)
    assert pipeline.execute_pipeline()==1
    assert isolated_pipeline==['ingestion']
    assert summary()['status']=='FAILED' and summary()['failed_stage']=='ingestion'
    assert summary()['pipeline_finished_at'] and summary()['duration_seconds']>0


def test_completed_run_records_every_stage_timing(isolated_pipeline):
    pipeline.execute_pipeline()
    report=summary()
    assert report['duration_seconds']>0
    assert all(s['duration_seconds']>=0 and s['return_code']==0 for s in report['stages'])
    assert report['pipeline_started_at'] and report['pipeline_finished_at']


def test_stage_failure_state_is_persisted_before_return(isolated_pipeline,monkeypatch):
    def fail_second(stage):
        isolated_pipeline.append(stage['name'])
        return {'stage':stage['name'],'status':'FAILED' if stage['name']=='data_quality' else 'SUCCESS',
                'return_code':1 if stage['name']=='data_quality' else 0,
                'duration_seconds':0.1,'log_file':'isolated.log'}
    monkeypatch.setattr(pipeline,'run_stage',fail_second)
    pipeline.execute_pipeline()
    assert isolated_pipeline==['ingestion','data_quality']
    assert len(summary()['stages'])==2 and summary()['failed_stage']=='data_quality'
