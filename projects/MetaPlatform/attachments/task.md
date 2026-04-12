# Context

Новая отдельная задача: довести до DONE текущий scope по удалению встроенной backend workspace browser panel над деревом проекта.

По текущему состоянию:
- browser panel markup уже убран из `ui/index.html`;
- process/generate panel уже оставлена;
- но в коде ещё остались browser-specific runtime/config хвосты, которые относятся к уже удалённой панели.

Это не следующий шаг плана. Это новый чистый task на завершение именно текущей задачи, потому что прошлый цикл сорвался и current diff нельзя считать завершённым.

# Current scope

Только дочистка оставшегося browser-specific wiring/config после уже удалённой встроенной browser panel.

В этом цикле делать только:
1. убрать мёртвые browser-specific runtime hooks и flows;
2. убрать browser-specific config/text/dom leftovers, которые больше не нужны после удаления панели;
3. сохранить process/generate panel и не сломать текущий UI/runtime.

В этом цикле не делать:
- новый modal/project picker;
- новый Browse flow;
- перевод всех сообщений в общие логи как отдельный scope;
- русский UX cleanup шире текущих затронутых хвостов;
- close confirmation;
- slug policy;
- общий refactor toolbar/tree/backend runtime.

# Target semantics

После правки должно быть истинно следующее:

1. В проекте больше нет browser-panel-specific runtime/config wiring для уже удалённой встроенной панели.
2. В `ui/index.html` отсутствует старая browser panel, и код больше не ожидает её DOM nodes.
3. В `ui/config/ui-config.js` не остаются browser-only DOM ids, class names, labels, status texts и presentation tokens, если они относятся только к удалённой панели.
4. В `ui/renderer/app.js` не остаются browser-only flows/helpers, если они относятся только к старой встроенной панели.
5. Process/generate panel остаётся рабочей и не теряет свою текущую семантику.
6. Не появляется новый project picker или временный substitute browser layer.

# What to inspect first

Reviewer должен поручить Codex сначала проверить:

## Markup/config mismatch
- `ui/index.html`
- `ui/config/ui-config.js`

Найти:
- DOM ids, которых уже нет в markup;
- browser-specific class names, которые больше не имеют рабочего смысла;
- browser-specific text labels/status messages, относящиеся только к удалённой панели.

## Runtime/browser leftovers
- `ui/renderer/app.js`
- `ui/renderer/runtime/backendCommandSessionOrchestrator.js`

Найти:
- browser-only presentation helpers;
- browser-only flow functions;
- browser-only status/result setters;
- вызовы/хуки, связанные со старой панелью;
- временные no-op заглушки, оставшиеся после удаления markup.

## Styles
- `ui/styles/styles.css`

Проверить:
- остались ли browser-only classes после удаления панели;
- нет ли мёртвого CSS для уже несуществующих browser sections.

## Helper
- `export_project_to_txt.py`, если набор реально затронутых repo files меняется.

# Required changes

1. Убрать из `ui/config/ui-config.js` все browser-panel-only DOM ids, class names, labels, status texts и related config values, если они больше не нужны после удаления встроенной browser panel.
2. Убрать из `ui/renderer/app.js` browser-only flows и presentation hooks, если они относятся именно к старой встроенной панели, включая:
   - browser presentation helpers;
   - browser status/result helpers;
   - browser-only transition helpers;
   - browser panel DOM expectations;
   - временные no-op заглушки, оставленные после удаления панели.
3. Если какие-то platform actions сейчас ещё завязаны на старый browser flow, сделать только минимальную нейтральную синхронизацию, чтобы не оставалось мёртвого wiring.
4. Убрать из `ui/styles/styles.css` browser-only CSS, относящийся к уже удалённой панели.
5. Если browser-specific логика частично живёт в `backendCommandSessionOrchestrator.js` или соседнем runtime-файле только ради старой панели, убрать и этот хвост.
6. Не трогать process/generate panel, кроме минимально необходимой синхронизации после удаления browser leftovers.
7. Не вводить новый modal/project picker и не переносить туда старый flow в этой задаче.
8. Не оставлять полуживые функции/константы “на будущее”, если они уже потеряли актуальный runtime consumer.
9. Не добавлять новые raw semantic literals / magic strings / magic numbers без необходимости; если нужны shared values, использовать существующий config/constants слой.

# Files allowed to change

Разрешено менять только:
- `ui/config/ui-config.js`
- `ui/renderer/app.js`
- `ui/renderer/runtime/backendCommandSessionOrchestrator.js`
- другие UI/runtime файлы только если после проверки там есть прямой browser-panel-specific leftover
- `ui/styles/styles.css`
- `ui/index.html` только если нужен минимальный sync
- `export_project_to_txt.py`
- минимально необходимые tests, если они реально затрагиваются этим cleanup

Не менять:
- backend slug logic
- новый project picker/modal
- close confirmation
- unrelated modules/editors/backend services

# Do not do

1. Не переходить к следующему UX step из плана.
2. Не делать новый browser/project selection flow.
3. Не начинать широкий русский UX cleanup.
4. Не делать общий toolbar redesign.
5. Не делать общий runtime refactor без прямой необходимости.
6. Не оставлять no-op заглушки вместо удаления мёртвого browser wiring, если этот wiring реально больше не нужен.
7. Не редактировать dump.
8. Не запускать долгоживущие foreground/watch/server-команды в `extra_test_commands` без bounded wrapper.

# Magic strings / magic numbers

Reviewer должен отдельно потребовать от Codex:
- не разбрасывать новые DOM ids / labels / status tokens / reason strings по коду;
- использовать существующий config/constants слой для shared значений;
- не делать бессмысленный over-extraction одноразовых локальных literals.

# Tests to add or update

Reviewer должен поручить Codex проверить существующие tests и, если это уместно без раздувания scope, обновить/добавить только то, что реально относится к cleanup текущего scope.

Минимум проверить:
1. приложение не падает из-за отсутствующих browser DOM nodes;
2. не осталось обращений к удалённой browser panel;
3. process/generate panel по-прежнему работает в текущем сценарии.

Если automated tests на это неуместны, reviewer должен потребовать явное объяснение и компенсировать это ручной проверкой.

# Verification

Reviewer должен потребовать от Codex реально прогнать:
- полный набор тестов проекта;
- targeted проверки на отсутствие browser-panel leftovers, если они нужны.

Reviewer должен проверить фактические результаты команд.

Обязательные ручные проверки:
1. в UI нет старой browser panel;
2. код не содержит runtime ожиданий её DOM/state;
3. нет browser-only status/result output logic для уже удалённой панели;
4. process/generate panel остаётся рабочей;
5. platform actions не ломаются из-за удаления старого browser wiring.

Если тесты/команды падают:
- отделить реальный дефект от ограничения среды;
- не списывать в “среду” без stderr/stdout.

# Helper script check

Reviewer должен отдельно потребовать от Codex проверить `export_project_to_txt.py`.

Если набор реально существующих/затронутых repo files изменился, helper должен быть синхронизирован.
При этом helper по-прежнему не должен экспортировать:
- иконки
- demo artifacts
- top-level tests
- package-lock files

# Result report

Reviewer должен потребовать структурированный итоговый отчёт:

- Summary
- Changed files
- What changed
- Verification
- Risks / open items

Обязательно указать:
1. какие browser-specific config/runtime leftovers были найдены;
2. какие из них удалены;
3. какие platform actions/flows пришлось минимально синхронизировать;
4. какие tests обновлены/добавлены;
5. какие команды реально прогнаны;
6. результаты полного тестового прогона;
7. остались ли риски перед переходом к следующему шагу плана.

# DONE

Задача считается DONE только если одновременно выполнено всё ниже:

1. встроенная browser panel уже отсутствует в markup и код больше не содержит browser-panel-specific runtime/config wiring;
2. browser-only DOM ids, labels, status texts, helpers и CSS-хвосты удалены, если они больше не нужны;
3. не осталось no-op заглушек, маскирующих старый browser flow, если этот flow реально уже удалён;
4. process/generate panel остаётся рабочей;
5. приложение не ломается из-за отсутствия старой панели;
6. `export_project_to_txt.py` проверен и синхронизирован при необходимости;
7. Codex реально прогнал полный набор тестов по проекту;
8. reviewer проверил фактические результаты и не принимает задачу без них.
