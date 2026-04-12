# Context

Новая отдельная задача: убрать запрещённый JS-слой `ui/renderer/ui/pngIconRenderer.js` и привести UI к правилу, что PNG-иконки существуют только как assets, без специализированного icon renderer helper-а в коде.

По текущему дампу видно, что:
- файл `ui/renderer/ui/pngIconRenderer.js` существует;
- он используется как минимум из `ui/renderer/ui/applyStaticText.js` и `ui/renderer/ui/createProjectTree.js`;
- это конфликтует с проектным правилом, что отдельный icon renderer JS для PNG запрещён.

Эта итерация должна убрать именно этот слой и его использования, не расширяя scope на большой UI-refactor.

# Current scope

Только удаление зависимости UI от `ui/renderer/ui/pngIconRenderer.js` и синхронизация связанных мест.

Не переходить в соседние темы:
- не делать общий cleanup UI;
- не менять lock/process/backend lifecycle;
- не менять module/editor semantics;
- не делать общий asset pipeline refactor;
- не трогать документы 01/02/03 в этом цикле, если только не потребуется минимальная синхронизация из-за прямого расхождения с итоговым состоянием.

# Target semantics

После правки должно быть истинно следующее:

1. В рабочем UI-коде больше нет специализированного helper-а `ui/renderer/ui/pngIconRenderer.js`.
2. `applyStaticText.js`, `createProjectTree.js` и другие затронутые UI-места больше не импортируют и не вызывают этот helper.
3. PNG-иконки, если они реально нужны UI, используются только как assets / обычные пути / обычные DOM-элементы без отдельного renderer abstraction layer.
4. Не должно появиться нового параллельного icon helper-а с тем же смыслом под другим именем.
5. `export_project_to_txt.py` должен быть актуализирован: удалённый `pngIconRenderer.js` не должен оставаться в whitelist.
6. Полный набор тестов по проекту должен быть реально прогнан Codex, reviewer должен проверить фактические результаты.

# What to inspect first

Сначала поручи Codex проверить в репозитории:

1. `ui/renderer/ui/pngIconRenderer.js` — что именно он делает и какой контракт даёт вызывающим местам.
2. Все импорты и использования `pngIconRenderer` по репозиторию.
3. `ui/renderer/ui/applyStaticText.js`
4. `ui/renderer/ui/createProjectTree.js`
5. Любые соседние UI-файлы, которые могут зависеть от того же icon contract.
6. `export_project_to_txt.py` — наличие `ui/renderer/ui/pngIconRenderer.js` в `PROJECT_FILES`.
7. Текущий способ хранения и использования PNG assets, чтобы не заменить удаление helper-а на скрытый второй renderer layer.

# Required changes

1. Найди и удали `ui/renderer/ui/pngIconRenderer.js`, если после анализа его можно полностью вывести из рабочего графа зависимостей.
2. Если вызывающие места используют helper только для генерации DOM/URL/markup для PNG-иконок, перенеси эту логику прямо в локальные места использования или в уже существующий допустимый UI-слой без создания нового специализированного icon renderer helper-а.
3. Обнови `ui/renderer/ui/applyStaticText.js`, чтобы он больше не зависел от `pngIconRenderer`.
4. Обнови `ui/renderer/ui/createProjectTree.js`, чтобы он больше не зависел от `pngIconRenderer`.
5. Проверь, нет ли других импортов/вызовов `pngIconRenderer`, и убери их.
6. Не вводи новый файл вида `iconRenderer`, `pngRenderer`, `assetIconRenderer`, `iconHelper` и т.п. с той же запрещённой семантикой.
7. Если для оставшейся логики нужны строки путей, class names, markers или иные shared semantic values, не оставляй новые raw semantic literals — используй существующий config/constants слой.
8. Актуализируй `export_project_to_txt.py`: удалённый `ui/renderer/ui/pngIconRenderer.js` не должен оставаться в whitelist.
9. Проверь, не появились ли после правки мёртвые импорты, неиспользуемые ветки и partially-updated fragments в затронутых UI-файлах.
10. Не менять package-lock files и не добавлять их в export.

# Files allowed to change

Разрешено менять только:
- `ui/renderer/ui/pngIconRenderer.js`
- `ui/renderer/ui/applyStaticText.js`
- `ui/renderer/ui/createProjectTree.js`
- другие UI-файлы только если после проверки там действительно есть прямой импорт/вызов `pngIconRenderer`
- `export_project_to_txt.py`
- связанные тесты, если они действительно существуют и требуют адаптации к корректной семантике

Не создавать новые helper-файлы для иконного renderer-слоя.

# Do not do

1. Не делать общий refactor UI.
2. Не менять backend, runtime client, process orchestration, lock lifecycle.
3. Не менять layout/naming/structure за пределами узкого icon-related scope.
4. Не заменять удаление `pngIconRenderer` новым helper-слоем под другим именем.
5. Не тащить в задачу cleanup несвязанных файлов “раз уж уже открыты”.
6. Не редактировать dump.
7. Не генерировать новый dump, если это отдельно не требуется для проверки helper-а.
8. Не добавлять package-lock files в export.
9. Не оставлять новые raw semantic literals / magic strings / magic numbers, если для них уже существует подходящий config/constants слой.
10. Не подгонять тесты под неправильную реализацию.

# Verification

Reviewer должен потребовать от Codex реально прогнать команды и затем проверить фактические результаты.

Обязательные проверки:

1. Поиск по репозиторию:
   - убедиться, что `pngIconRenderer` больше нигде не импортируется и не используется.
2. Статическая проверка:
   - убедиться, что удалённый файл не остался в `export_project_to_txt.py`.
3. Полный прогон тестов по проекту.
4. Дополнительно проверить, что после удаления helper-а не осталось:
   - мёртвых импортов;
   - unreachable branches;
   - второго competing source of truth для icon logic;
   - новых raw semantic literals.
5. Отдельно проверить, что в `export_project_to_txt.py` по-прежнему не экспортируются:
   - иконки;
   - тесты;
   - package-lock files.

Команды проверки:
- reviewer должен поручить Codex прогнать полный набор тестовых команд фактического проекта;
- reviewer должен проверить, что Codex привёл фактический stdout/stderr и статусы команд;
- в extra_test_commands запрещены любые долгоживущие foreground/watch/server-команды без bounded wrapper.

# Helper script check

Reviewer должен отдельно потребовать от Codex проверить и актуализировать `export_project_to_txt.py`.

В рамках этой задачи достаточно:
- статически обновить whitelist;
- не запускать helper, если это не требуется дополнительно;
- не оставлять в whitelist `ui/renderer/ui/pngIconRenderer.js`.

# Result report

Reviewer должен потребовать от Codex структурированный итоговый отчёт в формате:

- Summary
- Changed files
- What changed
- Verification
- Risks / open items

В отчёте обязательно перечислить:
1. какие файлы изменены;
2. удалён ли `ui/renderer/ui/pngIconRenderer.js` полностью;
3. где были убраны его импорты/вызовы;
4. как обновлён `export_project_to_txt.py`;
5. какие команды реально прогнаны;
6. результаты полного тестового прогона;
7. остались ли риски или открытые вопросы.

# DONE

Задача считается DONE только если одновременно выполнено всё ниже:

1. `ui/renderer/ui/pngIconRenderer.js` удалён или полностью выведен из рабочего использования без замены на новый запрещённый renderer helper.
2. В репозитории не осталось импортов/использований `pngIconRenderer`.
3. Все затронутые UI-файлы синхронизированы и не содержат мёртвых хвостов.
4. `export_project_to_txt.py` актуализирован и больше не содержит `ui/renderer/ui/pngIconRenderer.js`.
5. Package-lock files не добавлены в export.
6. Codex реально прогнал полный набор тестов по проекту.
7. Reviewer проверил фактические результаты команд и не принимает задачу без этого.
