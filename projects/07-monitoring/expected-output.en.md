> 日本語版: [expected-output.md](./expected-output.md)

# Sample output (for self-checking)

The numbers will differ in your environment — that's expected. What you're looking
for is "the same kind of log line, at the same moments."

> Note on wording: the log messages below are shown in English; the Japanese original
> uses lines like 「web-gate が CRITICAL になった」 ("web-gate went CRITICAL"). The exact
> log wording is your choice — the tests do not assert log output. The one wording
> contract that IS graded: `parse_config`'s ValueError message must contain the name
> of the offending target (e.g. `web-gate`).

## An ordinary loop (everything OK)

```
2026-07-17 09:00:00 INFO monitoring started: 2 targets / every 60s / recording to http://127.0.0.1:8000
(after this, as long as no state changes, no warnings appear. Silence is the signal that all is well)
```

## Logs during the demo scenario (measured example)

```
# the loop right after sudo systemctl stop nginx:
2026-07-17 09:05:00 WARNING web-gate went CRITICAL (http_health=0)

# after that, loops where it stays CRITICAL print nothing (no repeating itself)

# the loop right after sudo systemctl start nginx:
2026-07-17 09:12:00 WARNING web-gate went OK (http_health=8.3)
```

## The history kept by the API (recording happens every time)

```
$ curl -s "http://127.0.0.1:8000/servers/1/checks?limit=5"
[
  {"id": 12, "metric": "http_health", "status": "OK",       ...},   ← after recovery
  {"id": 11, "metric": "http_health", "status": "CRITICAL", ...},   ← while stopped
  {"id": 10, "metric": "http_health", "status": "CRITICAL", ...},   ← while stopped
  {"id":  9, "metric": "http_health", "status": "OK",       ...},   ← before the stop
  ...
]
```

## When the recording destination is stopped (the bonus experiment)

```
2026-07-17 09:20:05 ERROR couldn't record the result for web-gate (monitoring continues): ...
2026-07-17 09:20:05 ERROR couldn't record the result for this-server-disk (monitoring continues): ...
(the monitor process doesn't die. Bring the API back and recording resumes on the next loop)
```

## When the config is broken (it stops before starting)

```
$ python src/monitor.py --config config.json    # tried setting type to "ping"
2026-07-17 09:30:00 ERROR can't read the config: target web-gate: invalid type (must be http or disk)
$ echo $?
3
```

## Self-check points

- [ ] When all is well, no warnings appear (only the INFO startup log)
- [ ] On worsening and on recovery, a warning appears **exactly once each**
- [ ] The history keeps a record for every loop (the number of warnings and the number of history rows are different things)
- [ ] Monitoring continues even while the recording destination is dead / a config mistake stops it before starting
