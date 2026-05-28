# Local Machine Checklist

## Goal

Install the tools needed to build, test, run, and eventually deploy c3Ntr0l from your machine.

## Core Tools

Install these first:

```powershell
winget install Python.Python.3.11
winget install astral-sh.uv
winget install Docker.DockerDesktop
winget install GnuWin32.Make
```

Then open a new terminal and verify:

```bash
python --version
uv --version
docker compose version
make --version
```

Expected:

- Python should be `3.11.x` or newer.
- `uv` should print a version.
- Docker Compose should print a version.
- `make` should print a version.

## GitHub And Repository Tools

Install these too:

```powershell
winget install Git.Git
winget install GitHub.cli
```

Verify:

```bash
git --version
gh --version
```

After installing GitHub CLI, authenticate:

```bash
gh auth login
```

## Web App Tools

Install Node LTS before the web app work starts:

```powershell
winget install OpenJS.NodeJS.LTS
```

Verify:

```bash
node --version
npm --version
```

## Android Tools Later

Before Android work starts, install:

- Android Studio
- JDK 17 or newer
- Android SDK platform tools

This can wait until the backend and web Today flow are usable.

## First Repo Setup After Installing Tools

From the repo root:

```bash
cp apps/api/.env.example apps/api/.env
make api-lock
make api-install
make db-up
make api-migrate
make api-dev
```

Check:

```txt
http://127.0.0.1:8000/health
http://127.0.0.1:8000/api/v1/health
```

## Useful Commands

```bash
make help
make api-test
make api-lint
make api-check
make api-openapi
```
