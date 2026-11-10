select
  external_id as `externalId`,
  type as eventType,
  subtype as subtype,
  description as description,
  industry as industry,
  if(
    asset_external_id is null,
    null,
    named_struct('space', '{{ instance_space }}', 'externalId', asset_external_id)
  ) as equipment
from `{{ raw_db }}`.`events`
where isnotnull(external_id)
