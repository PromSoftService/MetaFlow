# Коротко

Следующая отдельная задача: перевести **close project flow** на DB-/lock-canonical semantics и убрать из этого контура зависимость от filesystem project root как части канонической модели закрытия проекта.

Зачем это нужно: `delete project`, `open project`, `save project` и `save as` уже сдвинуты в DB-canonical сторону. Следующий логичный шаг — сделать так, чтобы `close project` завершал backend lifecycle через `project_id + lock/session ownership`, а не через file-native workspace assumptions.

# Контекст

Уже есть:
- DB-backed project metadata и project documents;
- DB-canonical `list/open`;
- DB-first `delete project`;
- DB-canonical `save/save as`, где filesystem больше не source of truth, а mirror/adapter layer;
- lock/session lifecycle в БД уже существует и должен сохраняться.

Следующий логичный шаг:
- `close project` не должен опираться на обязательную filesystem integrity/model;
- закрытие проекта должно определяться каноническим backend state: ownership lock, session state, active process policy;
- filesystem не должен участвовать как критерий того, можно или нельзя закрыть проект.

# Границы

## Делать в этом цикле
- перевести `close project` на DB-/lock-canonical semantics;
- убрать из core close contract зависимость от `root_path`, `project_file_path`, project directory existence и похожей file-native логики, если такая зависимость ещё есть;
- сохранить active-process blocking и lost-lock semantics;
- синхронизировать backend tests;
- проверить и при необходимости обновить `export_project_to_txt.py`;
- при необходимости синхронизировать только узкие docs/runbook fragments, если они реально расходятся с новым close behavior.

## Не делать
- не переписывать import/export;
- не делать общий cleanup storage/config/constants;
- не трогать generation/process execution шире, чем нужно для close semantics;
- не делать широкий UI cleanup;
- не менять save/delete/open сверх того, что необходимо для непротиворечивости close flow;
- не делать полный lock/session redesign по всему проекту.

# Что сначала проверить в текущем дампе

Reviewer должен поручить Codex сначала проверить и кратко зафиксировать роль следующих мест:

- `rtb/app/services/project_storage.py`
- `rtb/app/services/project_catalog.py`
- `rtb/app/api/commands.py`
- `rtb/app/services/active_process_policy.py`
- `ui/renderer/runtime/backendCommandSessionOrchestrator.js`
- `ui/renderer/runtime/appCloseCoordinator.js`
- backend tests, которые покрывают close/lock path

Нужно отдельно установить:
1. где `close project` всё ещё зависит от filesystem metadata/integrity вместо DB/lock semantics;
2. какой close contract реально возвращается наружу;
3. какие ограничения close должны оставаться каноническими: active process blocking, lost lock, ownership release;
4. не завязаны ли UI/runtime ожидания на file-native close semantics.

# Что именно реализовать

1. Сделать так, чтобы `close project` семантически означал завершение backend project session / release lock / transition out of opened backend project по каноническому DB state.
2. Убрать из core close path обязательную зависимость от существования project directory и другой filesystem integrity логики, если проект уже известен через канонический DB state.
3. Сохранить текущие обязательные ограничения:
   - нельзя обходить active process blocking;
   - нельзя обходить lost lock semantics;
   - ownership release должен оставаться частью close lifecycle.
4. Если часть filesystem cleanup/logging ещё нужна:
   - разрешено оставить её как технический best-effort step;
   - но она не должна определять успешность или неуспешность close semantics.
5. Проверить, что после close:
   - проект корректно снимается с opened backend state;
   - lock/session lifecycle завершён корректно;
   - повторный open/list не зависит от filesystem residuals;
   - close result остаётся согласованным для UI.
6. Если для этого шага нужно точечно упростить guards или payload/result semantics вокруг close — сделать это узко, без расползания в соседние flows.
7. Не ломать внешний import/export contract и не менять YAML ZIP transport format.

# Границы свободы для reviewer

- Разрешена небольшая свобода в выборе конкретной close strategy.
- Но нельзя подменять задачу общим refactor всего backend lifecycle.
- Нельзя вычищать active-process / lost-lock semantics как “лишний шум”.
- Если Codex предлагает широкий UI/storage/lock redesign, reviewer должен сузить его до close scope.

# Магические строки и числа

- Не добавлять новые magic strings / magic numbers в рабочий код без необходимости.
- Все новые shared semantic values класть в существующий config/constants слой.
- Не создавать новый параллельный constants layer, если уже есть подходящий.
- Не разбрасывать новые reason ids, status values, error codes и lifecycle literals по коду.

# Какие тесты обязательно добавить/обновить

Нужно добавить или обновить тесты так, чтобы они явно покрывали:

1. `close project` работает по DB-/lock-canonical semantics без обязательной зависимости от project directory existence;
2. active process blocking при close сохранён;
3. lost lock handling при close сохранён;
4. successful close корректно завершает backend session / release semantics;
5. повторные `list/open` после close не зависят от filesystem residuals.

# Какие команды проверки реально прогнать

Reviewer должен потребовать от Codex реально прогнать и приложить фактические результаты для:

- `npm.cmd test`
- `npm.cmd run test:integration`
- `npm.cmd run test:backend`
- `npm.cmd run test:all`

Допустимы дополнительные короткие targeted-команды только если они реально нужны для диагностики этого scope.
Не использовать долгоживущие foreground/watch/server-команды без bounded wrapper.

# Helper-скрипт

Обязательно проверить и при необходимости актуализировать:

- `export_project_to_txt.py`

Отдельно проверить, что он по-прежнему не включает:
- иконки;
- demo project;
- top-level tests.

# Формат итогового отчёта reviewer

- Summary
- Changed files
- What changed
- Verification
- Risks / open items

Reviewer должен отдельно проверить, что:
- Codex действительно внёс изменения;
- Codex действительно прогнал обязательные команды;
- в отчёте есть фактические результаты команд;
- scope не расползся в import/export/save/delete/UI/general cleanup.

# Критерий DONE

1. `close project` опирается на DB-/lock-canonical semantics, а не на filesystem project root как часть канонической close model;
2. active process blocking и lost lock semantics сохранены;
3. close result остаётся согласованным для UI/runtime contract;
4. filesystem layer, если временно остаётся, не определяет close success/failure как source of truth;
5. scope не расползся в import/export/save/delete/general lifecycle cleanup;
6. тесты обновлены;
7. `export_project_to_txt.py` проверен и синхронизирован.
