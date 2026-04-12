# Context

Новая отдельная задача: исправить только backend policy для `slug`, чтобы удалённые проекты больше не резервировали slug навсегда.

Сейчас поведение такое:
- создать `qwe` → slug = `qwe`
- удалить `qwe`
- создать новый `qwe` → slug = `qwe-2`
- импорт похожего проекта даёт `qwe-3`

По текущему дампу видно, что свободный slug выбирается через `_next_available_slug(...)`, и reviewer должен сначала проверить, не учитываются ли там удалённые проекты как занятые. Эта задача только про это.

# Current scope

Только исправление slug reuse policy для create/import после delete.

В этом цикле не делать:
- модальное окно выбора проекта;
- перенос/удаление панели workspace browser;
- перевод сообщений в общие логи;
- русский UX cleanup;
- close confirmation;
- общий refactor backend workspace flow;
- unrelated backend cleanup.

# Target semantics

После правки должно быть истинно следующее:

1. Если проект `qwe` удалён и среди живых проектов slug `qwe` свободен, следующий новый проект `qwe` получает slug `qwe`, а не `qwe-2`.
2. Та же корректная slug policy применяется и к import flow.
3. Уникальность slug среди живых проектов сохраняется.
4. Не появляется второй competing slug allocation path.

# What to inspect first

Reviewer должен поручить Codex сначала проверить:

- `rtb/app/services/project_storage.py`
  - `_next_available_slug`
  - `prepare_new_project_metadata`
  - create flow
  - import flow
  - delete flow
- модель/таблицу проектов и поле `deleted_at`, если оно участвует в soft delete
- связанные tests на project storage / create / import, если они уже есть

# Required changes

1. Исправить backend slug allocation так, чтобы deleted projects не резервировали slug навсегда.
2. Для выбора slug учитывать только живые проекты, если отдельное постоянное резервирование deleted slug не является уже зафиксированной политикой.
3. Привести create и import к одной и той же корректной slug policy.
4. Не ломать существующую уникальность среди активных проектов.
5. Не вводить новый разрозненный slug policy layer.
6. Не добавлять новые raw semantic literals / magic strings / magic numbers без необходимости; если нужны shared values, использовать существующий config/constants слой.

# Files allowed to change

Разрешено менять только:
- `rtb/app/services/project_storage.py`
- связанные backend models/constants/settings files только если это действительно нужно для slug policy
- backend tests, если они реально существуют и требуют обновления/добавления
- `export_project_to_txt.py` только если после изменений helper нужно синхронизировать

# Do not do

1. Не менять UI.
2. Не трогать workspace browser panel.
3. Не делать модальные окна.
4. Не менять close/save/lock/process semantics.
5. Не делать общий backend cleanup.
6. Не редактировать dump.
7. Не подменять проблему обходом в UI, если корень в backend slug allocation.

# Magic strings / magic numbers

Reviewer должен отдельно потребовать от Codex:
- не разбрасывать новые slug-related literals по нескольким файлам;
- использовать существующий constants/config слой, если появляются shared semantic values;
- не делать бессмысленный over-extraction локальных одноразовых literals.

# Tests to add or update

Reviewer должен поручить Codex добавить или обновить tests как минимум на:

1. slug reuse после delete:
   - deleted project не должен навсегда занимать slug;
2. create flow:
   - после удаления `qwe` новый `qwe` снова получает `qwe`, если среди живых проектов slug свободен;
3. import flow:
   - import использует ту же корректную slug policy.

Если какие-то tests уже есть, их нужно адаптировать, а не дублировать второй конкурирующей веткой.

# Verification

Reviewer должен потребовать от Codex реально прогнать:
- полный набор тестов проекта;
- targeted tests для slug/create/import scenario, если такие команды нужны дополнительно.

Reviewer должен проверить фактические результаты команд от Codex, а не принимать задачу по описанию.

Если тесты падают:
- отделить реальный дефект от ограничения среды;
- не списывать в “среду” без stderr/stdout.

# Helper script check

Reviewer должен отдельно потребовать от Codex проверить `export_project_to_txt.py`.

Если после правки изменился набор реально затронутых repo files, helper должен быть синхронизирован.
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
1. где именно была причина старого slug behavior;
2. как теперь работает slug reuse после delete;
3. как синхронизированы create/import flows;
4. какие tests добавлены/обновлены;
5. какие команды реально прогнаны;
6. результаты полного тестового прогона;
7. остались ли риски.

# DONE

Задача считается DONE только если одновременно выполнено всё ниже:

1. deleted projects больше не резервируют slug навсегда;
2. новый `qwe` после удаления старого `qwe` получает ожидаемый slug без лишнего `-2`, если среди живых проектов slug свободен;
3. import использует ту же корректную slug policy;
4. добавлены/обновлены tests на это поведение;
5. `export_project_to_txt.py` проверен и синхронизирован при необходимости;
6. Codex реально прогнал полный набор тестов по проекту;
7. reviewer проверил фактические результаты и не принимает задачу без них.
