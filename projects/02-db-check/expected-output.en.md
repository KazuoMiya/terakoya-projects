> 日本語版: [expected-output.md](./expected-output.md)

# Sample output (for self-checking)

Your tool's output is fine if it roughly matches this sample in **items and format**.
Numbers naturally differ per environment, so **an exact match is not required**.

> Note: the Japanese original shows some labels in Japanese (e.g. `全体` for "Overall,"
> `前日比` for "vs. yesterday," and log lines `点検開始`/`点検終了` for "check started"/"check finished").
> The tests don't assert any output text, so your tool can print its messages in English.
> The samples below use English labels — the exact wording is up to you.

## Text output

```
[OK       ] connectivity         2.1ms
[OK       ] uptime               3.5hours
[OK       ] recovery_state       primary
[OK       ] db_size              9.42MB  [vs yesterday +0.15]
[OK       ] disk_usage           41.0%
[OK       ] connections          2/100
[OK       ] long_queries         0
[WARNING  ] idle_in_transaction  1
[OK       ] lock_waits           0
[OK       ] temp_files           0
[WARNING  ] dead_tuples          342

Overall: WARNING
```

Exit code: `1` (WARNING). You can check with `echo $?`.

## The log (make sure no password appears)

```
2026-07-16 09:00:00 INFO check started: postgresql://checker:***@localhost:5432/terakoya
2026-07-16 09:00:00 INFO check finished: WARNING
```

**If a raw password appears here, you're breaking Iron Rule 3.** Fix it before anything else.

## JSON output (`--json`)

```json
{
  "overall": "WARNING",
  "exit_code": 1,
  "checks": [
    { "name": "connectivity", "status": "OK", "value": 2.1, "unit": "ms" },
    { "name": "idle_in_transaction", "status": "WARNING", "value": 1 },
    { "name": "dead_tuples", "status": "WARNING", "value": 342, "table": "health_checks" }
  ],
  "deltas": { "db_size": 0.15 }
}
```

## Self-check points

- [ ] All 10 items appear
- [ ] The connection target in the log is masked with `***` (Iron Rule 3)
- [ ] Items that couldn't be measured are UNKNOWN (not disguised as 0 or CRITICAL)
- [ ] The overall state matches the most serious item / the exit code matches too
- [ ] A second run emits `deltas` (the day-over-day diff)
- [ ] **When you deliberately created an idle in transaction, item 8 caught it**

> `dead_tuples` being WARNING from the first run (about 342 rows) is expected. The sample data
> deliberately leaves remnants — nothing is broken.
