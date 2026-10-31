## Epic

### Outcome
ELMS запускается как воспроизводимый production Compose-контур без исходников в runtime, с Frappe, MariaDB, Redis, Keycloak и staged Caddy-проверкой; рабочий локальный стенд и текущий внешний edge не ломаются.

### In
- immutable ELMS image contract и отдельный local build override;
- Frappe backend/frontend/websocket/workers/scheduler, MariaDB, Redis и Keycloak;
- internal-only dependency ports, health/readiness и resource policy;
- high-port smoke до публичного переключения;
- безопасная интеграционная граница сервиса сверки через `ELMS_REVIEW_URL` и one-time handoff.

### Out
- копирование FastAPI/AI-сервиса сверки в app `elms`;
- Qdrant/Ollama/PostgreSQL из чужого runtime — они не являются зависимостями ELMS;
- live DNS, firewall, миграция данных и немедленный захват 80/443.

### Done when
1. Production Compose без build/source mounts валидируется с точным image tag/digest.
2. Staged profile поднимается на localhost/high ports и проходит `/login`, Keycloak discovery и внутренние healthchecks.
3. MariaDB, Redis, Keycloak DB и внутренние Frappe-порты не опубликованы на host.
4. Существующий dev Compose остаётся отдельным контрактом.

### Forbidden after
`latest`, build из checkout на production host, Vite/dev source mounts в prod, публичные DB/Redis/Keycloak-порты, скрытый fallback на сверку без handoff-секрета.

### Chat decisions
- ELMS runtime = Frappe Framework + custom app `elms`.
- Сверка заявок остаётся отдельным first-party сервисом; ELMS только выдаёт короткоживущий handoff.
- Production сначала staged/high-port, публичный Caddy — отдельный owner-approved этап.
