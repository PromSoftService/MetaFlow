# ARCHITECTURE EXCEPTIONS REGISTRY — METAPLATFORM

Краткий реестр принятых исключений, техдолга и правил классификации проблем.

Документ нужен, чтобы не поднимать повторно уже принятые решения как дефекты и не раздувать scope текущих задач.

---

## 1. Что явно не считать дефектом

### 1.1. Частичная реализация MetaLab / MetaView

Placeholder-level реализация MetaLab/MetaView допустима, пока модули архитектурно присутствуют и это не ломает текущий scope.

### 1.2. Рекурсивное сканирование модульных папок

Допустимо как задел на будущее, если не создаёт реальных конфликтов save/discovery semantics.

### 1.3. Ручной whitelist export helper

`export_project_to_txt.py` с ручным whitelist — сознательное ограничение, не баг.

### 1.4. Export helper в root

`export_project_to_txt.py` в root — принятое текущее состояние. Не предлагать перенос в `tools/` без отдельного решения и отдельного scope.

### 1.5. Не всякий literal является проблемой

Локальные технические микролитералы допустимы, если не участвуют в contract semantics и не создают новый source of truth.

### 1.6. Backend lock/process semantics

Не считать implementation noise:
- backend project lock ownership;
- heartbeat/session lifecycle;
- lost lock handling;
- active process blocking;
- блокировку close/save/switch/open/export/import/delete transitions по backend conditions.

Это текущая operational semantics платформы.

### 1.7. Briefing docs не правятся автоматически

`01_project_doctrine.md`, `02_codex_execution.md`, `03_architecture_exceptions.md` не нужно менять в каждой итерации.

Их правка нужна только при реальном расхождении с проектом, execution rules или architecture exceptions.

### 1.8. Артефакты цикла не являются repo diff

`reviewer_response.json`, `codex_task.md`, `git_diff.patch`, `tests_summary.json`, `test_results.txt`, `codex_trace.jsonl` и похожие orchestration artifacts не должны попадать в repo или `export_project_to_txt.py`.

### 1.9. Manual QA checklist

Manual QA checklist — пользовательский документ/инструкция для ручной проверки UI.

Он не означает, что reviewer/Codex должны проверять UI визуально. Ручная проверка UI выполняется пользователем; reviewer/Codex отвечают за repo changes, tests, docs и фактические artifacts в рамках scope.

---

## 2. Что не чинить без отдельного scope

Не превращать конкретную задачу в широкий cleanup.

Без отдельного scope не добавлять:
- unrelated core refactor;
- общий docs rewrite;
- layout restructuring;
- UX cleanup “заодно”;
- тотальную русификацию всего UI;
- новую browser E2E инфраструктуру;
- packaging/release discipline;
- production migration framework.

Если найден большой хвост техдолга — зафиксировать open item, а не расширять текущую задачу.

---

## 3. Отложенный техдолг

Помнить, но не чинить по умолчанию:

- UX/diagnostics для повреждённых документов;
- packaging/release/reproducibility;
- полнота архитектурного тестового покрытия;
- единая русификация UI за пределами затронутых flows;
- browser/visual E2E harness, если будет отдельное решение.

---

## 4. Не поднимать повторно как замечание само по себе

Не считать проблемой само по себе:

- web-only курс;
- модульную природу платформы;
- GUID-only identity;
- ручной whitelist export helper;
- `export_project_to_txt.py` в root;
- placeholder MetaLab/MetaView;
- допустимость recursive scan-layer;
- backend lock/process lifecycle semantics;
- briefing docs вне export whitelist;
- orchestration artifacts вне source repo;
- то, что reviewer принимает результат по diff/test artifacts, а Codex является исполнителем изменений и команд.

---

## 5. Классификация проблем

Перед задачей или аудитом разделять:

1. принятое исключение;
2. отложенный техдолг;
3. реальный дефект в scope;
4. подтверждённое ограничение среды запуска.

Не называть assert/error mismatch ограничением среды.

Не называть отсутствие npm script, рассинхрон README/package.json/helper/test expectation ограничением среды без проверки.

Ограничение среды подтверждается конкретной командой, stdout/stderr и объяснением.

---

## 6. Test commands

Не принимать работу без фактических команд, если scope требует проверки.

Запрещены long-running foreground/watch/server commands без bounded wrapper:

- `python -m uvicorn ...`;
- `npm run dev`;
- `vite`;
- `electron .`;
- аналогичные процессы.

Базовый явный набор для code/config/helper changes:

```powershell
npm.cmd test
npm.cmd run test:integration
npm.cmd run test:backend
```

Не использовать `test:all` как обязательную проверку.

Если задача чисто текстовая и runtime/product behavior не затронут, полный прогон может быть пропущен только с явным обоснованием. Helper/export изменения проверяются отдельно.

---

## 7. Ручная проверка пользователем

Если пользователь может проверить сценарий в UI/функционале приложения самостоятельно:

- не ставить reviewer/Codex task только на такую проверку;
- дать пользователю checklist;
- после найденного фактического бага ставить точечную задачу на исправление.

Codex CLI не должен “смотреть UI глазами”. Browser E2E harness не добавлять без отдельного scope.

---

## 8. Короткая суть

Документ удерживает reviewer от повторного спора по принятым исключениям и от лишнего scope.

Результат принимать только по фактическим artifacts: diff, changed files, logs, stdout/stderr, test summary.

Ручной UI smoke выполняет пользователь; Codex получает задачи на repo changes, tests, helper/docs или конкретные найденные баги.
