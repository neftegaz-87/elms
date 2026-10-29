# Vendor docs — Frappe Framework

Офлайн-зеркало официальной документации Frappe Framework для агентов и разработчиков.

| Каталог | Источник |
|---------|----------|
| `framework/` | https://docs.frappe.io/framework |

Индекс: `framework/llms.txt`. Физически это symlink на зеркало, скачанное в `PersonalProject/frappe-erp-crm/docs/vendor/framework` (`mirror-docs.py`).

## Как пользоваться (агент)

1. Сначала открыть `docs/vendor/framework/llms.txt` — оглавление.
2. Нужную страницу читать как локальный `.md` под `docs/vendor/framework/` (или через абсолютный путь зеркала).
3. Онлайн `docs.frappe.io` — только если локальной страницы нет.
4. Это справочник вендора, не SoT продукта ELMS: канон поведения — `memory-bank/` + код `elms/`.

## Обновить зеркало

```bash
python3 docs/vendor/mirror-docs.py --spaces framework
```

Скрипт и каталог `framework/` живут в общем зеркале `frappe-erp-crm`; из elms доступны через symlink.
