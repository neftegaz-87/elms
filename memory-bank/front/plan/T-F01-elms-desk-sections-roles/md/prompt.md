## Epic

### Outcome
Оператор ELMS после входа в Desk видит только разрешённые разделы (Operations / LMS / Settings) согласно роли, а на `/login` видит одну понятную кнопку входа через Keycloak. Выбор Yandex или локального fallback-пароля происходит внутри Keycloak — без отдельного SPA.

### In
- Workspace fixtures Operations, LMS, Settings с roles
- Ссылки на placeholder Section DocTypes / «скоро»
- SSO button label/icon для Keycloak
- UI smoke: три роли → разный sidebar; Frappe login показывает 1 SSO

### Out
- Создание Roles/DocPerm (BACK)
- OAuth callback/server config (BACK)
- Дизайн-система / Vue SPA / кастомный login rewrite
- Доменные экраны курсов и склада

### Done when
1. ELMS Operations User в sidebar видит Operations и не видит LMS/Settings
2. ELMS Admin видит все три workspace
3. На `/login` при enabled Keycloak Social Login Key видна подпись «Войти через Keycloak» (или эквивалент через Social Login Key title/icon); Yandex не является прямой кнопкой Frappe
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
Пользовательский контур foundation ELMS: Desk-навигация по трём разделам с ролевой видимостью и понятный единый SSO-вход через Keycloak на штатной login-странице; Yandex и локальный fallback доступны внутри Keycloak.

### Axes
- Desk Workspaces + role visibility (этот эпик)

### Invariants
- UI не обходит Frappe permissions
- Нет второго фронтенд-framework для login/Desk shell в этом batch
- Копирайт SSO согласован с Social Login Key

### Out
- Полный product UI Operations/LMS
- Unified design tokens epic
- Mobile app

### Done when
1. Sidebar соответствует матрице ролей
2. Единственная SSO-кнопка Keycloak видима и подписана при enable

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
Настраиваем рабочий стол ELMS так, чтобы сотрудник после входа видел только свои разделы меню: Operations, LMS или Настройки — в зависимости от роли. На странице входа делаем понятной единственную кнопку Keycloak; Yandex и локальный fallback остаются на стороне Keycloak.

  Зачем
  Права уже есть на уровне системы (предыдущие задачи). Здесь человек реально «видит» границы доступа в интерфейсе и понимает, чем можно войти.

  Что увидят роли
  • ELMS Admin — Operations, LMS и Settings.
  • ELMS Operations User — только Operations.
  • ELMS LMS User — только LMS.

  Стадии
  1) Создать три раздела меню (workspaces) с привязкой к ролям.
  2) В каждом разделе дать простую ссылку на заглушку раздела («скоро» / скелет).
3) Подписать кнопку входа: «Войти через Keycloak».
  4) Подготовить трёх тестовых пользователей под роли и проверить меню глазами.
  5) Зафиксировать чеклист приёмки (кто что должен видеть).

  Результат для наблюдателя
После входа меню совпадает с ролью. На Frappe login одна понятная кнопка SSO, а внутри Keycloak доступны Yandex и локальный fallback. Отдельное мобильное приложение и дизайн-система в эту задачу не входят.
