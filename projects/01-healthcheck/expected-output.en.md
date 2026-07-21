> 日本語版: [expected-output.md](./expected-output.md)

# Sample output (for self-checking)

Your tool's output is fine if it roughly matches this sample in **items and format**.
Numbers and server names naturally differ per environment, so **an exact match is not required**.
What matters is that "the same kinds of information come out, in a readable form."

> Note: the Japanese original shows some labels in Japanese (e.g. `全体` for "Overall,"
> and the error message `ログファイルが読めない` "cannot read the log file"). The tests don't
> assert any output text, so your tool can print its messages in English. The samples below
> use English labels — the exact wording is up to you.

## Text output (`--warn 70 --crit 90`)

```
[OK]       disk_usage   42%   (warn=70 crit=90)
[WARNING]  load_average 1.85  (warn=70 crit=90)
[UNKNOWN]  log_errors   -     (collection failed: cannot read the log file)

Overall: WARNING
```

Exit code: `1` (WARNING). To check it, right after the command:

```bash
echo $?
```

## JSON output (with `--json`)

```json
{
  "overall": "WARNING",
  "exit_code": 1,
  "checks": [
    { "name": "disk_usage",   "status": "OK",      "value": 42 },
    { "name": "load_average", "status": "WARNING", "value": 1.85 },
    { "name": "log_errors",   "status": "UNKNOWN",  "value": null, "error": "cannot read the log file" }
  ]
}
```

## Self-check points

- [ ] Every item carries a state (OK/WARNING/CRITICAL/UNKNOWN)
- [ ] Items that couldn't be measured are UNKNOWN (not disguised as 0 or CRITICAL)
- [ ] The overall state matches the most serious item
- [ ] The exit code matches the overall state (OK=0/WARNING=1/CRITICAL=2/UNKNOWN=3)
- [ ] The `--json` output is valid JSON that could be passed straight to another tool
