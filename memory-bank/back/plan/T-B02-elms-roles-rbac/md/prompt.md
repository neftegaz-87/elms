## Epic

### Outcome
На установленном site ELMS действуют ровно три продуктовые роли с явными правами на секции Operations / LMS / Settings: Admin видит всё, Operations User — только Operations, LMS User — только LMS; Guest и чужая роль не получают доступ к placeholder DocTypes секций.

### In
- Roles: `ELMS Admin`, `ELMS Operations User`, `ELMS LMS User`
- Placeholder DocTypes секций + Custom DocPerm
- after_install / fixtures seed fail-closed
- Тесты has_permission матрицы

### Out
- Docker/site bootstrap (предыдущая ось)
- Social Login Key / default SSO role wiring деталей провайдеров (следующая ось может читать default role)
- Desk Workspace sidebar UI (FRONT)
- Доменные DocTypes курсов / бизнес-процессов

### Done when
1. Три Role существуют после install/migrate
2. Operations User: read Operations Section = true; LMS/Settings Section = false
3. Admin: read всех трёх Section = true
4. Отсутствие роли в seed при поломанном install → явная ошибка, не «тихо без ролей»

### Forbidden after
мягко пропускать seed ролей · давать Guest read на секции · плодить четвёртую «временную» роль без записи в modules/plan

### Chat decisions
- Имена ролей зафиксированы: ELMS Admin / ELMS Operations User / ELMS LMS User
- Секции = placeholder DocTypes под Module Core/Operations/LMS

---

## Covering

### Outcome
ELMS получает воспроизводимый foundation: один Frappe site в Docker с custom app, БД User, тремя ролями-разделами и базовым SSO Keycloak+Яндекс — без vendor ERPNext/LMS apps и без доменной логики.

### Axes
- Docker + site + скелет app `elms`
- Ролевая модель на три роли и placeholder DocTypes секций
- Social Login Key для Keycloak и Яндекс

### Invariants
- Runtime = Frappe Framework; SoT продукта = app `elms`
- Секреты только env/site_config, не в git
- Ошибки явные; silent fallback FORBIDDEN
- Эталон `frappe-erp-crm` — read-only паттерны

### Out
- Доменные DocTypes Operations/LMS (курсы, BPM-документы, согласования)
- Отдельный Vue SPA
- Prod TLS / MFA
- Forge / 1С контур

### Done when
1. Site поднимается из compose с Administrator
2. Три роли ограничивают доступ к секциям на уровне permissions
3. На `/login` доступны Keycloak и Яндекс при корректных env

### Forbidden after
склеить оси в один mega-plan · ставить vendor apps «чтобы быстрее» · dual-path auth в обход Social Login Key

### Chat decisions
- SSO = Keycloak + Яндекс
- Роли = ELMS Admin / ELMS Operations User / ELMS LMS User
- Разделы = Desk Workspaces Operations / LMS / Settings

---

## Board

title: Три роли доступа к разделам ELMS

summary: |
  Что делаем
  Заводим в системе три продуктовые роли и жёстко прописываем права на разделы Operations / LMS / Settings.

  Зачем
  Чтобы с самого начала не было «все видят всё». Позже меню Desk и экраны будут опираться на эти же права, а не на скрытие кнопок «на глаз».

  Роли (точные имена)
  • ELMS Admin — все разделы (Operations, LMS, Settings).
  • ELMS Operations User — только Operations (бизнес-операции / BPM).
  • ELMS LMS User — только LMS (учебный контур).
  Гость и чужая роль к разделам доступа не имеют.

  Стадии
  1) Создать три роли: ELMS Admin, ELMS Operations User, ELMS LMS User.
  2) Создать якоря разделов (заглушки Operations / LMS / Settings без бизнес-данных).
  3) Назначить права чтения/записи по матрице ролей.
  4) Проверить автотестами: ELMS Operations User не читает LMS и Settings; ELMS Admin читает всё.
  5) Повторная установка/миграция не ломает роли и не создаёт дубликаты.

  Результат для наблюдателя
  В системе есть три роли с прозрачными границами. Можно выдавать доступ людям до появления реальных курсов и документов бизнес-процессов.
