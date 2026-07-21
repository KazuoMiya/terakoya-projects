> 日本語版: [expected-output.md](./expected-output.md)

# Sample output (for self-checking)

> Note: the report labels and messages below are shown in English; the Japanese
> original shows the same output with Japanese labels. The exact wording is your
> choice — the tests do not assert the output text. The diff lines and numbers must match.

## Diff report for the two samples (format is free; the content must match these 6 lines)

```
# Config Diff Report

+ packages: openssl 3.0.15-0ubuntu1
- packages: openssl 3.0.13-0ubuntu3
- services_running: nginx
+ listen_ports: 8080
+ users: tempuser
+ cron_entries: @reboot /tmp/.cache/update.sh
```

Exit code: `1` (WARNING). **`collected_at` must not appear anywhere.**

## On your own machine (Ubuntu / WSL2)

```
$ python src/config_diff.py
First run: saved the baseline. Diffs will appear from the next run.
$ echo $?
0

$ python src/config_diff.py
# Config Diff Report

No diff (same configuration as last time).
$ echo $?
0
```

If the second run doesn't come out as "no diff," a wobbling value isn't being dropped
by normalize. Look closely at what shows up in the diff — that is your list of
"values to drop."

## When you deliberately create a change (e.g. install one package)

```
$ sudo apt install -y sl
$ python src/config_diff.py
# Config Diff Report

+ packages: sl 5.02-1
$ echo $?
1
```

## The extension cleanup's dry-run (the default)

```
$ python src/cleanup.py /tmp/cleanup-practice --days 30
[dry-run] 2 deletion candidates (nothing actually deleted):
  /tmp/cleanup-practice/old1.log
  /tmp/cleanup-practice/old2.log
To really delete, add --execute.
$ echo $?
0
```

## Self-check points

- [ ] With the two samples, all five changes appear / collected_at does not
- [ ] First run = save only, ending OK; two consecutive runs give "no diff"
- [ ] You detected the change you deliberately created (and reverted it after confirming)
- [ ] It doesn't crash on items it can't collect (a "couldn't get" record appears)
- [ ] (Extension) cleanup deletes nothing by default, deletes only with --execute, and the second run says "nothing to delete"
