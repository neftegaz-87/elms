## Epic

### Outcome
Физлицо заполняет анкету с документами, оплачивает курс через платёжный шлюз и после подтверждения оплаты сразу попадает в обучение.

### In
- анкета слушателя и обязательные сканы;
- согласие на обработку ПДн;
- abstract payment + webhook paid/failed;
- зачисление только после оплаты.

### Out
1С; конкретный вендор как единственный hard-dep; B2B бланк; Bitrix как master статуса; конструктор полей курса.

### Done when
1. Без полного профиля и файлов оплата не стартует.
2. Webhook paid создаёт одно Active Enrollment; без paid зачисления нет.

### Forbidden after
Локальный «проставить оплачено» без payment event; silent enroll в обход payment port.

### Chat decisions
- Q9: docs before pay; Q8=D payment port; Q3b webhook; 1С out of cut.

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

title: Запись физлица на курс с оплатой

summary: |
Что делаем
Даём физлицу путь: заполнить анкету и загрузить документы, оплатить курс через платёжный шлюз и автоматически зачислиться после подтверждения оплаты.
Зачем это бизнесу
Школа принимает частных слушателей без ручной сверки оплаты и бумажных анкет в мессенджерах.
Технически
Learner Profile + файлы → abstract Payment Provider (create+webhook) → ELMS Enrollment только после paid.

