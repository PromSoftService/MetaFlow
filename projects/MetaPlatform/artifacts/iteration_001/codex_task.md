# Context
Новая отдельная задача: исправить только backend policy для `slug`, чтобы soft-deleted проекты не резервировали slug навсегда. По dump видно, что slug выбирается через `rtb/app/services/project_catalog.py:_next_available_slug(...)`, а create/import используют `prepare_new_project_metadata(...)`. Текущий scope только про backend slug reuse после delete.

# Current scope
Один узкий scope: backend slug allocation policy для create/import после soft delete.

# Target semantics
После правки должно быть истинно следующее:
1. Если проект `qwe` удалён и среди живых проектов slug `qwe` свободен, следующий новый проект `qwe` получает slug `qwe`, а не `qwe-2`.
2. Та же slug policy используется в import flow.
3. Уникальность slug среди живых проектов сохраняется.
4. Не появляется второй competing slug allocation path.

# What to inspect first
Сначала проверь и сопоставь:
- `rtb/app/services/project_catalog.py`
  - `_next_available_slug`
  - `prepare_new_project_metadata`
  - `create_project`
  - `delete_project`
- `rtb/app/services/project_storage.py`
  - `import_project_archive`
  - `_save_project_snapshot_as_new_project`
  - места, где используется `prepare_new_project_metadata`
- soft delete semantics в таблице `projects` и поле `deleted_at`
- существуют ли backend tests для `project_catalog` / `project_storage` / create / import / delete / slug behavior
- `export_project_to_txt.py` только на предмет необходимости синхронизации whitelist после изменений

# Required changes
1. Исправь slug allocation policy так, чтобы `_next_available_slug(...)` учитывал только живые проекты и не резервировал slug за soft-deleted записями.
2. Сохрани единый source of truth для slug allocation через существующий путь `prepare_new_project_metadata(...)`; не создавай второй параллельный allocation path.
3. Убедись, что create flow и import flow реально используют одну и ту же исправленную slug policy.
4. Добавь или обнови backend tests как минимум на:
   - reuse slug после delete;
   - create flow: после удаления `qwe` новый `qwe` снова получает slug `qwe`, если живого конфликта нет;
   - import flow: import использует ту же корректную slug policy.
5. Если для тестов или shared slug semantics нужны общие semantic values, используй существующий constants/config слой; не разбрасывай новые raw semantic literals по нескольким местам.
6. Статически проверь `export_project_to_txt.py`: если после правки изменился набор реально затронутых repo files и helper нужно синхронизировать — обнови whitelist. Если helper менять не нужно, явно так и напиши в отчёте.

# Files allowed to change
Разрешено менять только:
- `rtb/app/services/project_catalog.py`
- `rtb/app/services/project_storage.py` только если это действительно нужно для выравнивания import/create на один slug policy path
- связанные backend models/constants/settings files только если это действительно необходимо для slug policy
- backend tests, если они существуют или если нужно добавить новые tests в существующую backend test area
- `export_project_to_txt.py` только если после изменений helper нужно синхронизировать

# Do not do
1. Не меняй UI.
2. Не трогай workspace browser panel.
3. Не меняй close/save/lock/process semantics.
4. Не делай общий backend cleanup.
5. Не делай unrelated refactor.
6. Не редактируй attachments/dump.
7. Не подменяй backend-проблему обходом в UI.
8. Не создавай новый competing slug policy layer вне существующего backend source of truth.

# Verification
После изменений обязательно:
1. Прогони полный набор тестов проекта из `ui/package.json`:
   - `cd ui && npm.cmd test`
   - `cd ui && npm.cmd run test:integration`
   - `cd ui && npm.cmd run test:backend`
   - `cd ui && npm.cmd run test:all`
2. Если добавишь отдельные таргетные backend tests для slug/create/import, запусти их дополнительно и приведи точную команду.
3. Если backend tests падают, приложи точный stdout/stderr и отдели дефект продукта от ограничения среды; не списывай без фактов.
4. Отдельно проверь, что после изменений:
   - не появились новые raw semantic literals / magic strings / magic numbers;
   - create/import не разошлись в policy;
   - uniqueness среди живых проектов не сломана;
   - нет побочных эффектов вне slug policy scope.

# Result report
Верни структурированный отчёт в формате:
- Summary
- Changed files
- What changed
- Verification
- Risks / open items

Обязательно укажи:
1. где именно была причина старого slug behavior;
2. как теперь работает slug reuse после delete;
3. как синхронизированы create/import flows;
4. какие tests добавлены/обновлены;
5. какие команды реально прогнаны;
6. результаты полного тестового прогона;
7. нужен ли был апдейт `export_project_to_txt.py` и почему.