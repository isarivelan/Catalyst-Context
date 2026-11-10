# Catalyst Context CDF module

Cognite Toolkit module: data model + Streamlit app.

| Resource | What it is |
| --- | --- |
| Space `catalyst_context` | Home for schema and instances |
| 7 containers / 7 views | Physical storage + logical types |
| Data model `CatalystContext` `v1` | Collection of those views |
| RAW `catalyst_context_raw` | Seed tables |
| 4 transformations | RAW → data-model instances |
| Streamlit `catalyst_context_app` | Fusion-hosted app that reads the views |

## Schema

```text
Site 1──* Equipment 1──* ProcessSignal
                │
                ├──* ProcessEvent
                ├──* EngineeringFile
                └──* Batch 1──* QualityResult
```

## Deploy

```powershell
python scripts/deploy_cdf.py --seed-instances --run-jobs
```

Or:

```powershell
python -m cognite.toolkit build --env dev
python -m cognite.toolkit deploy --env dev
```

In Fusion: **Industrial tools → Streamlit → Catalyst Context**.
