## Board

title: ELMS — логи на хосте, чтение с ops-машины
summary: Сейчас логи при инциденте должны оставаться на сервере ELMS, а не копироваться на центральный склад. Зачем это бизнесу: быстрее разбор сбоев без лишнего трафика и без раздувания диска ops-машины. Технически: JSON в stdout с ротацией, без Vector/Loki ship; опциональный Dozzle только на localhost; контракт чтения из репозитория observability по SSH/туннелю.

## Epic

### Outcome
ELMS production/dev compose соответствует decision «логи локально»: нет remote sink, есть ротация и документированный способ чтения с ops-машины.

### In
Compose logging options, AC− на Loki/Vector remote, optional localhost Dozzle overlay, runbook pointer to observability inventory, JSON stdout hygiene for key services.

### Out
Центральный Loki/Grafana в ELMS, постоянный ship логов, Tempo, публичный UI логов, замена vpn-monitor/observability стека внутри ELMS.

### Done when
Policy/tests fail-closed на remote log ship; docs и decision совпадают; оператор с ops-хоста может прочитать логи ELMS без копирования на центр.

## Covering

- Decision: `memory-bank/decisions/observability-stack.md` (2026-11-12)
- Center plan: `/home/aero/PyProject/observability/memory-bank/plan/T-OBS-001-ops-console-pull-logs/md/plan.md`
