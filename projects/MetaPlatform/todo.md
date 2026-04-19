# TODO: ввести единый operation coordinator для app-level UI действий и сделать его единым execution contract между dialog, shell и runtime/backend

После web-only migration все пользовательские app-level операции должны выполняться по одному общему пути, а не частично из dialog/local flow. Нужен общий слой `operation coordinator` / `transition coordinator`, через который проходят app-level intents:

- `openProject`
- `createProject`
- `importProject`
- `deleteProject`
- `closeProject`
- `saveProject`
- `saveProjectAs`
- `exportProject`
- `exit`

## Целевая семантика

- dialog/surface не оркестрирует бизнес-операцию;
- dialog только:
  - собирает input;
  - возвращает intent/result;
  - может безопасно закрыться в любой момент;
- coordinator:
  - принимает app-level intent;
  - выполняет общие preflight/guards;
  - запускает shell/runtime/backend steps;
  - возвращает единый нормализованный typed outcome;
- shell остается только для browser/system actions;
- backend client остается только для transport/command execution;
- coordinator становится единым execution contract на стыке:
  - `dialog -> coordinator`
  - `coordinator -> shell`
  - `coordinator -> runtime/backend`
  - `coordinator -> UI result/outcome`

## Отдельно про Workspace dialog

Workspace dialog — первый и самый явный кандидат на перевод на coordinator.

Его flow не должен сам оркестрировать app-level операции `openProject`, `createProject`, `importProject`, `deleteProject` и связанные переходы.

Workspace dialog должен быть приведен к роли UI-слоя:

- показать список и локальное состояние интерфейса;
- собрать выбор пользователя;
- вернуть intent/result;
- безопасно закрываться;

а выполнение `openProject`, `createProject`, `importProject`, `deleteProject` должно идти через coordinator.

## Что важно

- не тащить в coordinator низкоуровневые DOM/UI события;
- coordinator работает на уровне action/intention, а не кнопок, `Escape` и локальных UI-хендлеров;
- не делать giant refactor за один проход;
- внедрять поэтапно;
- не плодить новые competing contracts между слоями;
- не оставлять Workspace dialog местом, где частично живет orchestration-логика catalog/project flow.

## Предпочтительный порядок

Первая волна:

- `openProject`
- `createProject`
- `importProject`
- `deleteProject`
- `closeProject`

В рамках этой первой волны — в первую очередь перевести Workspace dialog flow.

Вторая волна:

- `saveProject`
- `saveProjectAs`
- `exportProject`
- `exit`

## Зачем

Чтобы:

- все app-level операции были однотипны;
- guards/transition semantics жили в одном месте;
- dialogs были безопасны к закрытию и не держали business state;
- Workspace dialog перестал быть частичным orchestration-узлом;
- shell, runtime и backend взаимодействовали по одному понятному контракту;
- исчезла размазанная orchestration-логика между dialog/app/runtime flow.

---

# TODO: развести границы ответственности между config, runtime, manager, storage и transport слоями

Сейчас несколько слоев знают слишком много друг о друге и частично пересекаются по обязанностям. Это уже не просто архитектурный долг, а задача на поэтапное упрощение и нормализацию responsibility boundaries.

## Что считается проблемой

- config местами хранит не только semantic constants, но и runtime/policy/orchestration semantics;
- runtime частично тащит на себе orchestration и contract interpretation;
- `projectManager` совмещает слишком много ролей:
  - state holder;
  - document mutation layer;
  - snapshot/export/save payload assembler;
  - backend-aware orchestration node;
- `ProjectStorageService` перегружен и смешивает:
  - storage semantics;
  - import/export transport;
  - lock lifecycle;
  - generation-related knowledge;
- command ids, payload semantics, response envelope и error interpretation частично распределены по нескольким слоям вместо одного четкого контрактного центра;
- transport/contracts размазаны между несколькими слоями;
- `ui/config/ui-config.js` стал смешанным hub-файлом и одновременно содержит:
  - визуальный слой;
  - runtime-политику;
  - event vocabulary;
  - DOM wiring;
  - тексты.

## Целевая семантика

- каждый слой отвечает только за свой уровень;
- config/constants слой хранит semantic values и единые shared contracts, но не orchestration-логику;
- dialog/UI слой отвечает только за UI/input/result;
- runtime orchestration живет отдельно от UI config;
- `projectManager` отвечает за project/document state и связанные state operations, но не за лишнюю transport/backend orchestration semantics;
- `ProjectStorageService` отвечает за storage/persistence semantics, но не за import/export orchestration, lock lifecycle coordination и лишнюю generation-related knowledge;
- command/transport/response contract выделен явно и не размазан по нескольким слоям;
- transport/backend contract интерпретируется через один понятный контрактный центр;
- `ui/config/ui-config.js` перестает быть универсальной свалкой и разделяется по смысловым зонам без появления competing source of truth.

## Что важно

- не делать giant refactor за один проход;
- не создавать второй constants layer;
- не ломать существующий config/constants подход как таковой;
- разделять по смысловым границам, а не механически “разрезать большой файл”;
- внедрять маленькими bounded tasks;
- каждый шаг должен уменьшать пересечение обязанностей, а не просто переносить код между файлами;
- не плодить competing source of truth для command ids, payload semantics, response interpretation и shared policy values.

## Предпочтительный порядок

1. Выделить из `ui/config/ui-config.js` отдельно:
   - visual/ui config;
   - text/tokens;
   - runtime/action/transition vocabulary;
   - DOM ids/selectors.
2. Зафиксировать отдельный контрактный центр для:
   - command ids;
   - payload semantics;
   - response envelope;
   - error interpretation.
3. Зафиксировать отдельный contract boundary между dialog/shell/runtime/backend.
4. Упростить `projectManager` до state/document-level responsibilities.
5. Упростить `ProjectStorageService` до storage/persistence responsibilities.
6. После этого дочистить оставшиеся пересечения config/runtime/transport.

## Зачем

Чтобы:

- изменения стали локальнее и дешевле;
- исчезли лишние знания слоев друг о друге;
- config перестал быть смешанным policy/runtime hub;
- `projectManager` и `ProjectStorageService` вернулись к более узким и понятным обязанностям;
- command/transport/response semantics перестали жить в нескольких местах сразу;
- orchestration, contracts и state responsibilities были разделены по понятным границам;
- дальнейшие bounded tasks не требовали лезть во все слои сразу.

---

# TODO: оформить default user как минимальную системную identity-модель с заделом под будущую многопользовательность

Сейчас приложение однопользовательское, но в дальнейшем планируется многопользовательский режим с авторизацией. Нужно не вводить пользователей “по-настоящему” уже сейчас, а правильно оформить текущий single-user режим как минимальную архитектурную сущность, чтобы потом на нее можно было нарастить полноценную user/session/auth model.

## Целевая семантика

- в системе есть текущий application user как отдельная архитектурная сущность;
- сейчас это один системный пользователь по умолчанию;
- авторизация, login flow, user management и UI для пользователей не вводятся;
- default user не должен висеть случайным литералом в UI/dialog/runtime flow;
- identity должна задаваться централизованно и использоваться как source of truth для lock semantics;
- lock model уже сейчас должна работать через эту identity-модель;
- проекты должны блокироваться на уровне этой модели так, чтобы потом можно было естественно перейти к реальным пользователям.

## Что важно

- не вводить полноценную auth/session subsystem;
- не тащить user-specific UI без необходимости;
- не размазывать `default-user` строкой по разным слоям;
- не делать видимость многопользовательности без архитектурной основы;
- заложить расширяемую точку для будущих:
  - user id;
  - session/user context;
  - same-user / foreign-user lock semantics;
  - авторизации.

## Минимальный правильный результат

- есть явная системная identity сущность/контракт для текущего пользователя приложения;
- backend, runtime и lock lifecycle используют именно ее;
- UI не хранит и не придумывает пользователя сам;
- current single-user mode остается дешевым и простым;
- дальнейший переход к многопользовательности не потребует ломать lock model с нуля.

## Зачем

Чтобы:

- убрать случайный и размазанный `default-user`;
- не держать user identity как скрытый костыль;
- сохранить минимальную текущую реализацию;
- сразу построить правильный фундамент под будущую многопользовательность и авторизацию.

---

# TODO: заменить backend dispatcher `if-chain` на явный command handler registry

Текущий backend dispatcher не должен расти как длинная цепочка `if request.command == ...`. Нужно перевести его на явный registry handlers, сохранив текущий внешний command/response contract.

## Целевая семантика

- `dispatch_command()` остается единым entrypoint для backend command dispatch;
- `dispatch_command()` больше не содержит длинный `if-chain` по platform commands;
- routing выполняется через явный `command -> handler` registry;
- общие preflight/guard checks остаются централизованно в dispatcher;
- конкретная бизнес-логика команд выносится в отдельные handler-функции;
- response envelope и error mapping сохраняют текущий внешний контракт.

## Что важно

- не вводить тяжелый framework / plugin system / autodiscovery;
- не ломать текущие command ids и response shape;
- не смешивать routing, guards и бизнес-логику в одном длинном условном блоке;
- делать bounded refactor без расширения scope.

## Предпочтительный результат

- есть явный registry platform command handlers;
- dispatcher:
  - валидирует request/module;
  - применяет общие guards;
  - находит handler;
  - вызывает handler;
  - нормализует result/error;
- handler-функции живут отдельно от dispatcher;
- добавление новой команды больше не требует роста `if-chain`.

## Зачем

Чтобы:

- backend dispatcher перестал быть ручным роутером на длинной цепочке условий;
- routing стал прозрачнее и локальнее;
- handlers было проще тестировать и сопровождать;
- backend command layer рос без дальнейшего разрастания `dispatch_command()`.