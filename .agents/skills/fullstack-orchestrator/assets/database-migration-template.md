# Database migration and data change

```yaml
migration_id: <stable-name>
revision: <rN>
status: DRAFT
owner: <single migration owner>
database_engine_version: UNKNOWN
environment: <local/test/staging/production>
production_authorized: false
```

## Change and compatibility

- Current schema/data invariant:
- Target schema/data invariant:
- Affected objects and application/job consumers:
- Known data volume and violating-row query/evidence:
- Backfill/default/remediation and idempotency:
- Old/new reader-writer compatibility window:
- Ordered rollout steps and stop gates:
- Locking, downtime, batching and resume considerations:

## Recovery and authorization

- Code rollback:
- Schema rollback:
- Data recovery (backup/restore or compensating migration):
- Authorization required for backup/export/production operation:
- Point after which automatic rollback is unsafe:
- Decision owner for that point:

## Verification

- Pre-migration invariant and evidence:
- Post-backfill count/invariant and evidence:
- Constraint/index validation:
- New and old application read/write checks:
- Failure/partial batch/retry checks:
- Candidate/environment identity:
- Remaining UNKNOWN items and acceptance decision:
