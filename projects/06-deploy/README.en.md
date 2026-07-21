> 日本語版: [README.md](./README.md)

# Project 6: Deployment — Run It, Guard It

Right now you start Project 5's API with `uvicorn`, **by hand**. Close the terminal and it dies.
In this project you turn it into a **service that keeps running**. It comes up on its own when
the server reboots, comes back to life on its own when it falls over, and behaves itself behind
the front door (Nginx).
And you don't just run it — you **guard** it. A backup only becomes a backup once a restore has succeeded.

> This README is the authority for the project. The course lessons (proj-23–26) are
> your guide to reading and working through this spec. **This project has no auto-grading**,
> because a machine can't peek at what happens inside your environment. What certifies
> completion is the completion checklist and your runbook.

## Getting a machine — you need one Ubuntu where systemd runs

This project's counterpart is systemd (the manager of long-running services on Linux).

- **Windows (WSL2)**: your current Ubuntu can most likely be used as-is. To check:
  ```bash
  systemctl list-units --type=service | head -5   # if a list appears, systemd is running
  ```
  If you see "System has not been booted with systemd", add to `/etc/wsl.conf`:
  ```ini
  [boot]
  systemd=true
  ```
  then run `wsl --shutdown` in PowerShell and reopen Ubuntu.
- **Mac**: there is no systemd on a Mac. Use **Multipass** (a free tool from Canonical,
  the maker of Ubuntu) to stand up one disposable Ubuntu virtual machine.
  ```bash
  multipass launch --name deploy-practice -m 2G -d 10G   # one Ubuntu VM (give memory and disk some headroom)
  multipass shell deploy-practice                        # step inside (all work from here on happens in there)
  ```
  Install it from **the installer at canonical.com/multipass (the official site)**
  (macOS 14 or later, both Intel and Apple Silicon, free).
  If it breaks, delete it with `multipass delete --purge deploy-practice` and rebuild —
  the same disposable safety net as Docker.

> **Your workbench for this project is only "the Linux inside your own PC."** No real VPS
> or cloud (managing cost and exposure risk is outside this course). Nothing gets published
> to the internet either.

Inside the machine, set up the course repository and Project 5's API. **A bare Ubuntu has
neither venv nor sqlite3**, so install the tools first. WSL2 users can reuse the environment
from Project 0, but sqlite3 is newly needed this time:

```bash
sudo apt update && sudo apt install -y python3-venv sqlite3   # for venv and for backups
git clone <URL of your copy> terakoya-projects                # ★ clone under this exact name
cd terakoya-projects                                          # (the unit file's paths assume this name)
python3 -m venv .venv && source .venv/bin/activate
pip install -r projects/05-web-api/requirements.txt
cp projects/05-web-api/.env.example projects/05-web-api/.env   # ★ forget this and startup fails later
cd projects/05-web-api && python -m unittest && cd ../..       # Project 5 must be green
```

Forget the `.env` copy and the service will later fail to start with
"Failed to load environment files" (the grading tests stay green even without .env,
so this one is easy to miss here).

## How to proceed (a map in 8 stages)

This is a long project, so here's the whole map up front. Each stage ends with a
"check"; once it passes, you may move on. If you get tired, stop at a stage boundary
and pick it up tomorrow.

| Stage | What you do | Check |
|---|---|---|
| 1 | Get a machine ready | the `systemctl` list appears |
| 2 | Set up Project 5 on the machine | grading is green inside the machine |
| 3 | Keep it running with systemd | `status` is active (running) |
| 4 | Prove it keeps running | it revives after SIGKILL, and it's still there after a reboot |
| 5 | Stand Nginx up as the front door | `curl http://localhost/health` goes through |
| 6 | Experience TLS | `curl -k https://localhost/health` goes through |
| 7 | Check the logs, then backup → restore drill | you deleted it, and brought it back |
| 8 | Fill in the RUNBOOK and do one loop using only the runbook | it worked exactly as written |

## Run It (1) — keep it running with systemd

`deploy/terakoya-api.service` is a fill-in-the-blank template. Replace
`<あなたのユーザー名>` ("your username") with your own, place the file under
`/etc/systemd/system/`, and enable it (the steps are in the comment at the top of the template).

There are three points to hold on to.

1. **Every path is absolute.** In systemd's world, neither your venv nor your cd exists
   (the same setup as the trap cron taught you in Project 3).
2. **`--host 127.0.0.1` listens locally only.** The outside-facing front door is Nginx's job.
3. **Secrets come from .env via `EnvironmentFile`.** Never written directly into the unit file.

```bash
sudo systemctl status terakoya-api     # is it active (running)?
journalctl -u terakoya-api -n 20       # the logs are being collected by journald
curl http://127.0.0.1:8000/health      # {"status":"ok"}
```

**Two proofs that it keeps running.** (1) Kill the process **abnormally** and it revives within seconds:

```bash
sudo systemctl kill -s SIGKILL terakoya-api   # force-kill = cause an abnormal death
sleep 5 && curl -s http://127.0.0.1:8000/health   # it has already come back to life
```

`Restart=on-failure` reacts **only to abnormal terminations**. A plain `kill` (SIGTERM)
is the signal "stop politely"; systemd treats it as a clean shutdown and does not restart.
Try both and see the difference — that's how the meaning of on-failure sinks in.
(2) Reboot the machine (with Multipass: `multipass restart`) and it's already running
when you log back in (the effect of `enable`).

## Run It (2) — stand Nginx up as the front door

```bash
sudo apt update && sudo apt install -y nginx
```

Place `deploy/nginx-terakoya-api.conf` and enable it (the steps are in the comment at
the top of the file). **Always run `sudo nginx -t` before applying.** That's what keeps
a syntax mistake from being reloaded and breaking your front door.

```bash
curl http://localhost/health           # port 80 → Nginx → 127.0.0.1:8000 → the API
```

You now have a "reverse proxy": receive on 80, hand off to 8000. The reason you don't
expose the API directly is so that TLS, logs, and multiple co-hosted apps can all be
looked after at one front door.

## Guard It (1) — TLS, logs, backups

**TLS (self-signed, to learn the mechanism)**: uncomment the lower half of
`deploy/nginx-terakoya-api.conf` and create a key and certificate. Then **pass
`sudo nginx -t` before running `sudo systemctl reload nginx`** (every config change
means these two, every time). Now hit `https://localhost/health`
(you need curl's `-k`). In a browser you'd get a warning. It means **"the traffic is
encrypted, but nobody vouches for the issuer."** Real sites have a certificate
authority such as Let's Encrypt sign theirs. That requires a domain, so in this course
we stop at understanding the mechanism.

**Logs**: before building anything new, check what already exists.
```bash
journalctl -u terakoya-api --since today   # the app's logs (journald collects them automatically)
ls /var/log/nginx/                          # Nginx's logs
cat /etc/logrotate.d/nginx                  # the rotation config has been there from the start
journalctl --disk-usage                     # journald manages its own capacity too
```
The "logs grow without limit" problem is, in fact, already taken care of.
**Being able to check that** is this stage's learning.

**Backup → restore drill (the summit of this project)**:
```bash
bash projects/06-deploy/deploy/backup.sh projects/05-web-api/api.db ~/backups
```
Then **really break it, and really bring it back**:

1. Register 2–3 records with curl and confirm the list comes back
2. `sudo systemctl stop terakoya-api` → `rm projects/05-web-api/api.db` (**really delete it**)
3. start, then hit the list — see with your own eyes that the data is gone (empty)
4. stop → restore from the backup (`cp ~/backups/api-<timestamp>.db projects/05-web-api/api.db`)
5. start → confirm the list comes back **exactly as before**

> If deleting it feels scary, that's the right instinct. Which is exactly why you drill
> "being able to bring it back" into your body **while you're still in an environment
> you're allowed to break**. A backup owned by someone who has never restored is no
> different from a good-luck charm.

## Guard It (2) — the runbook (release and rollback)

Fill in `RUNBOOK.md` with the actual commands for your environment. **Write the rollback
first.** A release you can't undo isn't a release. Once it's filled in, try one more loop
**looking only at the runbook** (change one line of code → release steps → rollback steps).
That's how you test a runbook.

## Completion check (Project 6 is done when all of these hold)

- [ ] `systemctl status terakoya-api` shows active (running)
- [ ] It revives after you kill the process / it comes up on its own after you reboot the machine
- [ ] `curl http://localhost/health` goes through via Nginx (and you passed `nginx -t` before applying)
- [ ] `https://localhost/health` goes through with self-signed TLS, and you can state what the warning means in your own words
- [ ] You can follow the app's logs with journalctl / you checked nginx's logrotate config
- [ ] **You did the restore drill** — really deleted it, really brought it back
- [ ] RUNBOOK.md is filled with real commands, and you completed one loop looking only at the runbook
- [ ] No secrets are written directly in the unit file (they come via EnvironmentFile)
- [ ] You filled in `RETROSPECTIVE.md`

Submit with the usual loop (branch → PR → self-merge). There is no auto-grading;
the filled-in RUNBOOK.md and RETROSPECTIVE.md are this project's deliverables.

## If you get stuck (symptom → move)

| Symptom | Move |
|---|---|
| `status` keeps cycling activating / failed | Read `journalctl -u terakoya-api -n 50`. It's usually a wrong ExecStart path (is it absolute? is it the venv's uvicorn?) |
| `203/EXEC` error | The ExecStart command doesn't exist. Check the path by copy-pasting it |
| You fixed the unit but nothing changed | You forgot `sudo systemctl daemon-reload` |
| 502 Bad Gateway from Nginx | The front door is alive but the back (the API) is dead. Go to `systemctl status terakoya-api` |
| `nginx -t` reports an error | Look around the line number it printed. A missing semicolon is the classic |
| WSL2 says there is no systemd | Go to the wsl.conf steps under "Getting a machine" above |
| The Multipass VM got weird | `multipass delete --purge deploy-practice` → start over from launch (it's disposable) |

> **It's safe to break things.** Your counterpart is only the Linux inside your own PC.
> WSL2 and the VM can both be rebuilt at worst. You never touch a real server. No need to tiptoe.
