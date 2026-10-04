# HydroMet-ETL Manual GitHub Submission

No files were staged, committed or pushed by the agent. Team names, submission date and unassigned owners remain placeholders. Use this checklist after reviewing the working diff and evidence.

## Review first

```powershell
git status --short
git diff --check
git diff --stat
git diff -- src sql scripts tests README.md DATASHEET.md metrics.md docs
```

Unrelated local edits existed before this work in `notebooks/01_initial_data_profiling.ipynb` and `outputs/quality/data_quality_report.json`. Do not include them just because they appear in status; inspect and decide separately. Do not use `git add .`.

## Candidate files to include

- Reviewed README, root DATASHEET and metrics link, and the updated/new documentation under `docs/`, including tracker, evidence reports and colleague presentation guide.
- Updated ingestion, row-quality/quarantine, database loader, serving/refresh/dashboard, ML preparation and orchestration modules.
- `src/labs/__init__.py`, `src/labs/complete_labs.py`, `scripts/run_lab_evidence.ps1` and the focused safeguard/orchestration tests.
- Selected reviewed proof summaries, test results, benchmark CSV/JSON and generated dashboard snapshots under `outputs/evidence/`. Preserve historical reports rather than replace them with newer numbers.

The benchmark summarizes data and results; it does not include the downloaded raw archive or a local database. Generated dashboards embed monthly aggregate rows, so review that intended publication content before including them. Summaries contain local experiment paths but no intended credentials; inspect them before staging.

## Exclude

Keep credentials and tokens, `.env`, Python environments, raw/interim/processed data files, local DuckDB/PostgreSQL data directories, local rejected-row fixture files, WAL files, temporary files and unreviewed logs out of submission. `.gitignore` already excludes data layers, DuckDB files and logs. The temporary PostgreSQL cluster is inside the ignored processed-data directory; do not force-add it.

A code snapshot alone cannot reproduce local dataset-dependent tests without acquiring/restoring the retained archive. Tell the reviewer that requirement honestly. The local raw data remain available for demonstration but are not submitted as source code.

## Manual staging and commit

Stage individual reviewed files explicitly, inspect the staged diff, then commit. These are instructions for you; they have not been executed:

```powershell
# Review the exact candidate list before staging; remove any entries you exclude.
Get-Content -LiteralPath outputs/evidence/changed_files.txt
git add --pathspec-from-file=outputs/evidence/changed_files.txt
git diff --cached --name-only
git diff --cached --stat
git diff --cached --check
git diff --cached
# Commit only after reviewing the staged content.
git commit -m "feat: close HydroMet lab gaps with reproducible evidence"
```

Before pushing, verify the current branch and remote in your terminal and ensure no credentials are embedded in the remote URL. The last inspected branch is `main`, with GitHub repository `https://github.com/jovinvicent10/hydromet-data-pipeline.git`; report the actual current branch again if you switch it. Push manually only after reviewing the staged content and any team submission workflow.

```powershell
git branch --show-current
git remote -v
# Run only if the branch and remote above are the intended submission target.
git push origin main
```

Do not claim a deployed scheduler, live cloud automation, completed cold API profiling or trained-model accuracy. Final page counts for concise submission drafts still require review in the actual submission layout. Use the tracker to distinguish verified demonstrations from unresolved facts.

The exact changed/new file list is retained in `outputs/evidence/changed_files.txt`. It deliberately excludes the two unrelated pre-existing edits listed above. Final evidence: 70 tests passed in 8.04 seconds; relative documentation links/fences and diff whitespace passed; temporary datasets/databases/quarantine are ignored. Current branch is `main`, remote `https://github.com/jovinvicent10/hydromet-data-pipeline.git`.
