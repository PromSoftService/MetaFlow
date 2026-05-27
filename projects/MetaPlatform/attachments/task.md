# Context

Это минимальный end-to-end smoke task для проверки цепочки:

reviewer → Codex → MetaFlow post-Codex commands → reviewer.

Нужно проверить, что:
1. reviewer запускается;
2. reviewer формирует task для Codex;
3. Codex запускается и меняет repo;
4. после Codex выполняются extra commands;
5. MemLab-тест запускается через существующий `run-memlab.cmd`;
6. изменения коммитятся;
7. commit пушится;
8. reviewer на следующей итерации видит `METAFLOW_FINAL_HEAD`, `METAFLOW_ORIGIN_MAIN` и MemLab report.

# Current scope

Минимальная безопасная проверка workflow без изменения продуктовой логики.

# Target semantics

После выполнения Codex и post-Codex этапа в GitHub должен появиться новый commit с простым smoke-файлом, а reviewer должен увидеть:

- Codex summary;
- technical channel;
- extra commands output;
- hash-маркеры;
- опубликованный commit;
- MemLab report в `tools/memlab/reports`.

# What to inspect first

Reviewer должен проверить текущий GitHub repo и убедиться, что можно дать Codex минимальную задачу без затрагивания продуктового кода.

# Required changes

На первой итерации reviewer должен вернуть `status = "continue"` и дать Codex простой task:

1. Создать или обновить файл `metaflow-smoke-check.txt` в корне repo.
2. Записать в файл одну строку:
   `MetaFlow smoke check: Codex touched this file.`
3. Запустить:
   `git status -sb`
4. Не делать commit.
5. Не делать push.
6. Не запускать MemLab.
7. Вернуть summary с указанием изменённого файла и результата команды.

На следующей итерации reviewer должен проверить результат post-Codex этапа:

1. Найти `METAFLOW_FINAL_HEAD` в `[TECHNICAL_CHANNEL].extra_commands_output`.
2. Найти `METAFLOW_ORIGIN_MAIN` в `[TECHNICAL_CHANNEL].extra_commands_output`.
3. Проверить, что `METAFLOW_FINAL_HEAD == METAFLOW_ORIGIN_MAIN`.
4. Проверить, что GitHub repo содержит опубликованный commit `METAFLOW_FINAL_HEAD`.
5. Проверить, что в commit есть `metaflow-smoke-check.txt`.
6. Проверить, что MemLab report создан в `tools/memlab/reports`.
7. Если всё подтверждено — вернуть `status = "done"`.

# Files allowed to change

Codex может менять только:

- `metaflow-smoke-check.txt`

# Do not do

- Не менять продуктовый код.
- Не менять тесты.
- Не менять config.
- Не менять documentation.
- Не менять runner scripts.
- Не запускать MemLab из Codex task.
- Не делать commit из Codex task.
- Не делать push из Codex task.
- Не добавлять `extra_test_commands`, если не нужна точечная дополнительная проверка.

# Verification

Codex должен выполнить только:

`git status -sb`

MetaFlow post-Codex этап сам выполнит MemLab, commit и push через extra commands.

# Result report

Codex должен вернуть:

- changed files;
- command run;
- command result;
- explicit note that commit/push/MemLab were not performed by Codex.

Reviewer после post-Codex этапа должен вернуть `done`, только если опубликованный commit и MemLab report реально видны.