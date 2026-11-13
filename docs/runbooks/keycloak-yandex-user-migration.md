# Keycloak-only migration of legacy Yandex-linked users

This runbook is for an `ELMS Admin` operator during the Keycloak-only cutover.
It does not store or print user passwords or Yandex credentials.

## Order of operations

1. Keep the Keycloak realm available and run a dry run:

   `elms.elms.access.api.migrate_yandex_users(dry_run=True)`

2. Review the returned `migrated`, `skipped`, and `errors` counts. Resolve any
   error before applying the migration.

3. Run the apply operation:

   `elms.elms.access.api.migrate_yandex_users(dry_run=False)`

   The operation is admin-only and idempotent. Each provisioned user receives
   the local Keycloak `UPDATE_PASSWORD` required action. The legacy social link
   is replaced only after the Keycloak user upsert and action request succeed.

4. Verify the returned counts and the audit/runtime trace. Only after a clean
   apply may the realm seed/runtime be deployed without the legacy provider.

5. If an item fails, keep its legacy link for retry, inspect the typed error,
   and rerun the apply operation after the provider issue is corrected.

## Safety rules

- Run from a server-side Frappe context with Keycloak Admin credentials supplied
  by the runtime secret store.
- Never put a password, client secret, or token in a command, log, or evidence
  file.
- A non-admin caller must be rejected; a partial migration must not be reported
  as a successful full cutover.
