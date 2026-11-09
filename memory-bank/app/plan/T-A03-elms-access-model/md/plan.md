# T-A03 — Понятная модель доступа ELMS

## Product outcome

Администратор ELMS видит в Settings не только список пользователей, но и рабочую модель доступа: профили ролей с понятным составом, роли с переходом в матрицу прав, User Permissions и группы пользователей с явным объяснением их назначения. В runtime используется термин `ELMS Learner`; имя `ELMS LMS User` запрещено как тавтологичное.

## Decision

- Role — техническая capability-модель Frappe: права Read/Write/Create/Delete и дополнительные действия на DocType.
- Role Profile — назначаемый пользователю шаблон ролей. Системные профили ELMS создаются автоматически; `System Manager` в них не входит.
- User Group — организационная адресация и членство. Группа не выдаёт роли и не ограничивает записи.
- User Permission — ограничение области данных конкретного пользователя.
- `ELMS Admin` получает доступ к Settings, профилям, группам, User Permissions и read/write к странице Role Permissions Manager. `System Manager` сохраняется как техническая роль и может управлять всеми системными настройками.
- SSO mapping назначает профиль, если он указан; прямые роли остаются только для совместимости старых записей и специальных исключений.

## Canonical profiles

| Profile | Roles | Назначение |
|---|---|---|
| `ELMS Learner Profile` | `Desk User`, `ELMS Learner` | обучение, свои зачисления и прогресс |
| `ELMS Instructor Profile` | `Desk User`, `ELMS Instructor` | сопровождение потоков и проверка обучения |
| `ELMS Methodologist Profile` | `Desk User`, `ELMS Methodologist` | создание учебного контента и тестов |
| `ELMS Operations Profile` | `Desk User`, `ELMS Operations User` | управление каталогом, потоками, квотами и зачислениями |
| `ELMS Admin Profile` | `Desk User`, `ELMS Admin` | полный продуктовый доступ, включая Settings |

## Contract

- `/app/permission-manager` remains the native Frappe page; ELMS adds `ELMS Admin` to its page access and routes page API calls through an ELMS authorization wrapper.
- `elms.permissions.get_role_profile_summary` returns profile roles, role explanations, effective DocType permissions and users.
- Role Profile form renders the summary; Role form has a direct link to the matrix filtered by that role.
- User Group form displays the purpose and limitation of the group model.

## Migration

- Rename legacy role `ELMS LMS User` to `ELMS Learner`, including role references through Frappe rename support.
- Rename legacy `Elms` group to `ELMS Learners` when the target is absent; seed the remaining canonical groups idempotently.
- Seed canonical Role Profiles and migrate users whose role set is an exact canonical profile match.
- Normalize SSO mapping profile/role names.

## Non-goals

- User Groups do not automatically assign profiles.
- `ELMS Admin` does not receive `System Manager`.
- No custom parallel permission engine replaces Frappe DocPerm/User Permission.

## Done criteria

1. All runtime role references use `ELMS Learner`; migration handles existing installations.
2. Five profiles and five groups are idempotently seeded and visible in Settings.
3. Admin can open `/app/permission-manager` and see/update the effective matrix.
4. Profile and role forms explain what is granted and restricted.
5. Targeted unit tests and runtime smoke tests pass.
