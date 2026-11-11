> 日本語版: [README.md](./README.md)

# Project 1: Server Health-Check CLI

Build a command-line tool that automates the manual "morning server inspection."
It gathers the state of CPU, memory, disk, and more, judges each as **OK / WARNING / CRITICAL**,
and outputs the result in a form both humans and machines can read. **It's a tool you can use
for your own inspections starting Monday.**

> This README is the source of truth for the project. The course lessons (proj-06 through 08)
> are a walkthrough and guideposts for this spec. Whenever you're unsure, come back to the
> completion conditions written here.

## What you build

Finish `src/healthcheck.py` as a CLI that can do the following.

1. Gather server state **via OS commands** (e.g. `df`, `uptime`, `ps`, `ss`/`netstat`, error counts in logs). At least 1 item; ideally 2 or more, such as "disk usage" and "load average."
2. Judge each gathered value against **thresholds** (two levels: `--warn` and `--crit`).
3. Output results as both **text** and **JSON** (`--json`).
4. Exit with an **exit code** that reflects the overall state.
5. If one item fails along the way, **the other items continue** (a partial failure doesn't stop the whole).
6. Leave a **log** of what the tool did (`logging`).

## States and exit codes (the common language of monitoring)

| State | Exit code | Meaning |
|---|---|---|
| OK | 0 | Healthy |
| WARNING | 1 | Caution (at or above `warn`, below `crit`) |
| CRITICAL | 2 | Danger (at or above `crit`) |
| UNKNOWN | 3 | Couldn't measure at all (command failure, etc.) |

For the overall exit code, use the most serious state (**CRITICAL > WARNING > UNKNOWN > OK**).

> **Iron Rule**: Never mix "danger (CRITICAL/WARNING)" with "couldn't measure (UNKNOWN)."
> Mix them, and the tool cries "production is down!" when only the tool itself broke — or it
> crushes a real anomaly into silence. These are the two great monitoring accidents.
> When you couldn't measure, say so honestly: UNKNOWN.

## Completion conditions (with all of these, project 1 is complete)

- [ ] Thresholds can be passed as arguments (`--warn` / `--crit`)
- [ ] The four states OK / WARNING / CRITICAL / UNKNOWN are distinguished (UNKNOWN is not mixed into CRITICAL)
- [ ] Both text output and JSON output (`--json`) are supported
- [ ] The exit code reflects the overall state
- [ ] One failing item doesn't crash the whole; that item becomes UNKNOWN
- [ ] `logging` records what the tool did
- [ ] **The judging logic is separated into pure functions, and the tests are green** (`python -m unittest -v`)
- [ ] You've extended the README ("Usage" below) in your own words, so someone else could read it and run your tool
- [ ] You've filled in `RETROSPECTIVE.md`

## What the auto-grading checks

The auto-grading (`tests/test_healthcheck.py`) tests the **three pure functions**
in `src/healthcheck.py`. Getting these green first is the backbone of project 1.

| Function | Role |
|---|---|
| `judge(value, warn, crit)` | Judges a single value and returns "OK"/"WARNING"/"CRITICAL" |
| `worst_status(statuses)` | Returns the overall state (the most serious one) from a list of states |
| `status_to_exit_code(status)` | Converts a state to an exit code (0/1/2/3) |

Collection, display, argparse, logging, and `main()` are outside the auto-grading (their results vary by environment).
Assemble those yourself, using "Usage" and `expected-output.md` as your model, and self-check.

## How to proceed (four milestones)

Don't build everything at once. Keep something working at every stage.

1. **Judging and assembly** — Write `judge` / `worst_status` / `status_to_exit_code` and get the tests green. Collect the results into a dict and `print` it as JSON.
2. **Gather real values** — Call `df` and `uptime` with `subprocess.run(...)` and pull out the numbers you need.
3. **Exceptions and exit codes** — Turn a collection failure into UNKNOWN and continue. Decide the exit code from the overall state.
4. **Finish it as a tool** — Add `argparse` (`--warn/--crit/--json`) and `logging`, and write the README.

## Tests

```bash
# Inside this project's folder (projects/01-healthcheck)
python -m unittest -v
```

## Usage

<!-- ★ Write how to use YOUR tool here, in your own words. Use expected-output.md as a model too. -->

```bash
python src/healthcheck.py --warn 70 --crit 90
python src/healthcheck.py --warn 70 --crit 90 --json
```

## Submitting (one loop to finish the project)

1. Cut a working branch (e.g. `git switch -c task1-healthcheck`)
2. Implement, and confirm `python -m unittest -v` is green
3. push → Pull Request → **auto-grading green** → self-merge
4. Fill in `RETROSPECTIVE.md`

> **It's fine to break things.** This copy is yours alone. Everything stays inside the venv and this folder.
> If it gets weird, delete it and rebuild. No need to touch it gingerly.
