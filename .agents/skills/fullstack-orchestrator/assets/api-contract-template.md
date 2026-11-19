# API / event contract

```yaml
contract_id: <stable-name>
revision: <rN>
status: DRAFT
owner: <Main/role>
provider: <service/module>
consumers: [] # list known deployed versions, jobs and generated clients; UNKNOWN is allowed
compatibility_window: UNKNOWN
supersedes: null
```

## Boundary

- Kind: HTTP API / event / RPC / other
- Method + path or event name:
- Content type / protocol version:
- Authentication and authorization, including object ownership:
- Side effects and transaction boundary:

## Request or event

| Field | Type | Required | Nullable | Default/bounds | Validation/sensitivity |
|---|---|---:|---:|---|---|
| | | | | | |

## Success and errors

| Condition | HTTP/status or event outcome | Stable code | Response shape | Retryable/idempotent |
|---|---|---|---|---|
| Success | | | | |
| Validation | | | | |
| Unauthorized/forbidden | | | | |
| Conflict/rate limit/timeout | | | | |
| Unexpected failure | | | | |

## Compatibility and acceptance

- Versioning/deprecation and old-consumer compatibility:
- Timeout, duplicate submission, ordering, concurrency and partial success:
- Producer implementation owner/revision:
- Consumer implementation owners/revisions:
- Generated schemas/clients/types and generation command:
- Required checks and evidence paths:
- Open questions / UNKNOWN facts:
- Main acceptance decision and date:
