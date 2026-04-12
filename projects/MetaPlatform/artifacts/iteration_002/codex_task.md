# Context
Есть первый implementation pass по backend slug reuse policy. По diff исправлен `_next_available_slug(...)` и добавлены tests на create/import reuse после delete. Но текущие материалы противоречат друг другу: в technical channel полный набор тестов отмечен как passed, а в model summary явно сказано, что `cd ui && npm.cmd run test:backend` и `cd ui && npm.cmd run test:all` падали на `rtb/tests/test_startup_probe.py::test_bounded_uvicorn_startup_probe_starts_and_stops_cleanly`. До закрытия задачи нужно устранить это расхождение и дополнительно перепроверить побочный эффект от изменения slug у deleted rows.

# Current scope
Только доводка текущего backend scope:
1. проверить и при необходимости исправить побочные эффекты slug policy change;
2. добиться надёжной verification по обязательному полному набору тестов или чётко локализовать/исправить реальную причину падения в рамках текущего backend scope.

# Target semantics
После этой итерации должно быть истинно следующее:
1. Deleted projects больше не резервируют slug для новых create/import.
2. Create и import остаются на одном source of truth пути slug allocation.
3. Решение не вносит лишнего побочного эффекта в lifecycle soft-deleted rows без необходимости.
4. Полный обязательный набор команд проверки имеет непротиворечивый фактический результат с точным stdout/stderr.
5. Если backend test падал из-за продуктовой причины, она исправлена; если это environment issue, это доказано фактами запуска и не маскирует дефект текущего scope.

# What to inspect first
Сначала проверь:
- `rtb/app/services/project_catalog.py`
  - `_next_available_slug`
  - `delete_project`
- схему `projects.slug` и фактическую причину, почему потребовалось tombstone-переименование slug при soft delete
- backend tests:
  - `rtb/tests/test_commands.py`
  - `rtb/tests/test_imports.py`
  - `rtb/tests/test_startup_probe.py`
- все места, где кто-либо может опираться на slug deleted rows
- фактический stderr/stdout для:
  - `cd ui && npm.cmd run test:backend`
  - `cd ui && npm.cmd run test:all`

# Required changes
1. Перепроверь, является ли изменение slug у soft-deleted записи действительно минимально необходимым для совместимости с текущим DB unique constraint.
2. Если текущая tombstone-схема нужна, оставь её, но добавь/обнови тест так, чтобы это поведение было явно зафиксировано как internal storage detail и не ломало целевую semantics reuse slug среди живых проектов.
3. Если можно добиться той же semantics меньшим изменением без расширения scope и без ломки uniqueness, сделай это; не создавай второй competing path.
4. Разберись с расхождением по verification:
   - либо исправь причину падения `test:backend` / `test:all`, если она продуктовая и связана с текущими изменениями или с затронутым backend scope;
   - либо приложи точные фактические логи и докажи, что падение не связано с текущим slug scope.
5. Если потребуется правка backend tests для стабилизации запуска в рамках существующей тестовой инфраструктуры и это напрямую нужно для получения корректного полного прогона, меняй только соответствующий backend test/root setup, без расширения на unrelated refactor.
6. Отдельно проверь, что не появились новые raw semantic literals / magic strings / magic numbers в логике slug tombstone и тестах. Если tombstone marker реально становится shared semantic value, вынеси его в существующий constants layer; если это локальная одноразовая деталь только внутри `project_catalog.py`, не создавай лишний новый constants layer механически.
7. Статически перепроверь `export_project_to_txt.py`; менять helper только если после этой итерации реально изменится whitelist затронутых repo files.

# Files allowed to change
Разрешено менять только:
- `rtb/app/services/project_catalog.py`
- `rtb/app/services/project_storage.py` только если это действительно нужно для выравнивания create/import semantics
- `rtb/app/core/constants.py` только если понадобится один shared semantic marker для slug tombstone policy
- backend tests, включая:
  - `rtb/tests/test_commands.py`
  - `rtb/tests/test_imports.py`
  - `rtb/tests/test_startup_probe.py`
  - существующий backend test setup / `conftest.py`, если он реально существует и нужен для корректного bounded запуска
- `export_project_to_txt.py` только если helper нужно синхронизировать

# Do not do
1. Не меняй UI.
2. Не трогай workspace browser panel.
3. Не делай общий backend cleanup.
4. Не меняй close/save/lock/process semantics, кроме точечной правки теста/verification, если это строго нужно для полного прогона.
5. Не вводи новый competing slug allocation path.
6. Не редактируй dump и не запускай dump helper.
7. Не закрывай задачу без устранения противоречия в результатах обязательных тестов.

# Verification
После изменений обязательно выполни и приведи фактические результаты:
1. таргетные backend tests по slug policy;
2. полный обязательный набор:
   - `cd ui && npm.cmd test`
   - `cd ui && npm.cmd run test:integration`
   - `cd ui && npm.cmd run test:backend`
   - `cd ui && npm.cmd run test:all`
3. Если любая из команд падает, приложи точный stdout/stderr и явно укажи:
   - это product defect или environment issue;
   - связано ли это с текущим scope;
   - почему это не блокирует или блокирует завершение задачи.
4. Отдельно проверь:
   - reuse slug после delete для create;
   - reuse slug после delete для import;
   - uniqueness среди живых проектов;
   - отсутствие новых raw semantic literals;
   - отсутствие побочных эффектов вне slug scope.

# Result report
Верни структурированный отчёт:
- Summary
- Changed files
- What changed
- Verification
- Risks / open items

Обязательно укажи:
1. почему technical/model channels расходились по полному прогону;
2. нужна ли tombstone-подмена slug у deleted rows и почему;
3. какие именно tests были добавлены/обновлены;
4. точные результаты `test`, `test:integration`, `test:backend`, `test:all`;
5. есть ли ещё риски по deleted slug lifecycle.