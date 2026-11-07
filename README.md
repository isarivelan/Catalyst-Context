# Catalyst Context

Cognite Data Fusion POC for **process industries** — life sciences manufacturing and oil & gas operations — with a custom Streamlit flow.

The same contextualization pattern is reused in both lenses: **asset → time series → event → file**.

## Why this name

**Catalyst** is shared language in pharma process chemistry and energy refining. **Context** is what CDF adds on top of historians, MES/LIMS, CMMS, and engineering documents.

## Custom Streamlit flow

1. **Industry lens** — life sciences, oil and gas, or both  
2. **Connect** — guided demo catalog, or live CDF via Entra ID client credentials  
3. **Site graph** — ISA-95 / installation hierarchy  
4. **Process signals** — historian-style trends, golden-batch table (pharma)  
5. **Quality & integrity** — deviations, alarms, work orders, P&IDs, eBR / CoA  
6. **Context pack** — JSON export of the selected twin

## Demo catalog (no CDF required)

| Lens | Site | Pattern (from public Cognite materials) |
| --- | --- | --- |
| Life sciences | Helix Park Biologics | ISA-95 site/area/cell/unit + ISA-88 batch, QualityResult, MaterialLot-style events |
| Oil and gas | Harbor Ridge compression train | Open Industrial Data compressor pattern (suction cooler → scrubber → compressor → discharge cooler), rotating equipment, P&IDs |

Demo data is synthetic. It is shaped like CDF resources you would load from historians, MES/LIMS, PI, CMMS, and document stores.

| Object | Count | Notes |
| --- | --- | --- |
| Assets | 17 | 9 pharma (Helix Park) + 8 oil and gas (Harbor Ridge) |
| Time series | 14 | 7 per industry |
| Datapoints | 2,352 | 168 hourly samples × 14 tags (7-day window) |
| Events | 8 | deviations, OOS, alarms, work orders |
| Files | 8 | P&IDs, eBR, CoA, datasheets |
| Relationships | 8 | asset ↔ signal ↔ event ↔ file |
| Batches | 3 | golden / in-review / released |

## Data model and transformation jobs

These were **not deployed** to a live CDF project (no project credentials in this POC). They are **local definitions** you can publish:

- Data model `catalyst_context` / `CatalystContext` `v1` — 7 views in `cdf/data_models/`
- RAW seed tables in `cdf/raw/` (`equipment.csv`, `timeseries.csv`, `events.csv`)
- Three transformation jobs in `cdf/transformations/`:
  - `tr-catalyst-raw-to-equipment`
  - `tr-catalyst-raw-to-signals`
  - `tr-catalyst-raw-to-events`

Run the deploy script yourself (it will not run unless `.env` is filled):

```powershell
cd c:\code\catalyst-context
copy .env.example .env
# fill CDF_PROJECT, CDF_CLUSTER, CDF_TENANT_ID, CDF_CLIENT_ID, CDF_CLIENT_SECRET

.\.venv\Scripts\python.exe scripts\deploy_cdf.py --dry-run
.\.venv\Scripts\python.exe scripts\deploy_cdf.py
.\.venv\Scripts\python.exe scripts\deploy_cdf.py --run-jobs --seed-instances
```

Or: `.\scripts\deploy_cdf.ps1 -RunJobs -SeedInstances`

The script applies space `catalyst_context`, loads RAW tables, publishes GraphQL model `CatalystContext` `v1`, and upserts the three transformation jobs. `--run-jobs` starts those jobs. `--seed-instances` also writes the same rows as data-model nodes through the SDK (useful if Transformations ACL is not granted yet).

## Live CDF

OIDC client-credentials flow ([Cognite Python auth](https://docs.cognite.com/dev/sdks/python/python_auth_oidc)):

```text
CDF_PROJECT=
CDF_CLUSTER=api
CDF_TENANT_ID=
CDF_CLIENT_ID=
CDF_CLIENT_SECRET=
```

Live mode lists classic **assets, time series, events, files, relationships**. The GraphQL/YAML model in `cdf/` is the intended Data Modeling target once you deploy.

## Run

Python 3.10+.

```powershell
cd c:\code\catalyst-context
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

Stay on **Guided demo** until `.env` is filled.

## Project layout

```text
app.py                         Streamlit flow
cdf/data_models/               CatalystContext GraphQL + YAML
cdf/transformations/           3 SQL jobs (RAW → instances)
cdf/raw/                       Seed CSVs for those jobs
src/catalyst_context/
```

## Suggested next slice

- Publish `cdf/` into a real CDF project (space + RAW + transformations)  
- File download / P&ID overlay for a selected tag  
- Charts Agent or Atlas AI on the exported context pack
