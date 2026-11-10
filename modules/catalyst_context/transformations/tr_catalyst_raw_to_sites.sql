select
  external_id as `externalId`,
  name as name,
  industry as industry,
  description as description
from `{{ raw_db }}`.`equipment`
where isnotnull(external_id)
  and kind in ('Site', 'Field')
