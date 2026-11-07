select
  external_id as `externalId`,
  name as name,
  kind as kind,
  industry as industry,
  description as description,
  criticality as criticality,
  if(
    parent_external_id is null,
    null,
    named_struct('space', 'catalyst_context', 'externalId', parent_external_id)
  ) as parent,
  if(
    site_external_id is null,
    null,
    named_struct('space', 'catalyst_context', 'externalId', site_external_id)
  ) as site
from `catalyst_context_raw`.`equipment`
where isnotnull(external_id)
