Работать только по текущему срезу проекта.
Не опираться на старые версии/срезы.
Это НОВАЯ ОТДЕЛЬНАЯ ЗАДАЧА после завершения предыдущей итерации про runtime client/local adapter.
Предыдущую итерацию дальше не расширять.
Нужно довести до DONE небольшой следующий этап и не раздувать diff сверх этого этапа.
Перед началом изменений обязательно проверить helper-скрипты:
- create_project_structure.py
- export_project_to_txt.py
и после изменений привести их в актуальное состояние.
КОНТЕКСТ
В текущем срезе уже есть базовый runtime abstraction layer на frontend:
- renderer/runtime/runtimeClientContract.js
- renderer/runtime/runtimeClient.js
- renderer/runtime/adapters/createLocalRuntimeAdapter.js
- wiring в renderer/app.js
Это значит, что этап “ввести runtime client / local adapter” считать завершенным и НЕ продолжать в этой задаче.
Следующий логичный шаг — не трогать сразу locks/process execution/full workspace UI, а сделать минимальный backend skeleton и первый настоящий domain command contract.
ЦЕЛЬ ЭТОЙ ЗАДАЧИ
Реализовать минимальный Python runtime backend skeleton и подключить к frontend первый backend-backed domain command flow для project catalog, не ломая существующий local project open/save flow.
На этом этапе сделать только:
1. backend skeleton на Python
2. единый HTTP endpoint для command dispatch
3. Pydantic request/response модели командного контракта
4. минимальный backend storage bootstrap
5. SQLite bootstrap с минимальной схемой users/projects
6. domain commands:
- platform.listProjects
- platform.createProject
7. frontend HTTP runtime adapter или отдельный backend command adapter
8. минимальный frontend project browser/catalog UI только для:
- list projects
- create project
Без перевода всего приложения на новый workflow.
ВАЖНОЕ ОГРАНИЧЕНИЕ ЭТАПА
На этом этапе НЕ реализовывать:
- openProject через backend
- saveAll через backend
- saveProjectAs через backend
- import/export
- project locks
- sessions
- process execution engine
- metagen.generate
- metalab.run
- process console UI
- active-process mode
- полную замену старых menu open/save/save-as сценариев
- полный workspace browser вместо текущего project workflow
Это отдельные следующие задачи.
ЧТО СНАЧАЛА ПРОВЕРИТЬ
Обязательно просмотреть:
- create_project_structure.py
- export_project_to_txt.py
- renderer/runtime/runtimeClientContract.js
- renderer/runtime/runtimeClient.js
- renderer/runtime/adapters/createLocalRuntimeAdapter.js
- renderer/app.js
- renderer/core/projectManager.js
- tests/runtimeClient.test.js
- tests/localRuntimeAdapter.test.js
- tests/runtimeBoundary.test.js
- tests/configWiring.integration.test.js
Также проверить, есть ли уже в текущем runtimeClientContract удобная модель для domain commands и какие части лучше переиспользовать, а какие аккуратно расширить.
АРХИТЕКТУРНЫЙ СМЫСЛ ЗАДАЧИ
Нужно сделать следующий архитектурный шаг:
- перейти от low-level adapter abstraction к первому настоящему backend command layer;
- но не ломать существующий desktop/local project flow;
- не тащить в этот же diff locks/process/runtime execution.
То есть результат должен быть таким:
- backend уже существует как отдельный слой;
- frontend уже умеет работать с backend commands хотя бы для catalog/create;
- текущий open/save/save-as локального проекта пока живет отдельно и остается рабочим.
ЦЕЛЕВАЯ СЕМАНТИКА
После выполнения задачи должно быть так:
1. В репозитории появился Python backend слой, который можно поднять отдельно.
2. Backend имеет единый HTTP JSON endpoint команд, например /api/commands.
3. Frontend умеет отправлять backend-команды в формате:
{
  "requestId": "...",
  "module": "platform",
  "command": "...",
  "payload": { ... }
}
4. Backend отвечает в унифицированном формате:
{
  "requestId": "...",
  "ok": true | false,
  "result": { ... },
  "error": {
    "code": "...",
    "message": "..."
  }
}
5. Реально работают команды:
- platform.listProjects
- platform.createProject
6. При createProject backend:
- создает запись проекта в SQLite
- создает физическую структуру проекта на диске в backend workspace
- кладет project.yaml и стандартные папки metagen/metalab/metaview/generated
- возвращает project summary
7. Frontend имеет минимальный UI-контур, который может:
- запросить список backend projects
- создать backend project
- показать результат
8. Текущий local workflow через open/save/save-as dialogs и projectManager не ломается и не заменяется на этом этапе.
ТЕХНОЛОГИЧЕСКИЙ ВЫБОР
Backend реализовать на Python.
Использовать:
- Python 3.11+
- FastAPI
- uvicorn
- sqlite3 или SQLAlchemy без лишней сложности
- Pydantic
- pytest
Избыточную архитектурную тяжесть не разводить.
ИЗМЕНЕНИЯ В СТРУКТУРЕ РЕПОЗИТОРИЯ
Добавить новый backend слой, ориентировочно:
runtime_backend/
  app/
    __init__.py
    main.py
    api/
      __init__.py
      routes_commands.py
    db/
      __init__.py
      sqlite.py
      schema.py
      bootstrap.py
    services/
      __init__.py
      project_catalog_service.py
      command_dispatch_service.py
      user_service.py
    models/
      __init__.py
      commands.py
      projects.py
    utils/
      __init__.py
      ids.py
      paths.py
      time.py
  tests/
    test_backend_bootstrap.py
    test_commands_platform_catalog.py
Точные имена файлов можно скорректировать, но разделение по ответственности сохранить.
BACKEND STORAGE
Нужно ввести минимальный backend workspace root, например:
runtime_data/
  app.db
  projects/
    <project_id>/
      current/
        project.yaml
        metagen/
        metalab/
        metaview/
        generated/
На этом этапе backups/exports/imports/process/logs можно не реализовывать полноценно, если они не нужны для list/create.
Но layout paths helper’ами лучше заложить сразу аккуратно.
SQLITE МОДЕЛЬ НА ЭТОМ ЭТАПЕ
Сделать только необходимый минимум:
1. users
- id TEXT PRIMARY KEY
- username TEXT NOT NULL UNIQUE
- display_name TEXT NOT NULL
- role TEXT NOT NULL DEFAULT 'user'
- is_active INTEGER NOT NULL DEFAULT 1
- created_at TEXT NOT NULL
- updated_at TEXT NOT NULL
2. projects
- id TEXT PRIMARY KEY
- name TEXT NOT NULL
- slug TEXT NOT NULL UNIQUE
- description TEXT NULL
- storage_path TEXT NOT NULL
- schema_version INTEGER NOT NULL
- created_at TEXT NOT NULL
- updated_at TEXT NOT NULL
- created_by_user_id TEXT NOT NULL
- updated_by_user_id TEXT NOT NULL
- is_deleted INTEGER NOT NULL DEFAULT 0
Сложную auth не делать.
Current user можно инжектить простой заглушкой.
BACKEND COMMANDS
Реализовать только:
1. platform.listProjects
payload:
{}
result:
{
  "projects": [
    {
      "id": "...",
      "name": "...",
      "slug": "...",
      "updatedAt": "...",
      "lockedBy": null
    }
  ]
}
На этом этапе lockedBy всегда может быть null, потому что locks еще не реализуются.
Но поле лучше уже вернуть в совместимом виде.
2. platform.createProject
payload:
{
  "name": "string"
}
Поведение:
- валидировать имя
- создать project_id/slug
- создать физическую структуру current/
- создать project.yaml в формате, совместимом с текущей платформой
- зарегистрировать проект в SQLite
- вернуть project summary
FRONTEND ИЗМЕНЕНИЯ
1. Не ломать существующий local runtime client flow.
2. Аккуратно расширить runtime client так, чтобы появился backend command path.
3. Можно добавить отдельный adapter, например:
- renderer/runtime/adapters/createHttpRuntimeAdapter.js
или аналогичную структуру.
4. Не нужно переводить весь app.js на backend workflow.
5. Нужно добавить минимальный UI-контур для backend catalog/create.
Допустимо сделать временно:
- отдельную маленькую панель/кнопки/диалог для списка shared projects
- или отдельный временный экран/section
Но не городить сразу полноценный project browser на весь продукт.
6. Этот UI нужен только чтобы реально проверить:
- listProjects
- createProject
7. Старые пункты меню open/save/save-as не менять как основной пользовательский сценарий.
ГРАНИЦЫ СВОБОДЫ ДЛЯ REVIEWER
Reviewer может сам выбрать:
- использовать ли sqlite3 напрямую или тонкий repository/service слой;
- делать ли отдельный http adapter файл или встроить transport в runtime client более компактно;
- где именно разместить минимальный catalog UI.
Но reviewer не должен:
- расширять задачу до open/save/locks/processes;
- начинать полную миграцию project workflow;
- раздувать diff дополнительными несвязанными улучшениями.
ОШИБКИ И КОДЫ ОШИБОК
На этом этапе минимум поддержать:
- VALIDATION_ERROR
- INTERNAL_ERROR
- PROJECT_CREATE_FAILED
Если reviewer считает полезным, можно уже добавить общий error code registry в runtime contract/backend models.
ЧТО НЕ ДЕЛАТЬ
- не продолжать старую задачу про один только runtime client abstraction
- не переписывать projectManager под backend storage
- не переводить openProject/saveProject/saveProjectAs на backend
- не делать project locks
- не делать process execution
- не делать import/export
- не делать полноценный workspace browser
- не трогать staging/rollback save semantics текущего projectManager
- не тащить filesystem backend paths в основной frontend UI вне нужного backend слоя
ТЕСТЫ
ОБЯЗАТЕЛЬНО добавить и/или обновить тесты.
Минимально покрыть:
1. Backend:
- bootstrap sqlite/workspace
- platform.listProjects empty
- platform.createProject success
- повторное создание с конфликтующим slug/name если это предусмотрено
- созданная файловая структура проекта
2. Frontend:
- runtime client/backend adapter wiring
- успешный listProjects
- успешный createProject
- config wiring если были изменения
3. Existing:
- не сломать tests/runtimeClient.test.js
- не сломать tests/localRuntimeAdapter.test.js
- не сломать tests/runtimeBoundary.test.js
- не сломать tests/projectManager.save.integration.test.js
- не сломать tests/projectPaths.test.js
ОБЯЗАТЕЛЬНО прогнать весь набор тестов целиком, а не только измененные.
HELPER-СЦЕНАРИИ
Обязательно:
1. проверить create_project_structure.py
2. проверить export_project_to_txt.py
3. обновить их списки файлов/директорий с учетом:
- runtime_backend/*
- новых frontend runtime/backend adapter файлов
- новых тестов
КОМАНДЫ ПРОВЕРКИ
Исполнитель обязан перечислить и реально использовать точные команды проверки.
Минимально ожидается:
- npm test
- pytest runtime_backend/tests -q
- uvicorn runtime_backend.app.main:app --reload
или фактическая команда запуска backend, если структура немного иная
Если есть дополнительные команды build/typecheck/lint по фактической реализации — перечислить и прогнать тоже.
ФОРМАТ ИТОГОВОГО ОТЧЕТА
Итоговый отчет reviewer обязан вернуть в таком виде:
1. Что проверено в текущем проекте перед изменениями
- отдельно упомянуть create_project_structure.py
- отдельно упомянуть export_project_to_txt.py
- отдельно указать, что runtimeClient/local adapter слой уже существовал до начала этой задачи
2. Что было до изменений
- frontend abstraction layer уже был
- backend отсутствовал
- domain command backend отсутствовал
- project catalog shared workspace отсутствовал
3. Что реализовано
- Python backend skeleton
- SQLite bootstrap
- workspace bootstrap
- platform.listProjects
- platform.createProject
- frontend backend adapter/wiring
- минимальный catalog/create UI
4. Какие файлы добавлены
- полный список
5. Какие файлы изменены
- полный список
6. Какие тесты добавлены/изменены
- полный список
7. Какие helper-скрипты обновлены
- полный список
8. Какие команды проверки запущены
- точный список
9. Результаты проверок
- что прошло
- что не прошло
10. Старое и новое покрытие сценариев
- отдельно старые сценарии
- отдельно новые сценарии
11. Финальный статус
- DONE / PARTIAL / FAILED
КРИТЕРИЙ DONE
Эту задачу считать завершенной только если одновременно выполнено все:
- backend поднимается отдельной командой
- listProjects работает end-to-end
- createProject работает end-to-end
- backend реально создает проект на диске и запись в SQLite
- frontend умеет показать список и создать проект через backend
- существующий local open/save/save-as flow не сломан
- helper-скрипты актуализированы
- весь тестовый набор прогнан целиком

Дополнение к текущему ТЗ reviewer’у.
Нужно изменить helper-скрипт export_project_to_txt.py и связанные правила сопровождения helper-скриптов следующим образом:
1. Из project export to txt исключить:
- все иконки из public/icons/*
- весь demo-проект:
  - project-examples/demo-feedmill/project.yaml
  - project-examples/demo-feedmill/metagen/*
  - project-examples/demo-feedmill/metalab/*
  - project-examples/demo-feedmill/metaview/*
- всю папку tests/*
2. Аналогично привести в согласованное состояние create_project_structure.py:
- не возвращать в списки экспорта/структуры иконки
- не возвращать demo-feedmill
- не возвращать tests
3. Запрет:
- не добавлять иконки, demo-проект и tests обратно в PROJECT_FILES этих helper-скриптов
- если reviewer посчитает нужным, можно ввести явный комментарий над списками PROJECT_FILES, что:
  - helper export предназначен только для рабочего кода и конфигурации
  - assets/demo/tests намеренно исключены
4. Это изменение входит в текущую задачу и должно быть отражено:
- в списке измененных файлов
- в разделе про helper-скрипты
- в итоговом отчете reviewer’а
5. При проверке отдельно зафиксировать, что export_project_to_txt.py больше не экспортирует:
- public/icons/*
- project-examples/demo-feedmill/*
- tests/*