# Context
Нужно сделать первый implementation pass для восстановления dev-связки web UI ↔ runtime backend в scope CORS/preflight. По текущим материалам FastAPI app создаётся в `rtb/app/main.py` без CORS middleware, а UI runtime adapter ходит на `http://127.0.0.1:8000` из web UI dev origin `http://127.0.0.1:5173`/`http://localhost:5173`, поэтому browser preflight сейчас закономерно может падать на `OPTIONS`.

# Current scope
Только backend CORS/preflight integration для текущего dev workflow backend workspace browser.

# Target semantics
После правки должно быть истинно следующее:
1. Backend централизованно поддерживает browser CORS/preflight для текущего web UI dev workflow.
2. `OPTIONS` preflight к backend API surface, используемому UI, больше не падает из-за отсутствия CORS middleware.
3. Решение сделано на middleware/config уровне, а не точечным обработчиком одного `OPTIONS` route.
4. Не появляется второй competing source of truth для CORS policy.
5. Новые policy values не размазаны raw literals по нескольким местам без необходимости.

# What to inspect first
1. Проверь `rtb/app/main.py`:
   - как создаётся FastAPI app;
   - какие middleware уже есть;
   - где лучше централизовать CORS policy.
2. Проверь `rtb/app/core/constants.py` и/или другие existing backend config/constants files:
   - есть ли подходящее место для allowed origins / methods / headers / credentials policy;
   - не создаст ли новая константная секция competing policy layer.
3. Проверь `rtb/app/api/commands.py`:
   - нужны ли вообще route-level изменения после middleware;
   - не требуется ли ничего дополнительного для import/export routes.
4. Проверь `shared/config/platform-config.js`, `ui/config/ui-config.js`, `ui/renderer/runtime/adapters/createHttpRuntimeAdapter.js`:
   - подтверди фактические dev origins и заголовки, которые провоцируют preflight.
5. Проверь, есть ли в dump/backend layout тесты для FastAPI backend; если есть подходящий контур — добавь узкий тест на CORS/preflight.
6. Статически проверь `export_project_to_txt.py`:
   - если добавятся/затронутся новые repo files в scope, helper нужно синхронизировать;
   - сам helper не запускать и dump не генерировать.

# Required changes
1. Добавь корректную CORS middleware policy в backend entrypoint.
2. Разреши как минимум origins, реально используемые текущим dev UI:
   - `http://127.0.0.1:5173`
   - `http://localhost:5173`
3. Разреши методы и headers так, чтобы штатно проходил browser preflight для `POST /api/commands`, import и export-related HTTP surface, используемого UI.
4. Если policy values уместно вынести в существующий backend constants/config слой — вынеси; если нет, оставь один централизованный source of truth и явно объясни выбор.
5. Не добавляй ad-hoc `OPTIONS /api/commands` handler, если middleware полностью закрывает проблему.
6. Меняй `rtb/app/api/commands.py` только если после анализа это действительно требуется.
7. Если добавляешь/меняешь backend tests, делай это только узко под корректную CORS/preflight семантику.
8. Если затронут новый рабочий repo-file, синхронизируй `export_project_to_txt.py`; если не требуется — явно укажи это в отчёте.

# Files allowed to change
- `rtb/app/main.py`
- `rtb/app/core/constants.py` и другие existing backend config/constants files только если это нужно для единого CORS source of truth
- `rtb/app/api/commands.py` только если после анализа без этого нельзя
- backend tests, только если в проекте уже есть подходящий контур и можно узко покрыть CORS/preflight
- `rtb/README.md` только если после правки остаётся прямое фактическое расхождение
- `export_project_to_txt.py` только если требуется синхронизация whitelist из-за реально затронутых repo files

# Do not do
1. Не делай широкий backend refactor.
2. Не меняй lock/process semantics, command contract или project storage semantics.
3. Не обходи проблему UI-side workaround'ом.
4. Не добавляй route-level костыль только под один `OPTIONS` endpoint вместо middleware-level решения.
5. Не создавай второй parallel CORS/config layer.
6. Не разбрасывай raw origin/method/header literals по нескольким файлам.
7. Не редактируй dump и не запускай `export_project_to_txt.py`.
8. Не запускай долгоживущие foreground/watch/server-команды без bounded wrapper.

# Verification
После изменений обязательно:
1. Проверь, что backend import'ится/стартует без ошибок после добавления middleware.
2. Проверь preflight bounded-способом: либо через backend test client, либо через короткий HTTP-запрос/тест, который подтверждает, что `OPTIONS` к backend API surface больше не даёт 405 и возвращает ожидаемые CORS headers.
3. Если есть узкий automated test на это — добавь/обнови и запусти его.
4. Прогони полный набор тестов проекта фактическими командами:
   - `cd ui && npm.cmd test`
   - `cd ui && npm.cmd run test:integration`
   - `cd ui && npm.cmd run test:backend`
   - `cd ui && npm.cmd run test:all`
5. Если какая-то команда падает, отдели:
   - реальный дефект твоих изменений;
   - environment issue;
   - unrelated pre-existing failure.
6. Отдельно проверь, не появились ли новые raw semantic literals / competing config sources.
7. Отдельно проверь, не затронуты ли побочно другие backend routes (`/api/commands`, `/api/project-imports`, `/api/project-exports/...`).

# Result report
Дай структурированный отчёт:
- Summary
- Changed files
- What changed
- Verification
- Risks / open items

В отчёте обязательно укажи:
1. Где именно была причина `OPTIONS ... 405`.
2. Как именно исправлено решение и на каком уровне.
3. Какие файлы изменены.
4. Куда помещены policy values и почему это не создаёт competing source of truth.
5. Какие команды реально запущены и их результаты.
6. Есть ли подтверждение, что preflight больше не ломается.
7. Нужна ли была синхронизация `export_project_to_txt.py` или почему не нужна.