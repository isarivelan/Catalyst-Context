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

## Data model (space, containers, views)

The earlier GraphQL file only described *types*. CDF Data Modeling stores properties in **containers**, exposes them through **views**, and groups views in a **data model** — all inside a **space**. Those resources now live in a Cognite Toolkit module:

```text
modules/catalyst_context/
  data_modeling/
    catalyst_context.Space.yaml
    containers/*.Container.yaml    # 7 containers
    views/*.View.yaml              # 7 views
    CatalystContext.DataModel.yaml
  raw/                             # seed tables
  transformations/                 # RAW → instances
```

| Resource | External ID |
| --- | --- |
| Space | `catalyst_context` |
| Data model | `CatalystContext` `v1` |
| Containers / views | `Site`, `Equipment`, `ProcessSignal`, `ProcessEvent`, `EngineeringFile`, `Batch`, `QualityResult` |

Direct relations: `Equipment.site` → Site, `Equipment.parent` → Equipment, `ProcessSignal|ProcessEvent|EngineeringFile.equipment` → Equipment, `Batch.unit` → Equipment, `QualityResult.batch` → Batch.

`cdf/data_models/CatalystContext.graphql` is documentation of the same types. Deploy applies YAML containers/views, not GraphQL DML.

## Deploy to CDF

Use the same Entra client-credentials names as cognite-toolkit (`IDP_*`). Copy `.env.example` to `.env` and fill tenant, client id, and secret.

```powershell
cd c:\code\catalyst-context
copy .env.example .env

python scripts/deploy_cdf.py --dry-run
python scripts/deploy_cdf.py
python scripts/deploy_cdf.py --run-jobs --seed-instances
```

Or Toolkit:

```powershell
cdf build --env dev
cdf deploy --env dev
```

`config.dev.yaml` targets project `emb-vtsa-dev` on cluster `aw-was-gp-001`.

The Python script applies space → containers → views → data model `CatalystContext` `v1`, loads RAW, and upserts four transformation jobs (`tr-catalyst-raw-to-sites|equipment|signals|events`). `--seed-instances` writes nodes through the SDK if Transformations ACL is not granted yet.

## Live CDF

OIDC client-credentials flow ([Cognite Python auth](https://docs.cognite.com/dev/sdks/python/python_auth_oidc)):

```text
CDF_PROJECT=emb-vtsa-dev
CDF_CLUSTER=aw-was-gp-001
CDF_URL=https://aw-was-gp-001.cognitedata.com
IDP_TENANT_ID=
IDP_CLIENT_ID=
IDP_CLIENT_SECRET=
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
# fill IDP_TENANT_ID, IDP_CLIENT_ID, IDP_CLIENT_SECRET (project/cluster already set for emb-vtsa-dev)
streamlit run app.py
```

Stay on **Guided demo** until `.env` is filled.

## Project layout

```text
app.py                         Streamlit flow
modules/catalyst_context/      Toolkit module (space, containers, views, RAW, jobs)
cdf/data_models/               GraphQL companion of the same types
config.dev.yaml                Toolkit env for emb-vtsa-dev
src/catalyst_context/
```

## Suggested next slice

- Deploy `modules/catalyst_context` into emb-vtsa-dev (space + containers + views + RAW + transformations)  
- File download / P&ID overlay for a selected tag  
- Charts Agent or Atlas AI on the exported context pack
