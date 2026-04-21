# 02_codex_execution.md

## Назначение

Документ задаёт стандарт того, как reviewer пишет ТЗ для Codex.

Это инструкция **для reviewer**, не для пользователя и не для внешнего оркестратора.

Reviewer должен формировать компактные repo-задачи, которые Codex может выполнить в локальном репозитории: изменить файлы, запустить команды и вернуть фактический результат.

---

## 1. Роли

**Reviewer**:
- анализирует task, technical/model channels и доступные артефакты;
- выбирает один управляемый scope;
- пишет прямое ТЗ для Codex;
- проверяет diff, changed files, stdout/stderr и результаты тестов.

**Codex**:
- работает с реальным repo;
- читает и меняет файлы;
- запускает команды;
- возвращает фактический результат.

Нельзя писать ТЗ так, будто Codex редактирует dump, attachment или reference-файл.

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
- как отчитаться.

Не писать:
- reviewer-заметки вместо ТЗ;
- абстрактные пожелания;
- “сделай красиво”;
- verification-only pass без конкретной цели, если нужен code/doc/helper change.

---

## 3. Каноническая структура task

Используй структуру по умолчанию:

```md
# Context
# Current scope
# Target semantics
# What to inspect first
# Required changes
# Files allowed to change
# Do not do
# Verification
# Result report
```

Task должен быть:
- коротким;
- операционным;
- проверяемым;
- с явной границей scope;
- без MetaFlow/оркестраторной терминологии.

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
- не редактировать dump;
- не генерировать новый dump без явного разрешения;
- не добавлять magic strings / magic numbers вне существующего config/constants слоя.

Дополнительные запреты для текущей фазы:
- не вводить новый coordinator/orchestrator/facade/framework, если задача решается сужением существующего слоя;
- не вводить unified execution contract / typed outcome framework / central contract center;
- не переносить ту же сложность в новый слой без удаления старой;
- не делать “архитектурный cleanup вообще” без конкретного удаляемого пересечения обязанностей.

---

## 10. Config / constants / magic literals

Semantic values должны жить в существующем config/constants слое.

Кандидаты на обязательный вынос:
- module ids;
- document kinds;
- node types;
- action ids;
- command ids;
- status/reason/outcome/source ids;
- endpoint paths;
- timeout/retry/polling values;
- folder/file names/path prefixes;
- shared dialog tokens;
- shared policy values.

Локально допустимы:
- `0`, `1`, `-1`, `index + 1`;
- одноразовые internal guard strings;
- platform API literals;
- маленькие helper-only literals, если они не повторяются и не образуют contract.

Reviewer должен требовать:
- не создавать второй constants layer;
- не выносить микролитералы механически;
- проверять, что не появился competing source of truth;
- не выносить новые constants “на будущее”, если они ещё не являются реальным shared contract.

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
- запустить helper;
- сообщить фактический результат запуска.

---

## 12. Тесты и команды

После любых code/config/helper изменений требовать явный набор project-level проверок.

Поскольку Codex может работать и в Windows, и в Linux, а среда заранее неизвестна, reviewer должен требовать от Codex сначала определить, какой вариант команды доступен, и использовать рабочий вариант.

Для npm-команд правило такое:
1. сначала попробовать `npm test`;
2. если команда не запускается из-за среды/command resolution, попробовать `npm.cmd test`;
3. аналогично для script-команд:
   - сначала `npm run test:integration`, затем `npm.cmd run test:integration`;
   - сначала `npm run test:backend`, затем `npm.cmd run test:backend`.

Если в repo есть более точные scripts или изменённые имена, Codex обязан сначала сверить фактический `package.json` и использовать реально существующие команды.

Базовый обязательный набор после code/config/helper изменений:
```text
npm test
npm run test:integration
npm run test:backend
```

Если в данной среде нужен Windows-вариант, использовать:
```text
npm.cmd test
npm.cmd run test:integration
npm.cmd run test:backend
```

Не использовать `test:all` как обязательную проверку и не добавлять его в task. Если `test:all` есть как package alias, его можно удалить как избыточный или оставить по совместимости, но не использовать в reviewer/Codex tasks.

Для Python-тестов использовать:
```text
python -m pytest ...
```

Если cache не нужен, добавлять:
```text
python -m pytest ... -p no:cacheprovider
```

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

## 13. Environment-sensitive failures

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

## 14. Verification checklist для reviewer

В task требовать проверить:

- соседние сценарии;
- сохранение public contract;
- отсутствие второго source of truth;
- отсутствие временных веток/заглушек;
- отсутствие мёртвого кода;
- отсутствие `__pycache__/`, `*.pyc`, runtime artifacts в diff;
- helper/export consistency, если scope затрагивает файлы whitelist;
- что после правки не появился новый лишний orchestration/coordinator/framework слой;
- что сложность действительно уменьшилась, а не была только переразложена по новым файлам.

---

## 15. Manual UI QA

Reviewer/Codex не должны “проверять UI глазами”.

Если проверка выполняется пользователем вручную:
- не ставить Codex task;
- дать пользователю checklist;
- не добавлять Playwright/Cypress/browser E2E harness без отдельного scope;
- после найденного фактического UI бага сформулировать точечный repo-task.

Manual QA checklist может быть отдельным documentation/user artifact, но он не является product runtime test.

---

## 16. Result report

Требовать короткий структурированный отчёт:

- Summary;
- Changed files;
- What changed by file;
- Tests/commands run;
- Exit codes/results;
- export_project_to_txt.py status;
- Risks / open items.

Если Codex не запустил обязательные команды и не дал фактический вывод/exit codes, задача не считается завершённой.

Если какая-то команда не прошла из-за ограничения среды, отчёт должен явно содержать:
- exact command;
- stdout/stderr summary;
- exit code;
- why this looks environment-sensitive;
- затрагивает ли это product verdict или нет.

---

## 17. Cross-platform specifics

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

## 18. Короткая формула

Reviewer формирует прямое, компактное, repo-исполнимое ТЗ для Codex.

Codex меняет реальные файлы и запускает реальные команды.

Reviewer принимает результат только по фактическим артефактам: diff, changed files, stdout/stderr, test summary.

Manual UI checks выполняет пользователь по checklist; Codex получает задачу только на реальные изменения repo или на конкретный найденный баг.

Для текущей фазы проекта reviewer дополнительно следит, чтобы каждая задача уменьшала сложность, а не порождала новый общий abstraction layer.
