select
  external_id as `externalId`,
  name as name,
  mime_type as mimeType,
  kind as kind,
  if(
    asset_external_id is null,
    null,
    named_struct('space', '{{ instance_space }}', 'externalId', asset_external_id)
  ) as equipment
from `{{ raw_db }}`.`files`
where isnotnull(external_id)
