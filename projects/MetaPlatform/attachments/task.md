# Context

Новая отдельная задача: ввести единое модальное окно выбора проекта вместо отсутствующей встроенной browser panel.

Предыдущий шаг уже убрал встроенную backend workspace browser panel над деревом и оставил только process/generate panel. Следующий логический инкремент — дать пользователю новый единый project selection flow без возврата старой панели.

# Current scope

Только этот инкремент:

1. Добавить единое модальное окно выбора проекта.
2. Открывать его при старте приложения.
3. Открывать его по кнопке Browse.
4. Внутри окна загружать и показывать список backend projects.
5. Не делать пока полный UX polish, naming flow `Новый проект {N}`, общий русский cleanup или close confirmation — это следующие отдельные шаги.

В этом цикле не делать:
- изменение slug policy;
- отдельный flow минимального свободного номера для нового проекта;
- перенос сообщений в общие логи как отдельный scope;
- close confirmation;
- широкий refactor platform actions;
- unrelated backend cleanup.

# Target semantics

После правки должно быть истинно следующее:

1. При старте приложения открывается единое модальное окно выбора проекта.
2. Кнопка Browse открывает это же окно, а не отдельный второй flow.
3. Окно сразу загружает список backend projects.
4. В окне можно выбрать существующий backend project для открытия.
5. Старой встроенной browser panel по-прежнему нет.
6. Не появляется второй конкурирующий project picker.
7. Process/generate panel не ломается и не используется как substitute project picker.

# What to inspect first

Reviewer должен поручить Codex сначала проверить:

## UI / dialogs
- `ui/renderer/ui/dialogs.js`
- `ui/index.html`
- `ui/styles/styles.css`

## Runtime / app flow
- `ui/renderer/app.js`
- `ui/config/ui-config.js`
- `ui/renderer/runtime/browserShellAdapter.js`
- `ui/renderer/runtime/backendCommandSessionOrchestrator.js`

## Backend command usage
- где и как сейчас вызывается `listProjects`
- где и как открывается backend project
- как сейчас wired action `browseWorkspaceProjects`

## Helper
- `export_project_to_txt.py`, если появятся новые реально существующие repo files

# Required changes

1. Добавить единое модальное окно выбора проекта на существующем dialog/UI слое, без создания второго параллельного picker framework.
2. При старте приложения автоматически открывать это окно.
3. Привязать кнопку Browse к открытию этого же окна.
4. При открытии окна запускать загрузку backend project list.
5. Отображать список существующих backend projects в самом окне.
6. Выбор проекта из списка должен открывать его через существующий backend/open flow, а не через новый обходной путь.
7. Не возвращать встроенную browser panel в markup/CSS/runtime.
8. Если для модального окна нужны shared ids, action tokens, dialog texts или status labels, использовать существующий config/constants слой, а не разбрасывать новые literals.
9. Если нужен минимальный текстовый статус внутри окна (loading/empty/error), сделать только то, что необходимо для рабочего flow, без большого UX cleanup.
10. Не встраивать пока в этот task naming policy `Новый проект {N}` — это будет отдельный следующий инкремент.

# Files allowed to change

Разрешено менять только:
- `ui/renderer/ui/dialogs.js`
- `ui/renderer/app.js`
- `ui/config/ui-config.js`
- `ui/index.html` только если действительно нужен минимальный modal anchor/support markup
- `ui/styles/styles.css`
- другие UI/runtime файлы только если после проверки там есть прямой project-picker wiring
- `export_project_to_txt.py`
- минимально необходимые tests, если они реально затрагиваются этим изменением

Не менять:
- backend slug logic
- close confirmation
- naming policy для `Новый проект {N}`
- общий toolbar redesign
- unrelated backend services

# Do not do

1. Не возвращать старую browser panel.
2. Не делать второй отдельный flow для Browse.
3. Не строить полноценный новый workspace manager сверх нужного modal picker.
4. Не тащить в этот task русский UX cleanup целиком.
5. Не делать close-confirmation.
6. Не добавлять новый raw magic layer для dialog ids / labels / statuses.
7. Не редактировать dump.
8. Не запускать долгоживущие foreground/watch/server-команды в `extra_test_commands` без bounded wrapper.

# Magic strings / magic numbers

Reviewer должен отдельно потребовать от Codex:
- не разбрасывать новые dialog ids, picker states, status labels и action reasons по коду;
- использовать существующий config/constants слой для shared значений;
- не делать бессмысленный over-extraction одноразовых локальных literals.

# Tests to add or update

Reviewer должен поручить Codex проверить существующие tests и, если это уместно без раздувания scope, обновить/добавить только то, что реально относится к modal project picker.

Минимум проверить:
1. старт приложения не падает и открывает modal picker;
2. Browse открывает тот же modal picker;
3. список проектов загружается и selection flow не ломает open project path;
4. отсутствие старой browser panel сохраняется.

Если automated tests на это неуместны, reviewer должен потребовать явное объяснение и компенсировать это ручной проверкой.

# Verification

Reviewer должен потребовать от Codex реально прогнать:
- полный набор тестов проекта;
- targeted проверки, если они нужны для нового modal picker flow.

Reviewer должен проверить фактические результаты команд.

Обязательные ручные проверки:
1. при старте появляется modal picker;
2. Browse открывает тот же modal picker;
3. список backend projects виден в окне;
4. выбор существующего проекта открывает его;
5. старая встроенная browser panel не возвращена;
6. process/generate panel не сломана.

Если тесты/команды падают:
- отделить реальный дефект от ограничения среды;
- если единственный remaining fail — environment-sensitive startup probe under Codex environment при локальном PASS у пользователя и зелёных обязательных проверках, не считать это автоматическим незакрытым product defect.

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
1. как устроен новый modal picker;
2. как startup flow открывает его;
3. как Browse переиспользует тот же flow;
4. какие tests обновлены/добавлены;
5. какие команды реально прогнаны;
6. результаты полного тестового прогона;
7. остались ли риски перед следующим шагом с `Новый проект {N}`.

# DONE

Задача считается DONE только если одновременно выполнено всё ниже:

1. при старте приложения открывается единое модальное окно выбора проекта;
2. Browse открывает то же окно;
3. список backend projects загружается внутри окна;
4. выбор существующего проекта открывает его по штатному backend flow;
5. старая встроенная browser panel не возвращена;
6. process/generate panel остаётся рабочей;
7. `export_project_to_txt.py` проверен и синхронизирован при необходимости;
8. Codex реально прогнал полный набор тестов по проекту;
9. reviewer проверил фактические результаты и не принимает задачу без них.
