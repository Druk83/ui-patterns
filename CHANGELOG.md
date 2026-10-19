# Журнал изменений

## 0.3.0 - 2026-10-19

- Добавлены отдельные паттерн карточной ленты, шаблон применения и запускаемый эталонный прототип (live reference prototype); табличное представление сохранено как самостоятельный вариант списка.
- Синхронизированы публичный каталог, манифест экранных шаблонов, проверки версий и процедура выбора.

## 0.2.0 - 2026-09-14

- Добавлен публичный каталог переиспользуемых шаблонов экранного UI в `шаблоны-экранов/`.
- Добавлен framework-neutral HTML/CSS/JS reference prototype со статусом `reference-only`.
- Зафиксирована связь `pattern → application template → screen template` через
  `application_template_id` и реальные `pattern_id` каталога.
- Добавлены проверки совместимости шаблонов, provenance, fixture-only data и
  selectable application templates.
- Добавлены unit-тесты validator для положительного и отрицательных сценариев.
- Добавлены правила screen pool, viewport matrix и выбора шаблона экрана.
- Добавлен контракт и validator screen pool с обязательным подтверждением экранов,
  источниками и обоснованиями viewport в CSS px.
- Добавлена runtime и visual проверка reference-прототипов с временными screenshots,
  проверкой состояний, responsive-условий, accessibility hooks и fixture-only data.
- UI-схема дополнена ссылками на screen pool, template ID и template revision.

## 0.1.0 - 2026-08-23

- Создан baseline-каталог `ui-patterns`.
- Добавлены карточки `FORM_WORKFLOW_UI`, `LIST_DETAIL_UI`, `NAVIGATION_CONTENT_UI` и `DIALOG_OVERLAY_UI`.
- Внутренние реестры источников, доказательств и артефактов отделены от публичных результатов.
- Добавлены контракт и схема UI-пакета: экранный манифест, UI-блоки, данные, действия, состояния, переходы, reference artifacts и критерии приёмки.
- Добавлены шаблоны применения для формы, таблицы, меню и модального диалога.
- Публичный `pattern-catalog.yml` расширен до decision catalog с обязательным контекстом, порядком выбора, противопоказаниями, результатом решения и профилем UI-документации.
- Добавлены публичные `ui-pattern-selection.md`, `ui-pattern-application-templates.yml`, `ui-screen-specification-template.md` и `ui-specification-schema.yml`.
- Публичная публикация содержит только обработанные правила выбора и контракты результата; внутренние исходники и реестры остаются закрытыми.
- Подтверждён `DASHBOARD_MONITORING_UI` на основе Carbon Design System; добавлены карточка, application template и PlantUML/PNG, а проектные accessibility, responsive и data-state правила оставлены GAP.
- Удалён производный человекочитаемый список; каталог выбора сокращён за счёт удаления дублирующих состояний, действий и переходов, а карточки семейств связаны с индексом через `card_path`.
- Подтверждён `MOBILE_TOUCH_UI` на основе Apple Human Interface Guidelines, Android Developers и W3C Mobile Accessibility; добавлены карточка, application template и PlantUML/PNG, а platform-specific, accessibility, responsive и offline-правила проекта оставлены GAP.
- Подключён источник «Законы UX-дизайна» для нормализации общих UX-принципов; добавлены обязательные `principle_decisions`, проверка неидеальных сценариев и сквозные шаблоны `multi-step-workflow-ui`, `stateful-action-ui`, `progressive-onboarding-ui` и `responsive-ui`.
- Подключён источник по информационной архитектуре; добавлен сквозной шаблон `information-architecture-ui` с обязательными решениями по содержимому, классификации, маркировке, точкам входа, навигации, поиску и масштабированию структуры.
- Обогащены шаблоны контекстом использования, модальностью, масштабом данных, производительностью, интеграциями и компонентной основой; добавлены кандидатные templates для CLI, CUI, VUI, TUI, NUI, workflow process, role-based и enterprise UI со статусом `not_selectable`.
- Завершены задачи `A1-08`–`A1-13`: карточки и application templates CLI, CUI, VUI, TUI, NUI и workflow process переведены в `active`; публичная секция `extended_templates` и процедура выбора обновлены, а role-based и enterprise UI сохранены кандидатами до отдельного подтверждения.
- Добавлены подтверждённые источники и evidence для POSIX, W3C, VoiceXML, SRGS, BPMN, Kanban, NAUR и ECMA-48; проектные значения безопасности, приватности и среды остаются обязательными входами шаблонов.
- Карточки активных шаблонов дополнены параметрами конкретного проекта, минимальным составом прототипа и критериями завершённой проверки; устаревшие формулировки skeleton/candidate/gap удалены из задач и карточек.
