## Epic

### Outcome
Публичный ELMS host обслуживается контейнерным Caddy только после staged rehearsal, owner approval и проверенного rollback на прежний edge.

### In
High-port rehearsal, route/TLS checks, explicit port ownership, ACME state and rollback wrapper.

### Out
Немедленная остановка текущего Caddy, автоматический switch из CI, копирование сертификатов и публичные внутренние сервисы.

### Done when
Missing predecessor evidence or approval exits before changing host Caddy; forced failure restores old edge and proves it.
