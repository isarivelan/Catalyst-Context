# Catalyst Context

Cognite Data Fusion POC for **process industries** — life sciences manufacturing and oil & gas operations.

The Streamlit app reads the **CatalystContext** data model (`Site`, `Equipment`, `ProcessSignal`, `ProcessEvent`, `EngineeringFile`, `Batch`, `QualityResult`) and is deployed into CDF as a Streamlit app.

Pattern: **equipment → signal → event → file**.

## Streamlit flow

1. **Industry lens** — life sciences, oil and gas, or both  
2. **Data model** — live instance counts from CatalystContext views  
3. **Site graph** — Site + Equipment hierarchy  
4. **Process signals** — ProcessSignal nodes (classic datapoints if `externalTag` exists as a time series)  
5. **Quality & integrity** — ProcessEvent + EngineeringFile  
6. **Context pack** — JSON export of the selected twin  

## CDF module

```text
modules/catalyst_context/
  data_modeling/     space, 7 containers, 7 views, CatalystContext v1
  raw/               seed tables
  transformations/   RAW → instances
  data_sets/         ds_catalyst_context
  streamlit/         Catalyst Context app (Fusion-hosted)
```

| Resource | External ID |
| --- | --- |
| Space | `catalyst_context` |
| Data model | `CatalystContext` `v1` |
| Streamlit app | `catalyst_context_app` |

## Deploy to CDF

```powershell
cd c:\code\catalyst-context
copy .env.example .env
# fill IDP_TENANT_ID, IDP_CLIENT_ID, IDP_CLIENT_SECRET

python scripts/deploy_cdf.py --dry-run
python scripts/deploy_cdf.py --seed-instances --run-jobs
```

This applies the data model, loads RAW, upserts transformation jobs, seeds instances, and uploads the Streamlit app.

Or Toolkit (after `pip install cognite-toolkit`):

```powershell
python -m cognite.toolkit build --env dev
python -m cognite.toolkit deploy --env dev
```

In Fusion: **Industrial tools → Streamlit → Catalyst Context**. The hosted app uses the signed-in CDF user. Local `streamlit run app.py` uses `.env` client credentials.

## Run locally

```powershell
pip install -r requirements.txt
streamlit run app.py
```

## Project layout

```text
app.py                                           Local Streamlit entry
modules/catalyst_context/streamlit/              CDF Streamlit app (source of truth)
modules/catalyst_context/data_modeling/          Space, containers, views
scripts/deploy_cdf.py                            Deploy model + app
config.dev.yaml                                  Toolkit env for emb-vtsa-dev
```
