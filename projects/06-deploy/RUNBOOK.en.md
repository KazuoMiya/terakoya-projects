> 日本語版: [RUNBOOK.md](./RUNBOOK.md)

# Runbook — Release and Rollback (fill-in template)

In Guard It (2), you fill in this runbook with **the actual commands for your own environment**.
A runbook exists so you can "read first, then act" (see the release-day lesson in The Field of Development).
Once it's filled in, test it: can you go through one more loop **looking only at the runbook**? — that is the runbook's test.

> **Iron Rule: write the rollback steps first. A release you can't undo is not a release.**

## 0. Preconditions

- Target: the Check-Results API from Project 5 (systemd service name: `terakoya-api`)
- Operator: <name>
- Estimated time: <minutes>
- Preconditions: <e.g. main is green (the PR's auto-grading has passed)>

## 1. Release steps

| # | What to do | Command | Check |
|---|---|---|---|
| 1 | Back up right before | `<e.g. bash deploy/backup.sh ... >` | backup-complete message shown |
| 2 | Pull the new code | `<git pull, etc.>` | note down the commit ID you got |
| 3 | Tests | `<python -m unittest -v>` | all green |
| 4 | Restart | `<sudo systemctl restart terakoya-api>` | active (running) |
| 5 | Smoke check | `<curl http://localhost/health>` | `{"status":"ok"}` |

## 2. Rollback steps (write these first)

If you judge "after the release, /health doesn't respond or errors are rising," don't hesitate — come here.

| # | What to do | Command | Check |
|---|---|---|---|
| 1 | Return to the previous commit | `<git switch --detach <the ID you noted>, etc.>` | |
| 2 | Restart | `<sudo systemctl restart terakoya-api>` | active (running) |
| 3 | Smoke check | `<curl http://localhost/health>` | `{"status":"ok"}` |
| 4 | Report | record that you rolled back, and what you noticed | |

## 3. Decision criteria (fill in)

- Conditions to call the release a success: <e.g. /health returns 200, and one loop of register → record → list goes through>
- Conditions to roll back: <e.g. the above can't be met within 5 minutes>
- When in doubt: don't grind alone — write down the situation and ask (the question format)
