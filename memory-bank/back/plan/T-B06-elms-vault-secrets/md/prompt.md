## Epic

### Outcome
Статические production-секреты ELMS хранятся в локальном self-hosted HashiCorp Vault и доставляются сервисам только после authenticated render; sealed/missing/unauthorized Vault блокирует запуск.

### In
- single-node Vault с integrated Raft;
- KV v2, AppRole и Vault Agent render;
- MariaDB/Keycloak DB password files, Frappe/Keycloak/review/Yandex secrets;
- init, rotation, snapshot, restore и redaction checks.

### Out
Cloud secret manager, HA/auto-unseal, публичный Vault, изменение dev secrets и автоматический production bootstrap.

### Done when
1. Production не читает секреты из `.env` fallback.
2. Vault Agent render и backend/Keycloak startup fail closed.
3. Disposable snapshot restore подтверждён synthetic fixture.

### Forbidden after
Vault dev mode, root token runtime, public `8200`, secrets in images/logs/manifest, read-only Vault path вместо writable OAuth state.
