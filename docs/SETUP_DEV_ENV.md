# Shibo Finance — Developer Environment Setup

> This guide covers everything needed to set up a productive local development environment from scratch.
> Stack: Python 3.12 · FastAPI · Next.js 15 · Docker · WSL2 · VS Code

---

## Table of Contents

1. [System Prerequisites](#1-system-prerequisites)
2. [Repository Clone & First Boot](#2-repository-clone--first-boot)
3. [VS Code Setup](#3-vs-code-setup)
4. [Workspace Settings (.vscode/)](#4-workspace-settings-vscode)
5. [Git Configuration & Diffs](#5-git-configuration--diffs)
6. [MCP Servers](#6-mcp-servers)
7. [Daily Development Workflow](#7-daily-development-workflow)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. System Prerequisites

### WSL2 (Windows only)

```bash
# Enable WSL2 (PowerShell as Administrator)
wsl --install
wsl --set-default-version 2

# Verify
wsl --status
```

Install Ubuntu 24.04 LTS from the Microsoft Store, then open a WSL terminal for all subsequent steps.

### Docker Desktop

- Download Docker Desktop for Windows
- In Settings → Resources → WSL Integration: enable your Ubuntu distro
- Enable "Use the WSL 2 based engine"

Verify inside WSL:
```bash
docker --version      # Docker version 27+
docker compose version  # Docker Compose version 2+
```

### Node.js (for local type generation outside Docker)

```bash
# Using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
source ~/.bashrc
nvm install 22
nvm use 22
node --version  # v22+
```

### Python (for local tooling — backend runs in Docker)

```bash
# Python 3.12 via deadsnakes PPA (Ubuntu)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev

# uv — fast Python package manager (optional but recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Make

```bash
sudo apt install make
```

---

## 2. Repository Clone & First Boot

```bash
# Clone (adjust path to your preference)
git clone <repo-url> ~/repos/shibofinance
cd ~/repos/shibofinance

# Copy environment file
cp .env.example .env
# Edit .env if you need custom credentials (defaults work out of the box)

# Start the full stack
make up

# Apply database migrations
make migrate

# Verify API is up
curl http://localhost:8000/health
# Expected: {"status":"ok"}

# Verify frontend is up
curl -s http://localhost:3000 | head -5
```

### Service URLs

| Service | URL |
|---------|-----|
| Frontend (Next.js) | http://localhost:3000 |
| Backend API (FastAPI) | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| OpenAPI JSON | http://localhost:8000/openapi.json |
| pgAdmin (optional) | http://localhost:5051 |

To start pgAdmin:
```bash
docker compose --profile pgadmin up -d
```

---

## 3. VS Code Setup

### Install VS Code

Download from https://code.visualstudio.com/
On Windows with WSL2, install the Windows version and use the "Open in WSL" feature.

Open the project in WSL:
```bash
cd ~/repos/shibofinance
code .
```

### Essential Extensions

Install all at once (paste into terminal):
```bash
code --install-extension ms-vscode-remote.remote-wsl
code --install-extension ms-vscode-remote.remote-containers
code --install-extension ms-python.python
code --install-extension ms-python.pylance
code --install-extension ms-python.black-formatter
code --install-extension ms-python.isort
code --install-extension charliermarsh.ruff
code --install-extension dbaeumer.vscode-eslint
code --install-extension esbenp.prettier-vscode
code --install-extension bradlc.vscode-tailwindcss
code --install-extension ms-azuretools.vscode-docker
code --install-extension eamodio.gitlens
code --install-extension mhutchie.git-graph
code --install-extension ckolkman.vscode-postgres
code --install-extension humao.rest-client
code --install-extension yoavbls.pretty-ts-errors
code --install-extension usernamehw.errorlens
code --install-extension christian-kohler.path-intellisense
code --install-extension mikestead.dotenv
```

### Extension Details

| Extension | Purpose |
|-----------|---------|
| **Remote - WSL** | Open VS Code inside WSL2 (critical for Windows users) |
| **Remote - Containers** | Attach VS Code to running Docker containers |
| **Python** | Python language support |
| **Pylance** | Fast Python type checking and IntelliSense |
| **Black Formatter** | Auto-format Python on save |
| **isort** | Auto-sort Python imports on save |
| **Ruff** | Fast Python linter (replaces flake8/pylint) |
| **ESLint** | JavaScript/TypeScript linting |
| **Prettier** | JS/TS/JSON/CSS formatter |
| **Tailwind CSS IntelliSense** | Autocomplete for Tailwind classes |
| **Docker** | Manage containers, view logs, browse images |
| **GitLens** | Git blame, history, diffs inline in editor |
| **Git Graph** | Visual branch/commit graph |
| **PostgreSQL** | Query the database directly from VS Code |
| **REST Client** | Send HTTP requests from `.http` files (test API) |
| **Pretty TypeScript Errors** | Human-readable TS error messages |
| **Error Lens** | Show errors inline next to the code |
| **Path IntelliSense** | Autocomplete for file paths |
| **DotENV** | Syntax highlighting for `.env` files |

---

## 4. Workspace Settings (.vscode/)

Create the following files at the root of the repo:

### `.vscode/settings.json`

```json
{
  // --- Python ---
  "python.defaultInterpreterPath": "/usr/bin/python3.12",
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },
  "isort.args": ["--profile", "black"],
  "ruff.enable": true,
  "ruff.organizeImports": false,

  // --- TypeScript / JavaScript ---
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },
  "[css]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true
  },

  // --- Tailwind ---
  "tailwindCSS.experimental.classRegex": [
    ["cva\\(([^)]*)\\)", "[\"'`]([^\"'`]*).*?[\"'`]"],
    ["cx\\(([^)]*)\\)", "(?:'|\"|`)([^']*)(?:'|\"|`)"],
    ["cn\\(([^)]*)\\)", "(?:'|\"|`)([^']*)(?:'|\"|`)"]
  ],
  "tailwindCSS.includeLanguages": {
    "typescript": "javascript",
    "typescriptreact": "javascriptreact"
  },

  // --- Editor ---
  "editor.tabSize": 2,
  "editor.rulers": [88, 100],
  "editor.renderWhitespace": "boundary",
  "editor.minimap.enabled": false,
  "editor.bracketPairColorization.enabled": true,
  "editor.stickyScroll.enabled": true,
  "editor.inlayHints.enabled": "on",

  // --- Files ---
  "files.exclude": {
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/*.pyc": true,
    "**/node_modules": true,
    "**/.next": true
  },
  "files.watcherExclude": {
    "**/node_modules/**": true,
    "**/.next/**": true,
    "**/__pycache__/**": true
  },
  "search.exclude": {
    "**/node_modules": true,
    "**/.next": true,
    "**/package-lock.json": true
  },

  // --- Git ---
  "git.autofetch": true,
  "git.confirmSync": false,
  "git.enableSmartCommit": true,
  "diffEditor.ignoreTrimWhitespace": false,
  "diffEditor.renderSideBySide": true,

  // --- GitLens ---
  "gitlens.currentLine.enabled": true,
  "gitlens.hovers.currentLine.over": "line",
  "gitlens.blame.toggleMode": "file",
  "gitlens.codeLens.enabled": false,

  // --- Error Lens ---
  "errorLens.enabledDiagnosticLevels": ["error", "warning"],

  // --- TypeScript ---
  "typescript.tsdk": "apps/web/node_modules/typescript/lib",
  "typescript.preferences.importModuleSpecifier": "non-relative"
}
```

### `.vscode/extensions.json`

This file makes VS Code suggest extensions automatically when the repo is opened:

```json
{
  "recommendations": [
    "ms-vscode-remote.remote-wsl",
    "ms-vscode-remote.remote-containers",
    "ms-python.python",
    "ms-python.pylance",
    "ms-python.black-formatter",
    "ms-python.isort",
    "charliermarsh.ruff",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-azuretools.vscode-docker",
    "eamodio.gitlens",
    "mhutchie.git-graph",
    "ckolkman.vscode-postgres",
    "humao.rest-client",
    "yoavbls.pretty-ts-errors",
    "usernamehw.errorlens",
    "christian-kohler.path-intellisense",
    "mikestead.dotenv"
  ]
}
```

### `.vscode/launch.json`

Debug configurations for API and frontend:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI (local)",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
      "cwd": "${workspaceFolder}/apps/api",
      "env": {
        "DATABASE_URL": "postgresql+asyncpg://shibofinance:shibofinance@localhost:5432/shibofinance"
      },
      "jinja": true,
      "justMyCode": false
    },
    {
      "name": "Pytest",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/", "-v", "--no-header"],
      "cwd": "${workspaceFolder}/apps/api",
      "env": {
        "DATABASE_URL": "postgresql+asyncpg://shibofinance:shibofinance@localhost:5432/shibofinance"
      },
      "justMyCode": false
    }
  ]
}
```

### `.vscode/tasks.json`

Run common dev tasks from the Command Palette (`Ctrl+Shift+P` → "Run Task"):

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "make up",
      "type": "shell",
      "command": "make up",
      "group": "build",
      "presentation": { "reveal": "always", "panel": "dedicated" }
    },
    {
      "label": "make down",
      "type": "shell",
      "command": "make down",
      "group": "build",
      "presentation": { "reveal": "always", "panel": "dedicated" }
    },
    {
      "label": "make migrate",
      "type": "shell",
      "command": "make migrate",
      "group": "build",
      "presentation": { "reveal": "always", "panel": "dedicated" }
    },
    {
      "label": "make test",
      "type": "shell",
      "command": "make test",
      "group": "test",
      "presentation": { "reveal": "always", "panel": "dedicated" }
    },
    {
      "label": "make logs",
      "type": "shell",
      "command": "make logs",
      "group": "none",
      "presentation": { "reveal": "always", "panel": "dedicated" },
      "isBackground": true
    },
    {
      "label": "web-types (regenerate API types)",
      "type": "shell",
      "command": "make web-types",
      "group": "build",
      "presentation": { "reveal": "always", "panel": "dedicated" }
    }
  ]
}
```

### `.vscode/shibofinance.code-workspace` (optional multi-root)

Opens backend and frontend as separate roots for better IntelliSense:

```json
{
  "folders": [
    { "name": "root", "path": "." },
    { "name": "api", "path": "apps/api" },
    { "name": "web", "path": "apps/web" }
  ],
  "settings": {}
}
```

### REST Client — `apps/api/requests.http`

Use the REST Client extension to test the API without leaving VS Code:

```http
@base = http://localhost:8000

### Health
GET {{base}}/health

### List instruments
GET {{base}}/instruments

### Create instrument
POST {{base}}/instruments
Content-Type: application/json

{
  "name": "Santander Corrente",
  "type": "bank_account",
  "source": "santander_br",
  "source_instrument_id": "santander-br-001",
  "currency": "BRL"
}

### List bank transactions
GET {{base}}/bank-transactions?limit=10&offset=0

### List card transactions
GET {{base}}/card-transactions?limit=10&offset=0

### List import batches
GET {{base}}/imports?limit=10

### Spending summary (current month)
GET {{base}}/spending-summary?date_from=2026-03-01&date_to=2026-03-31

### List categories
GET {{base}}/categories
```

---

## 5. Git Configuration & Diffs

### View Diffs in VS Code

VS Code has a built-in diff viewer. Several ways to open it:

| Method | How |
|--------|-----|
| **Source Control panel** | Click the `Source Control` icon in the left sidebar (or `Ctrl+Shift+G`). Staged/unstaged files appear. Click any file to see a side-by-side diff. |
| **GitLens: File History** | Right-click a file → "Open File History" → compare any two commits |
| **GitLens: Line History** | Right-click a line → "Open Line History" |
| **Git Graph** | Click the Git Graph icon in the bottom status bar → visual commit graph → click any commit to see its diff |
| **Terminal diff** | `git diff HEAD` — opens inline in terminal |
| **VS Code diff command** | `Ctrl+Shift+P` → "Git: Open Changes" |

### Keyboard Shortcuts for Diffs

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+G` | Open Source Control panel |
| `F7` / `Shift+F7` | Next / previous change in diff editor |
| `Alt+F5` / `Shift+Alt+F5` | Next / previous changed file |
| `Ctrl+Z` (in diff editor) | Revert a single change block |

### Global Git Config (one-time)

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# Use VS Code as default diff and merge tool
git config --global core.editor "code --wait"
git config --global diff.tool vscode
git config --global difftool.vscode.cmd 'code --wait --diff $LOCAL $REMOTE'
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait $MERGED'

# Better log output
git config --global alias.lg "log --oneline --graph --decorate --all"
git config --global alias.st "status -sb"
git config --global alias.co "checkout"
```

Now `git difftool HEAD` opens the diff in VS Code.

### `.gitignore` additions (if not present)

```
.vscode/settings.json    # keep only settings you want shared
*.http                   # REST client files with tokens
```

> Note: `.vscode/extensions.json`, `launch.json`, and `tasks.json` should be committed so the whole team benefits. `settings.json` with personal preferences can be gitignored or committed depending on team preference.

---

## 6. MCP Servers

MCP (Model Context Protocol) servers extend Claude Code's capabilities. Configure them in `~/.claude/settings.json` (global) or `.claude/settings.json` (project-level).

### Currently Configured (`.claude/settings.json`)

Check what's already configured:
```bash
cat .claude/settings.json
```

### Recommended MCP Servers for This Project

#### 1. `mcp-server-postgres` — Query the database directly

Allows Claude Code to inspect schema, run queries, and validate data without leaving the conversation.

```bash
# Install
npm install -g @modelcontextprotocol/server-postgres
```

Add to `.claude/settings.json`:
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://shibofinance:shibofinance@localhost:5432/shibofinance"]
    }
  }
}
```

Usage in Claude Code: "Show me all instruments", "How many transactions were imported today?"

#### 2. `mcp-server-filesystem` — Extended file access

Useful when Claude needs to access files outside the working directory (e.g., sample PDFs in `data/`).

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/mnt/c/repos/shibofinance"]
    }
  }
}
```

#### 3. `mcp-server-github` — GitHub integration

If the repo is on GitHub, enables Claude to read issues, PRs, and create comments.

```bash
# Requires a GitHub personal access token
```

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_..."
      }
    }
  }
}
```

#### 4. `mcp-server-fetch` — Fetch URLs

Allows Claude to read API responses, check the OpenAPI spec live, and fetch documentation.

```json
{
  "mcpServers": {
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    }
  }
}
```

Particularly useful for: "Read the current OpenAPI spec from localhost:8000/openapi.json and check if the types match."

### Full `.claude/settings.json` example

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://shibofinance:shibofinance@localhost:5432/shibofinance"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/mnt/c/repos/shibofinance"]
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    }
  }
}
```

> **After editing `.claude/settings.json`, restart Claude Code** — MCP servers are only loaded at startup.
>
> The `postgres` MCP requires the stack to be running (`make up`) before use. The `fetch` MCP works without the stack.

---

## 7. Daily Development Workflow

### Start the stack

```bash
make up        # Start all services (db + api + web)
make logs      # Tail logs from all services (Ctrl+C to stop)
```

### Backend work (Python / FastAPI)

```bash
# Run tests
make test

# Open a shell inside the API container
make api-shell

# Inside the container:
pytest tests/test_health.py -v       # run single test file
alembic revision --autogenerate -m "add column"  # create migration
alembic upgrade head                 # apply migrations
alembic downgrade -1                 # rollback one migration

# From host: apply migrations
make migrate
```

Workflow for adding a new endpoint:
1. Add model/schema to `app/schemas.py`
2. Add router in `app/routers/`
3. Register router in `app/main.py`
4. Write test in `apps/api/tests/`
5. `make test`
6. Regenerate API types: `make web-types`

### Frontend work (Next.js)

The web container hot-reloads on file save. Just edit files in `apps/web/src/`.

```bash
# Regenerate TypeScript types from backend OpenAPI
make web-types

# Build for production
make web-build

# Lint
make web-lint
```

Workflow for adding a new page:
1. Create `apps/web/src/app/<route>/page.tsx`
2. Add nav link to `apps/web/src/components/shell/Sidebar.tsx`
3. Add hook in `apps/web/src/hooks/`
4. Add API function to `apps/web/src/lib/api.ts`

### Database inspection

**Via pgAdmin:**
```bash
docker compose --profile pgadmin up -d
# Open http://localhost:5051
# Login: admin@shibofinance.local / admin
# Add server: host=db, port=5432, user=shibofinance, password=shibofinance
```

**Via VS Code PostgreSQL extension:**
- Open Command Palette → "PostgreSQL: Add Connection"
- Host: `localhost`, Port: `5432`
- Database: `shibofinance`, User: `shibofinance`, Password: `shibofinance`
- Once connected: browse tables, run queries directly in VS Code

**Via psql in container:**
```bash
docker compose exec db psql -U shibofinance -d shibofinance
\dt            # list tables
\d instruments # describe a table
SELECT * FROM instruments;
\q             # quit
```

### Useful one-liners

```bash
# Restart only the API (after code changes that require restart)
docker compose restart api

# Rebuild the web image (after package.json changes)
docker compose build web && docker compose up -d web

# View logs for a single service
docker compose logs -f api
docker compose logs -f web

# Check which containers are running
docker compose ps

# Wipe the database and start fresh
docker compose down -v && make up && make migrate
```

---

## 8. Troubleshooting

### `make up` fails: port already in use

```bash
# Find what's using port 8000 or 3000
lsof -i :8000
lsof -i :3000
# Kill the process or change the port in docker-compose.yml
```

### Frontend can't reach the API

The web container calls `http://localhost:8000` from the browser (not from inside Docker). This is correct because `NEXT_PUBLIC_API_BASE_URL` is embedded at build time and runs in the browser.

If API calls fail in the browser:
1. Confirm `docker compose ps` shows both `api` and `web` as running
2. Check CORS: `curl -H "Origin: http://localhost:3000" http://localhost:8000/health`
3. Check `apps/api/app/main.py` has CORS middleware allowing `http://localhost:3000`

### `make migrate` fails: can't connect to db

```bash
# Check db is healthy
docker compose ps db
# Should show "healthy"

# If not, check db logs
docker compose logs db
```

### Python imports failing in tests

Tests run inside the `api` container. The `packages/` directory is mounted at `/packages`. Check `apps/api/pyproject.toml` for the path configuration:

```bash
make api-shell
python -c "import packages.core.money; print('ok')"
```

### TypeScript errors after backend schema change

```bash
make web-types
# Then restart the TS server in VS Code:
# Ctrl+Shift+P → "TypeScript: Restart TS Server"
```

### WSL2 file watching issues (Next.js hot reload not working)

Add to `apps/web/next.config.ts`:
```typescript
const config = {
  webpack: (config) => {
    config.watchOptions = { poll: 1000, aggregateTimeout: 300 };
    return config;
  },
};
```

Or set in the web service environment in `docker-compose.yml`:
```yaml
environment:
  WATCHPACK_POLLING: "true"
```

### VS Code Python IntelliSense not working

The backend runs in Docker, so there's no local Python environment with dependencies. For full IntelliSense, create a local venv:

```bash
cd apps/api
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
# Then in VS Code: Ctrl+Shift+P → "Python: Select Interpreter" → pick .venv
```

---

## Quick Reference Card

```
make up              Start all services
make down            Stop all services
make logs            Tail all logs
make migrate         Run Alembic migrations
make test            Run pytest suite (117 tests)
make api-shell       Shell into API container
make web-types       Regenerate TS types from OpenAPI

http://localhost:3000          Frontend
http://localhost:8000/docs     API Swagger UI
http://localhost:8000/health   Health check
http://localhost:5051          pgAdmin (with --profile pgadmin)

Ctrl+Shift+G         VS Code: Source Control (diffs)
Ctrl+Shift+P         VS Code: Command Palette
F7 / Shift+F7        Next / prev change in diff editor
git lg               Pretty commit log (alias)
git difftool HEAD    Open diff vs HEAD in VS Code
```
