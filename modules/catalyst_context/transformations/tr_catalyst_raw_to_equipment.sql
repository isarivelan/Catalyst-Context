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
    named_struct('space', '{{ instance_space }}', 'externalId', parent_external_id)
  ) as parent,
  if(
    site_external_id is null,
    null,
    named_struct('space', '{{ instance_space }}', 'externalId', site_external_id)
  ) as site
from `{{ raw_db }}`.`equipment`
where isnotnull(external_id)
  and (kind is null or kind not in ('Site', 'Field'))
