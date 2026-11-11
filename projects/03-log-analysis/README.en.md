> 日本語版: [README.md](./README.md)

# Project 3: Log Analysis and Incident Detection Tool

On the morning of an incident, you dig "since when, what, and how much" out of a
mountain of logs with grep and your eyes. This project turns that investigation into
**a tool that produces the same result no matter who runs it**.
It tallies the log, finds **spikes** in errors, puts them into a report, and notifies only when something is abnormal.

> This README is the authority for the project. The course lessons (proj-13–15) are
> your guide to reading and working through this spec. Whenever you're lost, come
> back to the completion conditions written here.

## The verification log (the answer is already decided)

`logs/app.log` holds two days of application logs. This log has
**an answer planted in it**: a spike of DB connection timeouts (44 events) in the 14:00 hour of 2026-07-15.
The usual ERROR rate is 2–4 per hour. Your tool finds this gap on its own.

Lines that don't fit the format — like the continuation of a stack trace — are
**deliberately mixed in**. Real logs always contain odd lines. An analysis tool
that crashes on them isn't a tool.

## What you build

Finish `src/log_check.py` as a CLI that can do the following.

1. Read the log **line by line** (don't load it all into memory — production logs reach gigabytes)
2. Break up each line (timestamp, level, message). **Count broken lines and skip them** (don't crash)
3. Tally ERRORs per time window
4. **Detect spikes** — at least the average of prior windows × `--factor`, **and**
   at least `--min-count`. A **two-part guard** of multiple and absolute count
5. Output the result as a **Markdown report**
6. Notify **only when there's a spike** (Slack Incoming Webhook). Stay silent when normal
7. End with an **exit code** matching the overall state (spike present = 1 / none = 0 / log unreadable = 3)

## Alert fatigue — the most important thing in this project

Judge spikes by multiple alone, and errors going from 1 to 3 in the middle of the night
ring a "3x increase!" notification. When that continues every night, **people stop
reading notifications**. A notification nobody reads is the same as one that doesn't
exist. The notification for a real incident gets ignored right along with it.

So this project's spike verdict is a two-part guard.

```
count >= average of prior windows × factor   (multiple: is it high compared to usual?)
and
count >= min_count                           (absolute count: is it even worth the noise?)
```

And **notify only on an abnormality**. Don't ring "all normal today" every day
when things are fine. Silence is the signal of normal. That's the etiquette of
notifications that keep being read.

## What the auto-grading checks

The auto-grading (`tests/test_log_check.py`) tests **three pure functions**.
File reading, the report, and notification depend on the environment, so they aren't graded (check them yourself).

| Function | Role |
|---|---|
| `parse_line(line)` | Breaks one line into `{"time", "level", "message"}`. Out-of-format lines return `None` (no crash) |
| `bucket_by_hour(records, level="ERROR")` | Counts events per time window (the first 13 characters) |
| `detect_spike(series, factor=3.0, min_count=10)` | Returns the time windows that spiked. **Two-part guard**; the boundaries are inclusive ("or more") |

`worst_status` and `status_to_exit_code` come pre-loaded, exactly as you wrote them yourself in Project 1.

## Notification (you can finish without Slack)

The notification target is Slack's **Incoming Webhook** (a mechanism where POSTing to a URL delivers a message).

- **The Webhook URL is "a password in the shape of a URL."** Anyone who knows it can
  post to that channel. Don't write it in code; put it in `.env` (`cp .env.example .env`).
- For people without a Slack environment: **if the URL is unset, just displaying the
  notification body on screen is enough**. That satisfies the completion conditions.
  What's worth building is the design — "notify only on an abnormality."
- pip setup (inside your venv): `pip install -r requirements.txt` (requests and python-dotenv)

## How to proceed (five milestones)

Move forward holding "something that works" at every step. 1–3 are pure functions, so each one you write adds green to the grading.

1. **Turn parse_line green** — you can break up one line, and return None on a broken line
2. **Turn bucket_by_hour green** — you can count per time window
3. **Turn detect_spike green** — you can find spikes. **The grading goes all green here**
4. **One full pass from the file** — read logs/app.log and reconcile against the reference numbers (471 lines analyzed, 163 ERRORs, the spike only in the 14:00 hour)
5. **Connect the notification** — to Slack only on a spike. Also confirm it stays silent when normal

## Completion conditions (Project 3 is done when all of these hold)

- [ ] You **detected** the spike in `logs/app.log` (the 14:00 hour of 2026-07-15, 44 events)
- [ ] It **doesn't fire** on the other time windows (around 4 or 3 events) (min_count is doing its job)
- [ ] It doesn't crash on broken lines, and counts them as "unreadable lines: N"
- [ ] It reads the log line by line (not the whole file with `f.read()`)
- [ ] A Markdown report comes out (the numbers match expected-output.md)
- [ ] Notification happens only on a spike. Nothing is sent when normal
- [ ] The Webhook URL isn't written in the code (it's in `.env`)
- [ ] The exit code matches the verdict (1/0/3)
- [ ] The auto-grading is green (`python -m unittest -v`)
- [ ] You added a "How to use" section to the README in your own words / filled in `RETROSPECTIVE.md`

## Tests

```bash
# inside this project's folder (projects/03-log-analysis)
python -m unittest -v
```

## How to use

<!-- ★ Write how to use your tool here, in your own words. expected-output.md is a sample too. -->

```bash
python src/log_check.py logs/app.log
python src/log_check.py logs/app.log --factor 3 --min-count 10
```

## Extension (optional): run it unattended

A tool a human runs by hand is still "only half automated." Put it on cron (the Linux
mechanism that runs a command at a fixed time) and it runs unattended. Two traps you
meet here for the first time:

1. **PATH and the working directory are different.** Inside cron is a different world
   from your terminal. Point at **the venv's python by absolute path**, not `python`,
   and write the log path as an absolute path too.
2. **You need a place for the results.** There's no screen, so leave the output in a file.

```bash
# example line for crontab -e: inspect at 7:00 every morning and keep the report
0 7 * * * /home/you/terakoya-projects/.venv/bin/python /home/you/terakoya-projects/projects/03-log-analysis/src/log_check.py /var/log/app.log >> /home/you/log_check_report.md 2>&1
```

On WSL2 you need the cron service running first (`sudo service cron start`).
Let it run for a few days, and if each morning's result is appended to the report
file, it worked. **Skipping this doesn't block finishing Project 3.**

## Submitting (the full loop that finishes a project)

1. Cut a working branch (e.g. `git switch -c task3-log-analysis`)
2. Implement, and confirm `python -m unittest -v` is green
3. push → Pull Request → **auto-grading green** → self-merge
4. Fill in `RETROSPECTIVE.md`

> **A caution before pointing this at real logs.** This tool is usable at your own
> workplace starting Monday. But real logs can have personal or confidential
> information captured in them. Where you put reports and who you share them with
> must follow your "customer data handling" rules. The more useful the tool becomes,
> the heavier the handling of its output.
