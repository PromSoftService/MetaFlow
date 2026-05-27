# codex_execution.md

## Назначение

Документ задаёт GitHub-based flow для связки:

`reviewer → Codex → MetaFlow post-Codex commands → reviewer`

## Роли

### Reviewer

Reviewer — основной архитектор, аналитик и постановщик задачи.

Reviewer выполняет:

1. Читает GitHub repo.
2. Использует `[URL]` как адрес репозитория.
3. Использует `[BASE]` как исходный commit текущего цикла.
4. Локализует задачу по GitHub repo и текущему reviewer input.
5. Формирует конкретный `codex_task_md`.
6. Формирует `extra_test_commands` для публикации и проверки результата после Codex.
7. Проверяет результат по:
   - `[MODEL_CHANNEL]`;
   - `[TECHNICAL_CHANNEL].extra_commands_output`;
   - GitHub compare `BASE...head`.

Reviewer не меняет repo руками.

### Codex

Codex — исполнитель изменений в локальном repo.

Codex выполняет:

1. Работает в локальной папке repo на Windows.
2. Меняет реальные файлы repo.
3. Запускает локальные Windows-проверки, указанные reviewer.
4. Делает commit.
5. Возвращает summary с локальным `head`.

Codex не выполняет публикацию commit. Публикация выполняется после Codex через `extra_test_commands`.

### MetaFlow

MetaFlow после Codex выполняет `extra_test_commands` в той же локальной папке repo на Windows.

MetaFlow передаёт результат reviewer в `[TECHNICAL_CHANNEL]`.

При включённой настройке:

`technical_channel.include_extra_commands_output: true`

в `[TECHNICAL_CHANNEL].extra_commands_output` попадает stdout/stderr команд из `extra_test_commands`.

## Execution context

Codex выполняет `codex_task_md` в локальной папке repo на Windows.

MetaFlow выполняет `extra_test_commands` в той же локальной папке repo на Windows после завершения Codex.

Команды в `codex_task_md` и `extra_test_commands` нужно писать под Windows shell.

Git-команды:

1. `git status -sb`
2. `git add <files>`
3. `git commit -m "MetaFlow. <commit-name>"`
4. `git rev-parse HEAD`
5. `git push origin main`
6. `git rev-parse origin/main`

Windows-команды проверки файлов:

1. `dir <file>`
2. `type <file>`
3. `powershell -NoProfile -Command "Get-Content .\<file>"`

## Входные данные

В первой итерации reviewer получает repo-контекст в attachments или во входных материалах через специальные секции.

### `[URL]`

GitHub URL репозитория.

Пример:

`https://github.com/PromSoftService/MetaPlatform`

### `[BASE]`

Базовый commit hash до начала работы Codex.

Пример:

`38a3a4bcb8659fe9c3482ebcd219682ece8848d3`

`URL` и `BASE` являются контекстом всей reviewer-сессии.

В следующих итерациях reviewer использует сохранённый контекст этой же сессии.

## Первая итерация

Если это первая итерация и Codex ещё не работал:

1. Reviewer берёт `URL` из секции `[URL]`.
2. Reviewer берёт `BASE` из секции `[BASE]`.
3. Reviewer изучает GitHub repo.
4. Reviewer находит релевантные файлы.
5. Reviewer определяет целевое решение.
6. Reviewer возвращает `status = "continue"`.
7. Reviewer формирует конкретный `codex_task_md`.
8. Reviewer формирует `extra_test_commands` для публикации и проверки результата после Codex.

## Требования к `codex_task_md`

Каждый `codex_task_md`, который предполагает изменение repo, должен указывать:

1. Текущий scope.
2. Файлы, которые Codex должен изменить.
3. Целевую семантику.
4. Локальные Windows-проверки.
5. Commit message в формате:

   `MetaFlow. <commit-name>`

6. Данные, которые Codex должен вернуть в summary:
   - `head`: локальный commit hash после commit;
   - commit message;
   - изменённые файлы;
   - запущенные проверки;
   - результат проверок;
   - краткое описание изменений.

## Commit

После выполнения изменений Codex выполняет:

1. Проверяет изменения локально.
2. Запускает указанные Windows-команды проверки.
3. Делает commit с сообщением:

   `MetaFlow. <commit-name>`

4. Выполняет:

   `git rev-parse HEAD`

5. Возвращает локальный `head` в summary.

Если Codex сделал несколько commit в одной итерации, `head` должен указывать на последний локальный commit.

## `extra_test_commands`

Reviewer задаёт `extra_test_commands` для публикации и проверки результата после Codex.

Базовый набор для repo-change задач:

1. `git push origin main`
2. `git rev-parse HEAD`
3. `git rev-parse origin/main`
4. `git status -sb`

Для проверки файлов добавляются Windows-команды, например:

1. `dir <file>`
2. `type <file>`
3. `powershell -NoProfile -Command "Get-Content .\<file>"`

MetaFlow выполняет эти команды после Codex и передаёт stdout/stderr в `[TECHNICAL_CHANNEL].extra_commands_output`.

## Требования к Codex summary

Codex summary содержит:

1. `head`: локальный commit hash после commit.
2. Commit message.
3. Краткое описание внесённых изменений.
4. Фактически изменённые файлы.
5. Запущенные проверки.
6. Результат проверок.

Минимальный обязательный фрагмент summary:

`head: <local commit hash after commit>`

## Проверка результата reviewer

После Codex reviewer получает:

1. `[MODEL_CHANNEL]` — summary Codex с локальным `head`.
2. `[TECHNICAL_CHANNEL].extra_commands_output` — stdout/stderr post-Codex команд.
3. `[TECHNICAL_CHANNEL].tests_summary` — краткий статус команд и тестов.

Reviewer проверяет:

1. `head` указан в `[MODEL_CHANNEL]`.
2. `git push origin main` в `extra_commands_output` завершился успешно.
3. stdout `git rev-parse HEAD` совпадает с `head`.
4. stdout `git rev-parse origin/main` совпадает с `head`.
5. GitHub compare `BASE...head` строится.
6. Diff `BASE...head` соответствует исходному scope.
7. Проверки файлов подтверждают ожидаемое содержимое.

Если всё подтверждено, reviewer возвращает `status = "done"`.

Если нужен следующий проход Codex, reviewer возвращает `status = "continue"` с новым конкретным `codex_task_md` и новым набором `extra_test_commands`.

Если нужно решение пользователя, reviewer возвращает `status = "question"`.

Если цикл требует внешнего вмешательства, reviewer возвращает `status = "escalate"`.

## Рекомендуемый каркас `codex_task_md`

# Context

Краткий контекст текущей задачи.

# Current scope

Ограниченный scope текущей итерации.

# Target semantics

Целевая семантика или целевая структура.

# Files allowed to change

Конкретные файлы, которые Codex должен менять.

# Required changes

Точные изменения.

# Verification

Windows-команды, которые Codex должен выполнить локально.

# Commit and summary

Указать:

1. Commit message: `MetaFlow. <commit-name>`.
2. Команду `git rev-parse HEAD`.
3. Summary с:
   - `head`;
   - commit message;
   - changed files;
   - проверками и результатами;
   - кратким описанием изменений.

## Рекомендуемый набор `extra_test_commands`

Для repo-change задач:

1. `git push origin main`
2. `git rev-parse HEAD`
3. `git rev-parse origin/main`
4. `git status -sb`

Для smoke-задачи с файлом:

1. `git push origin main`
2. `git rev-parse HEAD`
3. `git rev-parse origin/main`
4. `git status -sb`
5. `dir <file>`
6. `type <file>`
