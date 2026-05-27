[URL]
https://github.com/PromSoftService/MetaPlatform

[CURRENT_COMMIT]
5c15857121a4c4adc7b8d740e23a17566da06cc1

[TASK]
Ликвидировать утечку памяти в MetaPlatform в сценарии многократного открытия/закрытия документов через Workspace / project tree / tabs.

В repo уже есть рабочий MemLab runner и отчёты MemLab в `tools/memlab/reports`.

Основная цель:
- найти фактическую причину удержания памяти после open/close;
- устранить утечку в продуктовой логике;
- подтвердить результат повторным MemLab-прогоном.

Scope задачи:
- Workspace;
- project tree;
- document tabs;
- document open/close lifecycle;
- callbacks/listeners/subscriptions/runtime references, связанные с открытием и закрытием документов.

Что reviewer должен сделать на первой итерации:
1. Открыть GitHub repo.
2. Проверить текущую реализацию open/close flow, project tree callbacks и tabs lifecycle.
3. Посмотреть фактический MemLab report в `tools/memlab/reports`, если он уже есть в repo.
4. Сформировать для Codex конкретный первый task на локализацию и исправление ближайшей причины утечки.
5. Не описывать старый retained path как обязательную истину, если он не подтверждён текущим report.

Что Codex должен делать:
1. Работать только с текущим repo.
2. Сначала изучить фактические файлы, отвечающие за:
   - Workspace/project tree;
   - открытие документа;
   - закрытие вкладки;
   - очистку editor/runtime state;
   - регистрацию и снятие listeners/callbacks/subscriptions.
3. Использовать фактический MemLab report как диагностический вход, если он доступен.
4. Найти конкретную цепочку удержания или ближайший подозрительный lifecycle defect.
5. Исправить продуктовый код маленьким focused diff.
6. Запустить релевантные локальные проверки, которые применимы в Windows-среде.
7. Не делать commit.
8. Не делать push.
9. Не запускать MemLab вручную, если MemLab уже запускается post-Codex extra commands.

После Codex:
- MetaFlow сам запускает MemLab через extra commands;
- MetaFlow сам делает commit;
- MetaFlow сам делает push;
- reviewer проверяет `METAFLOW_FINAL_HEAD`, `METAFLOW_ORIGIN_MAIN`, опубликованный commit и новый MemLab report.

Target result:
- после многократного open/close не остаётся утечка памяти класса Workspace / project tree / tabs / document open-close;
- MemLab report после исправления не показывает исходную удерживающую цепочку;
- если появляется другой независимый retained path, reviewer явно отделяет его от текущей задачи и не смешивает в один scope.

Files allowed to change:
- UI/runtime файлы, отвечающие за Workspace, project tree, tabs и document lifecycle;
- связанные тесты, если нужно закрепить исправление;
- узкие helper/test files, если они нужны только для подтверждения исправления.

Do not do:
- не менять широкий архитектурный слой без необходимости;
- не делать общий refactor;
- не переписывать MemLab runner;
- не менять config flow;
- не добавлять новый framework/coordinator/orchestrator;
- не маскировать утечку задержками, таймерами или отключением проверок;
- не подгонять MemLab scenario вместо исправления product code;
- не делать commit/push из Codex task;
- не запускать MemLab из Codex task, если это уже делает MetaFlow extra commands.

Verification:
Codex должен запустить релевантные локальные проверки по изменённой зоне.

Reviewer после post-Codex этапа должен проверить:
1. `METAFLOW_FINAL_HEAD` найден.
2. `METAFLOW_ORIGIN_MAIN` найден.
3. `METAFLOW_FINAL_HEAD == METAFLOW_ORIGIN_MAIN`.
4. Commit опубликован в GitHub.
5. Diff commit соответствует текущему scope.
6. MemLab report создан в `tools/memlab/reports`.
7. Новый report подтверждает устранение утечки Workspace / project tree / tabs / document open-close либо показывает следующий конкретный retained edge для продолжения.

Done criteria:
- исправлен product code, а не только tooling/docs;
- post-Codex MemLab выполнен;
- commit опубликован;
- reviewer видит MemLab report;
- reviewer по report и diff может подтвердить, что исходная задача по утечке закрыта или нужен следующий focused pass.