# task.md

## Коротко
Финальная узкая задача: убрать tracked runtime/test artifacts из git diff, привести `.gitignore` к чистому и актуальному виду для текущего pytest/runtime flow, затем повторно прогнать тесты и подтвердить, что нерелевантный мусор больше не возвращается в diff.

## Контекст
Root-cause analysis и точечный fix test contract уже сделаны:
- backend temp issue закрыта через repo-local `tmp_path` fixture;
- `cacheprovider` отключён в фактическом `test:backend` execution path через `ui/package.json`;
- reviewer уже подтвердил, что текущий незавершённый хвост — это cleanup tracked artifacts и избыточные pytest/runtime ignore rules.

Сейчас в technical channel ещё фигурируют tracked artifacts:
- `rtb/runtime_data/platform.db`
- `rtb/tests/__pycache__/...pyc`

Также `.gitignore` содержит смесь актуальных, дублирующих и, вероятно, устаревших правил для pytest/runtime мусора.

## Current scope
Только:
1. решить `rtb/runtime_data/platform.db` и `rtb/tests/__pycache__/...` как tracked artifacts;
2. привести в порядок `.gitignore` только в части pytest/runtime cleanup;
3. прогнать тесты ещё раз;
4. проверить, что после повторного прогона нерелевантный мусор не возвращается в diff.

Не выходи за этот scope.

## Target semantics
После правки должно быть истинно всё ниже:
- `rtb/runtime_data/platform.db` больше не tracked artifact в diff;
- `rtb/tests/__pycache__/...pyc` больше не tracked artifact в diff;
- `.gitignore` отражает текущий repo layout и текущий pytest/runtime execution path без явных дублей и устаревших правил в этой зоне;
- `cd ui; npm.cmd run test:backend` проходит;
- `cd ui; npm.cmd run test:all` проходит;
- после повторного прогона `git status --short` не показывает новый нерелевантный runtime/test мусор;
- `pytest-cache-files-*` больше не появляются как новый мусор после backend/all test flow.

## What to inspect first
Сначала проверь:
- `.gitignore`
- `ui/package.json`
- `rtb/tests/conftest.py`
- текущий `git status --short`

Затем отдельно проверь:
- tracked ли сейчас `rtb/runtime_data/platform.db`
- tracked ли сейчас `rtb/tests/__pycache__/...`
- какие pytest/runtime ignore rules реально нужны под текущий flow:
  - `.pytest_cache/`
  - `.pytest-temp-tests/`
  - `pytest-cache-files-*/`
  - `__pycache__/`
  - `.tmp/`
- какие rules выглядят дублирующими или устаревшими для текущего repo layout
- существуют ли в проекте ещё реальные пути, ради которых нужны старые ignore entries вроде `runtime_backend/...`

## Required changes
1. Убери из git tracking:
   - `rtb/runtime_data/platform.db`
   - `rtb/tests/__pycache__/...`
   Используй корректный git-based cleanup, а не только локальное удаление файлов без решения tracking problem.

2. Обнови `.gitignore` только в зоне pytest/runtime artifacts.
   - Оставь только реально нужные правила под текущий repo layout и текущий execution path.
   - Удали явные дубли и устаревшие rules, если они действительно уже не нужны.
   - Не делай общий cleanup `.gitignore` вне этого scope.

3. Не меняй test contract повторно, если это не требуется.
   - `ui/package.json` и `rtb/tests/conftest.py` трогай только если повторная проверка покажет реальный незакрытый дефект.
   - Если текущий flow уже работает, не перерабатывай его заново.

4. После cleanup повторно прогоняй тесты и смотри именно на возврат мусора.
   - Отдельно зафиксируй, появляется ли снова:
     - `pytest-cache-files-*`
     - `.pytest_cache`
     - `.pytest-temp-tests`
     - `__pycache__`
     - `platform.db`
   - Важно не “ничего не должно существовать на диске вообще”, а “нерелевантный мусор не должен возвращаться в git diff”.

## Files allowed to change
Можно менять только:
- `.gitignore`

Можно:
- удалить tracked runtime/test artifacts из git index и рабочего дерева, если это необходимо для корректного cleanup.

Только при прямой необходимости по результатам проверки:
- `ui/package.json`
- `rtb/tests/conftest.py`

Новые файлы не создавать без необходимости.
README, helper scripts, docs и export whitelist не трогать.

## Do not do
- Не возвращайся к общему RCA.
- Не делай новый refactor test pipeline.
- Не трогай README, `export_project_to_txt.py`, docs и UI/runtime код вне текущего scope.
- Не оставляй tracked binary/runtime artifacts в финальном diff.
- Не раздувай cleanup до общего “наведения порядка по проекту”.
- Не добавляй новые ignore rules без проверки, что они реально нужны.
- Не держи одновременно общий и узко-дублирующий ignore rule, если один уже покрывает второй.

## Verification
Обязательно приведи фактические результаты этих команд:

```powershell
git status --short
cd ui; npm.cmd run test:backend
cd ui; npm.cmd run test:all
git status --short
```

Если для cleanup tracking нужны дополнительные команды, тоже перечисли их явно, например:
```powershell
git rm --cached rtb/runtime_data/platform.db
git rm --cached -r rtb/tests/__pycache__
```

После тестов отдельно проверь и укажи:
- вернулись ли `pytest-cache-files-*`
- появилась ли `.pytest_cache`
- появилась ли `.pytest-temp-tests`
- вернулись ли `__pycache__`
- вернулся ли `rtb/runtime_data/platform.db` в diff

## Result report
Итоговый отчёт дай строго в таком виде:

1. **Tracked artifacts**
   - что было tracked
   - как именно решено

2. **.gitignore cleanup**
   - какие rules оставлены
   - какие removed как дубли/устаревшие
   - почему итоговый набор достаточен

3. **Verification**
   - полный список реально выполненных команд
   - результат каждой команды
   - `git status --short` до и после

4. **Final state**
   - остался ли нерелевантный runtime/test мусор в diff
   - появляются ли ещё `pytest-cache-files-*`
   - `DONE` / `NOT DONE`

## DONE criterion
DONE только если одновременно:
- `rtb/runtime_data/platform.db` больше не tracked artifact в diff;
- `rtb/tests/__pycache__/...` больше не tracked artifact в diff;
- `.gitignore` очищен от явных дублей/устаревших pytest/runtime rules в текущем scope;
- `cd ui; npm.cmd run test:backend` проходит;
- `cd ui; npm.cmd run test:all` проходит;
- повторная проверка `git status --short` не показывает новый нерелевантный runtime/test мусор.
