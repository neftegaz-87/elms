## Epic

### Outcome
ELMS production state has encrypted off-host backup and a disposable restore path with RPO 24h/RTO 4h.

### In
- Frappe sites/logs and application files;
- MariaDB, Keycloak PostgreSQL, Redis queue, Vault Raft and Caddy state;
- capacity gate, retention, verification and restore rehearsal.

### Out
Destructive cleanup, automatic Docker prune, firewall/Caddy changes and active production restore.

### Done when
Failed/stale/unverifiable backup blocks production promotion, and restore never writes active volumes by default.
