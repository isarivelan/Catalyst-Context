select
  external_id as `externalId`,
  name as name,
  unit as unit,
  external_id as externalTag,
  industry as industry,
  if(
    asset_external_id is null,
    null,
    named_struct('space', 'catalyst_context', 'externalId', asset_external_id)
  ) as equipment
from `catalyst_context_raw`.`timeseries`
where isnotnull(external_id)
