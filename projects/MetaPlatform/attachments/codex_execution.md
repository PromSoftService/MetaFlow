# codex_execution.md

## Назначение

Документ задаёт стандарт того, как reviewer пишет ТЗ для Codex в текущем flow:

reviewer → Codex → MetaFlow post-Codex commands → reviewer.

Это инструкция **для reviewer**, не для пользователя и не для внешнего оркестратора.

Reviewer должен формировать компактные repo-задачи, которые Codex может выполнить в локальном репозитории: изменить файлы, запустить нужные локальные команды и вернуть фактический результат.

Commit и push в текущем flow выполняются post-Codex командами MetaFlow после завершения Codex.

---

## 1. Роли

**Reviewer**:
- анализирует task, GitHub repo, technical/model channels и доступные артефакты;
- выбирает один управляемый scope;
- пишет прямое ТЗ для Codex;
- проверяет diff, changed files, stdout/stderr, результаты команд/проверок, extra commands output и опубликованный commit.

**Codex**:
- работает с реальным repo;
- читает и меняет файлы;
- запускает команды, которые reviewer указал в task;
- возвращает фактический результат.

**MetaFlow post-Codex commands**:
- после Codex выполняют config-defined post-Codex commands;
- делают commit с изменениями Codex и post-Codex артефактами, если текущий config должен их создать;
- выполняют push;
- печатают hash-маркеры в `[TECHNICAL_CHANNEL].extra_commands_output`.

Нельзя писать ТЗ так, будто Codex редактирует attachment или reference-файл.

Нельзя требовать от Codex commit/push или другие post-Codex действия, если это выполняется post-Codex командами MetaFlow.

---

## 2. Главный принцип task

Пиши ТЗ напрямую для Codex:

- какой текущий scope;
- что сначала проверить;
- какая target semantics нужна;
- что изменить;
- какие файлы/области можно менять;
- что запрещено;
- какие команды запустить;
- как отчитаться;
- какие новые/изменяемые пользовательские строки, UI labels, menu labels, table headers, messages, errors, status texts и другие user-facing тексты должны быть сразу заведены через существующий механизм локализации;
- какие новые/изменяемые semantic values, identifiers, config values, defaults, paths, filenames, driver names, device names, table names, column ids и policy values должны быть сразу вынесены в существующий config/constants слой.

Не писать:
- reviewer-заметки вместо ТЗ;
- абстрактные пожелания;
- “сделай красиво”;
- verification-only pass без конкретной цели, если нужен code/doc/helper change.

---

## 3. Каноническая структура task

Используй структуру по умолчанию:

# Context
# Current scope
# Target semantics
# What to inspect first
# Required changes
# Files allowed to change
# Do not do
# Verification
# Result report

Task должен быть:
- коротким;
- операционным;
- проверяемым;
- с явной границей scope;
- без MetaFlow/оркестраторной терминологии внутри `codex_task_md`.

Reviewer может помнить про MetaFlow post-Codex этап, но Codex task не должен превращаться в описание работы MetaFlow.

---

## 4. Scope

Один task = один управляемый scope.

Не смешивать:
- архитектурный refactor;
- новую функциональность;
- широкий cleanup;
- тестовую инфраструктуру;
- визуальную доводку;
- docs rewrite.

Если текущий scope не закрыт, писать корректировку текущего scope, а не новую большую задачу.

Если пользователь может проверить сценарий сам в UI, не ставить reviewer/Codex задачу на эту проверку. Вместо этого дать пользователю manual checklist. Codex task нужен только после конкретного найденного бага или если нужно изменить repo.

Для текущей фазы проекта reviewer должен избегать задач вида:
- “ввести единый coordinator/orchestrator”;
- “ввести общий execution contract”;
- “зафиксировать central boundary layer”;
- “подготовить future-ready abstraction”.

Предпочтительный тип scope:
- сузить ответственность конкретного файла/узла;
- удалить дублирующее знание;
- схлопнуть лишнюю прослойку;
- вынести конкретную orchestration-ветку без создания нового framework.

---

## 5. Target semantics

Reviewer обязан формулировать, что должно быть истинно после правки.

Плохо:
- “исправь сохранение”;
- “почини рендер”;
- “убери баг”.

Хорошо:
- “dirty-state сбрасывается только после успешного full project-level save”;
- “close/switch не продолжается, если lock release заблокирован active process”;
- “export ZIP сохраняет прежний YAML transport contract”.

Для текущей фазы reviewer должен формулировать target semantics так, чтобы было ясно:
- какая сложность удаляется;
- какая ответственность сужается;
- какое дублирование исчезает.

---

## 6. What to inspect first

Блок обязателен.

Указывать:
- конкретные файлы/модули, если известны;
- функции/сервисы/flows;
- source of truth;
- соседние сценарии;
- возможные side effects.

Codex должен сначала проверить repo, а не сразу делать patch по предположению.

Если task связан с запуском команд, Codex должен сначала проверить:
- доступную ОС/среду исполнения;
- фактические package scripts;
- какие команды реально существуют;
- нет ли уже известных bounded wrappers / temp-dir подходов / environment-specific helpers.

---

## 7. Required changes

Писать нумерованным списком.

Каждый пункт должен быть предметным:
- что заменить;
- что сохранить;
- какой контракт не ломать;
- какие callers/tests/docs синхронизировать.

Разделять “проверить” и “изменить”.

Не использовать расплывчатые формулировки:
- “подчисти”;
- “гармонизируй”;
- “сделай правильно”.

Для текущей фазы reviewer должен по возможности явно требовать одно из двух:
- что удалить;
- что сузить по ответственности.

Не ставить задачи, которые только раскладывают ту же сложность по новым файлам без уменьшения общего glue-code.

---

## 8. Files allowed to change

Если точные файлы известны — перечислить их.

Если нет — указать область:
- `ui/renderer/runtime/**`;
- `rtb/app/services/**`;
- `shared/config/**`;
- docs/helper area.

Отдельно указать отношение к:
- tests;
- helper scripts;
- config/constants;
- README/runbook/docs;
- package/build files.

---

## 9. Do not do

Блок обязателен.

Типовые запреты:
- не расширять scope;
- не менять unrelated files;
- не менять public API без необходимости;
- не менять YAML ZIP contract, если task не об этом;
- не подгонять тесты под неверное поведение;
- не маскировать проблему отключением проверки;
- не оставлять временные заглушки;
- не добавлять magic strings / magic numbers вне существующего config/constants слоя;
- не требовать от Codex commit/push;
- не требовать от Codex запуск config-defined post-Codex commands, если они выполняются post-Codex командами MetaFlow.

Дополнительные запреты для текущей фазы:
- не вводить новый coordinator/orchestrator/facade/framework, если задача решается сужением существующего слоя;
- не вводить unified execution contract / typed outcome framework / central contract center;
- не переносить ту же сложность в новый слой без удаления старой;
- не делать “архитектурный cleanup вообще” без конкретного удаляемого пересечения обязанностей.

---

## 10. Localization / config / constants / magic literals

Если task добавляет новое поведение или меняет существующее поведение, reviewer обязан требовать от Codex сразу делать нормальную product-quality реализацию, без временного hardcode, который потом потребует отдельного cleanup.

### Localization

Все новые или изменяемые user-facing тексты должны сразу идти через существующий механизм локализации проекта.

К user-facing текстам относятся:

- menu labels;
- tree node titles;
- table titles;
- table column headers;
- button labels;
- dialog titles;
- dialog body texts;
- validation messages;
- error messages;
- status labels;
- tooltips;
- empty-state texts;
- download/import/generate action labels;
- report labels, если они видны пользователю в UI.

Запрещено добавлять новые user-facing строки прямо в компоненты, services или handlers, если в проекте уже есть слой локализации / UI text constants для этой зоны.

Если в конкретной зоне проекта ещё нет подходящего localization/helper слоя, Codex должен:
1. сначала найти существующий ближайший паттерн;
2. использовать его;
3. не создавать второй competing localization layer;
4. если локализация действительно невозможна без отдельного scope, явно написать это в result report и ограничить hardcode только временной внутренней строкой, не user-facing текстом.

Reviewer обязан проверять diff на новые raw user-facing strings.

### Config / constants

Semantic values должны жить в существующем config/constants слое.

Кандидаты на обязательный вынос:

- module ids;
- document kinds;
- node types;
- table ids;
- table names;
- column ids;
- action ids;
- command ids;
- menu item ids;
- download/import/generate action ids;
- status/reason/outcome/source ids;
- endpoint paths;
- timeout/retry/polling values;
- folder/file names/path prefixes;
- default device names;
- default driver names;
- default artifact names;
- shared dialog tokens;
- shared policy values.

Если task вводит новые project-level entities, tables, menu actions, artifact kinds, import/download kinds или lifecycle states, reviewer обязан требовать от Codex сразу завести их через существующий config/constants слой, а не разбрасывать строками по UI/backend.

Локально допустимы:

- `0`, `1`, `-1`, `index + 1`;
- одноразовые internal guard strings;
- platform API literals;
- маленькие helper-only literals, если они не повторяются, не user-facing и не образуют contract.

Reviewer должен требовать:

- не создавать второй constants layer;
- не выносить микролитералы механически;
- проверять, что не появился competing source of truth;
- не выносить новые constants “на будущее”, если они ещё не являются реальным shared contract;
- не оставлять hardcode только потому, что это первый implementation pass.

### Code quality bar

Reviewer должен принимать результат только если качество реализации в рамках текущего bounded scope не ниже 7.75/10.

Под 7.75/10 понимается:

- решение закрывает текущую задачу без очевидных хвостов;
- нет временных workaround, TODO, dead branches, debug remnants;
- нет raw user-facing strings вне локализации;
- нет новых semantic magic strings/magic numbers вне config/constants;
- нет второго source of truth;
- нет лишнего coordinator/orchestrator/manager/framework слоя;
- нет дублирования, которое сразу очевидно надо будет чистить отдельным cleanup;
- tests/commands действительно проверяют изменённую семантику;
- соседние сценарии не сломаны;
- result report честно перечисляет ограничения, если они есть.

Если реализация функционально работает, но оставляет очевидный cleanup-хвост, reviewer обязан вернуть `status = "continue"` и дать Codex точечную корректировку в этом же scope, а не закрывать задачу как done.

Цель reviewer — не принимать “работает, потом подчистим”, а доводить каждый bounded increment до состояния, которое можно оставить в repo без немедленного последующего cleanup.

---

## 11. Export helper

Helper:
- `export_project_to_txt.py`.

Правила:
- whitelist ручной;
- автоскан вместо whitelist не вводить по умолчанию;
- whitelist синхронизировать с фактическим repo layout и рабочими файлами.

Не включать:
- icons;
- tests / fixtures;
- demo artifacts;
- briefing docs;
- package-lock;
- runtime DB/cache/process/workspace artifacts;
- временные task/artifact files.

Если scope не затрагивает рабочие файлы/helper/layout, достаточно явно написать в отчёте, что export helper проверен и менять его не нужно.

Если scope затрагивает helper/export whitelist/layout, Codex обязан:
- проверить `export_project_to_txt.py`;
- при необходимости обновить whitelist;
- запустить helper, если task прямо разрешает запуск helper;
- сообщить фактический результат проверки helper.

---

## 12. Тесты и команды

Codex запускает только те локальные проверки, которые reviewer прямо указал в `codex_task_md`.

Config-defined post-Codex commands выполняет MetaFlow автоматически после завершения Codex. Reviewer видит их результат в `[TECHNICAL_CHANNEL].tests_summary` и/или `[TECHNICAL_CHANNEL].extra_commands_output`, в зависимости от текущего config.

Если reviewer добавляет дополнительные короткие проверки через `extra_test_commands`, их stdout/stderr также попадают в `[TECHNICAL_CHANNEL].extra_commands_output`.

Поскольку Codex может работать и в Windows, и в Linux, а среда заранее неизвестна, reviewer должен требовать от Codex сначала определить, какой вариант команды доступен, и использовать рабочий вариант.

Для npm-команд правило такое:
1. сначала попробовать `npm test`;
2. если команда не запускается из-за среды/command resolution, попробовать `npm.cmd test`;
3. аналогично для script-команд:
   - сначала `npm run test:integration`, затем `npm.cmd run test:integration`;
   - сначала `npm run test:backend`, затем `npm.cmd run test:backend`.

Если в repo есть более точные scripts или изменённые имена, Codex обязан сначала сверить фактический `package.json` и использовать реально существующие команды.

Базовый набор project-level проверок, если reviewer явно поручает Codex прогнать полный набор локально:
- `npm test`
- `npm run test:integration`
- `npm run test:backend`

Если в данной среде нужен Windows-вариант:
- `npm.cmd test`
- `npm.cmd run test:integration`
- `npm.cmd run test:backend`

Не использовать `test:all` как обязательную проверку и не добавлять его в task. Если `test:all` есть как package alias, его можно удалить как избыточный или оставить по совместимости, но не использовать в reviewer/Codex tasks.

Для Python-тестов использовать:
- `python -m pytest ...`

Если cache не нужен, добавлять:
- `python -m pytest ... -p no:cacheprovider`

Reviewer должен запрещать long-running foreground/watch/server commands без bounded wrapper.

Запрещены прямые долгоживущие запуски без ограничения времени и гарантированного завершения, включая:
- `python -m uvicorn ...`;
- `npm run dev`;
- `vite`;
- `electron .`;
- `npm start`, если он поднимает долгоживущий UI/backend process;
- любые watch / serve / dev / preview / start-команды без bounded wrapper.

Если нужен startup probe, он должен быть bounded:
- с timeout;
- с гарантированным завершением;
- с явным сбором stdout/stderr;
- с явным завершением дочернего процесса.

Codex не должен оставлять висящие процессы после проверки.

Для environment-sensitive запусков Codex обязан:
1. попытаться определить, является ли падение продуктовым дефектом или ограничением среды;
2. зафиксировать stdout/stderr и exit code;
3. если причина в среде, явно написать это в отчёте и не маскировать как product fix;
4. не придумывать ad-hoc workaround в продуктовый код только ради прохождения теста в ограниченной среде.

Если обязательная проверка не проходит предположительно из-за ограничения среды, Codex должен:
- описать, какая именно команда не прошла;
- привести фактический текст ошибки;
- указать, почему это похоже на environment limitation;
- отделить это от functional failure.

---

## 13. Post-Codex result and hash markers

После Codex reviewer должен смотреть результат post-Codex этапа в `[TECHNICAL_CHANNEL].extra_commands_output`.

Post-Codex этап задаётся текущим project config. Reviewer не должен предполагать точный список extra commands заранее, если task-specific section или текущий config не задают его явно.

Ожидаемые hash-маркеры:

- `METAFLOW_FINAL_HEAD=...`
- `METAFLOW_ORIGIN_MAIN=...`


Главный hash для проверки результата:

`METAFLOW_FINAL_HEAD`

Reviewer должен проверить:

1. `METAFLOW_FINAL_HEAD` найден.
2. `METAFLOW_ORIGIN_MAIN` найден.
3. `METAFLOW_FINAL_HEAD == METAFLOW_ORIGIN_MAIN`.
4. GitHub repo содержит commit `METAFLOW_FINAL_HEAD`.
5. В commit есть изменения Codex.
6. В commit есть post-Codex артефакты, если текущий project config должен был их создать.

Reviewer должен проверять фактические machine-readable markers, stdout/stderr и артефакты, которые заданы текущим project config.

Reviewer не должен ожидать фиксированную структуру post-Codex артефактов, если такой контракт не задан самим task-specific section или текущим config.

Если post-Codex command создал report/artifact и commit/push прошёл, reviewer проверяет содержимое report/artifact в repo и учитывает его при решении `continue/done/question/escalate`.

---

## 14. Environment-sensitive failures

Если есть конфликт:

- обязательные project-level tests зелёные;
- а красный только bounded startup probe / environment-specific запуск;

reviewer не должен автоматически гонять Codex по кругу.

Нужно:
1. считать source of truth по обязательным project-level проверкам;
2. проверить, что fail ограничен probe или ограничением среды;
3. отделить product failure от environment-sensitive issue;
4. не требовать кодовых изменений только ради обхода среды, если обязательные проверки зелёные;
5. явно написать это в отчёте.

Не применять это правило, если:
- есть assert/error mismatch в product tests;
- падают backend/integration/unit проверки;
- есть явный functional regression.

Если команда не прошла из-за ограничений среды, но это не удалось доказать по фактическим артефактам, reviewer не должен автоматически считать проблему environment-sensitive. Нужны stdout/stderr и понятная причина.

---

## 15. Verification checklist для reviewer

В task требовать проверить:

- соседние сценарии;
- сохранение public contract;
- отсутствие второго source of truth;
- отсутствие новых raw user-facing strings вне существующего localization слоя;
- отсутствие новых semantic magic strings / magic numbers вне существующего config/constants слоя;
- что новые/изменённые menu labels, table headers, button labels, validation/error/status texts локализованы сразу;
- что новые/изменённые ids, action kinds, artifact kinds, table/column ids, driver/device defaults и lifecycle states вынесены в существующий config/constants слой;
- качество реализации текущего bounded scope не ниже 7.75/10 и не требует немедленного cleanup;
- отсутствие временных веток/заглушек;
- отсутствие мёртвого кода;
- отсутствие `__pycache__/`, `*.pyc`, runtime artifacts в diff;
- helper/export consistency, если scope затрагивает файлы whitelist;
- что после правки не появился новый лишний orchestration/coordinator/framework слой;
- что сложность действительно уменьшилась, а не была только переразложена по новым файлам.

Если reviewer видит, что Codex сделал рабочую, но “черновую” реализацию с hardcode, нелокализованными текстами, временными helper-ветками, дублирующими constants или очевидным cleanup-хвостом, reviewer обязан вернуть `status = "continue"` и дать корректировку. Нельзя закрывать scope только потому, что тесты зелёные.

После post-Codex этапа reviewer дополнительно проверяет:

- hash-маркеры в `[TECHNICAL_CHANNEL].extra_commands_output`;
- что commit опубликован;
- что post-Codex report/artifact есть в repo, если текущий config должен был его создать;
- что reviewer смотрит фактически созданный report/artifact, а не ожидает фиксированную структуру без явного contract;
- что GitHub repo показывает фактический diff финального commit.

---

## 16. Manual UI QA

Reviewer/Codex не должны “проверять UI глазами”.

Если проверка выполняется пользователем вручную:
- не ставить Codex task;
- дать пользователю checklist;
- не добавлять Playwright/Cypress/browser E2E harness без отдельного scope;
- после найденного фактического UI бага сформулировать точечный repo-task.

Manual QA checklist может быть отдельным documentation/user artifact, но он не является product runtime test.

---

## 17. Result report

Требовать короткий структурированный отчёт от Codex:

- Summary;
- Changed files;
- What changed by file;
- Tests/commands run;
- Exit codes/results;
- helper/export status, only if the current scope touches helper/export/layout or the task explicitly requires it;
- Risks / open items.

Codex summary не обязан содержать финальный commit hash, потому что commit делает MetaFlow после Codex.

Финальный commit hash reviewer ищет в `[TECHNICAL_CHANNEL].extra_commands_output` по маркеру `METAFLOW_FINAL_HEAD`.

Если Codex не запустил команды, которые были прямо указаны в `codex_task_md`, и не дал фактический вывод/exit codes, задача не считается завершённой.

Если какая-то команда не прошла из-за ограничения среды, отчёт должен явно содержать:
- exact command;
- stdout/stderr summary;
- exit code;
- why this looks environment-sensitive;
- затрагивает ли это product verdict или нет.

---

## 18. Cross-platform specifics

Codex не должен предполагать заранее, что он находится в Windows или Linux.

Перед запуском команд он обязан:
- посмотреть фактические scripts и инструменты в repo;
- попробовать стандартный вариант команды;
- при проблеме command resolution попробовать платформенный альтернативный вариант;
- зафиксировать, какой вариант реально сработал.

Для npm-команд:
- сначала `npm ...`;
- если это не работает из-за среды — `npm.cmd ...`.

Для shell-sensitive команд reviewer должен требовать нейтральные и максимально переносимые команды. Если команда заведомо платформенно-специфична, это должно быть явно отмечено в task.

Если backend tests падают из-за temp/cache/permission/path/process issues:
- подтвердить это по stdout/stderr;
- отделить environment issue от product defect;
- использовать существующий project-level temp-dir approach, если он есть;
- не придумывать ad-hoc обходы в отдельных тестах без необходимости.

---

## 19. Короткая формула

Reviewer формирует прямое, компактное, repo-исполнимое ТЗ для Codex.

Codex меняет реальные файлы и запускает только те команды, которые указаны в его task.

MetaFlow после Codex выполняет config-defined post-Codex commands, делает commit и push.

Reviewer принимает результат только по фактическим артефактам: repo, changed files, stdout/stderr, tests summary, extra commands output, post-Codex reports/artifacts, если текущий config должен был их создать, и опубликованный commit.

Manual UI checks выполняет пользователь по checklist; Codex получает задачу только на реальные изменения repo или на конкретный найденный баг.

Для текущей фазы проекта reviewer дополнительно следит, чтобы каждая задача уменьшала сложность, а не порождала новый общий abstraction layer.

---

