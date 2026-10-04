"""Generate a local dashboard by querying the curated DuckDB output."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import duckdb
from src.serving.create_serving_layer import freshness_label, METADATA_PATH, DATABASE_PATH


def build_dashboard(database=DATABASE_PATH, metadata_path=METADATA_PATH, output=None):
    output=Path(output or 'outputs/dashboard/hydromet_dashboard.html')
    metadata=json.loads(Path(metadata_path).read_text(encoding='utf-8-sig'))
    now=datetime.now(timezone.utc)
    freshness=freshness_label(metadata,now)
    with duckdb.connect(str(database),read_only=True) as c:
        rows=c.execute('SELECT location_name,year,month,total_precipitation,mean_temperature,daily_observations FROM vw_monthly_climate_summary ORDER BY location_name,year,month').fetchdf()
        db_metadata=c.execute("SELECT logical_sha256 FROM serving_refresh_metadata WHERE output_name='mart_weather_daily'").fetchone()
    if not db_metadata or db_metadata[0] != metadata.get('logical_sha256'):
        raise ValueError('Refresh metadata does not identify the current curated output')
    payload={'rows':rows.to_dict(orient='records'),'metadata':metadata,'freshness':freshness,'generated_at':now.isoformat()}
    template='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>HydroMet climate explorer</title>
<style>body{font:16px system-ui;background:#f4f7fb;color:#163449;margin:32px auto;max-width:1100px;padding:20px}h1{font-size:36px}section{background:white;padding:24px;border-radius:14px;margin:20px 0}label{margin-right:16px}select{padding:8px}svg{width:100%;height:260px}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:8px;border-bottom:1px solid #dbe4ea}.badge{font-weight:bold}small{color:#4d6274}</style>
<h1>HydroMet climate explorer</h1><p>Historical rainfall and temperature at eight sampled Tanzanian points.</p>
<section><p id="status" class="badge"></p><p id="coverage"></p><small id="refresh"></small></section>
<section><label>Location <select id="location"></select></label><label>Year <select id="year"></select></label><h2>Monthly rainfall total (mm)</h2><svg id="chart" viewBox="0 0 1000 260" role="img" aria-label="Monthly rainfall totals"></svg><table><thead><tr><th>Month</th><th>Rain (mm)</th><th>Mean temperature (°C)</th><th>Days</th></tr></thead><tbody id="table"></tbody></table></section>
<p>Eight points do not represent complete national coverage. NASA POWER is the only integrated provider. Statistical extremes are retained. This dashboard is a snapshot queried from the curated output; regenerate it after a refresh. No predictive model is shown.</p>
<script>const data=PAYLOAD;const loc=document.getElementById('location'),yr=document.getElementById('year');
for(const v of [...new Set(data.rows.map(r=>r.location_name))])loc.add(new Option(v.replaceAll('_',' '),v));for(const v of [...new Set(data.rows.map(r=>r.year))])yr.add(new Option(v,v));yr.value='2025';
function show(){const r=data.rows.filter(r=>r.location_name===loc.value&&r.year===Number(yr.value));let max=Math.max(1,...r.map(x=>x.total_precipitation));document.getElementById('chart').innerHTML=r.map((x,i)=>{let h=x.total_precipitation/max*210;return `<rect x="${i*81+12}" y="${225-h}" width="55" height="${h}" fill="#168d9a"><title>${x.month}: ${x.total_precipitation.toFixed(2)} mm</title></rect><text x="${i*81+35}" y="250" text-anchor="middle">${x.month}</text>`}).join('');document.getElementById('table').innerHTML=r.map(x=>`<tr><td>${x.month}</td><td>${x.total_precipitation.toFixed(2)}</td><td>${x.mean_temperature.toFixed(2)}</td><td>${x.daily_observations}</td></tr>`).join('')}
function fresh(){let m=data.metadata,age=m.last_successful_refresh_at?(Date.now()-Date.parse(m.last_successful_refresh_at))/3600000:null;let label=m.last_attempt_status==='FAILED'?'FAILED_REFRESH':age===null?'UNKNOWN':age<=24?'FRESH':'STALE';document.getElementById('status').textContent=`Refresh status: ${label}`;document.getElementById('coverage').textContent=`Observation coverage: ${m.observation_coverage_start} to ${m.observation_coverage_end}`;document.getElementById('refresh').textContent=`Last good refresh: ${m.last_successful_refresh_at}; age ${age===null?'unknown':age.toFixed(2)+' hours'}. Snapshot generated ${data.generated_at}.`}
loc.onchange=yr.onchange=show;show();fresh();setInterval(fresh,60000);</script></html>'''
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(template.replace('PAYLOAD',json.dumps(payload).replace('<','\\u003c')),encoding='utf-8')
    return {'output':str(output),'monthly_rows':len(rows),'source_object':'vw_monthly_climate_summary','freshness':freshness,'generated_at':payload['generated_at']}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--database',type=Path,default=DATABASE_PATH);p.add_argument('--metadata',type=Path,default=METADATA_PATH);p.add_argument('--output',type=Path)
    a=p.parse_args();print(json.dumps(build_dashboard(a.database,a.metadata,a.output),indent=2))
