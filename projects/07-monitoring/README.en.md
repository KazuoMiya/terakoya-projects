> 日本語版: [README.md](./README.md)

# Final Project: Integrated Monitoring — One Loop of Rewiring

After six projects, every part is already in place. What you build here is a
**small monitoring system** that connects them: it checks the targets listed in a
config file at a fixed interval, records the results to Project 5's API, and raises
its voice only when a state changes.

**The only new technique to learn is "the periodic-execution loop."** Everything else is rewiring.

| Part you reuse | Where it came from |
|---|---|
| The 4 statuses and the way of judging | Project 1 |
| Separating config from secrets (.env) | Project 2 |
| A design that prevents alert fatigue | Project 3 |
| A place to send results (the API) | Project 5 |
| A foundation that keeps running (the API on systemd) | Project 6 |

> This README is the authority for the project. The course lessons (proj-27–30) are
> your guide to reading and working through this spec. Whenever you're lost, come
> back to the passing conditions written here.

## The overall shape

```
config.json ──→ monitor.py ──(every interval_seconds)──→ check each target
                    │                                        │
                    │  warning log only when a state changes  │ results (every time)
                    ▼                                        ▼
              journalctl / screen                 Project 5's API (:8000) → history in the DB
```

There are two kinds of targets: **http** (hit a URL and look at the response code
and time) and **disk** (disk usage — a reuse of Project 2's `shutil.disk_usage`).

One design decision matters here. **The monitoring route and the recording route are
separate.** The http target is `http://localhost/health` via Nginx (the front door);
results are recorded to `http://127.0.0.1:8000` (straight to the back, the API itself).
So even when the front door (Nginx) dies, that failure can still be recorded in the DB
behind it. The mechanism for telling "the target's failure" from "the monitor's own
failure" shows up in how the routes are split.

## Environment setup

On Project 6's machine (WSL2 / Multipass), Project 5's API should be running under
systemd. If you skipped Project 6, starting it by hand with
`uvicorn app:app --app-dir src` is fine too (in that case, set the http target's URL
to `http://127.0.0.1:8000/health`).

```bash
cd projects/07-monitoring
pip install -r requirements.txt
cp config.example.json config.json     # edit to match your environment
cp ../05-web-api/.env .env             # same API_KEY (used for recording)
```

## What you build

Finish `src/monitor.py` into a tool that can do the following.

1. Read `config.json` and validate it **before starting** (if something's wrong, stop with words a human can act on)
2. Check every target, every `interval_seconds`
3. POST the results to Project 5's API **every time** (history piles up in the DB)
4. Emit a warning log **only when a state changes** (worsening and recovery alike; stay silent while the state is the same)
5. One target's failure must not stop the whole run
6. **A recording failure must not stop the monitoring** (log it and move to the next loop)
7. `--once` runs exactly one loop (for tests and the demo)

## The non-functional requirements are just these three

Don't tense up at the phrase "non-functional requirements." In this project it means the following three things.

1. **Keep going through partial failure** — one target failing, or recording failing, must not stop the monitoring as a whole
2. **Keep the monitor's own logs** — what the monitor did and what it failed at must be traceable afterwards
3. **Thresholds live in the config file** — targets and thresholds can change without editing code

**What we don't do** (needed in the field, but outside this project): scaling to many
machines, redundancy (HA), more notification channels, encryption, a web UI. Two
targets are plenty. A sequential loop is plenty.

## What the auto-grading checks

The auto-grading (23 tests) looks at **three pure functions**. The loop and HTTP vary
with the environment, so you verify those yourself with the demo scenario.

| Function | Role |
|---|---|
| `parse_config(config)` | Config validation. Stop before starting, with words a human can act on |
| `judge_http(status_code, elapsed_ms, warn_ms, crit_ms)` | Unreachable, or anything but 200, is CRITICAL. Otherwise judge by response time |
| `should_alert(prev_status, curr_status)` | True **only when the state changed**. The final exam on alert fatigue |

`worst_status` and `status_to_exit_code` are already included, as your deliverables from Project 1.

```bash
# inside this project's folder (projects/07-monitoring)
python -m unittest -v
```

## How to proceed (five milestones)

1. **Get the pure functions green** — parse_config / judge_http / should_alert. **The grading turns fully green right here**
2. **Write the two check types** — check_http and check_disk. Run exactly one loop with `--once` and look at the results on screen
3. **Connect the recording** — POST to Project 5's API. Verify registration and records with `curl http://127.0.0.1:8000/servers`
4. **Turn it into a loop** — while + sleep. Hold a dict of states, and confirm warnings appear only on change
5. **The demo scenario** — stop nginx, and see detection → recording → suppression → recovery through to the end

## Passing condition — one demo scenario

What passes this system is not the number of checkboxes but **one scenario running
through from start to finish**.

```bash
# 0. Keep the monitor running (separate terminal; while learning, set interval to ~10 seconds)
python src/monitor.py --config config.json

# 1. Stop the front door (Nginx) = cause a failure of the monitored target
sudo systemctl stop nginx

# 2. On the next loop: a warning log — "web-gate went CRITICAL" — appears exactly once.
#    And that failure is recorded in the DB behind the API (:8000):
curl -s http://127.0.0.1:8000/servers          # find web-gate's id
curl -s "http://127.0.0.1:8000/servers/<id>/checks?limit=3"   # CRITICAL is recorded

# 3. While it stays CRITICAL over several loops, confirm the warning is NOT being repeated (important)

# 4. Recover
sudo systemctl start nginx

# 5. On the next loop: "web-gate went OK" (recovery) appears exactly once.
#    The history keeps both the CRITICAL period and the recovery
```

If this runs through, you have **detected a failure, recorded it, and seen it through
to recovery**. As a bonus experiment, also try `sudo systemctl stop terakoya-api`
(stopping the recording destination) partway through. The monitor doesn't die — it
keeps saying "couldn't record (monitoring continues)", and once you bring the API
back, recording resumes. That's the moment monitoring survives its own failure.

## Completion check (the course is complete when all of these hold)

- [ ] All 23 auto-grading tests are green
- [ ] Break the config file (e.g. change a type to ping) and it stops before starting, with a clear message (the skeleton suggests Japanese wording; what the tests assert is that the message contains the target's name, e.g. web-gate)
- [ ] **The demo scenario ran through** (all four: detection → recording → suppression → recovery)
- [ ] You confirmed with your own eyes that the warning is not being repeated
- [ ] You confirmed the monitor doesn't die when the recording destination is stopped
- [ ] You filled in `RETROSPECTIVE.md` (including your retrospective on the whole course)

Submit with the usual loop (branch → PR → grading green → self-merge).

## Going further (optional)

- Put monitor.py itself on systemd (a reuse of Project 6 — write the unit file yourself)
- Wire Project 3's Slack notification into should_alert (a notification fires only on change)
- Import Project 1's CLI verdict functions and add targets beyond disk

> **It's safe to break things.** The only thing you stop is the nginx inside your own
> machine, and `start` brings it back. The recording DB is api.db, and even if it's
> lost you can restore it from Project 6's backup — and confirming that was exactly
> what Project 6 was about.
