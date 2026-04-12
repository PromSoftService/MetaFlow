# PROJECT DOCTRINE — METAPLATFORM

Актуальная консолидированная версия для передачи reviewer в первой итерации и в любых следующих задачах.

Этот документ фиксирует:
- постоянные проектные правила;
- текущее архитектурное состояние проекта;
- принятые архитектурные инварианты;
- границы допустимых изменений на уровне проекта.

Документ должен оставаться устойчивым к дальнейшим перемещениям репозитория и не должен зависеть от одной конкретной локальной задачи.

---

## 0. БАЗОВОЕ НАПРАВЛЕНИЕ ПРОЕКТА

### 0.1. Что такое MetaPlatform
- MetaPlatform — это модульная инженерная платформа / workbench.
- Это не “обвязка вокруг MetaGen”.
- Платформа должна сохранять самостоятельный core/workbench слой и поддержку нескольких модулей.

### 0.2. Модульность сохраняется
На архитектурном уровне сохраняются модули:
- MetaGen
- MetaLab
- MetaView

Даже если MetaLab и MetaView пока частично реализованы, архитектурно они считаются частью платформы.

### 0.3. Web-only направление зафиксировано
- Electron из целевой архитектуры убирается полностью.
- Целевой UI — web-based IDE.
- Runtime backend существует отдельно от UI.
- Desktop-shell compatibility и packaging desktop app не являются текущим архитектурным приоритетом.

---

## 1. ТЕКУЩЕЕ АРХИТЕКТУРНОЕ СОСТОЯНИЕ РЕПО

### 1.1. Фактический рабочий layout
Текущий рабочий layout репозитория строится вокруг зон:
- `ui/`
- `rtb/`
- `shared/`

Дополнительные repo-level зоны допустимы, если они реально используются текущим проектом и отражены в коде и документации.

### 1.2. Export helper остаётся в root
- `export_project_to_txt.py` остаётся в корне репозитория.
- Нахождение этого helper-скрипта в root — часть текущего состояния проекта.
- Для этого helper-а не нужно навязывать перенос в `tools/` без отдельного решения и отдельного scope.

### 1.3. Shared layer допустим и нужен
- `shared/` используется как общий слой конфигов и контрактов.
- Если literal, id, token, reason, status, endpoint, prefix, folder name или иной semantic value реально общий для нескольких слоёв, его допустимо и желательно держать в `shared/` или в существующем config/constants слое соответствующего уровня.

---

## 3. IDENTITY И RUNTIME-ПРАВИЛА

### 3.1. Каноническая identity документа
- Единственная каноническая внутренняя identity документа = GUID.
- Внутренние runtime-операции должны строиться только на GUID.

### 3.2. Что НЕ является identity
Не являются identity:
- document name
- file name
- path
- tree label
- tab title

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
Переходы close/save/switch/open/export не должны игнорировать:
- release lock semantics;
- active process blocking;
- lost lock handling;
- heartbeat/session ownership.

Это не побочная реализация, а часть текущей архитектуры проекта.

---

## 6. КОРОТКАЯ ФИНАЛЬНАЯ ФОРМУЛИРОВКА

MetaPlatform развивается как web-only модульная инженерная платформа с фактическим рабочим layout вокруг `ui / rtb / shared`.
Identity документов строится только на GUID.
Backend workspace является основным operating mode.
Close/save/switch flows обязаны учитывать backend lock/process lifecycle.
`export_project_to_txt.py` остаётся в root как часть текущего состояния проекта.
