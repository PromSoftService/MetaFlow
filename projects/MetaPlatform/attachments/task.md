[URL]
https://github.com/PromSoftService/MetaPlatform

[BASE]
38a3a4bcb8659fe9c3482ebcd219682ece8848d3

[TASK]
Проверочный минимальный цикл MetaFlow.

Рабочее окружение:
- Codex выполняет `codex_task_md` в локальной папке repo на Windows.
- `extra_test_commands` выполняются MetaFlow в этой же локальной папке repo на Windows.
- Команды для Codex и `extra_test_commands` пиши под Windows shell.

Цель:
- проверить, что reviewer ставит Codex простую задачу на изменение repo;
- Codex вносит изменение и делает commit;
- Codex возвращает локальный head в summary;
- reviewer добавляет команды публикации и проверки через `extra_test_commands`;
- MetaFlow выполняет `extra_test_commands`;
- reviewer читает `[TECHNICAL_CHANNEL].extra_commands_output` и проверяет результат через GitHub compare `BASE...head`.

Что reviewer должен поручить Codex:
1. В корне репозитория создать файл:
   metaflow_smoke_test_2.txt

2. Записать в файл ровно одну строку:
   MetaFlow GitHub reviewer smoke test 2

3. Выполнить локальные Windows-проверки:
   - `dir metaflow_smoke_test_2.txt`
   - `type metaflow_smoke_test_2.txt`
   - `git status -sb`

4. Сделать commit с сообщением:
   MetaFlow. github-reviewer-smoke-test-2

5. В summary указать:
   - `head`: локальный commit hash после commit;
   - commit message;
   - созданный файл;
   - содержимое файла;
   - какие проверки запускались;
   - результат проверок.

Что reviewer должен добавить в `extra_test_commands` после Codex:
1. `git push origin main`
2. `git rev-parse HEAD`
3. `git rev-parse origin/main`
4. `git status -sb`
5. `dir metaflow_smoke_test_2.txt`
6. `type metaflow_smoke_test_2.txt`

Критерий проверки reviewer после `extra_test_commands`:
1. Взять `BASE` из секции `[BASE]`.
2. Взять `head` из Codex summary в `[MODEL_CHANNEL]`.
3. Прочитать `[TECHNICAL_CHANNEL].extra_commands_output`.
4. Убедиться, что `git push origin main` завершился успешно.
5. Убедиться, что stdout `git rev-parse HEAD` совпадает с `head`.
6. Убедиться, что stdout `git rev-parse origin/main` совпадает с `head`.
7. Проверить GitHub compare `BASE...head`.
8. Убедиться, что compare содержит файл `metaflow_smoke_test_2.txt`.
9. Убедиться, что файл содержит строку:
   MetaFlow GitHub reviewer smoke test 2

Если все пункты подтверждены — вернуть `status = done`.
Если нужен следующий проход — вернуть `status = continue` с конкретным `codex_task_md` и `extra_test_commands`.
