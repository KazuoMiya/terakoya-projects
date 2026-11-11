> 日本語版: [README.md](./README.md)

# Terakoya Projects — The Full Loop

This is the project repository for the course
**"The Full Loop — building operations tools through seven projects"** on the learning site **[Terakoya](https://terakoya.miya-dca.workers.dev)**.
Server checks, DB checks, log analysis, config diffs, a web API, deployment, and integrated monitoring —
seven projects you build into working tools with your own hands.

> **This course requires a PC.** You work not inside the browser, but in a Python environment on your own machine.
> If you haven't set one up yet, start from the course's **project 0 (Run Python locally)**.

## Once, at the very start

1. Use the green **"Use this template" → "Create a new repository"** button at the top right to make **your own copy** (Public or Private — either is fine).
2. `clone` the new repository to your PC.
3. Run project 0's `projects/00-setup/check_setup.py` to confirm your environment is ready.

> **It's fine to break things.** This copy is yours alone. Everything happens inside the venv
> and this folder. If it gets into a weird state, delete it and create a fresh one from the template.

## How to work through a project (the shared loop)

Every project follows the same small loop as the graduation exercise.

1. Cut a working branch (e.g. `git switch -c task1-healthcheck`)
2. Implement inside that project's folder
3. Check your answer with `python -m unittest -v` (**projects that have auto-grading**)
4. push → **Pull Request** → auto-grading turns **green ✓** → self-merge
5. Fill in `RETROSPECTIVE.md` (the retrospective)

**Auto-grading looks only at the projects your PR changed.** A PR that changes files under
`projects/01-healthcheck/` runs only Project 1's tests. Projects you haven't started are still
skeletons and always fail, so they are left out. To check every project at once, run it by hand:
the repository's "Actions" tab → "自動採点" → "Run workflow".

**Some projects have no auto-grading** (the DB check, deployment, and others that depend on your environment).
For those, check your own work against the completion checklist in each folder's `README.md` and
the sample in `expected-output.md`. What certifies completion is the green check and your retrospective.

## The projects

| # | Folder | Project | Auto-grading | Status |
|---|---|---|---|---|
| 0 | `projects/00-setup/` | Run Python locally | Environment check | Available |
| 1 | `projects/01-healthcheck/` | Server health-check CLI | Yes | Available |
| 2 | `projects/02-db-check/` | DB daily check (PostgreSQL main track / Oracle optional) | Partial | Available |
| 3 | `projects/03-log-analysis/` | Log analysis and notification | Yes | Available |
| 4 | `projects/04-config-diff/` | Config diff and change-making tools | Yes | Available |
| 5 | `projects/05-web-api/` | Check-Results API (FastAPI) | Yes | Available |
| 6 | `projects/06-deploy/` | Deployment (run it, guard it) | No | Available |
| 7 | `projects/07-monitoring/` | Integrated monitoring system | Partial | Available |

All projects are now available.

## Prerequisites

You should have completed Terakoya's three courses (Foundations of Systems and Code / Infrastructure Basics / The Field of Development).
In particular, **Git (module 3) and the graduation exercise** in The Field of Development are required.

## If you get stuck (quick reference)

| Symptom | What to do |
|---|---|
| Typing `python` opens the Microsoft Store / not found | Always type `python3`. See project 0's Windows/Mac lessons |
| A package says it's missing even though you installed it | You forgot to activate the venv: `source .venv/bin/activate` |
| `ModuleNotFoundError: No module named 'healthcheck'` | Run `python -m unittest` inside that project's folder (e.g. `projects/01-healthcheck`) |
| `python: command not found` | You forgot to activate the venv. `python` only exists inside the venv (outside, it's `python3`) |
| (Project 2) `docker compose up` doesn't work | Check that Docker Desktop is running. On a company PC, check the usage policy with your IT department |
| (Project 2) The container is running but you can't connect | Check that STATUS is `healthy` in `docker compose ps`. Right after startup, wait a few dozen seconds |
| (Project 2) `password authentication failed` | Did you create `.env` (`cp .env.example .env`)? To redo it, start from `docker compose down -v` |
| (Project 2) The DB got into a weird state | `docker compose down -v && docker compose up -d` returns it to a clean slate |
| Checks (auto-grading) are red | Open the red job and read the output of the failing test. That's the place to fix |
| Checks are red because of a project you never touched / fail before reaching the tests | Copies made before November 2026 have an outdated grading setup. See "Picking up template updates" below |
| A project you haven't started gets graded and goes red | Did this PR change anything inside that project's folder (its README, for example)? Grading covers every project whose folder the PR changed |
| Checks don't appear at all | Enable the workflow in the repository's "Actions" tab |
| Everything's a mess | You can delete this copy and recreate it from the template |

## Picking up template updates (for copies made before November 2026)

A copy made from the template is a snapshot of that moment. Fixes to the template do not reach
it automatically. Of the November 2026 fixes, these three are the ones to apply by hand.
How to tell: if your `.github/workflows/grade.yml` has no line saying "採点する課題を決める", your copy is an old one.

1. **Auto-grading (`.github/workflows/grade.yml`)** — the old setup graded every project on every PR.
   As a result, a PR that implemented only Project 1 always went red on the tests of projects not yet started.
   - Fix: open the template's [grade.yml](https://github.com/KazuoMiya/terakoya-projects/blob/main/.github/workflows/grade.yml)
     and copy its contents with "Copy raw file". Open the same file in your own repository on GitHub,
     click the pencil icon (Edit) → replace the whole contents → "Commit changes".
   - If you have a PR still open, click "Close pull request" and then "Reopen pull request". Grading reruns with the new setup.
     If the old grading still runs, push one new commit to your working branch.
   - Bring the change into your local repository too: `git switch main` → `git pull`.
2. **Project 2's `compose.yml`** — the DB ports are now opened only on `127.0.0.1` (this machine itself).
   Before, other machines on the same Wi-Fi or office LAN could connect too.
   - Fix: under `ports:`, change `"5432:5432"` to `"127.0.0.1:5432:5432"` and `"1521:1521"` to
     `"127.0.0.1:1521:1521"`, then run `docker compose up -d` again.
3. **Project 2's optional Oracle track (only if you use it)** — granting privileges to the inspection user was failing
   (the `v$` views could not be read: ORA-00942).
   - Fix: replace `projects/02-db-check/initdb-oracle/01-checker-grants.sql` with the template's latest version, then
     rebuild with `docker compose --profile oracle down -v` → `docker compose --profile oracle up -d`
     (the PostgreSQL data returns to its initial state too).

## About this repository

- This is a learning template. **Individual support and review are not guaranteed.**
  For questions, rather than opening an Issue, please go back and reread the [Terakoya course lessons](https://terakoya.miya-dca.workers.dev/).
- The code is **MIT licensed** (see `LICENSE`). Use it freely.

---

Made for **[Terakoya](https://terakoya.miya-dca.workers.dev)** ・ Run by Miya / [NexusCode](https://www.nexuscode-devs.asia/ja)
