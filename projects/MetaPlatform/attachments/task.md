# Corrective task: Workspace actions, cards, dialogs and locks

## 1. Коротко

Это corrective task по уже выявленным дефектам Workspace / project dialogs / top panel actions.

Цель — довести текущий Workspace/project-actions scope до фактического DONE:

- восстановить правильный mapping top panel actions;
- привести карточки create/import/existing project к одной layout-системе и одинаковой высоте;
- исправить create card inline editing и validation;
- исправить import cancel no-op;
- исправить existing project cards 3-row render;
- исправить same-user lock availability;
- исправить delete by projectId + confirm + refresh;
- убрать placeholder комментария в Save copy as;
- исправить точки в затронутых текстах;
- добавить/обновить автотесты только на поведение, не на ручной UI-визуал.

Reviewer должен поручить Codex внести repo-изменения и прогнать команды. Reviewer должен проверить фактические outputs команд и diff. Ручную UI-проверку глазами не ставить Codex/reviewer; пользователь проверит UI отдельно.

---

## 2. Контекст

После предыдущего Workspace cleanup пользователь вручную нашёл подтверждённые дефекты:

- `Создать` в top panel выполняет неправильный flow;
- `Импорт` в top panel открывает Workspace вместо import ZIP flow;
- Workspace create card отображается как постоянно открытая форма, а не inline card;
- duplicate/empty validation в create card не работает как Save copy as;
- можно создать проекты с одинаковым именем;
- existing cards склеивают comment/status через `|`;
- existing cards иногда повторяют project name в третьей/meta строке;
- same-user lock `default-user` отображается/работает как foreign lock;
- delete из Workspace card не удаляет проект;
- import cancel в Workspace зависает и блокирует dialog;
- Save copy as comment field показывает placeholder `Опишите копию проекта (необязательно)`;
- одно предложение `Выберите действие или карточку проекта.` выводится с точкой;
- create/import/existing project cards не выровнены как единая card-system по высоте.

Это не новый scope и не redesign. Это corrective pass по тому же Workspace/project-actions flow.

---

## 3. Границы scope

### В scope

A. Top panel action mapping.  
B. Workspace card layout system: create/import/existing одинаковой высоты.  
C. Create card inline editing + validation + no placeholder persistence.  
D. Import card minimal content + cancel file picker no-op/unfreeze.  
E. Existing project cards strict 3-row render.  
F. Same-user lock open/reclaim availability.  
G. Delete by projectId + confirm + refresh.  
H. Save copy as empty comment field without explanatory placeholder.  
I. Affected punctuation texts.  
J. Behavior tests and `export_project_to_txt.py` check.

### Не в scope

Не делать:

- новый UI redesign;
- новый Workspace architecture;
- новый browser E2E harness;
- Playwright/Cypress;
- изменение YAML ZIP import/export contract;
- изменение canonical project storage model;
- широкий backend lock redesign;
- широкий docs cleanup;
- перенос директорий;
- изменение MetaGen editor;
- ручную UI-проверку через Codex/reviewer.

---

## 4. Что сначала проверить в repo

Codex должен сначала найти фактические места реализации.

Проверить:

- Top panel action wiring:
  - `ui/renderer/ui/workbenchShell.js`
  - `ui/renderer/app.js`
  - `ui/renderer/runtime/browserShellAdapter.js`
  - `ui/renderer/runtime/createShellAdapter.js`
  - `ui/renderer/core/projectManager.js`
  - `ui/config/ui-config.js`
  - `shared/config/platform-config.js`

- Workspace / project picker:
  - фактический renderer create/import/existing cards;
  - project picker action ids;
  - create card state/validation;
  - import card click handler;
  - delete handler;
  - refresh/list reload flow.

- Dialogs:
  - `ui/renderer/ui/dialogs.js`
  - Save copy as dialog implementation;
  - delete confirm dialog implementation.

- Styles:
  - `ui/styles/styles.css`
  - classes `meta-dialog-project-picker-*`
  - primary/secondary/disabled button classes.

- Backend lock/delete if needed:
  - `rtb/app/services/project_catalog.py`
  - `rtb/app/services/project_storage.py`
  - `rtb/app/services/command_dispatcher.py`
  - `rtb/app/services/errors.py`
  - `rtb/app/models/project_snapshot.py`

- Tests:
  - existing JS tests for Workspace/actions/dialogs/runtime;
  - backend tests for lock/delete if affected.

- `export_project_to_txt.py`.

---

## 5. Target semantics

### A. Top panel actions

Restore exact action mapping:

```text
Создать       → create/new project flow
Открыть       → Workspace
Закрыть       → close current project
Сохранить     → save current project
Сохранить как → Save copy as dialog
Импорт        → import ZIP flow
Экспорт       → export current project
Выход         → exit/close flow
```

Current regressions to fix:

- `Создать` does wrong flow, likely close/switch;
- `Импорт` opens Workspace instead of import ZIP flow.

Check button id → action id → handler mapping. Do not rename action ids unless absolutely required. Use existing config/constants.

### B. Workspace cards: one vertical card system

Create card, import card and existing project cards must share one visual/layout system:

- same vertical height;
- same padding;
- same border/radius/background;
- same row structure:
  - top row;
  - middle row;
  - bottom/status/action row;
- primary actions right-aligned and black;
- secondary actions grey;
- empty rows reserved by CSS/layout, not by extra explanatory text.

Do not use text placeholders to fake height.

### C. Create card

Normal state must show only:

```text
Новый проект 1
Комментарий
[Создать]
```

Behavior:

- `Новый проект 1` is inline value;
- click on name turns it into input;
- `Комментарий` is placeholder-like inline value;
- click on comment turns it into input/textarea;
- if user never edited comment, created project must get `comment = ""`;
- string `Комментарий` must not be saved as project comment.

Validation while editing name:

```text
empty name → Укажите имя проекта
duplicate → Проект с таким именем уже есть
```

Invalid name behavior:

- `Создать` disabled;
- validation text visible inside card;
- duplicate project cannot be created;
- validation must compare against current catalog project list, same logic as Save copy as.

### D. Import card

Normal state:

```text
Импорт
[reserved empty row]
[Выбрать]
```

Must not show:

```text
Выберите ZIP-архив проекта для импорта в каталог.
```

Cancel file picker scenario:

```text
Workspace → Импорт / Выбрать → file picker → Cancel/no file selected
```

Target:

- no-op;
- no import command;
- busy/disabled state cleared;
- Workspace remains interactive;
- dialog remains closeable by close icon;
- list state not corrupted.

### E. Existing project cards

Strict 3-row render:

```text
Имя проекта
Комментарий
Статус / lock / availability
```

Fix current bad cases:

```text
2 | Заблокирован: default-user
```

must become:

```text
2
Заблокирован: default-user
```

and:

```text
qwe3
asd3
qwe3
```

must not happen. Third row must not repeat project name.

Rules:

- no `|` concat between comment and lock/status;
- comment row separate;
- status row separate;
- project name appears only in name row;
- empty comment row stays visually reserved but text is empty;
- card height does not shrink when comment is empty.

### F. Same-user lock

If current user is `default-user`, project locked by `default-user` must not be treated as foreign unavailable lock.

Target:

```text
locked by current user → can open/reclaim
locked by other user   → blocked
```

If backend already supports same-user reclaim/open, fix UI availability only.  
If backend does not support it, add minimal backend support without broad lock redesign.

### G. Delete project from Workspace

Clicking `Удалить` in an existing project card:

```text
Удалить
→ confirm dialog
→ Отмена / close icon = cancel
→ Удалить = delete by projectId
→ refresh Workspace list
```

Requirements:

- delete must call catalog delete by the card projectId;
- cancel does not delete;
- close icon does not delete;
- confirm deletes;
- successful delete refreshes list;
- delete should not accidentally close/switch/open another project unless existing contract explicitly requires special handling for opened project.

### H. Save copy as comment field

In `Сохранить копию проекта как`, comment field must not show explanatory placeholder:

```text
Опишите копию проекта (необязательно)
```

Target:

```text
Комментарий
[empty field]
```

If source comment is empty, field value and placeholder-like visible content are empty.  
Do not show `Комментарий не задан`.

### I. Text punctuation

Fix affected Workspace/project dialog texts according to rule:

- one sentence: no final dot;
- two sentences: each sentence has dots.

Known issue:

```text
Выберите действие или карточку проекта.
```

must be:

```text
Выберите действие или карточку проекта
```

Apply only to affected Workspace/project dialog texts. Do not do total Russian text cleanup.

---

## 6. Required changes

Reviewer should instruct Codex to:

1. Fix top panel action mapping first, before Workspace card behavior.

2. Refactor only the necessary Workspace card render/layout code so create/import/existing cards share one row-based layout and equal height.

3. Implement create card inline editing:
   - inline values by default;
   - input/textarea only after click;
   - empty/duplicate validation visible;
   - disabled create on invalid;
   - no placeholder persistence.

4. Implement import cancel no-op/unfreeze.

5. Implement existing project card strict 3-row render.

6. Fix same-user lock availability/reclaim with minimal scope.

7. Fix delete confirm → delete by projectId → refresh.

8. Remove Save copy as comment explanatory placeholder.

9. Fix affected punctuation texts.

10. Add/update behavior tests listed below.

11. Check `export_project_to_txt.py` and update whitelist only if new source files are added.

---

## 7. Files / areas allowed to change

Expected areas:

- `ui/config/ui-config.js`
- `ui/styles/styles.css`
- `ui/renderer/app.js`
- `ui/renderer/ui/workbenchShell.js`
- `ui/renderer/ui/dialogs.js`
- `ui/renderer/runtime/browserShellAdapter.js`
- `ui/renderer/runtime/createShellAdapter.js`
- `ui/renderer/runtime/backendProjectExportFlow.js` only if action flow requires it
- `ui/renderer/core/projectManager.js`
- existing JS tests
- `export_project_to_txt.py`

Backend only if same-user lock/delete behavior requires it:

- `rtb/app/services/project_catalog.py`
- `rtb/app/services/project_storage.py`
- `rtb/app/services/command_dispatcher.py`
- `rtb/app/services/errors.py`
- `rtb/app/models/project_snapshot.py`
- backend tests directly related to same-user lock/delete.

Do not modify unrelated UI/editor/backend modules.

---

## 8. Magic strings / constants

Do not add semantic magic strings/numbers outside existing config/constants layers.

Use existing config/constants for:

- action ids;
- command ids;
- dialog ids;
- button labels;
- validation texts;
- status ids;
- availability states;
- logger source ids;
- icon paths;
- lock/user identity values;
- CSS class names if already centralized.

Do not create a competing constants layer.  
Local micro-literals are acceptable only for purely technical one-off guards and not for cross-layer contract.

---

## 9. Tests to add/update

Add/update behavior tests only. Do not add manual visual UI checks for Codex/reviewer.

Required coverage:

### Top panel actions

- each top panel action id dispatches to correct handler:
  - create;
  - open;
  - close;
  - save;
  - save-as;
  - import;
  - export;
  - exit.
- specifically assert `Импорт` does not open Workspace but starts import ZIP flow.
- specifically assert `Создать` does not trigger close project flow.

### Create card

- renders inline mode by default:
  - `Новый проект N`;
  - `Комментарий`;
  - no always-open input fields before click.
- clicking name opens name input.
- clicking comment opens comment input/textarea.
- empty name shows `Укажите имя проекта` and disables `Создать`.
- duplicate name shows `Проект с таким именем уже есть` and disables `Создать`.
- duplicate project cannot be created.
- untouched `Комментарий` placeholder-like inline value is not saved as comment; saved comment is `""`.

### Import card

- no explanatory ZIP text.
- cancel/empty file selection is no-op.
- cancel does not call import command.
- cancel clears busy/disabled state.
- Workspace remains interactive/closeable.

### Existing project cards

- strict 3-row data model/render:
  - name;
  - comment;
  - status/lock.
- no `|` concat.
- project name is not repeated in status/meta row.
- empty comment row has no placeholder text.

### Delete

- delete click opens confirm.
- cancel does not delete.
- close icon does not delete.
- confirm deletes by projectId.
- successful delete refreshes Workspace list.

### Same-user lock

- current user lock is available/reclaimable.
- foreign lock remains blocked.

### Save copy as

- empty comment field has no explanatory placeholder.
- no `Комментарий не задан`.

### Punctuation

- affected one-sentence Workspace/project dialog texts have no final dot.
- specifically `Выберите действие или карточку проекта`.

Do not add Playwright/Cypress/browser E2E.

---

## 10. Verification commands

Reviewer must require Codex to run full project checks and report factual stdout/stderr/exit codes.

Required:

```powershell
npm.cmd test
npm.cmd run test:integration
npm.cmd run test:backend
```

Do not use `test:all` as required verification.

No long-running foreground/watch/server command is allowed without bounded wrapper. Do not use unbounded:

```powershell
python -m uvicorn ...
npm run dev
vite
electron .
```

If any command fails, reviewer must require Codex to classify the failure as:

- real code/test/docs defect;
- or confirmed environment limitation with exact command, stdout/stderr and reason.

---

## 11. export_project_to_txt.py

Codex must inspect `export_project_to_txt.py`.

Required:

- keep manual whitelist;
- include new source files if added;
- do not include tests/fixtures;
- do not include icons as file contents;
- do not include demo project;
- do not include package-lock;
- do not include briefing docs;
- do not include runtime DB/cache/process/workspace artifacts;
- do not include task/artifact files.

If no whitelist update is needed, state explicitly that helper was checked and why no change was required.

---

## 12. Manual UI check for user only

Do not ask Codex/reviewer to perform manual visual UI checks.

After repo/test part is done, user will manually check:

- top panel buttons perform correct actions;
- create/import/existing cards have equal height and one visual style;
- create card inline editing feels correct;
- duplicate/empty validation is visible;
- import cancel does not freeze Workspace;
- delete works from Workspace;
- existing cards show 3 lines without `|`;
- same-user lock opens/reclaims;
- Save copy as comment field is empty;
- punctuation looks correct.

Reviewer should not mark this as manual UI verification done. Reviewer only checks repo diff/tests/artifacts.

---

## 13. Result report required from reviewer

Reviewer must report:

- Summary;
- Changed files;
- What changed by file;
- Top panel action mapping changes;
- Workspace create/import/existing card changes;
- Delete/import-cancel/same-user lock changes;
- Save copy as and punctuation changes;
- Tests/commands Codex actually ran;
- Exit codes/results;
- `export_project_to_txt.py` status;
- Any failures with stdout/stderr classification;
- Risks/open items;
- Explicit DONE/not-DONE decision for repo/test part.

If Codex did not run required commands or did not provide factual outputs/exit codes, reviewer must not mark done.

---

## 14. DONE criteria

Repo/test part is DONE only when all are true:

1. Top panel actions map to correct flows.
2. Create/import/existing Workspace cards share one equal-height row-based layout.
3. Create card is inline by default and opens input/textarea only on click.
4. Create empty/duplicate validation is visible and disables create.
5. Duplicate project creation is blocked.
6. Untouched `Комментарий` placeholder-like value is not saved as comment.
7. Import card has no explanatory ZIP text.
8. Import file picker cancel is no-op and does not freeze Workspace.
9. Existing project cards render strict name/comment/status rows.
10. Existing cards do not use `|` concat and do not repeat project name in status row.
11. Same-user lock is available/reclaimable; foreign lock remains blocked.
12. Delete from Workspace opens confirm, cancel does not delete, confirm deletes by projectId and refreshes list.
13. Save copy as comment field has no explanatory placeholder.
14. Affected one-sentence texts have no final dot.
15. Behavior tests cover the fixed cases.
16. Required commands were actually run by Codex:
    - `npm.cmd test`
    - `npm.cmd run test:integration`
    - `npm.cmd run test:backend`
17. `export_project_to_txt.py` was checked/updated consistently.
18. No unrelated redesign/refactor/docs cleanup entered the diff.

Final user-facing DONE still requires user's manual UI confirmation for visual/click behavior.
