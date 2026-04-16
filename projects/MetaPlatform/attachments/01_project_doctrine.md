# PROJECT DOCTRINE — METAPLATFORM

Актуальная краткая доктрина для первой итерации reviewer → Codex вместе с `task.md`.

Документ фиксирует постоянные правила проекта, текущее архитектурное состояние и границы допустимых изменений.

---

## 1. Роли и цикл reviewer → Codex

- **User** формулирует задачу, проверяет результат и принимает финальное решение.
- **Reviewer** получает `task.md` и briefing-документы, ставит Codex конкретные repo-задачи и оценивает результат.
- **Codex** — единственный исполнитель изменений в локальном репозитории: меняет файлы, запускает команды, возвращает фактический результат.
- Reviewer не принимает работу без подтверждения, что Codex реально выполнил команды и предоставил вывод.

Reviewer может получать:
- `task.md`;
- briefing-документы первой итерации;
- technical channel с diff, changed files и результатами тестов;
- model channel со structured summary Codex;
- ответ пользователя;
- вложения пользователя.

Reviewer должен смотреть не только summary, но и фактические артефакты: diff, changed files, stdout/stderr, `tests_summary.json`, `test_results.txt`.

Рабочие статусы reviewer:
- `continue` — нужна следующая итерация Codex;
- `done` — scope закрыт;
- `question` — нужен ответ пользователя;
- `escalate` — нужен ручной разбор или решение пользователя.

`done` допустим только когда scope выполнен, diff проверен, команды реально запускались Codex и их результат понятен.

---

## 2. Базовое направление проекта

MetaPlatform — web-only модульная инженерная платформа / workbench, а не “обвязка вокруг MetaGen”.

Архитектурно сохраняются модули:
- MetaGen;
- MetaLab;
- MetaView.

Electron и desktop-shell не являются целевой архитектурой. UI — web-based IDE, runtime backend существует отдельно от UI.

---

## 3. Текущий layout repo

Фактический layout строится вокруг зон:

- `ui/` — web UI;
- `rtb/` — runtime backend;
- `shared/` — shared config / contracts;
- `tools/` — прикладные helper/tools;
- `export_project_to_txt.py` — root helper для проектного dump.

`export_project_to_txt.py` остаётся в root. Не предлагать перенос helper-а в `tools/` без отдельного решения и отдельного scope.

`shared/` используется как общий слой конфигов и контрактов. Общие semantic values между слоями должны жить в `shared/` или существующем config/constants слое соответствующего уровня.

---

## 4. Identity и runtime-инварианты

Каноническая внутренняя identity документа = **GUID**.

Не являются identity:
- document name;
- file name;
- path;
- tree label;
- tab title.

Следствия:
- rename не меняет identity;
- path/file remap не меняет identity;
- lookup open/active/update/delete/select должен опираться на GUID.

---

## 5. Backend workspace и operational semantics

Backend workspace — основной operating mode платформы.

Операции открытия, создания, сохранения, закрытия, импорта, экспорта и удаления backend-проектов — нормальная архитектура, а не временный обход.

UI/runtime обязаны уважать:
- backend lock ownership;
- heartbeat/session lifecycle;
- lost lock как отдельное состояние;
- active process blocking;
- close/save/switch/open/export/import/delete constraints.

Эти ограничения не являются implementation noise.

---

## 6. Import / export contract

Внешний формат проекта сохраняется как YAML ZIP transport:

- root `project.yaml`;
- YAML-документы по папкам `metagen/`, `metalab/`, `metaview/`;
- экспортный архив для пользователя — `MetaPlatformProject.zip`.

ZIP — транспорт, не canonical storage. При импорте ZIP читается, данные записываются в backend storage, ZIP не становится canonical storage. Внутренняя DB-модель не должна протекать во внешний export archive.

---

## 7. Magic strings / constants

Не добавлять новые magic strings / magic numbers без необходимости.

Если значение участвует в contract semantics, UI state, command id, error code, source id, endpoint, filename, folder name, status, reason, timeout, DOM id или shared policy — оно должно быть в существующем config/constants слое.

Локальные технические микролитералы допустимы, если они не создают новый source of truth и не участвуют в контракте между слоями.

---

## 8. Тесты и команды проверки

После любых code/config/helper изменений reviewer должен требовать явный полный набор проверок:

```powershell
npm.cmd test
npm.cmd run test:integration
npm.cmd run test:backend
```

Не использовать агрегирующую команду `test:all` как обязательную проверку. Если она есть в package scripts, её можно удалить как избыточный alias; если оставить по совместимости, не использовать в reviewer/Codex tasks.

Для чисто текстовых задач reviewer может не требовать полный прогон только при явном обосновании, что runtime/product behavior не затронут. Если изменялись helper/export/docs-whitelist policy, соответствующие helper-проверки всё равно нужны.

Long-running команды нельзя использовать как обычные проверки без bounded wrapper:
- `python -m uvicorn ...`;
- `npm run dev`;
- `vite`;
- `electron .`;
- аналогичные foreground/watch/server-процессы.

Если команда падает, reviewer должен отделить:
- реальный дефект кода/тестов/документации;
- подтверждённое ограничение среды запуска.

Ограничение среды нельзя утверждать без конкретного stdout/stderr и команды.

---

## 9. Export helper

`export_project_to_txt.py` нужно проверять при задачах, которые меняют layout, добавляют/удаляют рабочие файлы или меняют набор файлов проекта.

Helper не должен экспортировать:
- иконки;
- tests / fixtures;
- demo project;
- package-lock;
- cache/build/runtime artifacts;
- briefing docs `01_project_doctrine.md`, `02_codex_execution.md`, `03_architecture_exceptions.md`;
- временные task/artifact files.

---

## 10. Ручная UI-проверка

Не ставить reviewer/Codex задачи на проверки, которые пользователь может выполнить самостоятельно в UI и функционале приложения.

В таких случаях нужно:
- прямо указать пользователю, что проверить вручную;
- дать короткий checklist;
- не превращать ручной UI smoke в Codex/reviewer task.

Если ручная проверка выявила конкретный баг, тогда по фактическому багу формируется точечное ТЗ для reviewer/Codex.

Manual QA checklist может быть отдельным пользовательским документом. Он не означает, что Codex/reviewer должны “смотреть UI глазами” или добавлять browser E2E harness без отдельного scope.

---

## 11. Финальная формула

MetaPlatform развивается как web-only модульная инженерная платформа с layout вокруг `ui / rtb / shared / tools`.

Identity документов строится только на GUID.

Backend workspace является основным operating mode.

Close/save/switch/open/export/import/delete flows обязаны учитывать backend lock/process lifecycle.

Внешний import/export формат сохраняется как YAML ZIP transport.

`export_project_to_txt.py` остаётся в root и поддерживается вручную.

Reviewer ставит задачи Codex, Codex меняет repo и запускает команды, reviewer принимает результат только по фактическим diff/test artifacts.
