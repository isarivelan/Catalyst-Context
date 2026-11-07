select
  external_id as `externalId`,
  type as eventType,
  subtype as subtype,
  description as description,
  industry as industry,
  if(
    asset_external_id is null,
    null,
    named_struct('space', 'catalyst_context', 'externalId', asset_external_id)
  ) as equipment
from `catalyst_context_raw`.`events`
where isnotnull(external_id)
