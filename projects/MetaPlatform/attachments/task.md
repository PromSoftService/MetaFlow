# Task: PNG icons runtime fix — renderer иконки не отображаются, хотя menu `Файл` отображает их корректно

Этот документ является task для reviewer.
Он применяется вместе с обязательными reference-ограничениями:
- 01_project_doctrine.md
- 02_codex_execution_standard.md
- 03_architecture_exceptions.md
- актуальный dump проекта из attachments

## 0. Главная цель

Нужно закрыть конкретный runtime bug:

- menu `Файл` показывает PNG icons;
- renderer UI иконки визуально не показывает.

Нужно не продолжать косметический refactor icon architecture, а довести текущую PNG-path модель до рабочего состояния в живом приложении.

Это НЕ новый redesign иконок.
Это НЕ переход на другую icon system.
Это НЕ новая итерация про SVG.
Это fix текущего renderer asset serving / runtime wiring.

## 1. Что уже считается правильным и не должно быть сломано

В текущем срезе уже есть правильные решения, их не нужно откатывать:

1. канонический icon contract в `config/ui-config.js` уже использует browser paths вида `/icons/...`;
2. PNG лежат в верхнеуровневой папке `public/icons/*`;
3. native menu в `main.js` уже берёт те же canonical browser paths и переводит их в fs-path через bridge к `process.cwd()/public/icons`;
4. `platform-config.js` больше не хранит отдельную icon map;
5. renderer-side surfaces уже используют `pngIconRenderer.js`;
6. menu text labels уже text-only и не должны быть снова засорены emoji/glyphs.

Reviewer обязан удержать эти инварианты.

## 2. Проблема

Текущая проблема не в `ui-config.js` и не в наличии самих PNG-файлов.
Проблема в runtime serving для renderer.

Симптом:
- native menu работает;
- renderer icons визуально не видны.

На текущем срезе это объясняется тем, что:
- `vite.config.js` задаёт `root: 'renderer'`;
- browser paths уже записаны как `/icons/...`;
- PNG лежат в top-level `public/icons/*`;
- но Vite public wiring не доведён до этой структуры.

Итог:
- menu читает иконки напрямую с файловой системы и работает;
- renderer ожидает browser-served assets, но current Vite config это не гарантирует.

## 3. Целевая семантика

После исправления должно быть истинно всё:

1. renderer surfaces реально показывают PNG иконки в живом UI;
2. canonical browser icon contract остаётся `/icons/...`;
3. top-level `public/icons/*` сохраняется;
4. native menu продолжает работать через bridge в `main.js`;
5. не появляется новый второй source of truth;
6. не появляется новая ad-hoc path system;
7. не появляется новый asset relocation pass;
8. renderer не использует hand-made hacks вместо нормального Vite public wiring.

## 4. Что сначала проверить

Reviewer обязан сначала проверить и зафиксировать в `codex_task_md`:

1. `vite.config.js`
   - сейчас ли там только:
     - `root: 'renderer'`
     - server config
   - отсутствует ли явный `publicDir`

2. `config/ui-config.js`
   - все renderer/menu icon paths действительно имеют формат `/icons/...`

3. фактическое расположение PNG:
   - это top-level `public/icons/*`, а не `renderer/public/icons/*`

4. `main.js`
   - menu bridge уже переводит `/icons/...` в `process.cwd()/public/icons/...`
   - этот кусок не нужно переписывать без причины

5. `renderer/ui/pngIconRenderer.js`
   - проверить, не пытались ли там маскировать проблему через ad-hoc path rewrite вместо нормального Vite public wiring

6. tests:
   - проверить, что текущие tests в основном валидируют wiring/paths/existence, но не валидируют Vite public contract

## 5. Exact implementation path — без свободы выбора

Reviewer обязан зафиксировать для Codex ровно следующий путь.

### 5.1. Не менять icon contract
Оставить без изменения:
- browser paths в config как `/icons/...`
- top-level папку `public/icons/*`
- menu bridge в `main.js`, который резолвит browser paths в fs paths через `process.cwd()/public/icons`

### 5.2. Исправить Vite public wiring
В `vite.config.js` нужно явно задать:
- `publicDir: '../public'`

при сохранении:
- `root: 'renderer'`

Это обязательный fix.
Не переносить сейчас все PNG в другую папку.
Не менять `/icons/...` на другой формат.
Не перепридумывать asset contract.

### 5.3. Не лечить bug костылями в renderer helper
`pngIconRenderer.js` не должен становиться местом для новой ad-hoc системы резолва путей, если проблема решается корректной настройкой Vite.

Правило:
- renderer должен получать корректный browser-served path;
- источник правды = config `/icons/...`;
- Vite должен раздавать эти файлы правильно;
- не нужно городить path hacks, string replace pipelines, произвольные branch’и для dev вместо настройки publicDir.

Если в текущем helper уже есть временные path-hacks, reviewer должен потребовать от Codex оценить, нужны ли они после правильной настройки `publicDir`.
Если после фикса `publicDir` они не нужны — удалить их.
Если остаются — reviewer обязан потребовать очень чётко обосновать, зачем они нужны именно после корректного Vite wiring.

### 5.4. Не ломать menu
`main.js` уже должен продолжать:
- брать browser path из `APP_CONFIG.ui.icons.assets.menuByAction`
- переводить его в fs path через bridge к top-level `public/icons`

Этот кусок не переписывать в другую архитектуру без необходимости.

## 6. Что именно изменить

### Обязательно
1. `vite.config.js`
   - добавить `publicDir: '../public'`
   - сохранить `root: 'renderer'`
   - не раздувать config лишними unrelated options

2. При необходимости скорректировать tests так, чтобы они проверяли именно новую contract surface:
   - canonical browser paths = `/icons/...`
   - assets реально ожидаются в `public/icons/*`
   - `vite.config.js` содержит нужный `publicDir`
   - renderer wiring не строится на legacy `assets/...`
   - menu bridge остаётся согласованным с top-level `public/icons`

### Проверить, но не менять без причины
1. `renderer/ui/pngIconRenderer.js`
2. `renderer/ui/applyStaticText.js`
3. `renderer/ui/createProjectTree.js`
4. `renderer/ui/createWorkbenchTabs.js`
5. `renderer/app.js`
6. `main.js`

Если после фикса `publicDir` они уже корректны — не раздувать touched zone.

## 7. Что не делать

1. Не возвращать SVG/iconSystem.
2. Не переносить PNG в `renderer/public/icons` отдельным большим pass, если текущая структура чинится через `publicDir`.
3. Не менять canonical `/icons/...` contract.
4. Не возвращать `assets/icons/*` или `assets/menu-icons/*`.
5. Не создавать новый config source of truth для menu icons.
6. Не делать новый renderer-side path mapping pipeline без жёсткой необходимости.
7. Не лечить bug только тестами.
8. Не считать задачу закрытой по статическому wiring без живого runtime результата.
9. Не трогать unrelated save/open/project/runtime semantics.
10. Не запускать `export_project_to_txt.py`.
11. Не генерировать dump.

## 8. Тесты

Reviewer обязан потребовать от Codex:

### 8.1. Обновить / добавить targeted tests
Минимально проверить:

1. `tests/configWiring.integration.test.js`
   - `UI_CONFIG` icon assets используют `/icons/...`
   - required icon files существуют по пути `process.cwd()/public/icons/...`
   - `vite.config.js` содержит:
     - `root: 'renderer'`
     - `publicDir: '../public'`
   - `main.js` по-прежнему строит menu fs path из canonical browser path `/icons/...`

2. renderer wiring tests
   - top panel title wiring использует canonical `/icons/...`
   - tree wiring использует canonical `/icons/...`
   - tab close wiring использует canonical `/icons/...`

### 8.2. Не ограничиваться старыми assertions
Старые assertions уровня:
- path string correct
- file exists
- helper imported

недостаточны сами по себе.
Нужно добавить проверку contract around Vite public serving.

### 8.3. Полный набор тестов
После targeted tests прогнать весь набор тестов целиком.

## 9. Команды проверки

Reviewer должен потребовать от Codex перечислить и выполнить точные команды.
Минимум:
1. targeted tests для config/icon wiring
2. полный test suite целиком

В отчёте должны быть приведены exact command lines и результат каждой команды.

## 10. Что reviewer должен потребовать в итоговом отчёте

Codex обязан в финальном отчёте явно указать:

1. root cause bug’а;
2. какие файлы изменены;
3. что именно изменено в `vite.config.js`;
4. почему выбран именно `publicDir: '../public'`;
5. почему не понадобился relocation PNG в новую папку;
6. оставлен ли menu bridge в `main.js` без изменений;
7. потребовались ли изменения в `pngIconRenderer.js`, и если да — почему;
8. какие targeted tests добавлены/изменены;
9. результат полного набора тестов;
10. финальный статус:
   - renderer icons should now be served by Vite and visible in runtime UI.

## 11. Формат `codex_task_md`

Reviewer обязан выдать `codex_task_md` в жёстком операционном стиле с разделами:

1. Контекст и проблема
2. Целевая семантика
3. Что сначала проверить
4. Что именно изменить
5. Что не делать
6. Тесты
7. Команды проверки
8. Формат итогового отчёта

Codex не должен сам выбирать другой implementation path.