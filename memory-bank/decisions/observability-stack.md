# Решение: ELMS — цель для чтения логов, не источник ship-to-central

**Дата:** 2026-11-01  
**Пересмотр:** 2026-11-12  
**Статус:** принято (supersedes ship-to-central Loki)  
**Область:** только ELMS (app-сервер / compose)  
**Центр SoT:** отдельный репозиторий `/home/aero/PyProject/observability` (и его деплой на ops-машине)

## Что изменилось

Прежний контракт «Vector/Alloy → центральный Loki» **отменён**.  
Причина: логи нужны при инциденте; постоянная пересылка забивает диск/RAM ops-машины и гоняет трафик без пользы.

Новый принцип: **логи остаются на хосте ELMS**; ops-машина **подключается и читает** их по запросу (SSH / localhost UI через туннель). На ops-машине постоянно живут только **метрики здоровья и алерты**, не склад логов.

## Что живёт в ELMS

1. Приложения пишут **структурированный JSON** в stdout/stderr контейнеров.
2. Docker/json-file (или journald) с **жёсткой ротацией** (`max-size` / `max-file`) — единственное штатное хранилище логов runtime.
3. Опционально на хосте ELMS: локальный просмотрщик (**Dozzle** или аналог) **только на `127.0.0.1`**, без публичного порта и без push на центр.
4. В `docker/compose.prod.yaml` / `compose.dev.yaml` **FORBIDDEN**:
   - Loki / Grafana / Prometheus / Tempo как SoT;
   - Vector / Alloy / Fluent Bit с remote sink на центральный Loki;
   - dual path «и локально, и ship».
5. Health/readiness эндпоинты сервисов остаются; **метрики хоста** (CPU/RAM/disk) снимает центр с ops-машины (blackbox/SSH/node_exporter — решение центра, не ELMS).

## Контракт с центром (`observability`)

| Поток | Направление | Владелец |
|-------|-------------|----------|
| Логи приложений/контейнеров | **остаются на ELMS**; центр **читает** по SSH/туннелю | ELMS хранит; observability читает |
| Uptime / ping / HTTP health | центр **опрашивает** с ops-машины | observability |
| Load / disk / memory | центр **опрашивает** (без склада логов) | observability |
| Алерты (Telegram и т.п.) | с ops-машины при смене состояния | observability |

Секреты доступа (SSH keys, inventory) — только в ops/Vault центра, не в git ELMS.

## Центральный стек (ссылка)

Владелец и compose: репозиторий **observability**.  
Locked (2026-11-12):

- **На ops-машине:** Grafana (UI метрик) + Prometheus (+ Alertmanager) + blackbox/uptime probes; **без** центрального Loki как склада логов флота.
- **На целевых хостах (в т.ч. ELMS):** локальные логи + опционально Dozzle на localhost.
- **ELK не используется.** Центральный Loki / ship-агент — **out of scope** до явного revisit.

## AC−

- Нет remote sink логов с ELMS на ops-машину.
- Нет «обязательного» Vector/Alloy в ELMS SoT ради центрального Loki.
- Нет silent dual path (часть логов ship, часть только local) после cutover на этот decision.
- Нет публично открытого UI логов на ELMS (только localhost + туннель/SSH).
- Нет подмены алерта «прочитай логи на центре» — алерт = здоровье; логи = на хосте.
