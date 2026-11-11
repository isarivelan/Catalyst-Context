select
  external_id as `externalId`,
  batch_id as batchId,
  recipe as recipe,
  status as status,
  CAST(yield_pct AS DOUBLE) as yieldPct,
  CAST(cycle_hours AS DOUBLE) as cycleHours,
  CAST(deviations AS INT) as deviations,
  if(
    unit_external_id is null,
    null,
    named_struct('space', '{{ instance_space }}', 'externalId', unit_external_id)
  ) as unit
from `{{ raw_db }}`.`batches`
where isnotnull(external_id)
