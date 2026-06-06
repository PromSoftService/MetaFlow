[URL]
https://github.com/PromSoftService/MetaPlatform

[CURRENT_COMMIT]
0603719fb5e98855e02a329959fbe7c5bd42d8bb

[TASK]
Реализовать первый этап project-level цепочки HMI artifacts.

Текущий scope:
1. Добавить DB / storage / project model для project-level tables:
   - HMI Tags;
   - HMI Alarms;
   - HMI Trends.

2. Добавить UI / project tree:
   - эти 3 таблицы должны быть видны на уровне project;
   - пользователь должен иметь возможность открыть таблицы и посмотреть данные;
   - если текущий table/editor UI позволяет без redesign — разрешить ручное редактирование address-полей HMI Tags.

3. Подключить MetaGen Generate:
   - при генерации MetaGen должен формировать / обновлять project-level HMI Tags / HMI Alarms / HMI Trends;
   - использовать upsert;
   - не удалять старые строки автоматически;
   - не перезаписывать import/manual address-поля.

Импорт Siemens XML / CoDeSys XML / DB source реализуем позже.
Project-level Download / Weintek / WinCC / MetaLab artifacts реализуем позже.
Timestamp availability lifecycle реализуем позже.

Reviewer должен сам разбить текущий scope на небольшие Codex passes.
Один Codex pass = один небольшой завершённый scope.
Не отправлять Codex весь task целиком.

## Source of truth

Reviewer обязан сначала проверить текущий GitHub repo на commit `0603719fb5e98855e02a329959fbe7c5bd42d8bb`.

Reviewer сам определяет по repo:
- где сейчас project storage / DB / project model;
- где project tree / document registry / UI nodes;
- где существующий table/editor UI;
- где MetaGen Generate;
- где constants / localization;
- где тесты для storage/model/UI/MetaGen.

## Целевая project-level модель

В project должны появиться 3 таблицы:

- HMI Tags
- HMI Alarms
- HMI Trends

Они относятся ко всему project, а не к MetaGen / MetaLab / MetaView локально.
MetaView не является владельцем этих данных.

## HMI Tags

Целевая таблица / entity:

- id
- project_id
- name
- plc_tag
- device
- addr_type
- addr
- comment
- data_type
- updated_at

Семантика:

- name — имя HMI-тега из MetaGen;
- plc_tag — PLC tag / symbol из MetaGen, будущий ключ для импорта адресов;
- device — всегда `MetaGenDevice`;
- addr_type — future import/manual field;
- addr — future import/manual field;
- comment — из MetaGen;
- data_type — future import/manual field.

Будущая экспортная строка Weintek tags будет строиться из:

- name;
- device;
- addr_type;
- addr;
- comment;
- data_type.

`plc_tag` в Weintek export не уходит, это внутренний ключ связи.

## HMI Alarms

Целевая таблица / entity:

- id
- project_id
- name
- tag
- bit
- text
- category
- updated_at

Семантика:

- name — имя alarm в HMI;
- tag — HMI Tag.name;
- bit — bit in HMI Tag, используется для WinCC, может игнорироваться Weintek;
- text — alarm text;
- category — fault / warning / alarm.

## HMI Trends

Целевая таблица / entity:

- id
- project_id
- name
- tag
- updated_at

Семантика:

- name — имя trend;
- tag — HMI Tag.name.

## MetaGen Generate semantics

MetaGen Generate должен:

1. Сгенерировать PLC code как сейчас.
2. Дополнительно сформировать / обновить project-level HMI Tags.
3. Дополнительно сформировать / обновить project-level HMI Alarms.
4. Дополнительно сформировать / обновить project-level HMI Trends.
5. Не удалять строки из этих таблиц автоматически.
6. Не перезаписывать address-поля HMI Tags:
   - addr_type;
   - addr;
   - data_type.

Если текущая реализация MetaGen Generate сейчас auto-download PLC code, не менять это поведение в этом task без отдельной необходимости. Разделение Generate / Download будет отдельным следующим этапом.

## HMI Tags upsert rules

Ключ строки:

- project_id + name.

Если HMI Tag уже существует:

- обновить MetaGen-owned поля:
  - plc_tag;
  - comment;
  - device = MetaGenDevice;

- не трогать future import/manual fields:
  - addr_type;
  - addr;
  - data_type.

Если HMI Tag не существует:

- добавить строку:
  - name из MetaGen;
  - plc_tag из MetaGen;
  - device = MetaGenDevice;
  - comment из MetaGen;
  - addr_type = empty;
  - addr = empty;
  - data_type = empty.

MetaGen Generate не удаляет HMI Tags.
Удаление только руками пользователем, если UI уже поддержит удаление.

## HMI Alarms upsert rules

Ключ строки:

- project_id + name.

Если alarm уже существует:

- обновить:
  - tag;
  - bit;
  - text;
  - category.

Если alarm не существует:

- добавить.

MetaGen Generate не удаляет alarms.
Удаление только руками пользователем, если UI уже поддержит удаление.

## HMI Trends upsert rules

Ключ строки:

- project_id + name.

Если trend уже существует:

- обновить:
  - tag.

Если trend не существует:

- добавить.

MetaGen Generate не удаляет trends.
Удаление только руками пользователем, если UI уже поддержит удаление.

## UI requirements

В дереве проекта добавить project-level узлы:

- HMI Tags;
- HMI Alarms;
- HMI Trends.

При открытии узла пользователь должен видеть соответствующую таблицу.

Для HMI Tags:

- name;
- plc_tag;
- device;
- comment — MetaGen-owned поля, можно сделать read-only;
- addr_type;
- addr;
- data_type — future import/manual fields, желательно editable, если это укладывается в существующую table UI без redesign.

Для HMI Alarms:

- name;
- tag;
- bit;
- text;
- category.

Для HMI Trends:

- name;
- tag.

Все новые user-facing тексты должны идти через существующую localization/UI text систему:
- tree node titles;
- table titles;
- column headers;
- validation/error/status texts, если добавляются.

Не добавлять raw strings в components / services / handlers.

## What reviewer should inspect

Reviewer должен через GitHub repo проверить:

1. Project storage / DB / schema / project state:
   - где хранятся project-level данные;
   - как добавляются project-level entities;
   - как устроены migrations / default project state.

2. Project tree / document registry / UI:
   - как добавляются project-level nodes;
   - какие constants используются для node/document kinds;
   - где локализуются tree titles / table titles / column headers.

3. Existing table/editor UI:
   - есть ли reusable table/grid;
   - как сейчас редактируются табличные project-level данные.

4. MetaGen Generate:
   - где формируется PLC code;
   - какие данные MetaGen уже знает для HMI tags / alarms / trends;
   - где безопасно подключить upsert project-level tables.

5. Config/constants/localization:
   - куда правильно добавить:
     - HMI Tags;
     - HMI Alarms;
     - HMI Trends;
     - MetaGenDevice;
     - table ids;
     - column ids;
     - document/node kinds.

6. Tests:
   - существующие tests для project storage/model/UI tree;
   - existing tests for MetaGen Generate;
   - какие tests подходят для проверки upsert behavior.

## Reviewer decomposition

Reviewer должен разбить текущую задачу на маленькие Codex passes.

Рекомендуемый порядок:

1. Foundation pass:
   - DB/storage/project model for HMI Tags / HMI Alarms / HMI Trends;
   - constants/localization;
   - tests.

2. UI pass:
   - project tree nodes;
   - table view/editor;
   - tests.

3. MetaGen integration pass:
   - MetaGen Generate upsert HMI Tags / HMI Alarms / HMI Trends;
   - preserve addr_type / addr / data_type;
   - no automatic delete;
   - tests.

Reviewer может объединить пункты 1 и 2, если repo показывает, что это маленький diff.
Reviewer может разделить ещё мельче, если иначе diff становится большим.

## Что НЕ входит в scope этой задачи

Не делать:

- Siemens XML import;
- CoDeSys XML import;
- DB source import;
- import report;
- Project Download / MetaGen artifacts;
- Project Download / Weintek artifacts;
- Project Download / WinCC artifacts;
- Project Download / MetaLab artifacts;
- timestamp availability lifecycle;
- dirty-state lifecycle;
- full Generate / Download split;
- removal of old direct HMI artifact generation path;
- broad architecture redesign;
- rewrite MetaGen;
- rewrite MetaLab;
- rewrite MetaView;
- mapping engine;
- role hmi/conf;
- separate tables per driver;
- MetaView ownership for Tags / Alarms / Trends;
- new common coordinator/orchestrator/manager/framework;
- new competing localization/config/constants layer;
- YAML ZIP transport contract changes;
- unrelated backend cleanup;
- unrelated UI layout cleanup;
- package scripts / package-lock changes без прямой необходимости;
- docs / architecture timeline cleanup;
- export helper cleanup, если whitelist/layout не затронут.

## Жёсткие запреты по семантике

- MetaGen Generate не удаляет HMI Tags / HMI Alarms / HMI Trends.
- MetaGen Generate не перезаписывает addr_type / addr / data_type.
- `device` для HMI Tags по умолчанию всегда `MetaGenDevice`.
- HMI Tags / HMI Alarms / HMI Trends — project-level data, не MetaView-local data.
- Existing MetaLab OPC UA import не ломать.
- Existing YAML ZIP import/export contract не ломать.
- Не добавлять raw user-facing strings вместо localization.
- Не добавлять semantic magic strings/magic numbers вместо config/constants.

## Task-specific verification

Reviewer должен требовать от Codex проверки, релевантные конкретному pass.

Для этой задачи обязательно подтвердить:

- если затронуты project storage / model:
  - есть тесты на создание/чтение/сохранение HMI Tags / HMI Alarms / HMI Trends;
  - проверено, что данные относятся к project-level, а не к MetaView-local state.

- если затронут UI / project tree:
  - проверено, что HMI Tags / HMI Alarms / HMI Trends отображаются как project-level узлы;
  - новые labels / table headers идут через localization.

- если затронут MetaGen Generate:
  - проверено, что Generate добавляет новые HMI Tags / Alarms / Trends;
  - проверено, что повторный Generate обновляет MetaGen-owned поля;
  - проверено, что повторный Generate не затирает addr_type / addr / data_type;
  - проверено, что Generate не удаляет старые строки автоматически.

Reviewer после post-Codex должен дополнительно проверить именно task-specific пункты:

1. HMI Tags / HMI Alarms / HMI Trends являются project-level data.
2. MetaGen Generate добавляет новые строки и обновляет MetaGen-owned поля.
3. MetaGen Generate не удаляет старые строки.
4. MetaGen Generate не перезаписывает addr_type / addr / data_type.
5. device для HMI Tags по умолчанию = MetaGenDevice.
6. Новые UI labels / table headers локализованы.
7. Новые table ids / column ids / defaults вынесены в существующий config/constants слой.
8. Existing MetaLab OPC UA import не затронут.
9. Existing YAML ZIP import/export contract не затронут.

## Done criteria for this task

Текущая задача считается завершённой, когда:

1. Project-level HMI Tags / HMI Alarms / HMI Trends существуют в storage/model.
2. Эти таблицы доступны в project tree / UI на уровне project.
3. MetaGen Generate формирует / обновляет эти таблицы по upsert rules.
4. Existing addr_type / addr / data_type не затираются при повторном MetaGen Generate.
5. Старые строки не удаляются автоматически при MetaGen Generate.
6. `device = MetaGenDevice` применяется как default для HMI Tags.
7. Все новые user-facing тексты локализованы.
8. Все новые semantic ids/defaults/table ids/column ids/node kinds вынесены в существующий config/constants слой.
9. Existing MetaLab OPC UA import не сломан.
10. Existing YAML ZIP import/export contract не сломан.
11. Relevant tests/checks пройдены или environment limitations честно отделены от product verdict.
12. Финальный GitHub diff соответствует текущему scope.
13. Reviewer оценивает качество реализации >= 7.75/10.

## Result report для final done

Когда reviewer считает текущую задачу завершённой, summary должен содержать:

- какие passes были выполнены;
- какие области изменены;
- как реализованы HMI Tags / HMI Alarms / HMI Trends;
- как реализован UI/project tree доступ;
- как реализован MetaGen Generate upsert;
- как сохраняются addr_type / addr / data_type;
- какие parts явно отложены на следующие задачи:
  - import;
  - download;
  - timestamp availability;
- как сохранён MetaLab OPC UA import;
- как сохранён YAML ZIP contract;
- какие tests/checks прошли;
- итоговую субъективную оценку качества кода по шкале 0..10;
- METAFLOW_FINAL_HEAD.