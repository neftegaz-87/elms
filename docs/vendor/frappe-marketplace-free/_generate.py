#!/usr/bin/env python3
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APPS_DIR = ROOT / "apps"
APPS_DIR.mkdir(parents=True, exist_ok=True)

data = json.loads(Path("/tmp/fc-market/free_details.json").read_text())

CAT_BIZ = {
    "Accounting": (
        "Бухгалтерия, финансы, МСБ и mid-market с полноценным учётом",
        [
            "Ручной учёт и ошибки в проводках",
            "Нет единой картины денег и долгов",
            "Сложно закрывать период и сдавать отчётность",
        ],
    ),
    "Analytics": (
        "Руководители и аналитики с данными в ERP",
        [
            "Отчёты собирают вручную в Excel",
            "Нет BI поверх ERPNext",
            "Решения без актуальных цифр",
        ],
    ),
    "AI": (
        "Команды, ускоряющие рутину через ИИ внутри ERP",
        [
            "Долго пишут тексты и разбирают документы",
            "Нет ассистента по данным ERP",
            "Дорого держать людей на простые задачи",
        ],
    ),
    "Automation": (
        "Операционные команды с повторяющимися процессами",
        [
            "Повторяющиеся ручные шаги",
            "Забытые follow-up и просрочки",
            "Люди делают работу workflow",
        ],
    ),
    "Business": (
        "МСБ, которому нужны отраслевые или управленческие модули сверх базы ERPNext",
        [
            "Стандартного ERPNext не хватает",
            "Процессы в Excel и мессенджерах",
            "Нет отраслевой логики",
        ],
    ),
    "Collaboration": (
        "Команды и удалённые сотрудники",
        [
            "Переписка вне системы",
            "Теряется контекст задач",
            "Сложно синхронизировать работу",
        ],
    ),
    "Communication": (
        "Продажи, поддержка, маркетинг",
        [
            "Клиенты пишут в разных каналах",
            "Нет истории переписки в CRM/ERP",
            "Уведомления не доходят вовремя",
        ],
    ),
    "Compliance": (
        "Компании в регулируемых юрисдикциях (налоги, e-invoice)",
        [
            "Риск штрафов",
            "Ручная подготовка налоговых документов",
            "Сложно успевать за изменениями закона",
        ],
    ),
    "CRM Integration": (
        "Продажи и маркетинг с внешними lead-каналами",
        [
            "Лиды не попадают в CRM вовремя",
            "Двойной ввод",
            "Потеря заявок с рекламы/маркетплейсов",
        ],
    ),
    "Customer Relations": (
        "Продажи и клиентский сервис",
        [
            "Потеря касаний с клиентом",
            "Нет единого профиля клиента",
            "Слабый follow-up",
        ],
    ),
    "Developer": (
        "Разработчики и партнёры Frappe/ERPNext",
        [
            "Много boilerplate",
            "Сложно документировать API",
            "Неудобно сопровождать кастом",
        ],
    ),
    "Extension": (
        "Команды на Frappe/ERPNext, которым нужны точечные улучшения Desk",
        [
            "UX Desk тормозит работу",
            "Нет мелкой функции из коробки",
            "Пользователи обходят систему костылями",
        ],
    ),
    "Files": (
        "Компании с большим объёмом документов",
        [
            "Файлы разъезжаются по дискам и почте",
            "Нет контроля доступа",
            "Дорого хранить всё на сайте",
        ],
    ),
    "Healthcare": (
        "Клиники и медцентры",
        [
            "Разрозненные карты пациентов",
            "Сложный учёт приёмов",
            "Нет связки клиники с финансами",
        ],
    ),
    "Human Resources": (
        "HR и payroll",
        [
            "Ручной учёт явок и отпусков",
            "Ошибки в зарплате",
            "Нет self-service для сотрудников",
        ],
    ),
    "Integrations": (
        "Компании с внешними сервисами (платежи, банки, маркетплейсы, мессенджеры)",
        [
            "Нет синхронизации данных",
            "Двойной ввод в двух системах",
            "Ошибки ручной выгрузки",
        ],
    ),
    "Localization": (
        "Бизнес в конкретной стране с локальными налогами и форматами",
        [
            "Глобальный ERPNext не закрывает локальные требования",
            "Ручные правки под страну",
            "Риск несоответствия закону",
        ],
    ),
    "Marketing": (
        "Маркетинг и B2B growth",
        [
            "Кампании вне ERP",
            "Нет связки лидов и контента",
            "Сложно измерить эффект",
        ],
    ),
    "Mobile": (
        "Полевые сотрудники и мобильные команды",
        [
            "Нет удобного доступа с телефона",
            "Данные вносят поздно с бумажек",
            "Полевая работа не покрыта",
        ],
    ),
    "Non-Profit": (
        "НКО и фонды",
        [
            "Сложно учитывать бенефициаров и программы",
            "Донорская отчётность вручную",
            "Нет прозрачности помощи",
        ],
    ),
    "Payments": (
        "Компании, принимающие онлайн и банковские платежи",
        [
            "Оплата не связана с ERP",
            "Ручная сверка",
            "Долго выставлять и собирать оплату",
        ],
    ),
    "Productivity": (
        "Любые команды, ускоряющие ежедневную работу в Desk",
        [
            "Много кликов на простые действия",
            "Нет удобного планирования",
            "Потеря времени на рутину",
        ],
    ),
    "Retail": (
        "Розница, магазины, кафе, сети точек",
        [
            "Неудобный POS",
            "Расхождения остатков и кассы",
            "Сложно вести смены и скидки",
        ],
    ),
    "Storage": (
        "Компании с файловым хранилищем и бэкапами",
        [
            "Неудобное хранение файлов",
            "Нет внешнего S3/облака",
            "Риск потери вложений",
        ],
    ),
    "Support": (
        "Службы поддержки",
        ["Тикеты в почте и чатах", "Нет SLA/TAT", "Потеря обращений"],
    ),
    "Themes": (
        "Компании, которым важен бренд и UX Desk/портала",
        [
            "Стандартный Desk не подходит бренду",
            "Путаница test/prod",
            "Слабая визуальная иерархия",
        ],
    ),
    "Utilities": (
        "Операционные и IT-команды",
        [
            "Нет маленького инструмента под задачу",
            "Ручные обходные пути",
            "Слабая наблюдаемость",
        ],
    ),
    "Utility": (
        "Операционные и IT-команды",
        [
            "Нет маленького инструмента под задачу",
            "Ручные обходные пути",
            "Слабая наблюдаемость",
        ],
    ),
    "Website": (
        "Компании с сайтом/порталом на Frappe",
        [
            "Сайт и ERP разъехались",
            "Сложно публиковать контент",
            "Слабый SEO/формы/магазин",
        ],
    ),
}

# (pattern_on_title_name_cats, pattern_on_about_or_None, what, tasks, biz, pains)
RULES = [
    (
        r"whatsapp",
        r"whatsapp",
        "обмен сообщениями WhatsApp из ERP/CRM",
        [
            "Отправка и получение WhatsApp",
            "Шаблоны и уведомления клиентам",
            "Связка переписки с документами ERP",
        ],
        "Отделы продаж и поддержки",
        ["Клиенты пишут в WhatsApp вне CRM", "Нет истории переписки у сделки"],
    ),
    (
        r"telegram",
        r"telegram",
        "интеграцию Telegram с ERPNext",
        ["Уведомления и бот Telegram", "Связка сообщений с ERP"],
        "Операционные и sales-команды",
        ["Важные события не доходят в мессенджер", "Переписка вне системы"],
    ),
    (
        r"\bsms\b|msg91|telenor",
        r"\bsms\b|msg91|telenor sms",
        "отправку SMS из Frappe/ERPNext",
        ["SMS-уведомления", "Интеграция SMS-шлюза"],
        "Компании с SMS-коммуникациями",
        ["SMS шлюз не связан с ERP", "Ручная рассылка статусов"],
    ),
    (
        r"e-?invoice|zatca|etims|factur|peppol|myinvois|digi.?tax|einvoice",
        r"e-?invoice|zatca|etims|peppol|myinvois|tax authority|electronic invoic",
        "электронный докутинг и налоговый комплаенс",
        [
            "Выставление e-invoice",
            "Передача данных регулятору",
            "Локальные налоговые форматы",
        ],
        "Компании с обязательным e-invoicing",
        ["Риск штрафов за несдачу e-invoice", "Ручная подготовка XML/QR"],
    ),
    (
        r"\bpos\b|point of sale|lumenpos|vunapos|posnext|pospire|^ury$|pos restaurant|easy_pos",
        r"point of sale|\bpos\b terminal|cashier",
        "кассу и розничные продажи",
        ["Быстрые продажи на кассе", "Смены и оплаты", "Скидки, возвраты, остатки"],
        "Розница и HoReCa",
        ["Медленная/неудобная касса", "Расхождения кассы и склада"],
    ),
    (
        r"bank|reconcile|gocardless|simplefin|statement",
        r"bank (sync|statement|reconciliation)|gocardless|simplefin|reconcile",
        "банковскую синхронизацию и сверку",
        [
            "Импорт банковских операций",
            "Сверка с платежами/счетами",
            "Автоматизация reconcile",
        ],
        "Финансовые отделы",
        ["Долгая ручная сверка выписок", "Платежи «висят» неразнесёнными"],
    ),
    (
        r"stripe|razorpay|paypal|paystack|mpesa|tingg|sumup|pinelabs|lodinpay|^payments$",
        r"razorpay|stripe|paypal|braintree|paytm|payment gateway",
        "приём онлайн/терминальных платежей",
        [
            "Оплата счетов ссылкой/терминалом",
            "Создание Payment Entry",
            "Связка платежного шлюза с ERP",
        ],
        "Компании, принимающие безнал",
        [
            "Оплаты не попадают в ERP автоматически",
            "Ручная разноска платежей",
        ],
    ),
    (
        r"\bhr\b|payroll|attendance|leave|hrms|salary|check.?in|biometric|hr forms|hr addon",
        r"\bpayroll\b|\battendance\b|employee check|leave management|\bhrms\b",
        "HR, явки и/или расчёт зарплаты",
        ["Учёт рабочего времени", "Отпуска и кадровые процессы", "Payroll / check-in"],
        "HR и руководители смены",
        ["Ошибки в явках и зарплате", "Нет self-service для сотрудников"],
    ),
    (
        r"woocommerce|webshop|shopify|indiamart|easyecom|ondc|bezzie",
        r"woocommerce|shopify|indiamart|easyecom|marketplace sync|e-?commerce",
        "связку e-commerce / маркетплейса с ERP",
        ["Синхронизация товаров и остатков", "Импорт заказов/лидов", "Единый каталог"],
        "Интернет-магазины и продавцы на маркетплейсах",
        ["Двойной каталог", "Заказы не доходят в ERP вовремя"],
    ),
    (
        r"print.?designer|pdf_on_submit|letterhead|digital.?signature|esign|print.?encrypt",
        r"print format|print designer|digital signature|letterhead|\bPDF\b on submit",
        "печатные формы, PDF и подпись документов",
        [
            "Конструктор/улучшение print format",
            "PDF при submit",
            "Подпись или защита документов",
        ],
        "Отделы продаж, закупки, бухгалтерия",
        ["Некрасивые или небезопасные PDF", "Долго готовить печатные формы"],
    ),
    (
        r"theme|navbar|desk.?theme|saas.?theme|swift.?theme|nexus.?theme|solvronix|rukntheme|tekton|business.?theme|fintheme|red.?background",
        r"\btheme\b for (frappe|erpnext|desk)|desk theme|colorful material",
        "тему и внешний вид Desk/портала",
        ["Смена темы Desk", "Брендинг интерфейса", "UX-улучшения оболочки"],
        "Компании, которым важен UX и бренд",
        [
            "Стандартный Desk не нравится пользователям",
            "Путают test и prod",
        ],
    ),
    (
        r"\bai\b|gpt|openai|llm|chatbot|ocr|instagpt|changai|alyf|doc.?intelligence|noviz|sales.?ai|frappe.?assistant|next.?ai",
        r"\bchatgpt\b|\bopenai\b|\bLLM\b|AI (assistant|chatbot|agent)|OCR",
        "ИИ-помощника или разбор документов внутри ERP",
        ["Чат/ассистент по данным", "Генерация или правка текста", "OCR/разбор документов"],
        "Команды с большим объёмом текста и документов",
        ["Ручной разбор PDF и писем", "Нет помощи внутри ERP"],
    ),
    (
        r"helpdesk|incident.?management|helpdesk.?management",
        r"\bhelpdesk\b|\bticketing\b|\bSLA\b|\bticket(s|ing)\b",
        "тикеты и службу поддержки",
        ["Приём обращений", "SLA/TAT", "Эскалации и уведомления"],
        "Клиентский сервис",
        ["Тикеты теряются в почте", "Нет контроля сроков"],
    ),
    (
        r"^crm$|follow.?up|due.?diligence|mansico|indiamart",
        r"\bcrm\b platform|lead management|sales pipeline|follow-?ups?",
        "продажи и CRM-процессы",
        ["Лиды и сделки", "Follow-up", "КП и касания с клиентом"],
        "Отделы продаж",
        ["Лиды остывают", "Нет дисциплины воронки"],
    ),
    (
        r"learning|^lms$|education|pcat|course",
        r"\bLMS\b|learning management|courses? with|quizzes",
        "обучение и LMS",
        ["Курсы и уроки", "Тесты/прогресс", "Группы учеников"],
        "Учебные центры, корп. обучение, школы",
        ["Обучение вне системы", "Сложно отслеживать прогресс"],
    ),
    (
        r"^drive$|s3|storage|backup|multicloud|dfp.?s3|frappe.?s3|offsite.?backup",
        r"\bS3\b|file storage|drive app|backup to|attachments? to (s3|gcs|cloud)",
        "хранение файлов и/или бэкапы",
        ["Внешнее хранилище вложений", "Обмен файлами", "Бэкапы"],
        "Компании с большим объёмом файлов",
        ["Диск сайта забит вложениями", "Нет централизованного файлового доступа"],
    ),
    (
        r"^wiki$|blog|builder|frappe.?seo|web.?forms?",
        r"\bwiki\b|\bblog\b|website builder|SEO suite|web forms?",
        "сайт, контент или документацию на Frappe",
        ["Публикация контента", "Страницы/формы", "SEO или база знаний"],
        "Команды с сайтом/порталом на Frappe",
        ["Контент и ERP разъехались", "Сложно вести базу знаний"],
    ),
    (
        r"^raven$|gameplan|whiteboard|sketchboard|meeting.?management|clefin",
        r"\bchat app\b|team chat|whiteboard|meeting notes|gameplan",
        "командную коммуникацию и совместную работу",
        ["Чаты/обсуждения", "Совместные доски или встречи", "Контекст рядом с ERP"],
        "Команды внутри компании",
        ["Переписка в сторонних мессенджерах", "Теряется контекст задач"],
    ),
    (
        r"warehouse|stock|wms|inventory|gate.?entry|theatre.?3d|stone.?warehouse",
        r"warehouse management|\bstock\b reconciliation|inventory",
        "складской учёт и операции",
        ["Остатки и перемещения", "Складские процессы", "Контроль поступления/отгрузки"],
        "Дистрибуция, производство, ритейл",
        ["Не видно реальных остатков", "Ошибки на складе"],
    ),
    (
        r"shipping|eshipz|bob.?go|cargo|clickpost",
        r"shipping|courier|logistics|shipment",
        "логистику и доставку",
        ["Оформление отправлений", "Трекинг", "Интеграция с перевозчиками"],
        "E-commerce и отгрузки",
        ["Ручное создание накладных", "Нет статуса доставки в ERP"],
    ),
    (
        r"loan|lending|export.?lc|import.?lc|letter of credit",
        r"\bloan\b|\blending\b|letter of credit|\bLC\b",
        "кредиты, займы или аккредитивы",
        ["Учёт договоров", "Графики/погашения", "Контроль лимитов"],
        "Финансовые и торговые компании",
        ["Сложный ручной учёт графиков", "Риск ошибок в процентах/лимитах"],
    ),
    (
        r"hotel|rental|lease|property|estate|kamra|suit.?rental|utility.?&.?rental|propms",
        r"property management|lease|rental|hotel|short-?term",
        "аренду и управление объектами",
        ["Договоры аренды", "Напоминания об оплате", "Учёт объектов/помещений"],
        "Управляющие компании, отели, арендный бизнес",
        ["Просрочки аренды", "Договоры в Excel"],
    ),
    (
        r"restaurant|kitchen|ury|sajha",
        r"restaurant|kitchen screen|table order",
        "ресторанные операции",
        ["Заказы со столов", "Кухня/POS", "Учёт ресторанных продаж"],
        "Рестораны и кафе",
        ["Зал и кухня не синхронизированы", "Ошибки в заказах"],
    ),
    (
        r"twilio|exotel|telephony|call.?integration|smartflo",
        r"twilio|exotel|telephony|phone call|PBX",
        "телефонию и звонки",
        ["Интеграция АТС/звонков", "Связка звонков с CRM", "Уведомления о звонках"],
        "Отделы продаж и поддержки",
        ["Звонки не фиксируются в CRM", "Нет истории коммуникаций"],
    ),
    (
        r"india.?compliance|gstr|gst",
        r"\bGST\b|GSTR|India Compliance",
        "индийский налоговый комплаенс (GST и др.)",
        ["GST-отчёты", "Сверки", "Локальные требования Индии"],
        "Бизнес в Индии",
        ["Ручная подготовка GST", "Риск ошибок в налоговой отчётности"],
    ),
    (
        r"insights|report.?builder|lumen.?reports|ampower|bigquery",
        r"business intelligence|\bBI\b tool|open-source (BI|analytics)|analytics tool for",
        "аналитику и отчёты",
        ["Дашборды и отчёты", "Анализ транзакций", "Выгрузка/визуализация данных"],
        "Руководители и аналитики",
        ["Отчёты в Excel вручную", "Нет наглядной аналитики"],
    ),
]

CURATED = {
    "erpnext": {
        "what": (
            "**ERPNext** — open-source ERP на Frappe: учёт, склад, продажи, закупки, "
            "производство, проекты, поддержка и сайт в одной системе."
        ),
        "tasks": [
            "Бухгалтерия, платежи, долги и финансовая отчётность",
            "Склад, закупки, продажи и производство",
            "CRM/продажи, проекты, качество, основные средства",
            "Единая база вместо зоопарка Excel и разрозненных систем",
        ],
        "biz": [
            "Малый и средний бизнес, которому нужна полноценная ERP",
            "Производство, дистрибуция, торговля, услуги",
            "Компании, которые хотят open-source вместо дорогого проприетарного ERP",
        ],
        "pains": [
            "Учёт размазан по Excel, 1С-подобным кускам и почте",
            "Нет единой картины остатков, денег и заказов",
            "Дорогие лицензии и vendor lock-in у классических ERP",
        ],
    },
    "crm": {
        "what": (
            "**CRM** — современная open-source CRM от Frappe для воронки продаж, "
            "лидов, сделок и работы менеджеров."
        ),
        "tasks": [
            "Ведение лидов, сделок и активностей",
            "Кастомные представления воронки",
            "Ускорение работы sales-команды рядом с ERP",
        ],
        "biz": ["Отделы продаж B2B/B2C", "Компании на Frappe/ERPNext без удобной CRM"],
        "pains": [
            "Лиды в таблицах и мессенджерах",
            "Нет дисциплины воронки и follow-up",
            "Слабая связка продаж с остальной ERP",
        ],
    },
    "hrms": {
        "what": (
            "**HR & Payroll** (Frappe HR) — HRMS: сотрудники, онбординг, отпуска, "
            "явки, payroll и кадровые процессы."
        ),
        "tasks": [
            "Карточки сотрудников и оргструктура",
            "Отпуска, явки, онбординг",
            "Payroll и связанные HR-модули",
        ],
        "biz": ["HR-отделы компаний на Frappe/ERPNext", "Компании с штатом и регулярным payroll"],
        "pains": [
            "Явки и отпуска в Excel",
            "Ошибки в расчёте зарплаты",
            "Нет self-service для сотрудников",
        ],
    },
    "insights": {
        "what": (
            "**Insights** — open-source BI поверх данных Frappe/ERPNext: отчёты и "
            "аналитика без обязательного SQL для каждого среза."
        ),
        "tasks": [
            "Построение отчётов и дашбордов",
            "Анализ данных ERP для бизнеса",
            "Доступ к аналитике для нетехнических пользователей",
        ],
        "biz": ["Руководители и аналитики", "Компании с ERPNext, которым не хватает стандартных отчётов"],
        "pains": [
            "Отчёты собирают вручную в Excel",
            "SQL-барьер для бизнес-пользователей",
            "Нет единой BI-поверхности над ERP",
        ],
    },
    "raven": {
        "what": (
            "**Raven** — корпоративный чат на вашем Frappe-сайте рядом с ERPNext/CRM/HR, "
            "без per-user SaaS-платы за мессенджер."
        ),
        "tasks": [
            "Командные каналы и личные сообщения",
            "Обсуждения рядом с рабочими данными ERP",
            "Хранение переписки в своей БД",
        ],
        "biz": ["Команды на Frappe, которым нужен внутренний мессенджер", "Удалённые и распределённые команды"],
        "pains": [
            "Рабочая переписка в сторонних мессенджерах",
            "Теряется контекст задач и документов",
            "Per-user pricing у внешних чатов",
        ],
    },
    "wiki": {
        "what": (
            "**Wiki** — база знаний и документация на Frappe: страницы, ревизии, "
            "быстрые правки без даунтайма."
        ),
        "tasks": [
            "Ведение knowledge base / docs",
            "Публикация и обновление статей",
            "История изменений страниц",
        ],
        "biz": ["Продуктовые и support-команды", "Компании с внутренней/внешней документацией"],
        "pains": [
            "Документация размазана по Google Docs и чатам",
            "Сложно быстро опубликовать правку",
            "Нет единой wiki рядом с продуктом",
        ],
    },
    "drive": {
        "what": (
            "**Drive** — файловое хранилище и шаринг на Frappe: папки, превью, доступ, "
            "работа с большими файлами."
        ),
        "tasks": [
            "Загрузка и организация файлов",
            "Превью и шаринг",
            "Командная работа с документами",
        ],
        "biz": ["Компании с общим файловым контуром", "Команды, которым нужен Drive внутри Frappe"],
        "pains": [
            "Файлы по почте и личным дискам",
            "Нет контроля доступа",
            "Ограничения размера и хаос в вложениях",
        ],
    },
    "payments": {
        "what": (
            "**Payments** — слой платёжных интеграций для Frappe: Razorpay, Stripe, "
            "PayPal, PayTM, Braintree."
        ),
        "tasks": [
            "Подключение платёжных шлюзов",
            "Приём оплат из Frappe-приложений",
            "Единый payment layer вместо кастомных интеграций",
        ],
        "biz": ["Сайты и apps на Frappe с онлайн-оплатой", "Команды, подключающие несколько шлюзов"],
        "pains": [
            "Каждый шлюз пишется с нуля",
            "Оплаты не связаны с приложением",
            "Сложно поддерживать несколько провайдеров",
        ],
    },
    "print_designer": {
        "what": (
            "**Print Designer** — визуальный конструктор печатных форм для Frappe-приложений."
        ),
        "tasks": [
            "Дизайн print formats в UI",
            "Брендированные PDF/печатные документы",
            "Быстрые правки форм без глубокой разработки",
        ],
        "biz": ["Отделы продаж, закупки, бухгалтерия", "Партнёры, настраивающие документы клиентам"],
        "pains": [
            "Уродливые стандартные печатные формы",
            "Долго править HTML print format руками",
            "Документы не соответствуют бренду",
        ],
    },
    "helpdesk": {
        "what": (
            "**Helpdesk** — open-source тикет-система на Frappe для поддержки клиентов."
        ),
        "tasks": [
            "Приём и ведение тикетов",
            "Очереди и статусы обращений",
            "Работа support-команды в едином интерфейсе",
        ],
        "biz": ["Клиентский сервис", "SaaS и сервисные компании на Frappe"],
        "pains": [
            "Обращения в почте и чатах",
            "Нет прозрачного статуса тикета",
            "Сложно контролировать нагрузку support",
        ],
    },
    "lending": {
        "what": "**Lending** — open-source управление займами на Frappe.",
        "tasks": [
            "Учёт кредитных/заёмных продуктов",
            "Графики и погашения",
            "Контроль портфеля займов",
        ],
        "biz": ["МФО, кредитные подразделения, fintech на Frappe"],
        "pains": [
            "Сложный ручной учёт графиков",
            "Риск ошибок в процентах и просрочках",
            "Нет специализированного loan-модуля в базе ERPNext",
        ],
    },
    "builder": {
        "what": "**Builder** — low-code конструктор сайтов для дизайнеров на Frappe.",
        "tasks": [
            "Сборка посадочных и сайт-страниц",
            "Визуальное редактирование без тяжёлой разработки",
            "Публикация сайта рядом с Frappe-стеком",
        ],
        "biz": ["Маркетинг и продуктовые команды", "Агентства на Frappe"],
        "pains": [
            "Сайт отдельно от продукта",
            "Долго ждать разработку простых страниц",
            "Сложно быстро тестировать лендинги",
        ],
    },
    "lms": {
        "what": (
            "**Learning** — open-source LMS: курсы, уроки, квизы, батчи для обучения."
        ),
        "tasks": [
            "Создание курсов и уроков",
            "Тесты и прогресс учеников",
            "Запуск обучающих потоков",
        ],
        "biz": ["Учебные центры, корп. L&D, авторы курсов"],
        "pains": [
            "Обучение вне единой системы",
            "Сложно вести группы и прогресс",
            "Контент размазан по файлам и Zoom",
        ],
    },
    "webshop": {
        "what": "**Webshop** — open-source e-commerce витрина на Frappe/ERPNext.",
        "tasks": [
            "Каталог и корзина",
            "Онлайн-заказы в связке с ERP",
            "Витрина без отдельного магазинного монолита",
        ],
        "biz": ["Ритейл и бренды на ERPNext", "Компании, которым нужен магазин рядом с учётом"],
        "pains": [
            "Магазин и склад живут отдельно",
            "Двойной каталог товаров",
            "Заказы вручную переносят в ERP",
        ],
    },
}


def primary_cats(cats: str):
    found = []
    remaining = cats or ""
    # truncated labels from scrape
    remaining = re.sub(r"\bHuman\b(?!\s+Resources)", "Human Resources", remaining)
    for key in sorted(CAT_BIZ, key=len, reverse=True):
        if re.search(rf"\b{re.escape(key)}\b", remaining):
            found.append(key)
            remaining = re.sub(rf"\b{re.escape(key)}\b", " ", remaining)
    return found or ["Business"]


def uniq(seq):
    out, seen = [], set()
    for x in seq:
        k = x.lower().strip()
        if k and k not in seen:
            seen.add(k)
            out.append(x.strip())
    return out


def build_ru(app):
    title = app["title"]
    name = app["name"]
    about = re.sub(r"\s+", " ", (app.get("about") or "")).strip()
    about = re.sub(r"Read More.*$", "", about, flags=re.I).strip()
    cats = primary_cats(app.get("cats") or "")
    head = f"{title} {name} {app.get('cats', '')}".lower()
    about_l = about.lower()

    if name in CURATED:
        c = CURATED[name]
        return c["what"], c["tasks"], c["biz"], c["pains"], cats

    what_bits, tasks, biz, pains = [], [], [], []
    for title_pat, about_pat, what, tlist, b, plist in RULES:
        hit = re.search(title_pat, head, re.I)
        if not hit and about_pat:
            hit = re.search(about_pat, about_l, re.I)
        if hit:
            what_bits.append(what)
            tasks.extend(tlist)
            biz.append(b)
            pains.extend(plist)

    for c in cats:
        if c in CAT_BIZ:
            b, p = CAT_BIZ[c]
            biz.append(b)
            pains.extend(p)

    what_bits = uniq(what_bits)
    if what_bits:
        what = (
            f"**{title}** — бесплатное приложение Marketplace, "
            f"которое даёт {', '.join(what_bits[:3])}."
        )
    else:
        what = (
            f"**{title}** — бесплатное расширение для Frappe/ERPNext "
            f"из категории {', '.join(cats)}. Добавляет недостающую функцию "
            "поверх стандартного Desk/ERP без покупки отдельного SaaS."
        )

    if about and len(about) > 40:
        first = re.split(r"(?<=[\.\!\?])\s+", about)[0].strip()
        if 30 < len(first) < 220 and "documentation" not in first.lower():
            what += f"\n\nКратко по описанию издателя: _{first}_"

    def is_mostly_english(s: str) -> bool:
        letters = re.findall(r"[A-Za-zА-Яа-яЁё]", s)
        if not letters:
            return False
        en = sum(1 for ch in letters if ("A" <= ch <= "Z") or ("a" <= ch <= "z"))
        return en / len(letters) > 0.6

    # если правил мало — русские задачи из названия/категорий, EN-about только в цитате
    if len(tasks) < 2:
        tasks = [
            f"Даёт функциональность «{title}» прямо в Frappe/ERPNext",
            "Закрывает точечный пробел стандартного Desk без отдельного SaaS",
            "Держит сценарий рядом с основными документами и ролями ERP",
        ]
        if cats:
            tasks.append(f"Полезно в контуре: {', '.join(cats[:3])}")

    tasks = [t for t in uniq(tasks) if not is_mostly_english(t)][:7]
    if not tasks:
        tasks = [
            f"Расширяет ERPNext/Frappe модулем «{title}»",
            "Убирает ручной обходной процесс вне системы",
            "Держит данные рядом с основными документами ERP",
        ]
    biz = uniq(biz)[:4]
    pains = uniq(pains)[:5]
    if not biz:
        biz = ["Компании на Frappe/ERPNext, которым нужна эта функция сверх коробки"]
    if not pains:
        pains = [
            "Стандартного ERPNext/Frappe не хватает под конкретный процесс",
            "Работа уходит в Excel, почту и мессенджеры",
            "Ручные операции дают ошибки и задержки",
        ]
    return what, tasks, biz, pains, cats


def md_for(app):
    what, tasks, biz, pains, cats = build_ru(app)
    pub = app.get("publisher") or "—"
    installs = app.get("installs") or "—"
    cat_line = ", ".join(cats)
    return f"""# {app["title"]}

> Бесплатное приложение [Frappe Cloud Marketplace]({app["url"]})

| | |
|---|---|
| **Slug** | `{app["name"]}` |
| **Категории** | {cat_line} |
| **Издатель** | {pub} |
| **Установок** | {installs} |
| **Ссылка** | {app["url"]} |

## Что делает

{what}

## Какие задачи закрывает

{chr(10).join("- " + t for t in tasks)}

## Какому бизнесу нужно

{chr(10).join("- " + b for b in biz)}

## Какие боли закрывает

{chr(10).join("- " + p for p in pains)}

## Когда ставить

Если вы уже на **Frappe / ERPNext** и эти задачи сейчас делаете вручную, в Excel или во внешней системе без связки с ERP.

---
*Собрано по странице Marketplace. Блоки «бизнес» и «боли» — практическая интерпретация по описанию и категориям, не официальный текст издателя.*
"""


def main():
    index_rows = []
    for app in sorted(data, key=lambda x: x["title"].lower()):
        (APPS_DIR / f"{app['name']}.md").write_text(md_for(app), encoding="utf-8")
        cats = ", ".join(primary_cats(app.get("cats") or ""))
        index_rows.append((app["title"], app["name"], cats, app.get("installs") or "—"))

    readme = f"""# Free-приложения Frappe Cloud Marketplace

Сводка по **{len(index_rows)}** бесплатным приложениям.

Каталог: https://cloud.frappe.io/marketplace/search?category=All+Categories

На каждое приложение — файл в [`apps/`](apps/):

- что делает
- какие задачи закрывает
- какому бизнесу нужно
- какие боли закрывает

## Индекс

| Приложение | Файл | Категории | Установок |
|---|---|---|---|
"""
    for title, name, cats, installs in index_rows:
        readme += f"| {title} | [{name}.md](apps/{name}.md) | {cats} | {installs} |\n"

    readme += """
## Как пользоваться

1. Откройте файл приложения в `apps/`.
2. Смотрите блоки **Какому бизнесу нужно** и **Какие боли закрывает**.
3. Установка — через Frappe Cloud Marketplace (приложение free; хостинг Cloud отдельно).

## Ограничения

- Карточки собраны автоматически по публичным страницам Marketplace.
- Формулировки бизнеса/болей — эвристика по категориям и ключевым словам.
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print(f"Wrote {len(index_rows)} files to {APPS_DIR}")


if __name__ == "__main__":
    main()
