# MetaPlatform — жёсткий план после отката на `ebff531 db-only-project-storage`

## Главная цель

Не “почистить архитектуру”, не “красиво разложить файлы”, не “вынести код”.

Цель только одна:

- уменьшить центральность `ui/renderer/app.js`
- уменьшить центральность `ui/renderer/core/projectManager.js`
- сократить число runtime-слоёв
- сделать ownership состояния явным
- убрать дублирующие точки правды

---

## Жёсткие правила на весь план

### Что разрешено
Разрешены только шаги, которые одновременно дают хотя бы **два** эффекта из списка:

1. `app.js` знает меньше
2. `projectManager.js` знает меньше
3. у конкретного состояния появляется один явный владелец
4. уменьшается число ручных orchestration-переходов
5. boolean/null-семантика заменяется на явный outcome
6. UI начинает читать уже нормализованное состояние, а не собирать его сам

### Что запрещено
Запрещены шаги, которые:

- просто переименовывают
- просто переносят код между файлами
- создают новый `flow/coordinator/orchestrator`
- создают новый слой без owned state
- дробят код “для красоты”
- трогают несколько несвязанных проблем за один bounded task
- уменьшают размер файла, но не уменьшают его знания
- двигают сложность вбок, а не убирают её

### Критерий плохого шага
Шаг считается плохим, если после него:

- файлов стало больше
- зависимостей столько же
- старые центры знают почти всё то же самое
- появился новый thin-wrapper/service без своей истины
- стало труднее ответить, кто владеет `projectId`, `lockToken`, process state, close decision

---

# ЭТАП 1. Зафиксировать реальный ownership текущего состояния

## Цель
Не гадать, где проблема, а один раз зафиксировать реальную карту владения состоянием и решений.

## Обязательная область просмотра
Просмотреть и разметить роль как минимум этих файлов:

- `ui/renderer/app.js`
- `ui/renderer/core/projectManager.js`
- `ui/renderer/runtime/backendCommandSessionOrchestrator.js`
- `ui/renderer/runtime/processExecutionOrchestrator.js`
- `ui/renderer/runtime/processPollingLifecycle.js`
- `ui/renderer/runtime/backendProjectExportFlow.js`
- `ui/renderer/runtime/appCloseCoordinator.js`

## Для каждого файла выписать
1. Каким состоянием он владеет
2. Что он мутирует
3. Кто его вызывает
4. Какие решения он принимает
5. Какие знания он держит о:
   - UI
   - backend contract
   - session
   - tabs/documents
   - process
   - dialogs
   - close/save/open transitions

## Отдельно построить карту single-owner / multi-owner
Нужно явно выписать, кто владеет:

- `projectId`
- `lockToken`
- heartbeat lifecycle
- current backend project fact
- project snapshot
- open documents
- active tab
- dirty truth
- active process truth
- process polling
- process blocking signal
- close decision
- export input/output

## Отдельно отметить дубли
Обязательно зафиксировать:

- где одно и то же знание живёт в 2+ местах
- где один и тот же transition запускается из нескольких мест
- где `app.js` вручную сшивает сценарии
- где `projectManager.js` смешивает несвязанные зоны
- где UI вынужден трактовать неоднозначный runtime result

## Артефакт этапа
Сделать `current-runtime-ownership.md` со следующими разделами:

1. Владельцы состояния  
2. Места дублирования  
3. Перегруженные файлы  
4. Ручные orchestration-цепочки  
5. Неясные результаты операций  

## Критерий завершения
После этого документа должно быть возможно за 1–2 минуты объяснить:

- как открывается backend project
- кто удерживает lock
- как идёт heartbeat
- как работает save
- как работает close
- как запускается process
- кто решает blocked/allow

Если это невозможно — этап не завершён.

---

# ЭТАП 2. Зафиксировать не “идеальную архитектуру”, а жёсткие инварианты

## Цель
Не проектировать красивую систему заранее, а ввести правила, которые должен удовлетворять любой следующий рефакторинг.

## Сделать файл `runtime-invariants.md`

В нём зафиксировать как минимум такие инварианты:

### Инвариант 1
`projectId` имеет одного runtime-owner.

### Инвариант 2
`lockToken` имеет одного runtime-owner.

### Инвариант 3
Heartbeat lifecycle имеет одного owner и не управляется параллельно из нескольких мест.

### Инвариант 4
Правда о текущем backend project не размазана между `app.js`, `projectManager.js` и runtime helpers.

### Инвариант 5
`cancelled`, `blocked`, `failed`, `success` не смешиваются.

### Инвариант 6
Blocked close не должен маскироваться под обычный failure и не должен частично ломать session/workbench state.

### Инвариант 7
Truth о текущем процессе находится в одном owner.

### Инвариант 8
Blocking signal от активного процесса имеет один нормализованный источник.

### Инвариант 9
`app.js` не принимает доменные решения жизненного цикла проекта; он только собирает зависимости и связывает крупные узлы.

### Инвариант 10
Новый сервис/слой допустим только если он получает явное owned state и уменьшает знания старого центра.

## Что не делать на этапе
- не рисовать новую framework-архитектуру
- не делить заранее систему на много файлов
- не подгонять код под теоретическую схему

## Критерий завершения
Любую следующую задачу можно проверить вопросом:
- какой инвариант она улучшает?
- какой центр знания она уменьшает?

Если ответа нет — задачу не брать.

---

# ЭТАП 3. Определить минимальную target shape через зоны, но без фетиша к файлам

## Цель
Согласовать смысловые зоны ответственности, не превращая их сразу в обязательную файловую структуру.

## Целевые зоны
Ниже — не обязательные файлы, а смысловые владельцы ответственности.

### 1. ProjectSession
Отвечает только за:

- current backend project identity
- lock token
- heartbeat lifecycle
- open/close backend project session facts
- факт наличия открытого backend project

Не отвечает за:

- tabs
- documents
- save/save as semantics
- process output
- dialog interpretation

### 2. ProjectPersistence
Отвечает только за:

- save
- save as
- snapshot preparation
- export request preparation
- применение результата persistence-операций

Не отвечает за:

- heartbeat
- active process truth
- open project dialog flow
- tabs/documents ownership

### 3. WorkbenchState
Отвечает только за:

- open documents
- active tab
- document records
- dirty presentation dependencies

Не отвечает за:

- backend session
- lock lifecycle
- process lifecycle
- persistence contract

### 4. ProcessSession
Отвечает только за:

- active process truth
- polling lifecycle
- stop lifecycle
- process UI-ready state
- normalized blocking signal for runtime/UI

Не отвечает за:

- save/open/close semantics целиком
- document ownership
- backend project session ownership

### 5. DialogService
Отвечает только за:

- нормализацию результатов dialog-окон
- единый outcome `confirm/cancel/close/...`
- единый способ трактовать закрытие окна

Не отвечает за:

- project session
- save/open/close business logic
- process state

## Критерий завершения
Для любого runtime-вопроса можно сказать:
- это session
- это persistence
- это workbench
- это process
- это dialog normalization

Если задача не помещается ни в одну зону — границы определены плохо.

---

# ЭТАП 4. Первый реальный bounded task — один extraction, который одновременно бьёт по `app.js` и `projectManager.js`

## Цель
Не делать косметическую разгрузку одного файла. Сделать один разрез, который реально уменьшает оба центра знаний.

## Правило выбора первого extraction
Первым брать **не тот кусок, который выглядит красиво**, а тот, который:

1. имеет явный owned state
2. имеет меньше обратных зависимостей
3. уменьшает знания и `app.js`, и `projectManager.js`
4. убирает хотя бы одну ручную orchestration-цепочку
5. не требует создавать лес новых runtime-слоёв

## Возможные кандидаты
Смотреть в таком порядке:

### Кандидат A
Backend project session facts:
- current project id
- lock token
- session/open-close facts
- heartbeat ownership

### Кандидат B
Workbench/document state:
- open document records
- active document/tab
- часть dirty-related состояния
- document collection truth

### Кандидат C
Lifecycle outcome normalization around open/close/save, если именно это сейчас сильнее всего связывает `app.js` и `projectManager.js`

## Что обязательно сделать в рамках extraction
- вынести **owned state**, а не только helper-функции
- убрать соответствующее знание из `app.js`
- убрать соответствующее знание из `projectManager.js`
- сократить прямые cross-calls
- не оставлять старый файл формальным владельцем старой истины

## Что запрещено
- не делать thin-wrapper над старым кодом
- не выносить только “кусок логики без состояния”
- не плодить цепочку `app -> flow -> coordinator -> service -> manager`
- не резать по эстетике

## Критерий завершения
После шага должно быть одновременно верно:

- `app.js` знает меньше
- `projectManager.js` знает меньше
- есть новый реальный owner конкретного state slice
- хотя бы одна orchestration-цепочка стала короче

Если переехали только строки — этап провален.

---

# ЭТАП 5. Сразу после первого extraction — унифицировать lifecycle outcomes

## Цель
Перестать жить на boolean/null-семантике там, где есть реальные разные исходы операции.

## Сначала покрыть только главный путь
Не весь проект. Только:

- open project
- close project
- save project

Потом при необходимости:
- save as
- export
- import

## Для каждой операции выписать явные исходы
Минимум:

- `success`
- `cancelled`
- `blocked`
- `failed`
- `malformed`

Где нужно — уточнять `code`:
- `lock-lost`
- `active-process-busy`
- `missing-data`
- `invalid-project-id`
- и т.д.

## Ввести единый outcome shape
Например:

- `status`
- `code`
- `message`
- `details`

Форма может быть другой, но смысл должен быть один:
UI и runtime всегда понимают разницу между:
- отменено
- заблокировано
- сломалось
- успешно
- пришёл некорректный результат

## Что запрещено
- не строить общий framework outcome engine
- не растягивать это на весь repo
- не менять backend API без реальной необходимости
- не маскировать `blocked` и `cancelled` под `false`

## Критерий завершения
Для open/save/close по коду можно явно ответить, что произошло, без догадок по `true/false/null`.

---

# ЭТАП 6. Собрать process truth и blocking contract в одном владельце

## Цель
Сделать одно место истины не только для process state, но и для сигнала “этот процесс сейчас блокирует lifecycle-операции или нет”.

## Разобрать
- `processExecutionOrchestrator.js`
- `processPollingLifecycle.js`
- process-related код в `app.js`
- process panel integration
- места, где active process влияет на open/close/save/export/import

## Нужно явно определить
1. кто инициирует запуск
2. кто владеет active process truth
3. кто владеет polling lifecycle
4. кто владеет stop lifecycle
5. кто формирует UI-ready process view state
6. кто формирует normalized blocking signal

## Результат
Должен появиться один owner, который даёт:

- truth о текущем процессе
- truth о доступности stop
- truth о blocking/non-blocking
- нормализованное состояние для UI

UI не должен сам вручную склеивать эти данные из трёх мест.

## Что запрещено
- не добавлять ещё один process wrapper
- не дублировать truth между panel surface и runtime helper
- не держать отдельные local app-level flags о процессе
- не разносить process truth и process blocking в разные центры

## Критерий завершения
На вопрос “где правда о текущем процессе и его blocking effect?” можно указать один runtime-owner.

---

# ЭТАП 7. Только после стабилизации центра — второй responsibility slice из `projectManager.js`

## Цель
После первого extraction и outcomes/process cleanup сделать второй осмысленный разрез `projectManager.js`, если он всё ещё остаётся перегруженным.

## Возможные направления
В зависимости от результатов предыдущих шагов:

- backend session slice, если он не был вынесен первым
- workbench/document state slice
- persistence-related slice
- dirty/snapshot-related slice, если это реально единая зона ответственности

## Правило
Не дробить `projectManager.js` “до победы”.  
Каждый следующий разрез допустим только если:

- у него есть явный owned state
- он уменьшает знания текущего центра
- он не создаёт новую glue-layer архитектуру

## Критерий завершения
`projectManager.js` перестаёт быть системным центром и становится владельцем только ограниченной понятной зоны.

---

# ЭТАП 8. Только потом проверить config-слой

## Цель
Понять, мешает ли `ui/config/ui-config.js` после упрощения runtime-центра, а не до него.

## Что делать
Разделить содержимое на:

- стабильные константы
- тексты/labels
- иконки
- DOM ids
- runtime semantics disguised as config

Оставить в config только то, что реально является данными, а не поведением.

## Важно
Этот этап **не обязателен**.  
Если после упрощения runtime-центра config уже не мешает — его не трогать.

## Что запрещено
- не превращать это в отдельный refactor ради чистоты
- не дробить config на россыпь маленьких файлов
- не трогать runtime behavior под видом “чистки config”

---

# ЭТАП 9. Только после стабилизации ядра — вторичный техдолг

## Цель
Не подменить архитектурную работу локальными красивостями.

## Смотреть только после этапов 1–8
Потом уже можно отдельно оценивать:

- generator-related debt
- snapshot/document identity debt
- naming cleanup
- вспомогательные helper cleanup
- локальные места, где код объективно кривой, но не влияет на ownership

## Правило
Вторичный техдолг разрешён только если ядро уже стало проще и ownership стабилизирован.

---

# ЭТАП 10. Шаблон проверки после каждого bounded task

## Архитектурные вопросы
После каждого шага проверять:

1. `app.js` знает меньше?
2. `projectManager.js` знает меньше?
3. число точек правды уменьшилось?
4. ownership стал яснее?
5. новый узел реально владеет состоянием?
6. хотя бы одна orchestration-цепочка стала короче?
7. `blocked/cancelled/failed/success` различаются лучше?

## Практические вопросы
После каждого шага проверять:

- open работает?
- save работает?
- close работает?
- process start работает?
- process stop работает?
- active-process blocking не сломан?
- lock/heartbeat не сломан?
- blocked close/release не ломает state?

## Сигнал немедленного отката шага
Если получилось:

- больше файлов при той же сложности
- тот же объём знаний в старых центрах
- новый слой без owned state
- больше cross-calls
- сложнее объяснить жизненный цикл

значит шаг неудачный.

---

# Рекомендуемая последовательность реальных задач

## Задача 1
Сделать `current-runtime-ownership.md`.

## Задача 2
Сделать `runtime-invariants.md`.

## Задача 3
Зафиксировать target shape как смысловые зоны, не как обязательные файлы.

## Задача 4
Сделать один bounded extraction, который одновременно уменьшает знания `app.js` и `projectManager.js`.

## Задача 5
Унифицировать outcomes для open/close/save.

## Задача 6
Собрать process truth + blocking contract в одном owner.

## Задача 7
Сделать второй осмысленный responsibility slice из `projectManager.js`, только если он всё ещё перегружен.

## Задача 8
Проверить config-слой только если он всё ещё мешает после упрощения ядра.

## Задача 9
Только потом идти во вторичный техдолг.

---

# Короткая главная мысль

Мы не делаем новый виток “сначала придумали сложную архитектуру, потом её чистим”.

Мы берём `ebff531` как рабочую базу и дальше двигаемся только так:

1. сначала фиксируем ownership и инварианты
2. потом делаем один bounded extraction по реальной границе
3. сразу делаем outcomes явными
4. потом собираем process truth в один центр
5. не двигаем сложность вбок
6. не создаём новых уровней без owned state
7. не трогаем вторичное, пока не упростили ядро
