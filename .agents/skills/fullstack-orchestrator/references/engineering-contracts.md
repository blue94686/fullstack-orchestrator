# API, event and database change contracts

Use a compact project-native contract for changes crossing producers/consumers, API or event boundaries, persisted data, or independently deployed versions. For narrow changes that do not touch these boundaries, do not create a contract artifact just to satisfy a template. The examples in `assets/` are starting points, not mandatory schemas.

## Ownership and parallel work

Main owns the accepted contract revision and names one decision owner for each shared API/event contract and one migration owner for each schema/data migration. Implementers may work in parallel only after the relevant contract and version strategy are accepted, and only in disjoint writable scopes. A consumer cannot unilaterally redefine a provider's behavior. A migration cannot proceed on the assumption that code rollback also reverses data changes.

Before dispatch, identify the provider, all known consumers (including older deployed versions and jobs), generated clients/types, compatibility window, and relevant tests. Unknown consumers are a coverage limit, not proof of none. Main records which contract revision each producer/consumer implements; contract changes invalidate dependent checks and handoffs.

## API/event minimum fields

Record only applicable fields:

- Stable contract ID and revision, owner, status (DRAFT/ACCEPTED/SUPERSEDED), date/source identity.
- Provider, route/event name, method/protocol, content type, authn/authz and ownership checks.
- Request/event fields: type, required/optional, nullability, defaults, bounds/format, validation and sensitivity.
- Success and error envelopes: status/code, stable machine-readable code, safe user message, retryability, correlation/idempotency behavior.
- Pagination/order/versioning rules where relevant; timeout, duplicate, concurrency and partial-success behavior for side effects.
- Consumer list, compatibility/deprecation window, rollout order and generated artifacts.
- Acceptance checks, owner, exact evidence and known exclusions.

For any change to an error shape, field type/nullability, permission, retry semantics or side effect, trace producer→generated contract/client→all consumers→tests. A mock validates only the declared mock boundary; it is not evidence that a real provider matches.

## Database migration minimum fields

For schema/data changes record current and target schema identity, affected tables/columns/constraints/indexes, dependent code and known data volume/shape. Before tightening a constraint such as nullable→required, measure or otherwise verify existing violating rows, define a deterministic backfill/default or explicit remediation, and state the invariant check that must pass before enabling the constraint.

For rolling or independently deployed systems, define a compatible sequence (typically expand → deploy compatible readers/writers → backfill → verify → enforce/contract), the point each old/new application version is safe, lock/downtime risk, batching/resume behavior, transaction and idempotency guarantees, and the stop/rollback decision. Adapt the order to the actual database and deployment model; do not cargo-cult this sequence.

State separately:

- code rollback method;
- schema rollback method and whether it is safe after writes;
- data recovery method (backup/restore or compensating migration), authorization and recovery point;
- point of no safe automatic rollback and who decides;
- pre/post checks, row counts/invariants, representative reads/writes and monitoring evidence where available.

Never run a destructive or production migration without its action-specific authorization. Backups, data exports and snapshots are writes/costs and need the same scope and authorization checks. If rollback could lose or corrupt concurrent writes, stop and ask for a decision before the irreversible step.

## Templates

Copy only the relevant sections of [`api-contract-template.md`](../assets/api-contract-template.md) or [`database-migration-template.md`](../assets/database-migration-template.md) into the product project's own records. Do not overwrite an existing OpenAPI/schema/ADR/migration plan; link to it and add missing decisions there. Leave unknown facts explicitly `UNKNOWN`; unresolved material behavior keeps dependent work DRAFT/BLOCKED.
