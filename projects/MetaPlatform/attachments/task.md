# Task: MetaGen editor — исправить layout так, чтобы instances тянулся вниз вдоль всей правой рабочей области, а не заканчивался на уровне data

Этот документ является task для reviewer.
Он применяется вместе с обязательными reference-ограничениями:
- 01_project_doctrine.md
- 02_codex_execution_standard.md
- 03_architecture_exceptions.md
- актуальный dump проекта из attachments

## 0. Главная цель

Нужно скорректировать только layout MetaGen editor.

Сейчас layout фактически собран как:
- слева: params
- справа сверху: data + instances в одном верхнем ряду
- справа снизу: code

Из-за этого instances заканчивается по высоте на уровне data.

Это неверно для текущей цели.

Нужно получить такой итоговый layout:
- слева: params
- в центральной колонке сверху: data
- в центральной колонке снизу: code
- справа: instances
- instances должен тянуться по высоте всей правой рабочей области редактора, то есть располагаться рядом и с data, и с code

Целевая композиция:
params | ((data over code) | instances)

Или эквивалентно:
- внешний split: params | rightArea
- внутри rightArea: centerStack | instances
- внутри centerStack: data | code

## 1. Что входит в scope

В scope этой итерации входит только следующее:

1. Перестроить editor layout MetaGen под целевую композицию:
   params | ((data over code) | instances)

2. Сохранить существующие рабочие панели:
   - data panel
   - code panel
   - instances panel
   - params panel

3. Пересобрать split-иерархию так, чтобы:
   - instances больше не находился внутри верхнего ряда рядом с data
   - instances стал отдельной правой вертикальной колонкой полной высоты рабочей области editor-а

4. Перенести все новые layout-semantic literals в config/constants слой.

5. Обновить targeted tests под новый layout.

6. Прогнать весь набор тестов целиком.

## 2. Что НЕ входит в scope

Следующее запрещено и не входит в эту задачу:

1. Не менять contract/persistence semantics таблиц data и instances.
2. Не менять save/load behavior документа.
3. Не менять schema/validation без жёсткой необходимости.
4. Не менять IPC / preload / main / renderer boundary.
5. Не трогать MetaLab / MetaView.
6. Не делать общий refactor editor framework.
7. Не делать cleanup вне touched zone.
8. Не запускать export_project_to_txt.py.
9. Не генерировать dump.
10. Не менять helper-скрипты, если новые файлы не появляются.

## 3. Текущее состояние, от которого нужно отталкиваться

Reviewer обязан сначала проверить и зафиксировать:

1. В renderer/editors/metagen/createMetaGenEditor.js сейчас:
   - создаётся topTablesRow
   - в него кладутся dataPanel и instancesPanel
   - rightStack получает topTablesRow и codePanel
   - используются три split-а:
     - outerSplit
     - innerSplit
     - topTablesSplit

2. В renderer/modules/metagen/metagenConfig.js уже существуют:
   - editor.layout.outerSplit
   - editor.layout.innerSplit
   - editor.layout.topTablesSplit

3. В renderer/styles/styles.css уже есть стили для:
   - .metagen-editor-grid
   - .metagen-editor-right-stack
   - .metagen-editor-panel
   - .metagen-editor-panel-content

4. В targeted tests уже есть проверка текущей композиции params | ((data | instances) over code), и её нужно заменить на новую целевую композицию.

## 4. Роль reviewer

Reviewer должен:

1. Сам выбрать один точный implementation path.
2. После этого выдать Codex один жёсткий codex_task_md без альтернатив.
3. Не оставлять Codex свободы в архитектурных решениях.

В codex_task_md запрещены:
- "или"
- "если удобнее"
- "можно выбрать"
- "как считаешь лучше"
- "при необходимости подумай"

Codex здесь только исполнитель.

## 5. Предпочтительная техническая стратегия

Reviewer может отклониться только если найдёт доказательно более локальный и безопасный путь.

Предпочтительный путь:

### A. Пересобрать buildEditor()
В renderer/editors/metagen/createMetaGenEditor.js:
- оставить root
- оставить grid
- убрать текущую роль topTablesRow как верхнего ряда data + instances
- ввести отдельный centerStack
- ввести отдельную rightArea
- ввести отдельную full-height колонку instances

Предпочтительная новая иерархия DOM:
- grid
  - paramsPanel
  - rightArea
    - centerStack
      - dataPanel
      - codePanel
    - instancesPanel

### B. Пересобрать split-иерархию
Предпочтительно использовать:
1. outerSplit([paramsPanel, rightArea])
2. centerSplit([dataPanel, codePanel])
3. rightAreaSplit([centerStack, instancesPanel])

То есть:
- старый topTablesSplit должен исчезнуть
- вместо него нужен новый split между centerStack и instancesPanel
- instances не должен быть дочерним элементом верхнего ряда data

### C. Layout config
В METAGEN_CONFIG.editor.layout нужно:
- убрать или прекратить использовать topTablesSplit
- ввести новый конфиг для split-а между centerStack и instancesPanel
- при необходимости переименовать innerSplit / centerSplit, если reviewer считает это нужным для ясности
- не оставлять новую split-семантику inline в editor implementation

### D. Styles
В renderer/styles/styles.css нужно:
- сохранить существующую базу editor styles
- минимально добавить/скорректировать стили для новых layout containers
- обеспечить:
  - min-height: 0
  - min-width: 0
  - flex layout без переполнения
  - корректную растяжку instancesPanel по высоте всей правой рабочей области

Reviewer должен требовать от Codex не "подогнать как-нибудь визуально", а явно собрать layout-контракт.

## 6. Что reviewer должен проверить перед выдачей codex_task_md

Перед выдачей codex_task_md reviewer обязан посмотреть:

1. renderer/editors/metagen/createMetaGenEditor.js
   - buildEditor()
   - createSplitOptions()
   - actual Split(...) wiring
   - dispose()

2. renderer/modules/metagen/metagenConfig.js
   - editor.layout.*
   - editor container/runtime ids, если touched-zone layout rename их затрагивает

3. renderer/styles/styles.css
   - metagen editor layout classes
   - editorRightStack
   - metagen-editor-grid
   - metagen-editor-panel
   - metagen-editor-panel-content

4. targeted test file, где сейчас зафиксирована композиция:
   params | ((data | instances) over code)

## 7. Точная целевая семантика после реализации

После реализации должно быть истинно следующее:

1. params остаётся слева.
2. data находится в центральной колонке сверху.
3. code находится в центральной колонке снизу.
4. instances находится справа отдельной колонкой.
5. instances тянется по высоте всей правой рабочей области editor-а.
6. instances больше не заканчивается на уровне data.
7. split между data и code остаётся вертикальным.
8. split между centerStack и instances является горизонтальным.
9. внешний split между params и rightArea сохраняется.
10. contract/persistence таблиц не меняются.

## 8. Что reviewer должен потребовать от Codex

Codex должен сделать ровно следующее:

1. Перестроить buildEditor() под новую DOM-композицию:
   paramsPanel | rightArea
   rightArea = centerStack | instancesPanel
   centerStack = dataPanel over codePanel

2. Перестроить split wiring:
   - outerSplit([paramsPanel, rightArea])
   - centerSplit([dataPanel, codePanel])
   - rightAreaSplit([centerStack, instancesPanel])

3. Удалить старую схему:
   - topTablesRow.appendChild(dataPanel)
   - topTablesRow.appendChild(instancesPanel)
   - Split([dataPanel, instancesPanel])

4. Обновить layout config в METAGEN_CONFIG.editor.layout:
   - не оставлять старый topTablesSplit как active config
   - завести новый config для split-а между centerStack и instances
   - сохранить sizes/minSize/gutter/cursor в config, а не inline

5. Обновить styles так, чтобы instances действительно растягивался по полной высоте правой рабочей области.

6. Обновить targeted tests под новую композицию.

7. Прогнать весь test suite целиком.

## 9. Что reviewer должен явно запретить Codex

1. Не трогать createMetaGenDataSheet.js.
2. Не трогать createMetaGenInstancesSheet.js.
3. Не трогать metagenDataContract.js.
4. Не трогать metagenInstancesContract.js.
5. Не менять extract/save/load semantics документа.
6. Не менять metagenSchema.js, если layout не требует этого напрямую.
7. Не трогать helper-скрипты без появления новых файлов.
8. Не оставлять новый layout на inline-магии.
9. Не решать задачу чисто CSS-хаком без правильной перестройки DOM/split структуры.
10. Не оставлять старый topTablesRow как "мертвую" или partially used конструкцию.

## 10. Что reviewer должен считать хорошим результатом

Хороший результат:

1. UI реально стал params | ((data over code) | instances).
2. instances визуально тянется вниз до нижней границы рабочей области редактора, а не заканчивается на уровне data.
3. data и code остались в своей колонке.
4. split-контракты читаемы и лежат в config.
5. не появилось новой layout-магии.
6. persistence/data semantics не тронуты.
7. targeted tests проверяют именно новый layout, а не старый.

## 11. Что reviewer должен потребовать в тестах

Нужно обязательно потребовать:

1. Обновить targeted layout test так, чтобы он проверял:
   - отсутствие topTablesRow как активного data+instances row layout
   - наличие rightArea / centerStack или эквивалентной новой композиции
   - Split([paramsPanel, rightArea])
   - Split([dataPanel, codePanel])
   - Split([centerStack, instancesPanel]) или эквивалентный новый split
   - отсутствие старого Split([dataPanel, instancesPanel])

2. Если изменяются CSS class-level layout containers:
   - обновить assertions по styles.css

3. После этого прогнать весь набор тестов целиком.

## 12. Формат codex_task_md

Reviewer обязан выдать codex_task_md в жёстком операционном стиле с разделами:

1. Контекст и проблема
2. Целевая семантика
3. Что сначала проверить
4. Что именно изменить
5. Что не делать
6. Тесты
7. Команды проверки
8. Формат итогового отчёта

В codex_task_md reviewer обязан перечислить:
- точные файлы для проверки
- точные файлы, которые можно менять
- конкретный implementation path
- конкретные тесты и команды

## 13. Критерий завершения

Задача считается выполненной только если одновременно выполнено всё:

1. визуально instances занимает всю правую высоту editor area;
2. структура кода больше не соответствует old layout params | ((data | instances) over code);
3. targeted tests обновлены;
4. весь test suite зелёный;
5. новая layout-семантика вынесена в config/constants, без новой магии.