Новая задача: завершить backend export shared project из текущего состояния репозитория.

Перед началом изменений обязательно проверить helper-скрипты:
- create_project_structure.py
- export_project_to_txt.py
и после изменений привести их в актуальное состояние.

КОНТЕКСТ
По текущему состоянию уже видно следующее:
- в backend contract уже добавлены `projectExportsEndpoint`, `exportProject`, `PROJECT_EXPORT_FAILED`; :contentReference[oaicite:0]{index=0}
- в Electron/preload уже добавлен save binary dialog для сохранения zip на локальную машину; :contentReference[oaicite:1]{index=1}
- во frontend catalog уже есть кнопка `Export` и отдельный flow через `runBackendProjectExport(...)`; :contentReference[oaicite:2]{index=2}
- helper whitelist уже расширен новым файлом `renderer/runtime/backendProjectExportFlow.js`; :contentReference[oaicite:3]{index=3}

Это значит, что задача не “с нуля”, а на добивание и верификацию уже начатого export vertical slice.

ЦЕЛЬ ЭТОЙ ЗАДАЧИ
Довести до DONE backend export shared project:
1. backend command:
- platform.exportProject
2. backend download endpoint для zip-архива
3. frontend export action из backend catalog
4. локальное сохранение архива пользователю
5. тестовое подтверждение, что export не мутирует storage и реально работает end-to-end

ВАЖНОЕ ОГРАНИЧЕНИЕ ЭТАПА
На этом этапе НЕ реализовывать:
- importProject
- project locks
- sessions
- heartbeat
- process execution
- metagen.generate
- metalab.run
- active-process mode
- большой refactor project browser
- cloud/object storage
- async jobs/queues
- streaming/orchestration beyond simple current implementation

ЧТО СНАЧАЛА ПРОВЕРИТЬ
Обязательно просмотреть:
- create_project_structure.py
- export_project_to_txt.py
- config/platform-config.js
- renderer/app.js
- renderer/runtime/backendProjectExportFlow.js
- renderer/runtime/runtimeClientContract.js
- renderer/runtime/runtimeClient.js
- renderer/runtime/adapters/createHttpRuntimeAdapter.js
- renderer/runtime/fileSystemBridge.js
- main.js
- preload.cjs
- runtime_backend/app/main.py
- runtime_backend/app/api/commands.py
- runtime_backend/app/services/command_dispatcher.py
- runtime_backend/app/services/project_storage.py
- runtime_backend/tests/test_commands.py

После просмотра сначала дать короткую фактическую оценку:
- что уже реализовано полностью,
- что реализовано частично,
- чего не хватает до DONE.

ЧТО ИМЕННО НУЖНО ДОДЕЛАТЬ
Нужно закрыть именно export scope, без расползания в соседние задачи.

1. Backend command semantics
Проверить и при необходимости довести:
- `platform.exportProject`
payload:
{
  "projectId": "string"
}
result:
{
  "exportToken": "string",
  "downloadUrl": "string",
  "fileName": "string"
}
или другой уже реализованный эквивалентный контракт, если он последователен и покрыт тестами.

2. Backend export storage flow
Проверить и при необходимости довести:
- поиск project current/
- сборку zip во временную export area
- отсутствие мутаций current/ в процессе export
- cleanup export artifacts
- одноразовость или иная явно зафиксированная семантика export token
- корректное поведение при missing project / invalid token / повторном скачивании

3. Backend download route
Проверить и при необходимости довести:
- отдельный route скачивания архива
- корректный content-type/content-disposition
- безопасную выдачу готового zip
- cleanup временного файла после consumption, если выбрана такая модель

4. Frontend export flow
Проверить и при необходимости довести:
- кнопка `Export` в backend catalog
- вызов backend command
- скачивание binary payload
- сохранение через `saveBinaryFileAsDialog`
- корректный default file name
- корректная обработка cancel/error
- отсутствие влияния на текущий runtime/project state

5. Electron bridge
Проверить и при необходимости довести:
- `saveBinaryFileAsDialog` в main/preload/fileSystemBridge
- согласованность channel names/config wiring
- запись bytes без порчи архива

6. Tests
Обязательно довести покрытие до явного DONE.

ОБЯЗАТЕЛЬНЫЕ BACKEND TESTS
Минимум:
- exportProject success
- exportProject missing project -> PROJECT_NOT_FOUND
- download by valid token success
- invalid/unknown token -> согласованная ошибка/404
- archive реально содержит:
  - project.yaml
  - metagen/
  - metalab/
  - metaview/
  - generated/ если это часть текущего storage contract
- export не мутирует current project storage
- cleanup export artifacts работает
- если токен одноразовый, это должно быть явно покрыто тестом

ОБЯЗАТЕЛЬНЫЕ FRONTEND TESTS
Минимум:
- backend catalog export wiring
- export flow вызывает backend command, downloadBinary и saveBinaryFileAsDialog
- cancel сохранения не ломает runtime
- export не закрывает текущий проект
- export работает и для opened, и для non-opened backend project
- ошибки скачивания/сохранения логируются и не ломают UI state

ОБЯЗАТЕЛЬНО ПРОВЕРИТЬ СТАРЫЕ ТЕСТЫ
Не сломать:
- list/create/open/save/saveAs/delete backend tests
- local desktop flows
- runtime client / adapter wiring
- helper whitelist policy

ГРАНИЦЫ СВОБОДЫ ДЛЯ REVIEWER
Reviewer может сам выбрать:
- оставить текущий export contract как есть, если он уже консистентен;
- минимально поправить result shape, если это нужно для чистоты API;
- оставить одноразовый token flow, если он уже реализован и тестируем;
- минимально дооформить logging/messages.

Reviewer не должен:
- начинать import
- тянуть locks
- делать большой рефактор frontend
- менять local save/open semantics
- вводить новый формат архива
- раздувать diff задачами вне export scope

ЧТО НЕ ДЕЛАТЬ
- не переходить к importProject
- не делать project browser redesign
- не добавлять process/runtime execution
- не делать watch/server foreground команды без bounded wrapper в extra_test_commands
- не оставлять export только “частично wired” без end-to-end проверки
- не забыть обновить helper scripts

КОМАНДЫ ПРОВЕРКИ
Исполнитель обязан перечислить и реально использовать точные команды проверки.

Минимально ожидается:
- npm test
- python -m pytest runtime_backend/tests -q

Если нужен startup probe backend:
- использовать только bounded wrapper/probe, который сам завершается
- не добавлять в extra_test_commands:
  - python -m uvicorn ...
  - npm run dev
  - vite
  - electron .
  - любые server/watch процессы без bounded wrapper

HELPER-СЦЕНАРИИ
Обязательно:
1. проверить create_project_structure.py
2. проверить export_project_to_txt.py
3. добавить новые backend/frontend/runtime файлы и runtime_backend/tests/* если появятся
4. не возвращать top-level tests/, public/icons/, demo project

ФОРМАТ ИТОГОВОГО ОТЧЕТА
Итоговый отчет reviewer обязан вернуть так:

1. Что проверено перед изменениями
- отдельно create_project_structure.py
- отдельно export_project_to_txt.py

2. Что уже было реализовано к старту этой задачи
- перечислить готовые части export flow
- перечислить частично готовые части
- перечислить незакрытые пробелы

3. Что было до изменений
- backend export scope был начат, но не доведен до полностью подтвержденного DONE

4. Что реализовано
- platform.exportProject
- backend archive build
- download route
- frontend export flow
- saveBinaryFileAsDialog integration
- cleanup semantics
- final test coverage

5. Какие файлы добавлены
- полный список

6. Какие файлы изменены
- полный список

7. Какие тесты добавлены/изменены
- полный список

8. Какие helper-скрипты обновлены
- полный список

9. Какие команды проверки запущены
- точный список

10. Результаты проверок
- что прошло
- что не прошло

11. Старое и новое покрытие сценариев
- отдельно старые сценарии
- отдельно новые сценарии

12. Финальный статус
- DONE / PARTIAL / FAILED

КРИТЕРИЙ DONE
Эту задачу считать завершенной только если одновременно выполнено всё:
- backend project можно экспортировать через `platform.exportProject`;
- пользователь реально получает zip-архив;
- архив сохраняет каноническую структуру проекта;
- export не мутирует current storage;
- frontend export flow подтвержден тестами, а не только backend tests;
- local workflows не сломаны;
- helper scripts актуализированы;
- все тесты прогнаны целиком.