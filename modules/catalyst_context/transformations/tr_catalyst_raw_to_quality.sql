select
  external_id as `externalId`,
  test as test,
  status as status,
  result as result,
  if(
    batch_external_id is null,
    null,
    named_struct('space', '{{ instance_space }}', 'externalId', batch_external_id)
  ) as batch,
  if(
    lab_external_id is null,
    null,
    named_struct('space', '{{ instance_space }}', 'externalId', lab_external_id)
  ) as lab
from `{{ raw_db }}`.`quality`
where isnotnull(external_id)
