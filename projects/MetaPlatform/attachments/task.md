# task.md

## Коротко
Следующая отдельная задача: **move-runtime-backend-into-rtb-root**.

Нужно перенести runtime backend из `runtime_backend/` в `rtb/` и аккуратно перевязать все backend entrypoints, imports, pytest/run commands, `.gitignore` и helper-скрипты под новый layout, **не смешивая это с раздачей built UI, packaging или дополнительным repo-cleanup**.

---

## Контекст
Текущее состояние после `9fde428 move-ui-into-ui-root-done`:
- frontend уже находится в `ui/`;
- shared config уже находится в `shared/config/`;
- backend всё ещё живёт в `runtime_backend/`;
- `ui/package.json` всё ещё запускает backend tests через `../runtime_backend/tests`;
- `.gitignore` всё ещё игнорирует `runtime_backend/**/__pycache__/` и `runtime_backend/runtime_data/platform.db`;
- helper-скрипты `create_project_structure.py` и `export_project_to_txt.py` всё ещё перечисляют backend через пути `runtime_backend/...`.

Это видно в текущем дампе, поэтому следующий цикл должен быть именно про перенос backend-корня, без расширения scope.

---

## Границы этого цикла

### Что делать
1. Перенести backend-код из `runtime_backend/` в `rtb/`.
2. Перевязать Python imports / entrypoints / test commands / path references под `rtb/`.
3. Синхронизировать `.gitignore`.
4. Синхронизировать `create_project_structure.py` и `export_project_to_txt.py`.
5. Обновить связанные тесты и команды так, чтобы проект работал из нового backend-root.

### Что НЕ делать
- не трогать `ui/` layout повторно, кроме точечных path rewiring, которые нужны из-за переноса backend;
- не переносить helper-скрипты в `tools/` в этом цикле;
- не переносить docs в `docs/`;
- не делать cleanup “до идеала” по всему repo;
- не добавлять compatibility-layer вида “поддерживаем и `runtime_backend`, и `rtb`”;
- не смешивать эту задачу с раздачей built UI, static hosting, packaging, release-контуром;
- не делать новые большие рефакторы backend-архитектуры поверх переноса.

---

## Что сначала проверить в текущем дампе
Перед правками reviewer должен сначала явно проверить и перечислить:
1. Все текущие вхождения путей `runtime_backend/...` в:
   - `.gitignore`
   - `ui/package.json`
   - `create_project_structure.py`
   - `export_project_to_txt.py`
   - Python imports внутри backend
   - pytest / run commands
   - любые docs/comments внутри активных файлов whitelist-а, если они затрагиваются этим переносом
2. Где сейчас находится backend entrypoint:
   - `runtime_backend/app/main.py`
3. Какие backend-модули импортируют `runtime_backend.*` как package prefix.
4. Есть ли backend tests вне helper whitelist-а, которые всё равно надо запускать и чинить после переноса.
5. Не появятся ли из-за переноса новые raw literals путей, которые надо вынести в существующий config/constants слой либо локально оставить только если они действительно одноразовые и не образуют contract.

---

## Что именно реализовать

### 1. Перенос backend root
Нужно перенести:
- `runtime_backend/__init__.py` -> `rtb/__init__.py`
- `runtime_backend/requirements.txt` -> `rtb/requirements.txt`
- `runtime_backend/app/...` -> `rtb/app/...`
- `runtime_backend/tests/...` -> `rtb/tests/...` если тестовая директория реально существует в репо и используется фактическими командами

Ожидаемая целевая форма backend-корня в этом цикле:
- `rtb/requirements.txt`
- `rtb/app/main.py`
- `rtb/app/api/...`
- `rtb/app/core/...`
- `rtb/app/db/...`
- `rtb/app/models/...`
- `rtb/app/services/...`
- `rtb/app/utils/...`
- `rtb/tests/...` при наличии backend tests

### 2. Перевязка Python imports
После переноса reviewer должен привести imports к новой package-семантике:
- где сейчас используется `runtime_backend.app...`, должно стать `rtb.app...`
- не оставлять старые import-пути на `runtime_backend`
- не добавлять временные shim-модули ради обратной совместимости

Отдельно проверить:
- `rtb/app/main.py`
- `rtb/app/api/commands.py`
- все backend modules/services/utils/models/db imports

### 3. Перевязка test/run commands
Нужно обновить команды, завязанные на backend path, в первую очередь:
- `ui/package.json`

Проверить и привести к актуальному виду как минимум:
- backend pytest path
- combined full test command
- любой PYTHONPATH, если он сейчас завязан на старое имя каталога

Важно:
- не ухудшить текущую модель запуска тестов;
- не вводить foreground/watch/server команды в `extra_test_commands`;
- не подменять задачу на “давайте заодно переделаем весь script layout”.

### 4. Перевязка `.gitignore`
Нужно заменить backend-specific ignore paths на новые пути в `rtb/`, включая как минимум аналоги:
- `runtime_backend/**/__pycache__/`
- `runtime_backend/runtime_data/platform.db`

После цикла `.gitignore` не должен продолжать ссылаться на старый backend-root.

### 5. Синхронизация helper-скриптов
Обязательно обновить:
- `create_project_structure.py`
- `export_project_to_txt.py`

Требования:
- whitelist должен ссылаться на `rtb/...`, а не на `runtime_backend/...`;
- helper-скрипты должны остаться ручным whitelist, без автосканирования;
- `export_project_to_txt.py` не должен включать:
  - top-level tests
  - icons
  - `*.md`
  - demo project

Если после переноса backend tests находятся в `rtb/tests/`, это **не означает**, что их надо добавлять в `export_project_to_txt.py`. Правило про отсутствие tests в export остаётся в силе.

### 6. Точечная проверка frontend/backend integration paths
Проверить frontend-код только на предмет backend-root path assumptions, если такие есть.
Если frontend использует только HTTP base URL и не зависит от файлового пути backend-каталога, ничего лишнего там не менять.

### 7. Точечная проверка backend runtime data paths
Если backend settings/constants используют пути, завязанные на положение каталога `runtime_backend`, их нужно перевязать на новое положение `rtb/` так, чтобы runtime data / temp artifacts / storage bootstrap продолжали работать из новой структуры.

Здесь важна осторожность:
- менять только то, что реально завязано на старый backend root;
- не перерабатывать storage architecture шире этой задачи.

---

## Границы свободы для reviewer
Reviewer может сам выбрать:
- делать перенос физическим rename или серией file moves;
- как именно лучше минимально перевязать imports;
- какие из связанных тестов обновить точечно, а какие переписать минимально.

Reviewer НЕ может:
- расширять задачу до переноса `tools/` и `docs/`;
- расширять задачу до cleanup всего repo;
- добавлять совместимость со старым `runtime_backend/`;
- превращать задачу в packaging/release pass;
- тащить в этот цикл built UI serving или unified startup orchestration.

---

## Отдельно: про магические строки и числа
Не добавлять новые magic strings / magic numbers без необходимости.

Обязательно использовать существующий config/constants слой там, где значение:
- повторяется;
- участвует в wiring;
- является path token, command id, error code, prefix, marker, folder name, endpoint contract, runtime reason или другой cross-file semantic literal.

Если какое-то строковое path-значение остаётся локально:
- reviewer должен в итоговом отчёте явно указать, почему это допустимо как одноразовый локальный literal, а не часть общего контракта.

Отдельно:
- не разбрасывать raw `rtb`, `tests`, `requirements.txt`, `__pycache__`, `platform.db` по множеству файлов, если часть этих значений уже централизуется или явно просится в существующий constants/config слой;
- но и не делать ради этой задачи новый giant-config без необходимости.

---

## Какие тесты обязательно добавить или обновить
Нужно обновить/добавить тесты ровно там, где это нужно для фиксации нового layout contract.

Минимально проверить и при необходимости обновить:
1. Тесты, которые жёстко ожидают старые пути `runtime_backend/...`.
2. Тесты на backend entrypoint/import wiring, если такие уже есть.
3. Тесты/helper assertions для `create_project_structure.py` и `export_project_to_txt.py`, если они существуют.
4. Тесты, которые проверяют package/config wiring после прошлых рефакторингов, если перенос backend root их затрагивает.

Не нужно придумывать отдельный большой набор новых архитектурных тестов, если существующие можно минимально и достаточно адаптировать.

---

## Какие команды проверки реально прогнать
Reviewer должен прогнать и перечислить фактические команды.

Минимальный обязательный набор:
```bash
python create_project_structure.py
python export_project_to_txt.py
cd ui && npm test
cd ui && npm run test:integration
cd ui && npm run test:backend
cd ui && npm run test:all
```

Если после переноса эти команды должны измениться, reviewer должен:
- сначала изменить их в проекте,
- потом прогнать уже актуальные версии,
- и явно показать финальный список команд.

Запрещено включать в `extra_test_commands` без bounded wrapper любые долгоживущие foreground/watch/server-команды, включая:
- `python -m uvicorn ...`
- `npm run dev`
- `vite`
- любые аналогичные команды, которые сами не завершаются

Если нужен smoke-check backend startup, использовать только bounded wrapper / one-shot command, которая гарантированно завершается.

---

## Требование проверить helper-скрипты
Это обязательная часть DONE.

Reviewer обязан отдельно проверить, что после переноса:
- `create_project_structure.py` создаёт backend-дерево уже в `rtb/...`;
- `export_project_to_txt.py` экспортирует `rtb/...`, а не `runtime_backend/...`;
- `export_project_to_txt.py` по-прежнему не включает tests / icons / md / demo project;
- helper-скрипты синхронизированы между собой и не расходятся по whitelist.

---

## Формат итогового отчёта reviewer
Итоговый отчёт нужен в структурированном виде:

1. Что проверил сначала
2. Какие файлы/пути были перенесены из `runtime_backend/` в `rtb/`
3. Какие imports и команды были перевязаны
4. Какие helper-скрипты обновлены
5. Какие тесты обновлены/добавлены
6. Полный список реально прогнанных команд
7. Что сознательно НЕ делалось в этом цикле
8. Отдельно:
   - какие literals были вынесены в config/constants
   - какие literals оставлены локально и почему
9. Финальный статус:
   - DONE / NOT DONE
   - список оставшихся проблем, если что-то не закрыто

---

## Критерий DONE
Задача считается DONE только если одновременно выполнено всё ниже:

- backend физически перенесён в `rtb/`;
- в активном коде и командах больше нет рабочих ссылок на `runtime_backend/...`;
- Python imports и backend entrypoints работают из `rtb/...`;
- `.gitignore` перевязан на `rtb/...`;
- `ui/package.json` и связанные test/run commands перевязаны на новый backend root;
- helper-скрипты синхронизированы и используют `rtb/...`;
- `export_project_to_txt.py` не включает tests / icons / md / demo project;
- полный набор тестов прогнан целиком и проходит;
- scope не расползся в `tools/docs/final cleanup`.
