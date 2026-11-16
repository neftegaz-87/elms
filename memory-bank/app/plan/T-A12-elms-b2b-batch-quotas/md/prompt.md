## Epic

### Outcome
Компания подтверждает разобранный бланк и зачисляет слушателей в пределах квоты мест организации.

### In
- confirm import rows;
- org-wide quota;
- flags owner-catalog / publish-own;
- Active enrollments.

### Out
AI parse; B2C payment; acting-as admin submit; 1С.

### Done when
1. Confirm при достаточной квоте создаёт Active enrollments и списывает места.
2. Over-quota — явная ошибка без тихого превышения.

### Forbidden after
Enroll без T-A11 parse; ignore subscription seats.

### Chat decisions
- Q6=A; Q7=A; Q2b=B; depends T-A11.

---

## Covering

### Outcome
ELMS принимает слушателей двумя каналами — физлицо само проходит анкету, загружает документы и оплачивает курс через платёжный порт, а компания-партнёр загружает бланк заявки, система разбирает его и зачисляет людей в пределах квоты — плюс школы задают свои поля курса/программы/потока, а платформенный админ видит все организации без подачи от их лица.

### Axes
- B2C: Learner Profile + сканы → Payment port/webhook → Enrollment
- AI-parse: XLSX бланк заявки → структурированные строки (+ synthetic credentials)
- B2B: confirm parse → квота org → Active Enrollment
- Custom fields MVP: Course + Program + Batch
- Admin: view-all organizations (без acting-as submit)

### Invariants
- Одно место квоты на org на любое зачисление (owner-каталог или свои курсы).
- Нет email в бланке → синтетические креды; админы раздают later.
- Payment Provider — абстрактный port; конкретный вендор и 1С вне cut.
- Bitrix status SoT — deferred, не блокирует native admission.
- Единый Learner Profile для B2C и строк B2B.
- Fail-closed: нет silent PASS через legacy/Bitrix dual path в новых эпиках.

### Out
1С счета; Bitrix как master статуса; custom fields на Category/Chapter/Lesson; acting-as submit админом от лица компании; корпоративный SSO заказчика.

### Done when
1. Нельзя закрыть нарезку, пока физлицо не может пройти pay→enroll и партнёр не может зачислить из бланка по квоте.
2. Эпик AI-parse ship-ready до B2B enroll; B2B не стартует без structured rows.
3. Form-builder MVP даёт кастомные поля на Course/Program/Batch без жёсткой схемы-only.

### Forbidden after
mega-plan · Covering как SoT REPLAN · читать соседние plan/ · optional SoT без follow-up в queue

### Chat decisions
- Multi-epic по поверхностям; Q13=C AI до B2B; Q14=B MVP C/P/Batch; Q15=A unified profile; Q16 Bitrix в воздухе; Q17 synthetic creds; Q4=C view-all only.


---

## Board

title: Пакетное зачисление по квоте компании

summary: |
Что делаем
После разбора бланка компания подтверждает список и зачисляет людей на программы/курсы в пределах одной квоты мест организации.
Зачем это бизнесу
Партнёр сам набирает поток по договору, не выходя за оплаченную квоту.
Технически
Confirm import → enforce ELMS Subscription seats → Active Enrollment; flags can_use_owner_catalog / can_publish_own.

