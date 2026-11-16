## Epic

### Outcome
Бланк заявки компании разбирается в структурированный список слушателей с синтетическими учётками при отсутствии email — без зачисления.

### In
- upload XLSX бланка;
- AI parse → validated rows;
- synthetic credentials для админов;
- preview/ошибки строк.

### Out
Enrollment; списание квоты; 1С; Bitrix master.

### Done when
1. Fixture бланка и sample Сметанин парсятся в DTO.
2. Эпик не создаёт Enrollment.

### Forbidden after
Считать B2B enroll done этим эпиком; silent OK при битом файле.

### Chat decisions
- Q13=C; Q17 synthetic creds; fixtures SoT.

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

title: Разбор бланка заявки компании

summary: |
Что делаем
Загруженный XLSX бланк заявки разбирается в структурированные строки слушателей (с синтетическими учётками, если нет email), готовые к зачислению.
Зачем это бизнесу
Кадровик компании не перебивает заявку вручную; учебный центр получает проверяемый список «кто на какую программу».
Технически
Upload бланка → neftegaz-ai-layer/ELMS AI parse → validated row DTO + synthetic credentials; enroll — следующий эпик.

