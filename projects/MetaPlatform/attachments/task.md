# Task: MetaGen params table — реализовать custom undo/redo только для params, с params-only hotkey interception и тестовыми кнопками в top panel, не затрагивая native edit behavior остальных контролов

Этот документ является task для reviewer.
Он применяется вместе с обязательными reference-ограничениями:
- 01_project_doctrine.md
- 02_codex_execution_standard.md
- 03_architecture_exceptions.md
- актуальный dump проекта из attachments

## 0. Главная цель

Нужно реализовать undo/redo только для таблицы параметров MetaGen.

Это НЕ общий undo/redo framework для всей платформы.
Это НЕ undo/redo для data / instances / code editor.
Это НЕ Edit menu.
Это НЕ copy/cut/paste.
Это НЕ global clipboard router.

Это первый целевой контур:
- custom undo/redo только для MetaGen params
- 2 тестовые кнопки в верхней панели приложения
- params-only keyboard interception для undo/redo shortcuts
- нативное edit behavior всех остальных контролов оставить как есть

## 1. Ключевое архитектурное правило этого этапа

На этом этапе все нативные edit-команды должны остаться нативными для всех контролов, КРОМЕ focused MetaGen params.

То есть:
- обычные нативные текстовые контролы — не трогать
- другие Univer-таблицы (`data`, `instances`) — не трогать
- будущий Monaco — не трогать
- другие модули (`MetaView`, `MetaLab`) — не трогать

Единственный special-case:
- если активный target = focused MetaGen params table,
  тогда undo/redo должны идти в custom params history,
  а не в native undo/redo путь.

Это правило нужно заложить уже сейчас.
Но без построения общего edit-framework для всей платформы.

## 2. Что является проблемой сейчас

Сейчас params table отличается от остальных таблиц тем, что поверх табличного runtime на него навешан auto-style слой.

В текущем params auto-style config `undo` и `redo` уже входят в `fullRefreshCommandIdIncludes`.
Это означает, что built-in workbook undo/redo конфликтует с params auto-style lifecycle.

Следовательно, для params нельзя просто оставить native Univer undo/redo как рабочий механизм feature.

## 3. Целевая семантика результата

После реализации должно быть истинно следующее:

### 3.1. Undo/redo работает только для params
Работает:
- MetaGen params

Не работает и не внедряется на этом этапе:
- MetaGen data
- MetaGen instances
- code editor
- другие модули
- app-wide edit framework

### 3.2. Source of truth для params undo/redo
История params должна храниться как собственная semantic history chain приложения, а не как workbook-native undo stack.

Нужно использовать semantic snapshots params документа:
- format: header-plus-rows
- header: [...]
- rows: [...]

Именно эти snapshots являются source of truth для undo/redo params.

### 3.3. History model
История должна иметь форму:
- past[]
- present
- future[]

Правила:
1. При открытии editor создаётся initial present snapshot из текущего params payload.
2. Новый шаг добавляется только при реальном semantic diff.
3. Одинаковые semantic snapshots не должны дублироваться в истории.
4. После undo новое изменение очищает future[].
5. Должен быть max depth через config.

### 3.4. Replay semantics
Undo/redo params не должен использовать native workbook undo()/redo().
Вместо этого:
1. выбирается snapshot из custom history;
2. snapshot программно применяется обратно в params sheet;
3. визуальное состояние params table снова приводится в корректный вид;
4. replay не создаёт новый history step.

### 3.5. Auto-style semantics
Auto-style params остаётся рабочим, но не является history source.

Требования:
- auto-style не создаёт отдельные undo/redo шаги
- replay undo/redo не зацикливает auto-style
- после replay params table визуально выглядит корректно
- ordinary auto-style path для обычных изменений остаётся рабочим

### 3.6. Top panel test buttons
В верхней панели приложения должны появиться 2 тестовые кнопки:
- Undo
- Redo

Эти кнопки:
- работают только для active MetaGen params context
- disabled во всех остальных случаях
- вызывают custom params undo/redo
- не запускают native undo/redo других контролов

### 3.7. Params-only hotkey interception
На этом этапе уже нужно предусмотреть keyboard routing для undo/redo shortcuts, но только как узкий special-case для focused MetaGen params.

Требование:
- если фокус находится в MetaGen params, `undo/redo` hotkeys не должны уходить в native path
- вместо этого они должны вызывать custom params undo/redo
- если фокус не в MetaGen params, код этого этапа не должен вмешиваться, всё остаётся нативным

Это не означает внедрение полного global edit framework.
Это только узкий carve-out для params.

## 4. Что входит в scope

В scope этой задачи входит только следующее:

1. Реализовать custom semantic history controller только для params.
2. Реализовать replay snapshot -> params sheet.
3. Развести history и params auto-style.
4. Добавить 2 тестовые кнопки в top panel.
5. Добавить params-only interception для undo/redo hotkeys.
6. Обновить touched config/constants.
7. Обновить tests.
8. Обновить helper whitelist, если появятся новые файлы.

## 5. Что НЕ входит в scope

Следующее запрещено и не входит в эту задачу:

1. Не делать custom undo/redo для data.
2. Не делать custom undo/redo для instances.
3. Не делать custom undo/redo для code editor.
4. Не внедрять Edit menu.
5. Не внедрять copy/cut/paste.
6. Не строить общий edit-router для всех модулей.
7. Не менять native edit behavior остальных контролов.
8. Не трогать IPC/preload/main contracts шире, чем это абсолютно необходимо.
9. Не делать общий refactor editor framework.
10. Не отключать целиком params auto-style.
11. Не ломать dirty tracking.
12. Не менять schema/persistence semantics без прямой необходимости.
13. Не запускать export_project_to_txt.py.
14. Не генерировать dump.

## 6. Что reviewer обязан проверить в коде в первую очередь

Перед формированием codex_task_md reviewer обязан проверить:

### 6.1. Params sheet runtime
Проверить:
- renderer/modules/metagen/tables/createMetaGenParamsSheet.js

Нужно выяснить:
- где создаётся params runtime
- где пишется initial document в sheet
- где извлекается semantic snapshot
- где подключается auto-style
- где проще всего ввести replay метода обратно в sheet

### 6.2. Params contract
Проверить:
- renderer/modules/metagen/metagenParamsContract.js

Нужно зафиксировать:
- какой exact normalized semantic shape используется для params
- какой helper является правильным source-of-truth для сравнения snapshots
- как считается required dimensions
- как не потерять строки beyond bootstrap

### 6.3. Params auto-style engine
Проверить:
- renderer/modules/metagen/tables/metaGenParamsTableAutoStyle.js
- renderer/modules/metagen/tables/metaGenParamsTableAutoStyleInterpretation.js
- config в renderer/modules/metagen/metagenConfig.js

Нужно определить:
- где именно undo/redo входят в auto-style refresh flow
- как не зациклить history/replay/auto-style
- нужно ли убрать `undo` и `redo` из native command-based auto-style refresh path после перехода на custom params history
- как после replay корректно переапплаить автостиль уже по новому целевому состоянию

Reviewer должен сам принять один точный policy и потом зафиксировать его для Codex.

### 6.4. MetaGen editor integration
Проверить:
- renderer/editors/metagen/createMetaGenEditor.js

Нужно найти:
- где создаётся paramsTable
- где сидит dirty tracking на workbook.onCommandExecuted(...)
- где есть active table context logic
- где есть finishActiveTableEditing()
- где лучше встроить params history controller
- где лучше встроить params-only hotkey interception
- где хранить runtime API, который смогут вызывать top-panel buttons

### 6.5. Top panel app shell
Проверить:
- renderer/index.html
- renderer/app.js
- renderer/ui/applyStaticText.js
- renderer/ui/workbenchShell.js
- renderer/ui/createWorkbenchTabs.js
- renderer/ui/editorContextLifecycle.js

Нужно определить:
- как добавить 2 кнопки в top panel без лишнего platform-wide refactor
- как получить active editor instance
- как безопасно маршрутизировать top button click в active MetaGen params runtime
- как держать disabled state

### 6.6. Existing menu/hotkey infrastructure
Проверить:
- main.js
- текущий `before-input-event`
- текущую menu action wiring
- текущий renderer-side menu action handling

Нужно определить:
- как сделать params-only undo/redo shortcut interception уже сейчас
- при этом не внедрять Edit menu и не менять native behavior вне params

Reviewer должен выбрать один точный путь.
Предпочтительно — локальный params-only interception path с минимальным scope.
Codex не должен выбирать это сам.

### 6.7. Tests
Проверить:
- tests/metagenParamsSheetLifecycle.test.js
- tests/metagenParamsContract.test.js
- tests/metagenSheetSnapshot.test.js
- tests/finalizeEditingOnContextLeave.test.js
- tests/editorContextLifecycle.test.js
- tests/tabEditLifecycle.test.js
- tests/configWiring.integration.test.js

### 6.8. Helper scripts
Проверить:
- create_project_structure.py
- export_project_to_txt.py

## 7. Предпочтительная архитектура реализации

Reviewer может отклониться только если найдёт доказательно более локальный и безопасный путь.
Но перед передачей задачи Codex reviewer обязан выбрать один exact implementation path.

### Предпочтительный путь

#### A. Отдельный controller истории только для params
Создать dedicated helper/controller для params history.

Его ответственность:
- хранить past/present/future
- push snapshot
- canUndo/canRedo
- undo
- redo
- reset(initialSnapshot)
- branch cut
- max depth trimming

### B. Отдельный apply path для params snapshot
Выделить отдельный apply path:
- либо как новый helper
- либо как runtime method внутри params sheet
- но с одной чёткой реализацией

Требования:
- применяет normalized params document обратно в sheet
- не зависит от hard upper bound 100
- не теряет content beyond bootstrap
- не использует native workbook undo/redo
- может быть вызван из custom history replay

### C. Replay guard
Нужен явный suppress/history-replay guard.

Во время replay:
- history capture должен быть выключен
- обычный dirty/history listener не должен пушить новый шаг
- ordinary mutation processing не должен воспринимать replay как новое ручное изменение

Reviewer должен выбрать один guard mechanism и потом жёстко зафиксировать его в codex_task_md.

### D. Auto-style integration
После replay автостиль должен приводить params table в корректный визуальный вид.
Но auto-style не должен формировать history entry и не должен триггерить recursion.

Reviewer должен зафиксировать один конкретный порядок:
1. finish active edit
2. apply semantic snapshot
3. auto-style refresh / restyle path
4. release replay guard
5. update dirty/button state

### E. Params-only app-level action path
Нужно уже сейчас заложить узкий app-level action path для Undo/Redo тестовых кнопок.

Но только для params.
Не общий framework для всего edit menu.

Требование:
- top buttons не должны напрямую лезть во внутренние поля workbook
- они должны вызывать editor/runtime API уровня params undo/redo
- этот же narrow API потом можно будет использовать для будущего menu/hotkey special-case params

### F. Params-only hotkey interception
Нужно уже сейчас предусмотреть special-case interception для:
- Ctrl/Cmd+Z
- Ctrl/Cmd+Shift+Z
- если reviewer сочтёт нужным для платформенной политики — Ctrl+Y как alias redo на Windows

Но только когда active target = focused MetaGen params.

Во всех остальных случаях:
- не intercept
- не override
- native behavior остаётся нетронутым

Reviewer обязан выбрать один конкретный interception layer:
- либо renderer-local params editor capture
- либо другой локальный путь
Но без построения общего global edit framework.
Codex не должен решать это сам.

## 8. Что reviewer должен потребовать от Codex

Reviewer должен написать codex_task_md так, чтобы Codex сделал ровно следующее.

### 8.1. Реализовать custom semantic history только для params
Нужно:
1. Выделить semantic snapshot source для params.
2. Создать params history controller.
3. Поддержать:
   - initial present
   - push on real diff only
   - undo
   - redo
   - branch cut
   - max depth

### 8.2. Реализовать apply/replay path
Нужно:
1. Добавить отдельный apply path для params snapshot.
2. Не вызывать native workbook undo()/redo().
3. Не терять semantic shape params payload.
4. Не зависеть логически от 100 как upper bound.
5. Не создавать новый history entry при replay.

### 8.3. Развести auto-style и history
Нужно:
1. Сохранить params auto-style.
2. Не позволить auto-style стать history source.
3. Исключить recursion на replay.
4. Явно зафиксировать порядок replay + restyle.
5. Если reviewer выбрал убрать native `undo/redo` из command-based auto-style refresh списка — сделать это.
6. Не ломать ordinary params auto-style path для обычных изменений.

### 8.4. Добавить test buttons в top panel
Нужно:
1. Добавить две тестовые кнопки в верхнюю панель:
   - Undo
   - Redo
2. Подключить их только к active MetaGen params undo/redo.
3. Держать disabled state, если:
   - нет активного MetaGen editor
   - нет focused params context
   - history action недоступна

### 8.5. Добавить params-only hotkey interception
Нужно:
1. Перехватывать undo/redo shortcuts только когда active target = focused MetaGen params.
2. В этом случае:
   - блокировать native path
   - вызывать custom params undo/redo
3. Во всех остальных случаях не вмешиваться.

### 8.6. Не менять native behavior остальных контролов
Нужно:
1. Не вмешиваться в native undo/redo для остальных контролов.
2. Не трогать data/instances.
3. Не трогать code editor.
4. Не делать edit routing для других модулей.

## 9. Что reviewer должен явно запретить Codex

1. Не делать custom undo/redo для data.
2. Не делать custom undo/redo для instances.
3. Не делать custom undo/redo для code editor.
4. Не внедрять Edit menu.
5. Не внедрять copy/cut/paste.
6. Не делать общий global edit framework.
7. Не трогать native edit behavior вне params.
8. Не использовать native workbook.undo()/redo() как source of truth для params feature.
9. Не оставлять params replay на inline-магии без config/constants.
10. Не отключать auto-style целиком.
11. Не ломать current save/load semantics.
12. Не делать тяжёлый IPC/main/preload refactor.
13. Не менять helper scripts, если новые файлы не добавляются.
14. Не запускать export_project_to_txt.py.
15. Не генерировать dump.
16. Не оставлять Codex свободы в выборе архитектурного варианта.

## 10. Config/constants policy

В touched zone нужно вынести в config/constants всё, что становится устойчивым contract surface.

App-level:
- ids / labels / titles / disabled text для top-panel Undo/Redo buttons
- если reviewer выберет action ids для app-level dispatch, они должны быть в config

MetaGen-level:
- params history max depth
- logger source names для params history
- replay guard reasons/tokens
- supported params hotkey command ids
- любые новые repeated literals history/replay/interception semantics

Не нужно механически выносить вообще все локальные одноразовые строки.

## 11. Что reviewer должен считать хорошим результатом

Хороший результат — это когда одновременно выполнено всё:

1. Params table имеет custom semantic undo/redo history.
2. Top-panel Undo/Redo реально работают только для active/focused MetaGen params.
3. Params hotkeys undo/redo больше не уходят в native path.
4. Вне params native edit behavior не тронут.
5. Auto-style после replay работает корректно.
6. Replay не создаёт новый history entry.
7. Ordinary params edits продолжают работать.
8. Save/open не ломаются.
9. touched-zone магия вынесена в config/constants.
10. задача не расползлась в общий edit framework.

## 12. Тесты, которые reviewer должен потребовать

### 12.1. History controller tests
Нужны tests на:
- initial present
- push only on semantic diff
- duplicate snapshot ignored
- undo
- redo
- branch cut
- max depth trimming

### 12.2. Params replay tests
Нужны tests на:
- replay восстанавливает header + rows
- replay работает для строк beyond bootstrap
- replay не зависит от hard upper bound 100
- replay не создаёт новый history step

### 12.3. Auto-style interaction tests
Нужны tests на:
- replay + auto-style не зацикливаются
- after replay visual params state корректен
- ordinary auto-style path остаётся рабочим

### 12.4. Top panel integration tests
Нужны tests на:
- top panel buttons существуют
- buttons disabled вне params
- buttons enabled в focused params context
- click вызывает custom params undo/redo

### 12.5. Params-only hotkey interception tests
Нужны tests на:
- focused params -> shortcut routed to custom params handler
- not params -> interception does not happen
- native behavior outside params remains untouched as far as current test surface allows to prove

### 12.6. Regression tests
Сохранить зелёными:
- tests/metagenParamsContract.test.js
- tests/metagenSheetSnapshot.test.js
- tests/metagenParamsSheetLifecycle.test.js
- tests/finalizeEditingOnContextLeave.test.js
- tests/editorContextLifecycle.test.js
- tests/tabEditLifecycle.test.js
- tests/configWiring.integration.test.js

### 12.7. Helper scripts
Если появляются новые файлы:
- обновить create_project_structure.py
- обновить export_project_to_txt.py

Если новых файлов нет:
- явно зафиксировать в отчёте, что whitelist update не нужен

## 13. Проверки, которые reviewer должен потребовать

После изменений Codex обязан:
1. Прогнать targeted tests для params history / replay / top buttons / params-only hotkey interception.
2. Прогнать весь набор тестов целиком.
3. Статически проверить helper scripts.
4. В итоговом отчёте перечислить:
   - какие файлы изменены
   - какие новые config/constants добавлены
   - какой exact replay guard выбран
   - какой exact params-only hotkey interception path выбран
   - как именно исключён native params undo/redo path
   - какие targeted tests добавлены
   - результат полного test suite

## 14. Формат codex_task_md

Reviewer обязан выдать codex_task_md в жёстком операционном стиле с разделами:

1. Контекст и проблема
2. Целевая семантика
3. Что сначала проверить
4. Что именно изменить
5. Что не делать
6. Тесты
7. Команды проверки
8. Формат итогового отчёта

Reviewer обязан помнить:
- он анализирует по dump
- но пишет ТЗ напрямую для Codex, который работает с живым репозиторием
- reviewer сначала сам снимает техническую неопределённость
- затем фиксирует один exact implementation path
- Codex не должен ничего проектировать сам