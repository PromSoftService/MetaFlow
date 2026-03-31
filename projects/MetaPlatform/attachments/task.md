# Task: MetaGen editor stage 1 — заменить правую `data`-панель на `instances`-панель над `code`, сохранить надёжную table semantics и не вносить новую магию

Этот документ является first-iteration task для reviewer.

Он применяется вместе с обязательными reference-ограничениями:
- `01_project_doctrine.md`
- `02_codex_execution_standard.md`
- `03_architecture_exceptions.md`
- `04_metaplatform_project_dump.txt`

Считать эти документы обязательными ограничениями всей задачи.

---

## 0. Главная цель текущего этапа

Нужно выполнить **первый этап** изменения MetaGen editor.

Текущая целевая семантика этапа:

- в MetaGen editor слева остаётся `params`;
- справа вместо текущей `data`-панели должна появиться `instances`-панель;
- `instances` должна располагаться **над** `code` editor;
- между `instances` и `code` должен быть **горизонтальный splitter**;
- между левым `params` и правой зоной (`instances + code`) должен остаться **вертикальный splitter**;
- таблица `instances` должна иметь **ровно 2 фиксированных столбца**:
  - `Экземпляр`
  - `Функциональный блок`
- эти тексты должны отображаться как column headers;
- структура столбцов `instances` не должна быть пользовательски изменяемой;
- по надёжности хранения / загрузки / bootstrap-поведения `instances` не должна быть хуже текущей `data`-таблицы:
  - значения за пределами bootstrap 100 должны корректно сохраняться и восстанавливаться;
  - реализация не должна быть жёстко завязана на магическую цифру `100`;
  - runtime shape должен определяться по тем же здоровым принципам: `max(bootstrap seed, persisted payload shape)`, а не через жёсткий предел.

Это именно **stage 1**.

---

## 1. Что считать scope текущей итерации

Текущий scope не про полный redesign MetaGen и не про общий табличный framework refactor.

Текущая итерация должна решить **ровно этот контур**:

1. Перестроить editor composition:
   - убрать `data` из правой панели MetaGen editor;
   - сделать новую правую вертикальную композицию:
     - верх: `instances`
     - низ: `code`
   - сохранить `params` слева.

2. Поднять для `instances` полноценную редактируемую sheet/table runtime с фиксированной двухколоночной семантикой.

3. Обеспечить корректный extract/save/load path для `instances` как минимум на том уровне надёжности, который уже есть у `data`-таблицы в части:
   - строк beyond bootstrap;
   - actual sheet dimensions;
   - compact persisted payload.

4. Вынести все новые semantic/layout/table literals в существующий config/constants слой.

---

## 2. Что не входит в текущий этап

В эту итерацию **не входит**:

1. Полное удаление всей `data`-подсистемы проекта.
2. Полный schema migration/rethink всего MetaGen document.
3. Рефакторинг ради “унификации всех таблиц в один мегадвижок”.
4. Изменение IPC / preload / main / renderer boundary.
5. Затрагивание MetaLab / MetaView.
6. Перестройка project save/open semantics вне реально затронутой зоны.
7. Введение нового общего shared contract через спорную архитектурную унификацию.
8. Механическое вытаскивание в config вообще всех локальных literals подряд.

---

## 3. Исходная техническая картина, от которой нужно отталкиваться

Reviewer должен исходить из следующей текущей структуры кода.

### 3.1. Текущее состояние документа MetaGen

У документа уже есть:
- `params`
- `data`
- `instances`
- `code`

Поле `instances` уже существует в persisted document shape.
Сейчас оно не поднято как полноценная editable table на месте `data`.

### 3.2. Текущее состояние editor composition

Сейчас MetaGen editor фактически строится как:
- `paramsPanel`
- `codePanel`
- `dataPanel`

и собирается через один горизонтальный `Split`.

### 3.3. Текущее состояние `data`-table semantics

У `data` уже есть полезная готовая семантика, которую нужно использовать как reference baseline, а не терять:

- bootstrap rows;
- actual payload-aware runtime dimensions;
- extract path, который сохраняет строки beyond bootstrap;
- tests на строки > 100;
- fixed header-oriented table semantics.

Reviewer должен считать это **source of reference behavior**, а не случайной реализацией.

---

## 4. Главная роль reviewer в этой задаче

В этой задаче reviewer не должен ограничиваться расплывчатым “перенести таблицу”.

Reviewer обязан:

1. Точно локализовать, какие участки текущего MetaGen editor отвечают за:
   - panel composition;
   - split layout;
   - `data` table runtime;
   - extract/save path;
   - persisted table contract;
   - tests.

2. Принять **один конкретный технический путь** реализации stage 1.

3. После этого выдать Codex **один жёсткий `codex_task_md` без альтернатив и без свободы архитектурного выбора**.

### Критически важное правило

В этой задаче:
- reviewer может сам выбрать минимально рискованный технический путь;
- **но Codex не должен ничего решать**.

То есть reviewer сначала сам принимает решение:
- какие файлы менять;
- будет ли создан отдельный `instances contract`;
- будет ли создан отдельный `instances sheet factory`;
- какие старые `data`-пути оставить нетронутыми на этом этапе;
- как именно собрать новый right-side layout;

а затем формулирует для Codex **не варианты**, а **один конкретный план исполнения**.

В итоговом `codex_task_md` запрещены:
- “или”;
- “можно выбрать”;
- “если удобнее”;
- “при необходимости подумай”;
- “возможно стоит”.

Для Codex должен остаться только режим:
- открыть указанные файлы;
- внести указанные изменения;
- прогнать указанные проверки;
- вернуть указанный отчёт.

Codex в этой задаче — **чистый исполнитель**.

---

## 5. Предпочтительная техническая стратегия

Reviewer может отклониться от этого только если по текущему репозиторию найдёт доказательно более локальный и менее рискованный путь.

### Предпочтительная стратегия

#### A. Layout
В `renderer/editors/metagen/createMetaGenEditor.js`:
- перестроить build/editor composition так, чтобы:
  - `params` остался отдельной левой панелью;
  - правая зона стала контейнером с двумя панелями:
    - `instances`
    - `code`
- внешний splitter между левой и правой зонами остаётся вертикальным;
- внутренний splitter между `instances` и `code` делается горизонтальным.

#### B. New instances table runtime
Не перегружать `data`-таблицу прямым переименованием “как попало”.

Предпочтительный путь:
- создать отдельный contract-файл для `instances`;
- создать отдельный table factory для `instances`;
- использовать существующие общие reusable helpers только там, где это реально оправдано.

То есть prefer:
- `renderer/modules/metagen/metagenInstancesContract.js`
- `renderer/modules/metagen/tables/createMetaGenInstancesSheet.js`

а не превращать `data`-код в мутный hybrid “data-or-instances”.

#### C. Persisted shape
На этом этапе не делать тяжёлый schema redesign.

Предпочтительный путь:
- сохранить top-level field `instances`;
- использовать компактную persisted shape через `rows`;
- не вводить пользовательски редактируемую dynamic columns metadata для `instances`;
- фиксированные headers брать из config, а не из user-editable persisted columns.

Если reviewer выберет другой путь, он обязан доказать, что он:
- проще;
- безопаснее;
- не расширяет scope;
- не добавляет лишней архитектурной массы.

---

## 6. Что reviewer должен проверить в коде в первую очередь

Перед формированием `codex_task_md` reviewer обязан сам проверить и сопоставить следующие зоны.

### 6.1. Editor composition
Проверить:
- `renderer/editors/metagen/createMetaGenEditor.js`
- где создаются `paramsPanel`, `codePanel`, `dataPanel`
- где собирается `Split`
- как сейчас организован layout контейнеров
- где задаются panel class names и panel headers

### 6.2. Existing data-table path
Проверить:
- `renderer/modules/metagen/metagenDataContract.js`
- `renderer/modules/metagen/tables/createMetaGenDataSheet.js`
- `renderer/modules/metagen/tables/createMetaGenSimpleSheet.js`
- `renderer/modules/metagen/tables/sheetSnapshot.js`

Нужно понять:
- как реализован fixed headers path;
- как извлекаются rows;
- как runtime dimensions выбираются из payload;
- как сохраняются rows beyond bootstrap;
- как запрещается structural column mutation у `data`.

### 6.3. Existing document shape
Проверить:
- `renderer/modules/metagen/metagenDocumentFactory.js`
- примеры YAML в `project-examples/demo-feedmill/metagen/*.yaml`

Нужно понять:
- как сейчас создаётся `instances`;
- какая persisted shape уже существует;
- что можно сохранить без лишней миграции.

### 6.4. Config/constants layer
Проверить:
- `config/ui-config.js`
- `renderer/modules/metagen/metagenConfig.js`
- при необходимости `config/project-config.js`

Нужно заранее определить:
- куда выносить новые panel header texts;
- куда выносить splitter sizes/min sizes/gutter/cursor, если появятся новые independent layout constants;
- куда выносить `instances` table headers;
- куда выносить `instances` table bootstrap row count / fixed column count / permissions / hidden commands / retry config.

### 6.5. Tests
Проверить:
- `tests/metagenDataContract.test.js`
- существующие MetaGen table/editor lifecycle tests
- helper whitelist scripts:
  - `create_project_structure.py`
  - `export_project_to_txt.py`

---

## 7. Точная целевая семантика stage 1

После выполнения stage 1 должно быть истинно следующее.

### 7.1. Layout
При открытии MetaGen document:
- слева отображается `params`;
- справа сверху отображается `instances`;
- справа снизу отображается `code`;
- между `params` и правой зоной работает вертикальный splitter;
- между `instances` и `code` работает горизонтальный splitter.

### 7.2. Instances table
`instances` table:
- имеет ровно 2 колонки;
- показывает в заголовках:
  - `Экземпляр`
  - `Функциональный блок`
- не позволяет пользователю менять структуру колонок;
- использует stable extract/save/load flow;
- не теряет строки beyond bootstrap 100;
- не завязана жёстко на магическую `100`;
- сохраняет compact persisted payload.

### 7.3. Existing data semantics
На этом этапе не требуется удалять `data` из persisted document shape.
Но `data` не должна больше быть активной editor panel в MetaGen editor.

### 7.4. Magic/config policy
Всё новое, что является:
- panel id / panel label;
- table header text;
- table behavior constant;
- fixed column count;
- runtime mode / marker / permission;
- repeated splitter/layout constant;
- repeated sheet/runtime wiring literal;

должно быть вынесено в существующий config/constants слой.

Локальные одноразовые технические strings/messages допустимо оставить локально только если они не являются semantic/wiring contract.

---

## 8. Что reviewer должен считать допустимой свободой выбора

У reviewer в этой задаче есть **небольшая свобода выбора**, но только на своём уровне, до выдачи `codex_task_md`.

Допустимо, чтобы reviewer сам решил:
- создавать ли новый dedicated `metagenInstancesContract.js`;
- создавать ли новый dedicated `createMetaGenInstancesSheet.js`;
- какие существующие generic helpers можно безопасно переиспользовать;
- нужно ли оставить `data`-подсистему в проекте нетронутой как отложенный слой;
- нужны ли новые tests отдельными файлами или можно расширить существующие.

Но после этого reviewer обязан:
- выбрать один путь;
- запретить все альтернативные пути в `codex_task_md`;
- не оставлять Codex свободы решать это самостоятельно.

---

## 9. Что reviewer должен потребовать от Codex как обязательные изменения

Reviewer должен потребовать у Codex **ровно такой тип implementation pass**.

### 9.1. Layout changes
Codex должен:
1. Перестроить MetaGen editor composition.
2. Убрать `dataPanel` из active layout.
3. Ввести `instancesPanel`.
4. Сформировать right-side stacked layout `instances + code`.
5. Собрать внешний vertical split и внутренний horizontal split.
6. Не оставлять старую layout-логику в partially-used состоянии.

### 9.2. Instances contract/runtime
Codex должен:
1. Поднять отдельный working table path для `instances`.
2. Сделать ровно 2 фиксированных столбца.
3. Вынести тексты headers в config.
4. Запретить structural column mutation.
5. Сделать extract path без жёсткой привязки к `100`.
6. Сохранять строки за пределами bootstrap.
7. Корректно восстанавливать таблицу при reopen/load.

### 9.3. Document integration
Codex должен:
1. Интегрировать `instances` в `extractValue()` и в editor runtime.
2. Не сломать `params` и `code`.
3. Не ломать сохранение всего документа целиком.
4. Не удалять `data`-field из persisted document schema, если это не требуется для компиляции/тестов.

### 9.4. Config/constants
Codex должен:
1. Не добавлять новые raw semantic literals в рабочий код.
2. Вынести в config/constants:
   - panel headers
   - instances table headers
   - fixed column count
   - layout constants
   - repeated permissions / hidden commands / retry settings / behavior tokens
3. Не делать вредный over-extraction одноразовых локальных технических literals.

---

## 10. Что reviewer должен явно запретить Codex

Reviewer обязан явно запретить следующие действия.

1. Не трогать IPC / preload / renderer / main boundary.
2. Не объединять IPC contracts ради дедупликации.
3. Не делать общий table framework rewrite.
4. Не превращать `data` и `instances` в один неясный hybrid abstraction, если для этого нет жёсткой необходимости.
5. Не удалять старую `data`-подсистему глубоко по проекту на этом этапе.
6. Не трогать MetaLab / MetaView.
7. Не делать cleanup вне реально затронутой зоны.
8. Не оставлять новые magic strings / magic numbers / raw semantic literals в wiring/layout/table behavior.
9. Не использовать магическую `100` как логический предел.
10. Не редактировать dump.
11. Не генерировать dump.
12. Не запускать `export_project_to_txt.py`.
13. Не менять helper-скрипты, если изменения состава файлов этого реально не требуют.
14. Не оставлять Codex свободы выбирать между несколькими implementation paths.

---

## 11. Что reviewer должен считать хорошим результатом текущего этапа

Хороший результат stage 1:

1. Новый layout реально работает как:
   - `params | (instances over code)`.
2. `instances` — это не заглушка, а рабочая таблица.
3. В `instances` есть 2 фиксированных header columns:
   - `Экземпляр`
   - `Функциональный блок`
4. Данные строк beyond bootstrap не теряются.
5. В код не внесена новая магия.
6. Изменения локальны и понятны.
7. `data` не торчит как partially broken editor artifact.
8. Reviewer может технически внятно объяснить:
   - какие файлы изменены;
   - почему выбран именно этот implementation path;
   - почему `instances` не хуже `data` в части save/load/runtime dimensions;
   - почему задача не расползлась в лишний refactor.

---

## 12. Что reviewer должен обязательно потребовать в тестах

После изменений reviewer должен потребовать от Codex:

### 12.1. Полный прогон
- обязательно прогнать **весь набор тестов целиком**.

### 12.2. Targeted coverage
Добавить или обновить targeted tests, которые доказывают минимум следующее:

1. `instances` contract:
   - normalizes persisted rows predictably;
   - uses runtime dimensions as `max(bootstrap, payload shape)`;
   - не обрезает строки beyond bootstrap.

2. `instances` extract/save path:
   - сохраняет данные в строках > 100;
   - не жёстко зависит от `100` как предела;
   - корректно восстанавливает values после reopen/load path на уровне contract/extract semantics.

3. Если тронут editor composition:
   - добавить проверку или иное доказательство, что editor теперь собирается как:
     - left `params`
     - right `instances + code`
   - если прямой UI test слишком тяжёлый, reviewer может разрешить code-level verification + targeted unit/integration coverage, но обязан явно зафиксировать почему этого достаточно на данном этапе.

### 12.3. Helper scripts
Обязательно проверить helper-скрипты:
- `create_project_structure.py`
- `export_project_to_txt.py`

Но:
- `export_project_to_txt.py` проверять **только статически**;
- не запускать;
- не генерировать dump;
- если добавлены новые файлы, reviewer должен потребовать обновить whitelist в helper-скриптах;
- если новые файлы не добавлены — reviewer должен потребовать явно зафиксировать, что whitelist update не нужен.

---

## 13. Как reviewer должен сформулировать `codex_task_md`

Reviewer обязан выдать `codex_task_md` в жёстком операционном стиле.

Внутри него должны быть:

### A. Exact scope
Только current stage 1:
- editor composition;
- working instances table;
- integration into save/load/runtime;
- config/constants cleanup только в затронутой зоне.

### B. Exact files
Reviewer должен перечислить точные файлы:
- которые нужно проверить сначала;
- которые можно менять;
- которые запрещено трогать.

### C. Exact implementation path
Reviewer должен выбрать один путь и описать его как sequence:
1. Проверить X.
2. Обновить Y.
3. Создать/изменить Z.
4. Интегрировать A в B.
5. Прогнать C.

### D. Exact prohibitions
Без общих слов.
Нужен конкретный список “не делать”.

### E. Exact verification
С конкретными командами, конкретными tests, конкретными static checks.

---

## 14. Политика reviewer / Codex именно для этой задачи

### Reviewer
- может самостоятельно выбрать минимально рискованный путь;
- не должен задавать вопрос пользователю до первого реального implementation pass;
- не должен просить dump преждевременно;
- должен сначала попытаться решить всё по текущему dump и репозиторию;
- должен помнить, что перед окончательным `done` всё равно обязателен финальный `question`.

### Codex
Для этой задачи Codex:
- не проектирует;
- не выбирает архитектуру;
- не решает между вариантами;
- не делает “как считает лучше”;
- не расширяет scope;
- только исполняет выбранный reviewer путь.

---

## 15. Что reviewer должен считать ошибкой выполнения

Следующие вещи считать ошибкой:

1. Reviewer оставил Codex свободу выбора implementation path.
2. Reviewer выдал task с альтернативами вместо одного точного плана.
3. Codex полез в большой refactor.
4. Изменения вышли за MetaGen editor / instances / related save-load path.
5. Появились новые semantic literals вне config/constants.
6. Реализация всё ещё жёстко упирается в bootstrap 100.
7. Структура колонок `instances` осталась пользовательски изменяемой.
8. `data` и `instances` оказались смешаны в неясную semi-shared abstraction без явной пользы.
9. Helper whitelist сломался после добавления новых файлов.
10. `export_project_to_txt.py` был запущен.
11. Полный прогон тестов не выполнен.
12. Reviewer пытается закрыть задачу без точной проверки layout/composition и save/load semantics.

---

## 16. Важный приоритет

При равных вариантах reviewer должен предпочесть решение, которое:
- локальнее;
- понятнее;
- не создаёт лишний framework;
- не оставляет Codex свободы трактовки;
- сохраняет текущую архитектуру проекта;
- даёт working stage 1 без лишней теоретической “идеальности”.