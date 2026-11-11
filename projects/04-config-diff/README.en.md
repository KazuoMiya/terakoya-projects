> 日本語版: [README.md](./README.md)

# Project 4: Configuration Collection and Drift Detection

Build the tool that eliminates "the settings had changed by the time I noticed."
It writes a server's configuration (packages, services, ports, users, cron) out to JSON,
compares against the previous snapshot, and reports **only what changed**.

> This README is the authority for the project. The course lessons (proj-16–18) are
> your guide to reading and working through this spec. Whenever you're lost, come
> back to the completion conditions written here.

**No environment setup needed.** No Docker, no DB to stand up. You build the diff engine
with the two bundled samples, and as the finishing touch, run it against the real
configuration of your own machine (WSL2/Ubuntu recommended).

## The heart of this project — "zero diff is normal"

A configuration-diff tool's enemy isn't missed detection — it's **noise**.
Mix "values that naturally wobble," like the collection time, into the diff, and the
report fills with diffs every day.
When that happens, nobody reads it after 3 days (it's the report version of Project 3's alert fatigue).

So the order is fixed. **First, build the state where "zero diff" comes out.**
Drop the wobbling values before comparison (`normalize`). Run twice in a row on the
same machine and it can say "no diff." That's the baseline (the foundation for comparison).
Precisely because the everyday report is quiet, the real changes float up.

## What you build

Finish `src/config_diff.py` as a CLI that can do the following.

1. Collect configuration **via OS commands** and write it to JSON (record the collection time too)
2. Drop wobbling values and align ordering (`normalize`)
3. Compare against the previous snapshot and output **added, removed, changed** (`diff_config`)
4. Compare lists by their **contents**, not wholesale (a usable report doesn't say
   "packages changed" — it can say "this version of openssl was added, this one removed")
5. Zero diff → OK(0); any diff → WARNING(1); snapshot unreadable → UNKNOWN(3)
6. On the first run (no previous), save the baseline and end OK
7. Even if some items can't be collected, don't crash — record "couldn't get" and continue

**Why it stops at WARNING.** A diff is the detection of the fact that "something changed."
Whether that's a legitimate change or an accident, the tool can't tell. Judging is a human's job
(the same idea as Project 2's Iron Rule, "separate detection from response").

## Items to collect (assuming Ubuntu / WSL2)

| Item | Hint for getting it |
|---|---|
| Packages and versions | `dpkg-query -W` (shape it into a list of "name version") |
| Running services | `systemctl list-units --type=service --state=running` |
| Listening ports | `ss -tlnH` (the port number is at the end of column 4, `0.0.0.0:80`) |
| Users who can log in | read `/etc/passwd` (only lines whose shell is `/bin/bash` etc.) |
| cron | `crontab -l` (**returns exit code 1 when empty. Empty isn't an abnormality** — crush this and you fall into the same hole as Project 1's "collection failure") |

To Mac folks: many of the commands above don't exist on Mac. **The diff engine (the
graded part) can be completed with the two samples alone**, so collection is the
finishing touch for people with a WSL2/Ubuntu environment. Items you can't get should
be recorded as "couldn't get" without the tool crashing. That itself is one of the
completion conditions.

## The samples have a story planted in them

`samples/baseline.json` (yesterday) and `samples/current.json` (today) are two days of the same server.
A correctly built diff engine finds **exactly five changes**.

1. `openssl`'s version went up (3.0.13 → 3.0.15) — wears the face of a legitimate patch
2. `nginx` **disappeared from services_running** — the package is still there. **"Installed" and "running" are different things**
3. Port **8080** newly opened — by whom, and for what?
4. User **tempuser** was added — for temporary work? forgotten cleanup?
5. **`@reboot /tmp/.cache/update.sh`** was added to cron — a mysterious script that runs
   from /tmp on every reboot.
   **This is the textbook face of a suspicious change** (think back to the security chapter of Infrastructure Basics)

And `collected_at` (the collection time) differs between the two files, but **must not appear in the diff**.
That's normalize's job.

## What the auto-grading checks

The auto-grading (21 tests) looks at **four pure functions**. Collection varies with the environment, so it isn't graded.

| Function | Role |
|---|---|
| `normalize(snapshot)` | Drops wobbling values and sorts lists. **Doesn't modify the original dictionary** |
| `diff_config(prev, curr)` | added / removed / changed. Compares lists by content |
| `judge_diff(diff)` | Zero diff → OK; anything there → WARNING |
| `select_old_files(entries, days, now_epoch)` | [for the extension] **Only selects** paths at least `days` days old. **Doesn't delete** |

`worst_status` and `status_to_exit_code` come pre-loaded as your own Project 1 deliverables.

The grading also includes a **full-loop test** that uses the two files in samples/.
The machine confirms that your engine finds all of the "five changes" above and
doesn't put `collected_at` in the diff.

## How to proceed (five milestones)

Build the engine first. Because the two samples give you "input with a known answer."

1. **Turn normalize green** — you can drop wobbling values and sort lists
2. **Turn diff_config green** — you can output added, removed, changed
3. **One full pass on the samples** — write judge_diff too and the grading's full-loop test (finding all five changes) goes green. **The grading is all green here**
4. **Add collection** — gather from your own machine one item at a time. Record items you can't get as "couldn't get" and continue
5. **Complete the baseline** — first run = save only; second run = "no diff." Then deliberately create a change and detect it

## Completion conditions (Project 4 is done when all of these hold)

- [ ] The auto-grading is green (`python -m unittest -v`) = you found all five changes in the samples
- [ ] `collected_at` doesn't appear in the diff (this is in the grading too)
- [ ] The first run only saves the baseline and ends OK; diffs appear from the second run on
- [ ] **Running twice in a row on your own machine gives "no diff"** (the baseline is complete)
- [ ] After that, you **deliberately created a change and detected it** (e.g. add a package with `sudo apt install sl`,
      or add a line with `crontab -e` → confirm the detection → revert)
- [ ] It doesn't crash even when some items can't be collected (records "couldn't get" and continues)
- [ ] The exit code matches the state (OK=0 / WARNING=1 / UNKNOWN=3)
- [ ] You added a "How to use" section to the README in your own words / filled in `RETROSPECTIVE.md`

## Tests

```bash
# inside this project's folder (projects/04-config-diff)
python -m unittest -v
```

## How to use

<!-- ★ Write how to use your tool here, in your own words. expected-output.md is a sample too. -->

```bash
python src/config_diff.py            # first run: save the baseline
python src/config_diff.py            # second run: report the diff against last time
python src/config_diff.py --json
```

## Extension: a cleanup tool with dry-run as the default (this course's first "mutating" tool)

Projects 1–4 so far have all been **read-only** tools. What's truly scary in the field
(= what's valuable) is a tool that **changes things**. With a small cleanup tool that
deletes old logs, get the manners of mutating tools into your body.

What you build: `src/cleanup.py`. It picks "files at least days days old" from the given folder and deletes them. But keep these rules.

1. **The default is dry-run (a rehearsal).** Running it **only shows the list — it deletes nothing**
2. It really deletes only when you add `--execute`. Show the target list before deleting, and log what was deleted
3. "Selecting" uses the already-graded `select_old_files` (separating select from delete was for exactly this)
4. Make it **idempotent** — run it twice in a row, and the second run ends normally with "nothing to delete"
5. Point it only at a practice folder you made yourself (`mkdir /tmp/cleanup-practice` and
   make old files with `touch`. `touch -d "40 days ago" /tmp/cleanup-practice/old.log`)

**Iron Rule: show before deleting. Don't delete by default. Record what you delete.**
Pointing a real deletion tool at a real log folder is a story outside this course.
If you ever do, backups (the Infrastructure Basics session) and permission come first.

## Submitting (the full loop that finishes a project)

1. Cut a working branch (e.g. `git switch -c task4-config-diff`)
2. Implement, and confirm `python -m unittest -v` is green
3. push → Pull Request → **auto-grading green** → self-merge
4. Fill in `RETROSPECTIVE.md`

> **It's safe to break things.** This tool only reads (and the extension's cleanup
> deletes nothing by default). The snapshot JSON gets rebuilt even if you delete it.
> No need to touch it timidly.
