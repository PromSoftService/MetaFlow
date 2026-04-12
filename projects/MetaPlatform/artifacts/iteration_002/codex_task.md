# Context
В предыдущем implementation pass CORS/preflight fix уже внесён: добавлены `CORS_POLICY` в `rtb/app/core/constants.py`, `CORSMiddleware` в `rtb/app/main.py`, и узкий preflight test в `rtb/tests/test_imports.py`. По структуре решения это близко к целевой семантике.

Но текущий scope ещё не закрыт по двум конкретным причинам:
1. В `git diff` попали побочные бинарные `__pycache__/*.pyc`, что является недопустимым side effect вне продуктового scope.
2. Есть противоречие между каналами: в `TECHNICAL_CHANNEL` полный набор тестов помечен как passed, а в `MODEL_CHANNEL` сказано, что `test:backend` / `test:all` раньше падали по environment issue. Нужно привести verification к одному фактическому, непротиворечивому состоянию и отчитаться строго по реально наблюдаемым результатам.

# Current scope
Refinement текущего CORS/preflight scope: убрать побочные артефакты, подтвердить корректность verification, не меняя семантику решения без необходимости.

# Target semantics
После этой итерации должно быть истинно следующее:
1. В diff остаются только осмысленные продуктовые изменения, относящиеся к CORS/preflight scope.
2. `__pycache__/*.pyc` и другие побочные generated artifacts не остаются в изменениях.
3. Verification report непротиворечив: для каждой команды указан один фактический итог.
4. Подтверждено, что backend CORS fix работает bounded-способом и не сводится к approximation.
5. Не появились новые raw semantic literals / competing config sources.

# What to inspect first
1. Проверь текущее рабочее дерево и `git diff`:
   - найди все `__pycache__/*.pyc` и другие generated artifacts, попавшие в diff;
   - убери их из изменений.
2. Перепроверь ровно изменённые продуктовые файлы:
   - `rtb/app/core/constants.py`
   - `rtb/app/main.py`
   - `rtb/tests/test_imports.py`
3. Перепроверь verification commands и их фактические exit codes/outputs:
   - особенно `cd ui && npm.cmd run test:backend`
   - и `cd ui && npm.cmd run test:all`
4. Проверь, не нужен ли `export_project_to_txt.py` sync после фактического состава changed files.

# Required changes
1. Удали из diff все изменённые `__pycache__/*.pyc` и любые другие generated binary artifacts, не относящиеся к задаче.
2. Не меняй уже внесённый CORS fix, если только при перепроверке не выявится конкретный дефект.
3. Если по итогам cleanup helper sync не нужен — зафиксируй это явно в отчёте.
4. Перезапусти verification так, чтобы итоговый отчёт не содержал противоречий:
   - backend import/start bounded check;
   - узкий preflight/CORS test;
   - полный набор проектных тестов.
5. Если какая-то команда всё же падает, не сглаживай это формулировкой summary: приведи точный статус и отдели product defect от environment issue на основе stdout/stderr.
6. Отдельно проверь, что route-level CORS костыли не появились и что policy всё ещё централизована в одном месте.

# Files allowed to change
- Только cleanup артефактов рабочего дерева, не относящихся к продуктовым файлам
- `rtb/app/core/constants.py` только если обнаружится конкретный дефект
- `rtb/app/main.py` только если обнаружится конкретный дефект
- `rtb/tests/test_imports.py` только если обнаружится конкретный дефект или нужен очень узкий fix теста
- `export_project_to_txt.py` только если после фактического анализа состава changed files это действительно требуется

# Do not do
1. Не переходи к новому scope.
2. Не делай verification-only pass без cleanup конкретных расхождений.
3. Не оставляй в diff `__pycache__`, `.pyc` или другие generated files.
4. Не делай docs cleanup или backend refactor.
5. Не раздувай CORS policy без подтверждённой необходимости.
6. Не редактируй dump и не запускай `export_project_to_txt.py`.

# Verification
Обязательно выполни и отрази единообразно:
1. `python -c "from rtb.app.main import app; print(app.title)"`
2. `python -m pytest rtb/tests/test_imports.py -k cors_preflight -q`
3. `cd ui && npm.cmd test`
4. `cd ui && npm.cmd run test:integration`
5. `cd ui && npm.cmd run test:backend`
6. `cd ui && npm.cmd run test:all`
7. Покажи итоговый `git diff --stat` / состав changed files после cleanup и отдельно подтвердить, что `__pycache__` больше не изменены.
8. Отдельно проверь:
   - не появились ли новые raw semantic literals;
   - не возник ли второй source of truth для CORS policy;
   - не затронуты ли побочно другие backend routes.

# Result report
Дай структурированный отчёт:
- Summary
- Changed files
- What changed
- Verification
- Risks / open items

В отчёте обязательно укажи:
1. Что именно было очищено из побочных артефактов.
2. Каков фактический окончательный статус каждой verification-команды.
3. Нужен ли был `export_project_to_txt.py` sync.
4. Остались ли какие-либо реальные открытые вопросы в текущем scope.