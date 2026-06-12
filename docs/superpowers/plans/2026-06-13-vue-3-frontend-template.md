# Vue 3 Frontend Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Initialize a standard Vue 3 + Vite JavaScript frontend project in `frontend/`.

**Architecture:** The frontend will be a standalone Vite application under `frontend/`, separate from the existing backend folder. The scaffold will use Vite's official Vue JavaScript template, with no additional router, state management, test framework, or TypeScript setup.

**Tech Stack:** Vue 3, Vite, JavaScript, npm.

---

## File Structure

Create or update these frontend files:

- Create: `frontend/package.json` — npm metadata, scripts, Vue and Vite dependencies.
- Create: `frontend/package-lock.json` — locked npm dependency graph produced by `npm install`.
- Create: `frontend/index.html` — Vite HTML entry point.
- Create: `frontend/vite.config.js` — Vite config with Vue plugin.
- Create: `frontend/public/vite.svg` — static template asset.
- Create: `frontend/src/main.js` — Vue app bootstrap.
- Create: `frontend/src/App.vue` — template root component.
- Create: `frontend/src/style.css` — template global styles.
- Create: `frontend/src/assets/vue.svg` — Vue logo asset.
- Create: `frontend/src/components/HelloWorld.vue` — template example component.
- Delete: `frontend/.gitkeep` — placeholder is no longer needed once real files exist.

Do not modify `backend/` during this task.

---

### Task 1: Scaffold the Vite Vue Template

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/vite.config.js`
- Create: `frontend/public/vite.svg`
- Create: `frontend/src/main.js`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/style.css`
- Create: `frontend/src/assets/vue.svg`
- Create: `frontend/src/components/HelloWorld.vue`
- Delete: `frontend/.gitkeep`

- [ ] **Step 1: Check the frontend directory before scaffolding**

Run:

```bash
ls -la frontend
```

Expected: `frontend/` exists and only contains the placeholder `.gitkeep`, or contains no meaningful project files. If files other than `.gitkeep` exist, stop and report them before overwriting anything.

- [ ] **Step 2: Run the official Vite Vue JavaScript scaffold**

Run from the repository root:

```bash
npm create vite@latest frontend -- --template vue
```

Expected: Vite creates the Vue JavaScript template in `frontend/`. If the command refuses because `frontend/` is not empty due only to `.gitkeep`, remove `frontend/.gitkeep` and rerun the scaffold.

- [ ] **Step 3: Remove the placeholder if it remains**

Run:

```bash
rm -f frontend/.gitkeep
```

Expected: `frontend/.gitkeep` no longer exists.

- [ ] **Step 4: Confirm expected scaffold files exist**

Run:

```bash
ls frontend
ls frontend/src
ls frontend/src/components
```

Expected: output includes `package.json`, `index.html`, `vite.config.js`, `src`, `public`; `src` includes `main.js`, `App.vue`, `style.css`, `assets`, `components`; `components` includes `HelloWorld.vue`.

---

### Task 2: Install Dependencies

**Files:**
- Create: `frontend/package-lock.json`
- Modify: `frontend/node_modules/` is created locally but should not be committed if repository ignores it.

- [ ] **Step 1: Install npm dependencies**

Run:

```bash
cd frontend && npm install
```

Expected: npm installs Vue, Vite, and related dependencies. `frontend/package-lock.json` is created.

- [ ] **Step 2: Confirm npm scripts are available**

Run:

```bash
cd frontend && npm run
```

Expected: output lists at least these scripts:

```text
dev
build
preview
```

---

### Task 3: Verify the Template Build

**Files:**
- No source changes expected.
- `frontend/dist/` may be created by the build and should remain uncommitted if ignored or be deleted after verification if not ignored.

- [ ] **Step 1: Run the production build**

Run:

```bash
cd frontend && npm run build
```

Expected: command exits successfully and Vite reports built files under `dist/`.

- [ ] **Step 2: Check generated files and git status**

Run:

```bash
git status --short
```

Expected: changes are limited to the frontend scaffold files, `frontend/package-lock.json`, the design/plan docs, and removal of `frontend/.gitkeep`. Do not include unrelated changes such as `backend/.gitkeep` deletion in this implementation.

- [ ] **Step 3: If `frontend/dist/` appears as untracked, remove it**

Run only if `git status --short` shows untracked `frontend/dist/`:

```bash
rm -rf frontend/dist
```

Expected: build artifacts are not left as untracked files.

---

## Commit Policy

The user explicitly requested no git commit for this work. Do not commit. Leave changes in the working tree after successful verification.

---

## Self-Review

- Spec coverage: The plan creates the official Vue 3 + Vite JavaScript template in `frontend/`, removes the placeholder, installs dependencies, and verifies `npm run build`.
- Placeholder scan: No TBD/TODO/fill-in placeholders remain.
- Scope check: The plan does not add TypeScript, router, Pinia, linting, formatting, tests, UI design, or backend integration.
- Consistency check: File paths and commands consistently target `frontend/`; `backend/` is explicitly out of scope.
