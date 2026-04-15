# PROJECT DOCTRINE — METAPLATFORM

Актуальная консолидированная версия для передачи reviewer в первой итерации вместе с task.md.

Документ фиксирует:
- постоянные проектные правила;
- текущее архитектурное состояние MetaPlatform;
- рабочую механику цикла reviewer → Codex;
- принятые архитектурные инварианты;
- границы допустимых изменений на уровне проекта.

Документ должен оставаться устойчивым к дальнейшим перемещениям репозитория и не должен зависеть от одной локальной задачи.

---

## 0. РОЛИ И МЕХАНИКА ЦИКЛА REVIEWER → CODEX

### 0.1. Роли
- User формулирует задачу и получает итоговую оценку результата.
- Reviewer получает task.md и briefing-документы, ставит Codex конкретные repo-задачи и оценивает результат.
- Codex — единственный исполнитель изменений в локальном репозитории.
- Codex запускает команды проверки и возвращает фактические результаты.
- Reviewer не должен принимать работу без подтверждения, что Codex реально выполнил команды и предоставил вывод.

### 0.2. Каналы, которые reviewer получает в цикле
Reviewer может получать:
- основной task.md;
- briefing-документы первой итерации;
- technical channel с diff, changed files и результатами тестов предыдущей итерации;
- model channel со structured summary от Codex;
- ответ пользователя на вопрос reviewer;
- вложения пользователя для следующей итерации.

Reviewer должен использовать эти данные как вход для следующей итерации, но не расширять scope без необходимости.

### 0.3. Артефакты итерации, на которые можно опираться
Типовые артефакты итерации:
- `reviewer_request.txt` — полный запрос reviewer;
- `reviewer_response.json` — JSON-ответ reviewer;
- `codex_task.md` — задача, которую reviewer передал Codex;
- `codex_trace.jsonl` — stdout / JSONL-трасса Codex;
- `codex_stderr.txt` — stderr Codex;
- `codex_summary.json` — structured summary от Codex;
- `git_diff.patch` — полный diff после Codex;
- `git_diff_stat.txt` — статистика diff;
- `changed_files.txt` — список изменённых файлов;
- `test_results.txt` — полный лог команд проверки;
- `tests_summary.json` — краткий JSON по результатам проверок.

Reviewer должен смотреть не только текстовые заявления Codex, но и фактические артефакты: diff, список файлов, вывод команд, summary тестов.

### 0.4. Статусы reviewer
Reviewer должен возвращать один из рабочих статусов:
- `continue` — нужна следующая итерация Codex;
- `done` — задача закрыта;
- `question` — нужен ответ пользователя;
- `escalate` — нужен ручной разбор или решение пользователя.

`done` допустим только когда scope выполнен, diff проверен, команды действительно запускались Codex и результат команд понятен.

---

## 1. БАЗОВОЕ НАПРАВЛЕНИЕ ПРОЕКТА

### 1.1. Что такое MetaPlatform
- MetaPlatform — это модульная инженерная платформа / workbench.
- Это не “обвязка вокруг MetaGen”.
- Платформа должна сохранять самостоятельный core/workbench слой и поддержку нескольких модулей.

### 1.2. Модульность сохраняется
На архитектурном уровне сохраняются модули:
- MetaGen;
- MetaLab;
- MetaView.

Даже если MetaLab и MetaView пока частично реализованы, архитектурно они считаются частью платформы.

### 1.3. Web-only направление зафиксировано
- Electron из целевой архитектуры убирается полностью.
- Целевой UI — web-based IDE.
- Runtime backend существует отдельно от UI.
- Desktop-shell compatibility и packaging desktop app не являются текущим архитектурным приоритетом.

---

## 2. ТЕКУЩЕЕ АРХИТЕКТУРНОЕ СОСТОЯНИЕ РЕПО

### 2.1. Фактический рабочий layout
Текущий рабочий layout репозитория строится вокруг зон:
- `ui/` — web UI;
- `rtb/` — runtime backend;
- `shared/` — shared config / contracts;
- `tools/` — прикладные helper/tools, если они уже реально используются.

Дополнительные repo-level зоны допустимы, если они реально используются текущим проектом и отражены в коде, тестах или документации.

### 2.2. Export helper остаётся в root
- `export_project_to_txt.py` остаётся в корне репозитория.
- Нахождение этого helper-скрипта в root — часть текущего состояния проекта.
- Не навязывать перенос helper-а в `tools/` без отдельного решения и отдельного scope.

### 2.3. Shared layer допустим и нужен
- `shared/` используется как общий слой конфигов и контрактов.
- Если literal, id, token, reason, status, endpoint, prefix, folder name или иной semantic value реально общий для нескольких слоёв, его допустимо и желательно держать в `shared/` или в существующем config/constants слое соответствующего уровня.

---

## 3. IDENTITY И RUNTIME-ПРАВИЛА

### 3.1. Каноническая identity документа
- Единственная каноническая внутренняя identity документа = GUID.
- Внутренние runtime-операции должны строиться только на GUID.

### 3.2. Что НЕ является identity
Не являются identity:
- document name;
- file name;
- path;
- tree label;
- tab title.

Это display/storage/presentation attributes, но не identity.

### 3.3. Последствия
- rename не должен менять identity документа;
- path change не должен менять identity документа;
- file remap не должен превращаться в смену identity;
- lookup open/active/update/delete/select должен опираться на GUID.

---

## 4. BACKEND WORKSPACE И OPERATIONAL SEMANTICS

### 4.1. Backend workspace — основной режим работы
- Backend workspace является основным operating mode платформы.
- Операции открытия, создания, сохранения, закрытия, импорта, экспорта и удаления backend-проектов считаются частью нормальной архитектуры платформы, а не временным обходным сценарием.

### 4.2. Lock / process constraints обязательны
UI и runtime-слой обязаны уважать:
- ограничения backend lock lifecycle;
- ограничения активного процесса;
- потерю lock как отдельное семантическое состояние;
- heartbeat/session lifecycle.

### 4.3. Close / save / switch flows обязаны учитывать backend lifecycle
Переходы close/save/switch/open/export/import/delete не должны игнорировать:
- release lock semantics;
- active process blocking;
- lost lock handling;
- heartbeat/session ownership.

Это не побочная реализация, а часть текущей архитектуры проекта.

---

## 5. IMPORT / EXPORT CONTRACT

### 5.1. Внешний формат сохраняется
Внешний import/export формат проекта должен сохраняться как YAML ZIP transport:
- корневой `project.yaml`;
- YAML-документы по модульным папкам `metagen/`, `metalab/`, `metaview/`;
- экспортный архив для пользователя — `MetaPlatformProject.zip`.

### 5.2. ZIP — транспорт, не canonical storage
- При импорте ZIP используется как временный транспорт: данные читаются, записываются в backend storage, ZIP не становится canonical storage.
- При экспорте пользователь получает архив во внешнем YAML-формате.
- Внутренняя backend DB-модель не должна протекать во внешний export archive.

---

## 6. МАГИЧЕСКИЕ СТРОКИ, ЧИСЛА И CONFIG/CONSTANTS СЛОЙ

### 6.1. Новые semantic values централизовать
Не добавлять новые magic strings / magic numbers без необходимости.
Если значение участвует в contract semantics, UI state, command id, error code, source id, endpoint, filename, folder name, status, reason, timeout или DOM id, оно должно быть добавлено в существующий config/constants слой соответствующего уровня.

### 6.2. Локальные literals допустимы только точечно
Одноразовое локальное сообщение или чисто технический микролитерал допустимы, если они не создают новый source of truth и не участвуют в контракте между слоями.

Reviewer должен проверять, что Codex не разбрасывает новые semantic values по коду.

---

## 7. ТЕСТЫ И КОМАНДЫ ПРОВЕРКИ

### 7.1. Полный прогон обязателен
В каждой задаче reviewer должен требовать, чтобы Codex прогнал полный набор тестов по фактическому проекту, если только задача явно не является чисто текстовой и это обосновано.

Если команды падают, reviewer должен различить:
- реальный дефект кода/тестов/документации;
- подтверждённое ограничение среды запуска.

Ограничение среды нельзя утверждать без конкретного stdout/stderr и команды, на которой это подтверждено.

### 7.2. Long-running команды нельзя использовать как обычные проверки
В extra_test_commands нельзя добавлять долгоживущие foreground/watch/server-команды без bounded wrapper, например:
- `python -m uvicorn ...`;
- `npm run dev`;
- `vite`;
- `electron .`;
- любые аналогичные процессы, которые сами не завершаются.

Если нужно проверить startup, команда должна быть ограниченной по времени или оформленной как bounded smoke check.

---

## 8. EXPORT HELPER

### 8.1. export_project_to_txt.py нужно проверять при изменениях repo layout
При задачах, которые меняют layout, добавляют/удаляют файлы или меняют набор файлов проекта, reviewer должен требовать у Codex проверить и при необходимости актуализировать `export_project_to_txt.py`.

### 8.2. Что helper не должен экспортировать
`export_project_to_txt.py` не должен возвращать:
- иконки;
- demo project;
- top-level tests;
- package-lock;
- cache/build artifacts;
- briefing docs, если они не являются частью repo source whitelist.

---

## 9. КОРОТКАЯ ФИНАЛЬНАЯ ФОРМУЛИРОВКА

MetaPlatform развивается как web-only модульная инженерная платформа с фактическим layout вокруг `ui / rtb / shared`.
Identity документов строится только на GUID.
Backend workspace является основным operating mode.
Close/save/switch/open/export/import/delete flows обязаны учитывать backend lock/process lifecycle.
Внешний import/export формат сохраняется как YAML ZIP transport.
`export_project_to_txt.py` остаётся в root и должен поддерживаться в актуальном состоянии.
Reviewer ставит задачи Codex, Codex меняет repo и запускает команды, reviewer принимает результат только по фактическим артефактам diff/test output.
