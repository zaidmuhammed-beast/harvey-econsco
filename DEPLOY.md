# Deploying Harvey (ECONSCO) on a Hostinger VPS

Runs Harvey's loop and dashboard 24/7 in Docker, independent of any PC.
Needs a **Hostinger KVM VPS** with Ubuntu (not shared/web hosting).

## What is NOT in this repository (copy these yourself)

These hold passwords, API keys or prospect data, so they are gitignored and
must never be committed:

| File | What it is |
|---|---|
| `.env` | SMTP/IMAP login, Hunter/Reoon keys, LinkedIn login |
| `harvey.local.yaml` | Your settings: persona, ICP, send limits, send windows |
| `skills/product_knowledge.md`, `skills/competitive_intel.md` | What Harvey learned from econsco.com |
| `data/harvey.db` | Contacts, sent history, conversations (keep it, or Harvey re-emails people) |

## 1. Prepare the VPS (once)

SSH in (hPanel → VPS → SSH access), then:

```bash
curl -fsSL https://get.docker.com | sh
git clone https://github.com/zaidmuhammed-beast/harvey-econsco.git /opt/harvey
cd /opt/harvey
mkdir -p data ~/.claude
chown -R 1000:1000 data ~/.claude
```

## 2. Copy your private files from the Windows PC

**Stop Harvey on the PC first** (close the "Harvey" window) so the database
copy is complete. From PowerShell on the PC, in `D:\Harvey\harvey`:

```powershell
scp .env harvey.local.yaml root@YOUR_VPS_IP:/opt/harvey/
scp skills/product_knowledge.md skills/competitive_intel.md root@YOUR_VPS_IP:/opt/harvey/skills/
scp data/harvey.db root@YOUR_VPS_IP:/opt/harvey/data/
```

Then on the VPS: `chown -R 1000:1000 /opt/harvey/data`

**Set the dashboard password.** On the VPS, edit `/opt/harvey/.env` and set
`DASHBOARD_PASSWORD=` to a long password (4+ unrelated words). The dashboard
refuses to start on the server without it.

## 3. Sign in to Claude on the server (once)

```bash
cd /opt/harvey
docker compose build
docker compose run --rm harvey claude
```

Type `/login`, choose your **Claude subscription** account, open the link it
prints on your PC, paste the code back, then `/exit`. The login is saved in
`~/.claude` on the VPS and reused by Harvey.

## 4. Start it

```bash
docker compose up -d
docker compose logs -f harvey      # watch it work (Ctrl+C stops watching, not Harvey)
```

Both services restart automatically after a crash or a VPS reboot.

## 5. Open the dashboard (SSH tunnel)

The dashboard can send email, so it has a login page **and** is not exposed to
the internet. From the PC:

```powershell
ssh -L 5555:127.0.0.1:5555 root@YOUR_VPS_IP
```

Keep that window open and browse to http://localhost:5555, then sign in with
your `DASHBOARD_PASSWORD`. Five wrong attempts lock sign-in for 15 minutes.

## 6. Turn off the PC copy

Only one Harvey may run, or prospects get emailed twice. On the PC press
Win+R → `shell:startup` and delete the **Harvey** shortcut.

## Updating

Push changes to GitHub, then on the VPS:

```bash
cd /opt/harvey && git pull && docker compose up -d --build
```

Edits to `harvey.local.yaml` or `prompts/` only need `docker compose restart`.
