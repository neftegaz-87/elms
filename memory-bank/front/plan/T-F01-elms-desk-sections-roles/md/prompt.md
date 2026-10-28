## Epic

### Outcome
Оператор ELMS после входа в Desk видит только разрешённые разделы (ERP / LMS / Settings) согласно роли, а на `/login` однозначно читает кнопки входа через Keycloak и Яндекс — без отдельного SPA.

### In
- Workspace fixtures ERP, LMS, Settings с roles
- Ссылки на placeholder Section DocTypes / «скоро»
- SSO button labels/icons для Keycloak и Yandex
- UI smoke: три роли → разный sidebar; login показывает 2 SSO

### Out
- Создание Roles/DocPerm (BACK)
- OAuth callback/server config (BACK)
- Дизайн-система / Vue SPA / кастомный login rewrite
- Доменные экраны курсов и склада

### Done when
1. ELMS ERP User в sidebar видит ERP и не видит LMS/Settings
2. ELMS Admin видит все три workspace
3. На `/login` при enabled providers подписи «Войти через Keycloak» и «Войти через Яндекс» (или эквивалент через Social Login Key title/icon)
4. Проверка зафиксирована Playwright или ручной AC-чеклист в plan

### Forbidden after
прятать разделы только CSS при открытом доступе DocType · свой login SPA · игнорировать roles на Workspace

### Chat decisions
- Разделы = Desk Workspaces
- Три роли как в BACK
- SSO UI на стандартной Frappe login

---

## Covering

### Outcome
Пользовательский контур foundation ELMS: Desk-навигация по трём разделам с ролевой видимостью и понятный SSO-вход Keycloak/Яндекс на штатной login-странице.

### Axes
- Desk Workspaces + role visibility (этот эпик)

### Invariants
- UI не обходит Frappe permissions
- Нет второго фронтенд-framework для login/Desk shell в этом batch
- Копирайт SSO согласован с Social Login Key

### Out
- Полный product UI ERP/LMS
- Unified design tokens epic
- Mobile app

### Done when
1. Sidebar соответствует матрице ролей
2. SSO кнопки видимы и подписаны при enable

### Forbidden after
кастомный SPA «вместо Desk» в этом эпике · dual navigation SoT

### Chat decisions
- FRONT зависит от BACK RBAC+SSO
- Desk-only shell

---

## Board

title: Разделы меню и кнопки входа для людей

summary: |
  Что делаем
  Настраиваем рабочий стол ELMS так, чтобы сотрудник после входа видел только свои разделы меню: ERP, LMS или Настройки — в зависимости от роли. На странице входа подписи кнопок Keycloak и Яндекс делаем понятными для людей.

  Зачем
  Права уже есть на уровне системы (предыдущие задачи). Здесь человек реально «видит» границы доступа в интерфейсе и понимает, чем можно войти.

  Что увидят роли
  • Администратор — ERP, LMS и Настройки.
  • Сотрудник ERP — только ERP.
  • Сотрудник LMS — только LMS.

  Стадии
  1) Создать три раздела меню (workspaces) с привязкой к ролям.
  2) В каждом разделе дать простую ссылку на заглушку раздела («скоро» / скелет).
  3) Подписать кнопки входа: «Войти через Keycloak», «Войти через Яндекс».
  4) Подготовить трёх тестовых пользователей под роли и проверить меню глазами.
  5) Зафиксировать чеклист приёмки (кто что должен видеть).

  Результат для наблюдателя
  После входа меню совпадает с ролью. На входе две понятные кнопки SSO. Отдельное мобильное приложение и дизайн-система в эту задачу не входят.
