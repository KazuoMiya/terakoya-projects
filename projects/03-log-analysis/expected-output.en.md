> 日本語版: [expected-output.md](./expected-output.md)

# Sample output (for self-checking)

This is the sample for a run against the bundled `logs/app.log`. This log has
**a decided answer** — a spike of DB connection timeouts (44 events) is planted in
the 14:00 hour of 2026-07-15. If your tool doesn't pick this up, something is off.

The report's appearance may differ somewhat. What matters is that **the numbers and
the verdict** match.

> Note: the report labels below are shown in English; the Japanese original shows
> the same report with Japanese labels. The exact wording is your choice — the tests
> do not assert the output text. The numbers must match exactly.

## Example run

```
$ python src/log_check.py logs/app.log
```

```
# Log Inspection Report

- Lines analyzed: 471 (unreadable lines: 3)
- Counts: ERROR 163 / WARN 20 / INFO 288

## ⚠ Time windows with a detected spike

- **2026-07-15 14:00 hour**: 44 ERROR events

## ERROR counts by time window (descending, top 5)

| Time window | Count |
|---|---|
| 2026-07-15 14 | 44 ⚠ |
| 2026-07-15 23 | 4 |
| 2026-07-14 01 | 3 |
| 2026-07-14 03 | 3 |
| 2026-07-14 05 | 3 |
```

Exit code: `1` (WARNING). You can check it with `echo $?`.

## Numbers that must match

| What | How many |
|---|---|
| Lines analyzed | **471** |
| Unreadable lines (blank lines don't count) | **3** |
| Total ERRORs | **163** |
| Time windows judged a spike | **2026-07-15 14 only** (44 events) |
| Exit code | **1** (spike present = WARNING) |

- It matters that **exactly one** spike is detected. If it fires on the 23:00 hour
  of 2026-07-15 (4 events) or the middle-of-the-night 3s, the min_count guard isn't working.
- If nothing is detected instead, suspect factor or the direction of the comparison (`>=`).

## Checking the notification

- If `SLACK_WEBHOOK_URL` is unset: it's fine as long as you can see the notification
  body with a display like "notification target unset — display only"
  (**you can finish the project without Slack**).
- If it is set: the message arrives only on a spike. Also confirm that **nothing
  arrives when you run against a normal log** (silence when normal — that's
  notification etiquette).

## Self-check points

- [ ] Lines analyzed, unreadable lines, and total ERRORs match the table above
- [ ] The spike is detected **only** in the 14:00 hour of 2026-07-15
- [ ] Broken lines (stack traces etc.) raise no exception; they're counted and skipped
- [ ] The exit code matches the verdict (spike present = 1 / none = 0 / log unreadable = 3)
- [ ] No notification is sent when normal (no spike)
