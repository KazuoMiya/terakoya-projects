> 日本語版: [README.md](./README.md)

# Project 2: DB Daily Check Tool

Make "is the DB okay this morning?" answerable with a single command.
Can we connect? Is the size creeping up? Are any sessions stuck?
Take the inspection that people in operations do by eye, and turn it into a tool as-is.

> This README is the source of truth for the project. The course lessons (proj-09 through 12)
> are a walkthrough and guideposts for this spec. Whenever you're unsure, come back to the
> completion conditions written here.

**The main track is PostgreSQL. If Oracle is your world, build the PostgreSQL version first. Then
translate it into the language of your own workplace in the final "Optional Oracle Track"**
(because the way of thinking about inspection is the same).

## The three Iron Rules (the most important thing in this project)

Get one thing wrong in how you write an inspection tool, and it becomes a tool that
"takes down the very production it was supposed to protect."
Come back to these three again and again while you implement.

1. **The inspection tool itself must never become the cause of an outage.**
   Set **both** a connect timeout and a statement timeout (either one alone can wait forever).
   Read only the light statistics views; never full-scan a real table.
   *"We stopped production for the sake of monitoring" is an accident that really happens.*
2. **Read-only, least privilege. Don't mix in a "fix" feature.**
   Don't give the inspection user write privileges. Don't implement "responses" in the tool,
   like force-disconnecting sessions. **Separate detection from response — in privileges, and in who decides.**
   *A false-positive inspection tool killing a production batch is the classic accident.*
3. **The inspection results themselves can be confidential.**
   Personal data can be captured verbatim in the SQL that's currently running. Mask the password
   in the connection info before output. Where you put the results when saving or sharing them
   is part of the "secret" too.

## The verification environment (a finished product — it just works)

What you learn in this project is **DB inspection**, not Docker. The environment is provided.

```bash
cp .env.example .env          # secrets go in .env (already in .gitignore; never committed)
docker compose up -d          # PostgreSQL starts
docker compose ps             # wait until STATUS becomes healthy
```

On first startup, a **read-only user `checker`** dedicated to inspection — plus sample data
worth inspecting — is created automatically. The connection info is in `DB_DSN` in `.env`.

```bash
# If anything goes wrong, these two return you to the initial state (your safety net)
docker compose down -v        # removes the container and the data
docker compose up -d          # rebuilds from a clean slate
```

Python setup (inside the venv from project 0):

```bash
pip install -r requirements.txt   # installs psycopg (the PostgreSQL driver)
```

## What you build

Finish `src/db_check.py` as a CLI that can do the following.

1. Connect to PostgreSQL with `DB_DSN` from `.env` (as the read-only `checker`)
2. Inspect the **10 items** below and judge each OK/WARNING/CRITICAL/UNKNOWN
3. Output as both text and JSON
4. Exit with an **exit code** reflecting the overall state (the same 0/1/2/3 as project 1)
5. If one item fails, **the other items continue**
6. Log the connection target **masked** (Iron Rule 3)
7. Save results as JSON, and on the next run emit a **day-over-day diff**

## The 10 items to inspect

"Where to look" is written down. **You assemble the SQL yourself.** That is the heart of this project.

| # | Item | What to look at | The point |
|---|---|---|---|
| 1 | Connectivity / response time | Send `SELECT 1` and measure the round trip | Can't connect = the top-priority anomaly |
| 2 | Uptime | `pg_postmaster_start_time()` | Can't be called good or bad alone. **Shorter than yesterday means a restart happened** |
| 3 | Recovery state | `pg_is_in_recovery()` | primary or standby? If it differs from expectations, that's serious |
| 4 | DB size | `pg_database_size(current_database())` | Can't be called good or bad alone. Watch the **day-over-day diff** |
| 5 | Disk free | Python's `shutil.disk_usage()` | **The body of capacity monitoring lives outside the DB** |
| 6 | Connections | count in `pg_stat_activity` ÷ `max_connections` in `pg_settings` | Watch the usage ratio. Exhaustion means nobody can connect |
| 7 | Long-running queries | `pg_stat_activity` (`state`, `query_start`) | Finding clogs. Exclude yourself |
| 8 | idle in transaction | `pg_stat_activity` (`state`, `xact_start`) | **A PostgreSQL-specific item to watch.** An abandoned transaction keeps holding its locks |
| 9 | Lock waits | `pg_stat_activity` (`wait_event_type`) | **Inspect locks without taking locks** (Iron Rule 1) |
| 10 | Dead tuples / last autovacuum | `pg_stat_user_tables` | A PostgreSQL daily-check staple. Performance drops as they pile up |

> **dead_tuples being WARNING from the very first run is normal.** The sample data deliberately
> leaves about 342 rows of "remnants" from updates and deletes (and automatic cleanup is stopped
> for that table alone). Item 10 reports something from the start. That's **proof the item is alive**.
> An inspection tool that only ever says "all OK" against a healthy DB proves nothing.

> **Why is there no "tablespace usage"?** (for those with Oracle experience)
> Unlike Oracle's, a PostgreSQL tablespace has no usage ratio and no cap —
> it's just a directory assignment. **The body of capacity monitoring is on the OS's filesystem side.**
> That's why item 5 looks at the disk. A good example of a concept not carrying over as-is.

## What the auto-grading checks

The auto-grading (`tests/test_db_check.py`) tests **three pure functions that can judge without a DB**.
The parts that connect to the DB vary by environment, so they aren't graded (you verify them yourself).

| Function | Role |
|---|---|
| `mask_dsn(dsn)` | Replaces the password in a connection string with `***` (Iron Rule 3) |
| `judge_ratio(used, total, warn_pct, crit_pct)` | Judges by usage ratio. If `total` is 0/None, `UNKNOWN` (no division-by-zero crash) |
| `diff_snapshot(prev, curr)` | Compares last time with this time and returns the changes (only keys present in both) |

`worst_status` and `status_to_exit_code` are **the ones you wrote yourself in project 1**,
so they're included from the start as tools. No need to rebuild them.

## How to proceed (five milestones)

Don't aim at all 10 items at once. Keep something working at every stage.

1. **Connect to the environment** — `docker compose up -d` → wait for healthy → `\dt` works in psql
2. **Get the pure functions green** — Write `mask_dsn` / `judge_ratio` / `diff_snapshot` and get the grading tests green (don't touch the DB yet)
3. **An inspection of item 1 only** — Connect, measure the `SELECT 1` response time, and print a single line. **This is the moment it becomes a tool connected to a DB**
4. **Grow to 10 items** — Add one item at a time. Run after each one, and watch the output grow
5. **Finish** — JSON saving and the day-over-day diff, `--json`, and confirming the log is masked. Compare against expected-output.md

## Create an anomaly, and confirm you can detect it

**An inspection tool becomes an inspection tool only when it can find an anomaly.**
"All OK" against a healthy DB proves nothing.
Open a second terminal and create an anomaly on purpose.

```bash
# Terminal 2: deliberately create an "idle in transaction" and a lock wait
docker compose exec postgres psql -U postgres -d terakoya
```

```sql
-- Inside psql (leave it hanging without committing)
BEGIN;
UPDATE servers SET role = 'web' WHERE hostname = 'web-01';
-- Leave it here. This creates one "idle in transaction."
```

In this state, run `python src/db_check.py` and confirm that **item 8 catches it**.
Once confirmed, go back to psql and `ROLLBACK;` to restore everything (`\q` to quit).

## Completion conditions (with all of these, project 2 is complete)

- [ ] You can connect with `DB_DSN` from `.env`, going in as the **read-only `checker`**
- [ ] All 10 items are inspected
- [ ] **Both the connect timeout and the statement timeout** are set (Iron Rule 1)
- [ ] The log shows the connection target, but **the password is `***`** (Iron Rule 3)
- [ ] No "fix" behavior (disconnecting sessions, etc.) is **implemented** (Iron Rule 2)
- [ ] One failing item doesn't crash the whole; that item becomes UNKNOWN
- [ ] Both text and JSON output work / the exit code matches the overall state
- [ ] Results are saved as JSON, and a second run emits the **day-over-day diff**
- [ ] **You created an anomaly on purpose and confirmed it was detected** (the section above)
- [ ] Auto-grading is green (`python -m unittest -v`)
- [ ] You've extended "Usage" in the README in your own words / filled in `RETROSPECTIVE.md`

## Tests

```bash
# Inside this project's folder (projects/02-db-check)
python -m unittest -v
```

## Usage

<!-- ★ Write how to use YOUR tool here, in your own words. Use expected-output.md as a model too. -->

```bash
python src/db_check.py --warn 70 --crit 90
python src/db_check.py --json
```

## Optional Oracle Track

For those whose workplace runs Oracle: **the way of thinking about inspection is the same —
only the names of the places you look differ.** Finish the PostgreSQL version first,
then translate with this correspondence table.

| Check item | PostgreSQL | Oracle |
|---|---|---|
| Connectivity | `SELECT 1` | `SELECT 1 FROM dual` |
| Instance state | `pg_is_in_recovery()` | `v$instance` (`status`, `database_status`) |
| Uptime | `pg_postmaster_start_time()` | `v$instance.startup_time` |
| Capacity | DB size + **OS disk** | `dba_data_files` / `dba_free_space` (there is a concept of a **tablespace**) |
| Session count | `pg_stat_activity` ÷ `max_connections` | `v$session` ÷ `sessions` in `v$parameter` |
| Long-running SQL | `pg_stat_activity.query_start` | `v$session` (`status='ACTIVE'`, `last_call_et`) |
| Lock waits | `wait_event_type='Lock'` | `v$session.blocking_session` |
| Invalid objects | Almost no such concept (closest is an invalid index) | `dba_objects` (`status='INVALID'`) |
| Backup results | **Outside the DB** (pg_dump logs, etc.) | `v$rman_status` / `v$backup_set` |

**If you run the Oracle environment** (it's heavy: 4GB+ RAM, roughly 10GB of disk, and a huge first pull):

```bash
docker compose --profile oracle up -d    # takes several minutes to start; wait for healthy
```

Classic Oracle stumbling points:
- **Old articles lure you into installing Instant Client** → `python-oracledb`'s Thin mode needs
  no client library. `oracledb.connect()` is all you need.
- **Wrong connection target (ORA-12514)** → the target is the PDB `FREEPDB1` (`host:1521/FREEPDB1`).
- **Can't see the `v$` views (ORA-00942)** → the inspection user needs `SELECT_CATALOG_ROLE`.
- **Bind variables are written differently** → psycopg uses `%s`; oracledb uses `:name`.

## Submitting (one loop to finish the project)

1. Cut a working branch (e.g. `git switch -c task2-db-check`)
2. Implement, and confirm `python -m unittest -v` is green
3. push → Pull Request → **auto-grading green** → self-merge
4. Fill in `RETROSPECTIVE.md`

> **It's fine to break things.** The DB is a disposable inside Docker. `docker compose down -v`
> returns it to a clean slate. Not a single byte of real data is in it. No need to touch it gingerly.
