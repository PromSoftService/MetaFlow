# Context

Новая отдельная задача: восстановить рабочую связку web UI ↔ runtime backend для backend workspace browser.

По текущему состоянию:
- UI работает через Vite dev server на `127.0.0.1:5173`;
- backend работает отдельно на `127.0.0.1:8000`;
- при нажатии Refresh браузер шлёт preflight `OPTIONS /api/commands`;
- backend отвечает `405 Method Not Allowed`;
- из-за этого UI показывает `Backend workspace unavailable. Retry Refresh and verify backend connectivity.`

Это означает, что сейчас проблема не в запуске uvicorn как таковом, а в отсутствии корректной CORS/preflight поддержки между web UI и backend.

# Current scope

Только исправление web-to-backend CORS/preflight integration для текущего dev workflow.

В этом цикле не делать:
- общий refactor backend;
- изменения lock/process semantics;
- cleanup UI;
- изменения export helper, кроме случаев если это реально понадобится из-за нового затронутого файла;
- docs-cleanup вне прямой необходимости;
- любые unrelated fixes, даже если они заметны рядом.

# Target semantics

После правки должно быть истинно следующее:

1. Web UI, запущенный через Vite dev server, может делать запросы к backend на `http://127.0.0.1:8000` без preflight failure.
2. Preflight `OPTIONS` для backend API, используемого UI, больше не падает с `405 Method Not Allowed`.
3. Нажатие Refresh в backend workspace browser больше не ломается из-за CORS/preflight.
4. Решение не должно быть точечным “костылём” только для одного endpoint, если проблема относится к общему backend API surface, используемому web UI.
5. Не должно появиться второй competing CORS policy в другом месте backend.
6. Все новые policy values должны быть оформлены без новых лишних magic literals вразброс по коду.

# What to inspect first

Сначала reviewer должен поручить Codex проверить:

1. `rtb/app/main.py`
   - как создаётся FastAPI app;
   - какие middleware уже подключены;
   - есть ли CORS middleware;
   - где лучше всего централизовать CORS policy.
2. `rtb/app/api/commands.py`
   - какие HTTP methods реально используются;
   - нужно ли что-то менять в router после добавления middleware.
3. `ui/config/ui-config.js`
4. `shared/config/platform-config.js`
   - какие backend base URL и web dev origins реально используются сейчас.
5. `ui/renderer/runtime/adapters/createHttpRuntimeAdapter.js`
   - как именно отправляются запросы;
   - подтверждается ли browser preflight scenario.
6. README/run instructions, если они уже описывают dev startup flow и должны быть синхронизированы с исправленным поведением.

# Required changes

1. Добавить корректную CORS/preflight поддержку в backend entrypoint для текущего web UI dev workflow.
2. Разрешить origins, реально используемые web UI в dev-режиме. Как минимум проверить необходимость для:
   - `http://127.0.0.1:5173`
   - `http://localhost:5173`
3. Разрешить методы и headers так, чтобы browser preflight для backend API, используемого UI, проходил штатно.
4. Не делать локальный ad-hoc handler только под один `OPTIONS /api/commands`, если правильное решение — централизованный middleware-level policy.
5. Если для allowed origins / methods / headers / credentials policy уже есть подходящий config/constants слой, использовать его.
6. Не разбрасывать новые raw semantic literals по нескольким backend-файлам без необходимости.
7. Если для dev startup/run instructions нужен минимальный sync, обновить только те текстовые файлы, которые реально расходятся с новым фактическим поведением.
8. Проверить, не создаёт ли новая CORS policy конфликтов для существующих backend routes.

# Files allowed to change

Разрешено менять только то, что реально нужно для этого scope:

- `rtb/app/main.py`
- `rtb/app/api/commands.py` только если это действительно требуется после анализа
- backend config/constants files, если туда уместно вынести policy values
- минимально необходимые README/runbook/docs файлы, если без этого остаётся явное расхождение
- тесты, если они существуют и должны быть обновлены/добавлены под новую семантику

Не менять UI-логику без прямой необходимости.
Не трогать unrelated backend services.

# Do not do

1. Не делать широкий backend cleanup.
2. Не менять command contract без прямой необходимости.
3. Не менять lock lifecycle, process orchestration и project semantics.
4. Не добавлять новый competing source of truth для backend origin policy.
5. Не хардкодить новые policy literals в нескольких местах одновременно.
6. Не маскировать проблему обходом в UI, если корень проблемы в backend preflight/CORS.
7. Не объявлять проблему “environment-only”, если реальный лог уже показывает `OPTIONS ... 405`.
8. Не редактировать dump.
9. Не запускать долгоживущие foreground/watch/server-команды в `extra_test_commands` без bounded wrapper.

# Magic strings / magic numbers

Reviewer должен отдельно потребовать от Codex:

- не разбрасывать новые origin strings, header names, method lists и policy flags по коду;
- если есть подходящий config/constants слой, использовать его;
- не делать бессмысленный over-engineering ради выноса каждого локального литерала;
- не создавать второй параллельный policy layer рядом с уже существующим.

Особенно внимательно проверить:
- allowed origins
- allowed methods
- allowed headers
- credentials policy
- любые новые backend/web integration constants

# Tests to add or update

Reviewer должен поручить Codex проверить, какие automated tests уже есть для backend API / runtime adapter / integration path, и:

1. добавить или обновить тесты на CORS/preflight поведение, если тестовый контур проекта это поддерживает;
2. если automated test на это сейчас неуместен или отсутствует инфраструктура, явно зафиксировать это в итоговом отчёте, но не подменять этим обязательные реальные проверки.

Важно:
- если тесты реально можно добавить узко и без раздувания scope, их нужно добавить;
- если нет, reviewer должен потребовать чёткое объяснение, почему именно.

# Verification

Reviewer должен потребовать от Codex реально прогнать проверки и затем проверить фактические результаты.

Обязательно:

1. Проверить, что backend стартует после изменений.
2. Проверить, что preflight `OPTIONS` больше не падает с `405` для backend API surface, используемого UI.
3. Проверить, что Refresh в backend workspace browser теперь работает в dev workflow или, если остаётся ошибка, зафиксировать уже новый точный failure mode.
4. Прогнать полный набор тестов по проекту.
5. Если часть команд не проходит, reviewer должен отделить:
   - реальный дефект;
   - ограничение среды;
   - unrelated pre-existing failure.

Нельзя бездоказательно списывать падение в “среду”.

Команды:
- reviewer должен поручить Codex прогнать фактические команды проекта;
- reviewer должен проверить stdout/stderr и итоговые статусы;
- запрещены долгоживущие foreground/watch/server-команды в `extra_test_commands` без bounded wrapper.

Если для ручной проверки нужен dev server/backend run, это не должно попадать в `extra_test_commands` как бесконечный процесс. Нужен bounded способ проверки или явная фиксация результата без зависания цикла.

# Helper script check

Reviewer должен отдельно потребовать от Codex проверить `export_project_to_txt.py`.

Что проверить:
1. если появились новые затронутые repo-files, helper должен быть синхронизирован;
2. helper не должен начать экспортировать тесты, иконки, package-lock files и demo artifacts;
3. если новые файлы в scope не требуют изменения helper-а, это нужно явно отметить в отчёте.

# Result report

Reviewer должен потребовать структурированный итоговый отчёт:

- Summary
- Changed files
- What changed
- Verification
- Risks / open items

В отчёте обязательно указать:
1. где именно была причина `OPTIONS ... 405`;
2. как именно это исправлено;
3. какие файлы изменены;
4. вынесены ли новые policy values в config/constants или почему локальное размещение допустимо;
5. какие команды реально прогнаны;
6. результаты полного тестового прогона;
7. подтверждён ли рабочий Refresh из web UI;
8. есть ли оставшиеся риски.

# DONE

Задача считается DONE только если одновременно выполнено всё ниже:

1. backend больше не отвечает `405 Method Not Allowed` на browser preflight для используемого UI API path;
2. web UI dev workflow может обращаться к backend без CORS/preflight block на текущем сценарии Refresh;
3. решение сделано на правильном уровне, без локального одноточечного костыля там, где нужен middleware/config-level fix;
4. новые policy literals не размазаны по коду без необходимости;
5. `export_project_to_txt.py` проверен и синхронизирован при необходимости;
6. Codex реально прогнал полный набор тестов по проекту;
7. reviewer проверил фактические результаты команд и не принимает задачу без этого.
