select
  external_id as `externalId`,
  name as name,
  unit as unit,
  external_id as externalTag,
  industry as industry,
  if(
    asset_external_id is null,
    null,
    named_struct('space', '{{ instance_space }}', 'externalId', asset_external_id)
  ) as equipment
from `{{ raw_db }}`.`timeseries`
where isnotnull(external_id)
