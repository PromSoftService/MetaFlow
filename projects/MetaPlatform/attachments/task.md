[URL]
https://github.com/PromSoftService/MetaPlatform

[CURRENT_COMMIT]
54a946e5c7414a02334634486e6eb6577851a5dd

[TASK]
Cleanup product-кода MetaPlatform после серии попыток устранить утечку памяти.

Это НЕ задача на устранение текущей известной Univer-утечки.
Это задача на очистку product-кода от возможного мусора, workaround-логики, monkey-patch следов и лишней защитной обвязки, накопленных во время memory-leak investigation.

Текущий baseline:
- `54a946e5c7414a02334634486e6eb6577851a5dd`;
- MemLab tooling, MemLab scenarios, reports, config extra commands и test infrastructure НЕ являются scope этой задачи;
- workspace memory guard уже настроен в MetaFlow config и используется только как post-Codex safety check.

Главная цель:
- довести product-код вокруг Univer/editor/tabs/tree lifecycle до качества примерно 7.75/10;
- удалить только реально лишние или криво лежащие memory-leak workaround следы;
- оставить всё, что легитимно, просто, стабильно и имеет понятную ответственность;
- не переписывать систему ради красоты;
- не открывать architecture redesign.

Reviewer должен сам разбить этот глобальный cleanup на небольшие последовательные Codex passes.

Один Codex pass = один небольшой product-code scope.

Запрещено отправлять Codex весь этот task целиком.

## Source of truth

Reviewer обязан сначала проверить текущий GitHub repo на commit `54a946e5c7414a02334634486e6eb6577851a5dd`.

Список ниже — это не приказ удалить всё подряд, а направления проверки.

Если конкретный участок уже выглядит нормально и не содержит memory-leak workaround мусора, reviewer должен оставить его в покое.

Если участок выглядит криво, но правка раздувает diff или требует архитектурного разворота, reviewer должен ограничить scope и не тянуть это в текущий cleanup pass.

## Что НЕ входит в scope

Не трогать в рамках этой задачи:
- `tools/memlab/**`;
- MemLab scenarios;
- MemLab reports;
- test cleanup;
- переписывание тестов под “финальную семантику”;
- magic strings / magic numbers cleanup как отдельную тему;
- docs / architecture_timeline / todo cleanup;
- export helper cleanup;
- package scripts;
- package-lock;
- backend;
- import/export YAML contract;
- UI visual/layout cleanup.

Допустимо запускать существующие проверки, но не превращать задачу в cleanup тестов.

## Общий критерий качества

После cleanup product-код должен быть:

- понятнее;
- короче там, где текущая сложность не доказана;
- без “лечения вокруг причины”;
- без monkey-patch / timer / MessageChannel / guessed DOM root логики;
- без двойных/повторных dispose “на всякий случай”, если нет source-proven причины;
- без временных diagnostic hooks;
- без временных leak-specific flags;
- без новых общих lifecycle manager/coordinator/orchestrator/framework слоёв.

Код не обязан быть идеальным.
Целевой уровень — примерно 7.75/10: достаточно чисто, сопровождаемо, без очевидной кривизны и временного мусора.

## Post-Codex safety check

MetaFlow post-Codex этап уже запускает workspace memory guard.

Reviewer должен считать memory guard PASS, если:
- `METAFLOW_MEMORY_GUARD_STATUS=ok`;
- `METAFLOW_MEMORY_GUARD_OTHER_LEAK=false`;
- `METAFLOW_MEMORY_GUARD_CLASS=no_leaks` или `known_univer_leak`.

`known_univer_leak` не блокирует этот cleanup task.

Reviewer должен блокировать cleanup-pass, если:
- `METAFLOW_MEMORY_GUARD_CLASS=unknown_non_univer_leak`;
- `METAFLOW_MEMORY_GUARD_CLASS=memlab_failed`;
- `METAFLOW_MEMORY_GUARD_CLASS=summary_parse_failed`;
- `METAFLOW_MEMORY_GUARD_OTHER_LEAK=true`;
- guard не вывел machine-readable markers;
- `METAFLOW_FINAL_HEAD` и `METAFLOW_ORIGIN_MAIN` отсутствуют или не совпадают.

Если появилась новая non-Univer утечка, reviewer должен остановить обычный cleanup и вернуть `status = "question"` или `status = "escalate"` с кратким retained edge и ссылкой на committed report.

## Область 1. Univer runtime lifecycle wrapper

Главная зона проверки:
- `ui/renderer/modules/metagen/tables/createMetaGenSimpleSheet.js`

Проверить:
- owned mount container;
- runtime render container detection;
- child snapshot logic;
- `detachRuntimeDesignRoot`;
- двойной `@univerjs/design unmount`;
- `disposeUnit`;
- `univerAPI.dispose`;
- `univer.dispose`;
- ручной `clearRuntimeContainer`;
- detach owned mount container;
- ручное обнуление runtime refs;
- комментарии, которые объясняют workaround, но больше не соответствуют фактическому решению.

Target semantics:
- wrapper создаёт Univer sheet runtime;
- wrapper отдаёт workbook/sheet/API наружу;
- wrapper имеет idempotent dispose;
- dispose выполняет только доказанно нужные шаги;
- порядок dispose понятен и не выглядит как “магическая шрапнель”;
- exact root container semantics сохранена, если она действительно нужна;
- host DOM cleanup остаётся только там, где wrapper реально владеет DOM node;
- wrapper не пытается лечить root retention через DOM-tail cleanup.

Что можно удалить или упростить, если reviewer подтвердит по коду, что это memory-leak workaround без пользы:
- child snapshot / renderContainer guessing;
- повторный design unmount;
- clear render child;
- clear host container;
- лишнюю owned-container обвязку;
- лишние refs/nulling, если они не дают реального release и только шумят;
- comments про старую гипотезу.

Что можно оставить:
- owned mount container, если он реально нужен для exact root ownership;
- один понятный design unmount, если он source-proven;
- `disposeUnit`, если он реально нужен для workbook/sheet/render cleanup;
- `univer.dispose`, если это реальный owner dispose;
- idempotent dispose;
- безопасное nulling refs после dispose, если оно компактное и не маскирует проблему.

Done criteria по области:
- `createMetaGenSimpleSheet.js` стал проще или reviewer явно подтвердил, что текущая сложность оправдана;
- нет private React marker probing;
- нет guessed child unmount вместо exact root container;
- нет DOM-tail cleanup как основного fix;
- dispose contract читается сверху вниз;
- нет комментариев, противоречащих текущему known leak status;
- Codex summary объясняет, какие dispose шаги оставлены и почему.

## Область 2. Table factories вокруг Univer runtime

Проверить:
- `ui/renderer/modules/metagen/tables/*Sheet.js`;
- `ui/renderer/modules/metalab/tables/*Sheet.js`;
- вызовы `createMetaGenSimpleSheet`.

Target semantics:
- конкретные table factories не знают про memory leak;
- они только готовят данные/стили/конфиг таблицы;
- вызывают общий Univer sheet runtime wrapper;
- возвращают table-specific API;
- не содержат delay/unmount/DOM clear/dispose workaround logic.

Что искать:
- параметры, добавленные только ради leak workarounds;
- cleanup hooks, размазанные по конкретным таблицам;
- повторные dispose/clear;
- временные container hacks;
- leak-specific names/comments.

Done criteria по области:
- table factories либо чистые и не менялись, либо очищены от leak-specific workaround;
- общий lifecycle остаётся в одном runtime wrapper;
- table-specific файлы не компенсируют проблемы Univer lifecycle.

## Область 3. Editor wrappers dispose cleanup

Проверить:
- `ui/renderer/editors/metagen/createMetaGenEditor.js`;
- `ui/renderer/editors/metalab/createMetaLabEditor.js`;
- `ui/renderer/editors/metalab/createMetaLabOpcUaTagsEditor.js`.

Target semantics:
Editor wrapper должен:
- создать DOM editor root;
- создать table runtime;
- подписать dirty/readiness/hotkeys/listeners;
- при dispose отписаться от своих listeners/subscriptions;
- вызвать `table.dispose()`;
- dispose-ить Monaco/Split, если они принадлежат editor;
- убрать свой DOM;
- занулить только свои ссылки.

Editor wrapper не должен:
- лечить Univer leak;
- повторно чистить чужой Univer container;
- делать delay/timer cleanup;
- делать двойной dispose таблиц “на всякий случай”;
- держать diagnostic guards, если они были нужны только для memory investigation.

Что проверить особенно:
- `runtimeActive` guards в Metalab editors: оставить, если они нужны для dirty tracker safety после dispose; удалить/упростить, если это лишний workaround;
- `pendingDisposals` orchestration: оставить, если table.dispose реально может быть async; упростить, если фактически всё sync и код раздут;
- `clearMountElement` + `hostRoot.replaceChildren/remove`: оставить только если это нормальный host cleanup, а не попытка лечить Univer DOM retention;
- `disposeSafely` wrappers: оставить, если они реально улучшают failure isolation; упростить, если они превращают dispose в шум.

Done criteria по области:
- editor dispose логика выглядит как обычный ownership cleanup;
- нет leak-specific workaround на уровне editor;
- нет лишней двойной очистки чужих контейнеров;
- table lifecycle не размазан между editor и table wrapper;
- если файл оставлен без изменений, reviewer объяснил, что он уже достаточно чистый.

## Область 4. Tabs lifecycle sanity cleanup

Проверить:
- `ui/renderer/ui/createWorkbenchTabs.js`.

Предварительная гипотеза:
- tabs lifecycle, скорее всего, в целом нормальный;
- не надо переписывать его без конкретной найденной кривизны.

Что можно оставить:
- `runtime.dispose()`;
- ожидание promise-like dispose, если runtime.dispose может быть async;
- detach pageNode;
- detach tabNode;
- `tabs.delete(...)`;
- `releaseClosedTabEntryReferences(...)`;
- protection against concurrent close;
- sync before close.

Что искать и удалить только если есть:
- MessageChannel workaround;
- setTimeout/delay workaround;
- повторные dispose ради leak;
- временные diagnostic hooks;
- leak-specific comments;
- лишние workaround branches, не влияющие на нормальный close flow.

Done criteria по области:
- если явного мусора нет, файл не трогать;
- closeTab остаётся простым и предсказуемым;
- никакой новой lifecycle abstraction не добавлено;
- tabs не знают про Univer leak.

## Область 5. Project tree / app event boundary sanity cleanup

Проверить:
- `ui/renderer/ui/createProjectTree.js`;
- `ui/renderer/app.js`.

Предварительная гипотеза:
- во время leak investigation могли появиться event-boundary изменения;
- часть из них может быть нормальной decoupling-моделью;
- часть могла быть следом гипотезы “direct click leaks / synthetic click does not leak / MessageChannel helps”.

Reviewer должен отделить одно от другого.

Оставить, если это реальная архитектурная decoupling-модель:
- project tree не знает `projectManager` напрямую;
- tree dispatches explicit action/request events;
- app централизует backend/project actions;
- boundaries имеют понятный contract;
- код реально уменьшает coupling.

Удалить или упростить, если найдено:
- MessageChannel workaround;
- synthetic click workaround;
- dispatch wrappers, существующие только ради leak-гипотезы;
- event indirection без настоящего product contract;
- stale test-only fake DOM branches в product path, если они реально мусор;
- comments про старые leak hypotheses.

Не делать:
- не переписывать project tree architecture целиком;
- не возвращать direct coupling только ради “меньше строк”;
- не ломать реальные UI/action contracts;
- не трогать app/tree, если по коду там нет memory-leak мусора.

Done criteria по области:
- app/tree boundary либо признан нормальным и оставлен, либо упрощён точечно;
- нет MessageChannel/click-boundary workaround следов;
- нет новой общей abstraction;
- changed files минимальны.

## Область 6. Naming / ownership clarity вокруг createMetaGenSimpleSheet

Проверить:
- имя `createMetaGenSimpleSheet`;
- фактическое использование в MetaGen и MetaLab table factories.

Проблема:
- имя может быть misleading: runtime используется как общий Univer sheet runtime, а не только MetaGen simple sheet.

Reviewer должен решить по фактическому diff-risk:
- если переименование локальное и безопасное — можно сделать отдельным Codex pass;
- если переименование раздувает diff и не улучшает текущий cleanup materially — оставить имя сейчас и зафиксировать как future cleanup note в summary;
- не делать rename вместе с lifecycle cleanup в одном pass, если это раздувает review.

Возможные целевые имена:
- `createUniverSheetRuntime`;
- `createMetaPlatformUniverSheetRuntime`.

Done criteria по области:
- либо имя улучшено и imports синхронизированы;
- либо reviewer явно решил не переименовывать в текущем cleanup, чтобы не раздувать diff;
- не должно быть half-renamed state.

## Reviewer decomposition

Reviewer должен начинать с области 1.

Рекомендуемый порядок:
1. `createMetaGenSimpleSheet.js` lifecycle cleanup.
2. Table factories cleanup only if area 1 revealed leaked workaround parameters/spread.
3. Editor wrappers cleanup.
4. Tabs lifecycle sanity check; change only if actual workaround found.
5. Project tree/app boundary sanity check; change only if actual workaround found.
6. Optional naming cleanup as separate pass.

Reviewer может остановить cleanup раньше, если после первых passes product-код уже достигает качества 7.75 и оставшиеся зоны выглядят нормально.

Reviewer не обязан проходить все области с изменениями.
Reviewer обязан пройти все области с inspection verdict.

## Каждый codex_task_md должен содержать

- Context;
- Current scope;
- Target semantics;
- What to inspect first;
- Required changes;
- Files allowed to change;
- Do not do;
- Verification;
- Result report.

Codex task должен быть конкретным и маленьким.

Codex task не должен:
- поручать Codex “разобраться во всём cleanup”;
- менять MemLab tooling;
- менять tests ради cleanup;
- менять config;
- менять docs;
- менять export helper;
- делать commit/push;
- запускать MemLab вручную, если это уже делает MetaFlow post-Codex.

## Verification

Codex должен запускать только существующие релевантные проверки по изменённой зоне, если они есть и если это не требует долгого/нестабильного окружения.

Если затронут `createMetaGenSimpleSheet.js`, предпочтительно запустить существующие проверки:
- `cd ui && node --test ../tests/metagen_univer_runtime_dispose.test.js`
- `cd ui && node --test ../tests/metalabOpcUaTags.test.js`

Если затронуты editors/tabs/tree/app:
- выбрать существующие точечные `node --test` файлы по этим зонам;
- если точного теста нет, не добавлять новый тест только ради cleanup;
- в summary явно написать, что проверено кодом и какие существующие проверки запущены.

MetaFlow post-Codex сам выполнит project-level commands и workspace memory guard.

Reviewer после post-Codex обязан проверить:
1. `METAFLOW_FINAL_HEAD` найден.
2. `METAFLOW_ORIGIN_MAIN` найден.
3. `METAFLOW_FINAL_HEAD == METAFLOW_ORIGIN_MAIN`.
4. Commit опубликован в GitHub.
5. Changed files соответствуют текущему small scope.
6. Workspace memory guard не выявил новую non-Univer утечку.
7. Нет запрещённых workaround подходов в diff.
8. Код стал проще или reviewer явно объяснил, почему оставленная сложность оправдана.

## Do not do

- Не трогать `tools/memlab/**`.
- Не трогать MemLab scenarios/reports/guard.
- Не менять `config.yaml`.
- Не делать test cleanup.
- Не переписывать tests под финальную семантику.
- Не делать magic strings/magic numbers cleanup отдельной темой.
- Не трогать docs/todo/architecture timeline.
- Не трогать export helper.
- Не трогать backend.
- Не трогать package scripts/package-lock.
- Не открывать broad architecture cleanup.
- Не вводить RuntimeLifecycleManager / DisposeOrchestrator / Coordinator / Manager / Framework.
- Не вводить new common lifecycle abstraction.
- Не использовать React private markers:
  - `__reactContainer$`;
  - `_reactRootContainer`.
- Не угадывать React root через DOM descendants.
- Не лечить `HTMLCollection`, `CSSStyleDeclaration`, `children`, `style` как самостоятельную причину.
- Не добавлять timer flushing.
- Не monkey-patch `setTimeout`.
- Не добавлять MessageChannel workaround.
- Не добавлять delay “на всякий случай”.
- Не делать cleanup ради уменьшения строк, если код сейчас понятный и корректный.

## Общий done criteria

Cleanup считается завершённым, когда:

1. Reviewer проверил все области из task.
2. Все реально найденные memory-leak workaround следы в product-коде либо удалены/упрощены, либо reviewer явно подтвердил, что они уже стали нормальной product semantics.
3. `createMetaGenSimpleSheet.js` либо упрощён, либо reviewer доказал, что текущая dispose сложность оправдана и безопасна.
4. Editor wrappers не содержат лишней leak-specific компенсации.
5. Tabs не содержат MessageChannel/timer/repeated-dispose workaround.
6. Project tree/app boundary не содержит click-boundary workaround, если он не является реальным product contract.
7. Никакие MemLab tools/config/tests/docs/backend/export/package files не менялись без отдельной причины.
8. Diff маленький по каждому pass.
9. Код после cleanup оценивается reviewer как минимум на 7.75/10 по читаемости, ответственности, отсутствию временного мусора и сопровождению.
10. Post-Codex checks опубликованы.
11. `METAFLOW_FINAL_HEAD == METAFLOW_ORIGIN_MAIN`.
12. Workspace memory guard вернул PASS:
    - `METAFLOW_MEMORY_GUARD_STATUS=ok`;
    - `METAFLOW_MEMORY_GUARD_OTHER_LEAK=false`;
    - class `no_leaks` или `known_univer_leak`.
13. Reviewer проверил GitHub diff финального commit, а не только Codex summary.

## Result report для final done

Когда reviewer считает cleanup завершённым, summary должен содержать:

- какие области проверены;
- какие области изменены;
- какие области оставлены без изменений и почему;
- какие workaround следы удалены;
- что оставлено как нормальная product semantics;
- итоговую субъективную оценку качества кода после cleanup по шкале 0..10;
- `METAFLOW_FINAL_HEAD`;
- memory guard verdict.