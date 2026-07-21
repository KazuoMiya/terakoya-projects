> 日本語版: [README.md](./README.md)

# Project 5: Check-Results API

The tools from Projects 1–4 put their results on the screen and into files. In this
project you switch sides and build the part that **receives, stores, and shows**
results — a Web API. In Project 7 (integrated monitoring), Project 1's health-check
CLI will send its reports to this API.
**You are building the "other half" of your own system.**

> This README is the authority for the project. The course lessons (proj-19–22) are
> your guide to reading and working through this spec. Whenever you're lost, come
> back to the completion conditions written here.

## Setup (inside your venv)

```bash
cd projects/05-web-api
cp .env.example .env
pip install -r requirements.txt   # installs FastAPI, uvicorn, and the test tools
```

The skeleton has only `/health` implemented. Start it first and watch one full loop.

```bash
uvicorn app:app --reload --app-dir src
```

Open http://127.0.0.1:8000/health in a browser and `{"status":"ok"}` comes back.
Then open **http://127.0.0.1:8000/docs** — your API's manual already exists.
FastAPI is a tool where "write the types, and validation and documentation come
with them." Stop the server with Ctrl+C.

## What you build (the API spec)

| Method and path | Role | Auth | Main responses |
|---|---|---|---|
| GET `/health` | liveness check (already implemented) | not required | 200 |
| GET `/servers` | list servers | not required | 200 |
| POST `/servers` | register a server | **required** | 201 / 401 / 409 / 422 |
| GET `/servers/{id}` | fetch one server | not required | 200 / 404 |
| POST `/servers/{id}/checks` | record a check result | **required** | 201 / 401 / 404 / 422 |
| GET `/servers/{id}/checks?limit=N` | list check results (**newest first**) | not required | 200 / 404 |

### Input shapes and validation

- **Server**: `hostname` (1–64 characters, required, **duplicates are 409**), `role` (1–32 characters, required)
- **Check**: `metric` (1–64 characters), `value` (a number), `status` (**only the 4 values
  you have used since Project 1**: OK / WARNING / CRITICAL / UNKNOWN. Anything else is 422)

Write the validation as Pydantic models. Write the types and constraints, and FastAPI
returns the 422s for you. The rule "every write operation must limit string lengths"
doesn't have to turn into a mountain of hand-written if statements.

### Choosing the right status code (the learning at the heart of this project)

| Code | Meaning | Example in this project |
|---|---|---|
| 401 | we don't know who you are | X-API-Key is missing or wrong |
| 404 | the target doesn't exist | a nonexistent server_id |
| 409 | state conflict | a duplicate hostname (the input's shape is fine, but it conflicts with the current state) |
| 422 | the input's shape is invalid | hostname is empty, status is outside the 4 values, value is not a number |

### Auth — one API key, and no more

Write operations (POST) pass only when the request header **`X-API-Key`** matches
`API_KEY` in `.env`. Read operations (GET) need no auth.
We don't step into OAuth or session management. **This project's auth deliberately stops here.**

### Error messages are part of the design

An error response may carry only "information the caller can act on." Never return
internal details — table names, SQL, tracebacks — to the client (this is part of
the grading, too).

## The design promise — SQL lives only in db.py

`src/db.py` is the DB access layer. **Not one line of SQL goes into app.py.**
This separation exists for the final challenge, "swap SQLite for PostgreSQL."
If SQL is scattered everywhere, the swap means reworking every file. Kept inside
db.py, it's a one-file swap.
`init_db()` (the table definitions) is fixed by the spec, so it's already implemented. You write the remaining 6 functions.

## What the auto-grading checks

The auto-grading (22 tests) uses **TestClient** (a test tool that calls your API
without starting a server) to confirm the API behaves exactly as the spec table
above says. It uses a temporary file for the DB, so `api.db` stays clean.

```bash
# inside this project's folder (projects/05-web-api)
python -m unittest -v
```

With the bare skeleton, exactly one test — `/health` — is green. From there you stack up the other 21.

## How to proceed (four milestones)

Turn the tests green one at a time. Run `python -m unittest -v` each round and watch the green count grow.

1. **GET /servers** — the easiest one. Build it together with list_servers in db.py
2. **POST /servers** — the big climb. Pydantic validation (422), 201, the API key (401), and duplicates (409) all arrive at once. **Get past this, and the rest is the same pattern repeated**
3. **GET /servers/{id}** — learn the 404 pattern
4. **The two checks endpoints** — reuse the patterns from 2 and 3. To finish, take one full loop through /docs

## Completion conditions (Project 5 is done when all of these hold)

- [ ] All 22 auto-grading tests are green
- [ ] You opened `/docs` and looked at your own API's manual
- [ ] With curl (or Try it out in /docs), you traced one loop by hand: register → record → list
- [ ] You can explain, in your own words, when to use 401 / 404 / 409 / 422
- [ ] Not one line of SQL exists outside db.py
- [ ] Error responses show no internal details (table names, SQL, tracebacks)
- [ ] You added a "How to use" section to the README in your own words / filled in `RETROSPECTIVE.md`

## Challenge (optional): swap SQLite for PostgreSQL

Project 2's PostgreSQL (docker compose) is still on your machine. Swap db.py for a
psycopg version and you will fall into **three holes**, in order. That's the learning.

1. **The placeholders differ**: sqlite3 uses `?`, psycopg uses `%s`.
   Confining SQL to db.py was exactly so this swap stays a one-file job.
2. **`lastrowid` doesn't work**: on PostgreSQL, rewrite it as `INSERT ... RETURNING id`.
3. **Commit manners differ**: sqlite3's `with conn:` commits but does not close the connection.
   psycopg's `with connect() as conn:` commits **and closes the connection**.
   Keep querying in the same transaction after an error and you get `InFailedSqlTransaction`
   (rollback, then continue).

If it works, your API has become a tool that knows "SQLite in development, PostgreSQL in production."

## Submitting (the full loop that finishes a project)

1. Cut a working branch (e.g. `git switch -c task5-web-api`)
2. Implement, and confirm `python -m unittest -v` is green
3. push → Pull Request → **auto-grading green** → self-merge
4. Fill in `RETROSPECTIVE.md`

> **It's safe to break things.** Delete api.db and it gets rebuilt (it's already in
> .gitignore and never committed). The dev server stops with Ctrl+C. No need to tiptoe.
