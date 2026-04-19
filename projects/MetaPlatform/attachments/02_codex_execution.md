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
- проверять, что не появился competing source of truth.

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

---

## 12. Тесты и команды

После любых code/config/helper изменений требовать явный набор:

```powershell
npm.cmd test
npm.cmd run test:integration
npm.cmd run test:backend
```

Не использовать `test:all` как обязательную проверку и не добавлять его в task. Если `test:all` есть как package alias, его можно удалить как избыточный или оставить по совместимости, но не использовать в reviewer/Codex tasks.

Если scripts изменились, Codex сначала сверяет фактический `ui/package.json`.

Для чисто текстовых задач полный прогон можно не требовать только при явном обосновании, что runtime/product behavior не затронут. Если менялся helper/export whitelist, запуск helper-а обязателен.

Запрещены long-running foreground/watch/server commands без bounded wrapper:
- `python -m uvicorn ...`;
- `npm run dev`;
- `vite`;
- `electron .`;
- аналогичные процессы.

Если нужен startup probe, он должен быть bounded: timeout, гарантированное завершение, stdout/stderr.

Pytest запускать через:

```powershell
python -m pytest ...
```

Если cache не нужен, добавлять:

```powershell
-p no:cacheprovider
```

---

## 13. Environment-sensitive failures

Если есть конфликт:

- `TECHNICAL_CHANNEL.tests_summary` зелёный по обязательным проверкам;
- а в model/codex tail красный только bounded startup probe / uvicorn-related сценарий;

reviewer не должен автоматически гонять Codex по кругу.

Нужно:
1. считать source of truth по обязательным проверкам `TECHNICAL_CHANNEL.tests_summary`;
2. проверить, что fail ограничен startup probe;
3. отделить product failure от environment-sensitive issue;
4. не требовать кодовых изменений только ради обхода среды, если обязательные project-level tests зелёные;
5. явно написать это в отчёте.

Не применять это правило, если есть assert/error mismatch в product tests или другие красные functional/backend/integration проверки.

---

## 14. Verification checklist для reviewer

В task требовать проверить:

- соседние сценарии;
- сохранение public contract;
- отсутствие второго source of truth;
- отсутствие временных веток/заглушек;
- отсутствие мёртвого кода;
- отсутствие `__pycache__/`, `*.pyc`, runtime artifacts в diff;
- helper/export consistency, если scope затрагивает файлы whitelist.

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

---

## 17. Windows specifics

Для PowerShell использовать `npm.cmd`, а не `npm`:

```powershell
npm.cmd test
npm.cmd run test:integration
npm.cmd run test:backend
```

Если backend tests падают из-за temp/cache/permission issues:
- подтвердить по stdout/stderr;
- отделить environment issue от product defect;
- использовать существующий project-level temp-dir approach, если он есть;
- не придумывать ad-hoc обходы в отдельных тестах без необходимости.

---

## 18. Короткая формула

Reviewer формирует прямое, компактное, repo-исполнимое ТЗ для Codex.

Codex меняет реальные файлы и запускает реальные команды.

Reviewer принимает результат только по фактическим артефактам: diff, changed files, stdout/stderr, test summary.

Manual UI checks выполняет пользователь по checklist; Codex получает задачу только на реальные изменения repo или на конкретный найденный баг.
