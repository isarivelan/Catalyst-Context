# Catalyst Context CDF module

Cognite Toolkit module for the process-industry POC (life sciences + oil & gas).

This module is the source of truth for CDF Data Modeling:

| Resource | What it is |
| --- | --- |
| Space `catalyst_context` | Home for schema and instances |
| 7 containers | Physical property storage |
| 7 views | Logical types used for ingest and query |
| Data model `CatalystContext` `v1` | Collection of those views |
| RAW `catalyst_context_raw` | Seed tables |
| 4 transformations | RAW → data-model instances |

## Schema

```text
Site 1──* Equipment 1──* ProcessSignal
                │
                ├──* ProcessEvent
                ├──* EngineeringFile
                └──* Batch 1──* QualityResult
```

Direct relations live on the many-side containers (`Equipment.site`, `ProcessSignal.equipment`, …). Views map those properties and type the relation to the target view.

## Deploy with Cognite Toolkit

```powershell
cdf build --env dev
cdf deploy --env dev
```

`config.dev.yaml` targets project `emb-vtsa-dev`. Toolkit reads the same Entra client-credentials variables as the generated `.env` (`IDP_CLIENT_ID`, `IDP_CLIENT_SECRET`, `IDP_TENANT_ID`, `CDF_CLUSTER`, `CDF_PROJECT`).

## Deploy with this repo’s script

```powershell
python scripts/deploy_cdf.py
python scripts/deploy_cdf.py --seed-instances --run-jobs
```

The script applies space → containers → views → data model from this module (not GraphQL DML). GraphQL in `cdf/data_models/` is documentation of the same types.
