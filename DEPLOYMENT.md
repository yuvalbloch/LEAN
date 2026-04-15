# LEAN — Deployment Guide (Vultr / Ubuntu 24.04)

This guide deploys the LEAN digest pipeline on an existing Ubuntu 24.04 server.
It assumes you are logged in as **root** and that another service (e.g. a Tor web tunnel)
is already running — the steps below are fully isolated and will not touch it.

---

## 1. Install system dependencies

```bash
apt update
apt install -y git python3-venv
```

> Python 3.12 is already included in Ubuntu 24.04. `python3-venv` adds the
> virtual-environment module needed in the next step.

---

## 2. Clone the repository

```bash
cd /root
git clone https://github.com/yuvalbloch/LEAN.git
cd LEAN
```

> **If the repo is still private** when you run this, you will be prompted for
> credentials. Use a GitHub Personal Access Token (PAT) as the password:
> Settings → Developer settings → Personal access tokens → Fine-grained →
> grant read access to the LEAN repo. Once the repo is public, plain HTTPS
> clone works with no credentials.

---

## 3. Create a virtual environment and install dependencies

Ubuntu 24.04 blocks global `pip install` (PEP 668). A virtual environment keeps
LEAN's packages isolated from both the system Python and any other project on
the server.

```bash
python3 -m venv /root/LEAN/venv
/root/LEAN/venv/bin/pip install -r /root/LEAN/requirements.txt
```

---

## 4. Set secrets via a `.env` file

Create the file:

```bash
nano /root/LEAN/.env
```

Paste and fill in your values:

```
ANTHROPIC_API_KEY=sk-ant-...
SMTP_USER=your_gmail@gmail.com
SMTP_PASSWORD=your_gmail_app_password
```

> `SMTP_PASSWORD` must be a **Gmail App Password**, not your account password.
> Generate one at: Google Account → Security → 2-Step Verification → App passwords.

Lock the file so only root can read it:

```bash
chmod 600 /root/LEAN/.env
```

`config.py` loads this file automatically on every run — no shell exports needed.

---

## 5. Test the pipeline manually

```bash
cd /root/LEAN
/root/LEAN/venv/bin/python digest.py
```

You should see output like:

```
Fetching articles...
  42 raw articles fetched
Filtering (AI)...
  18 articles after AI filter
Summarising with Claude...
Running critic review...
Sending email...
Done.
```

Check your inbox before proceeding to cron setup.

---

## 6. Schedule the daily cron job

```bash
crontab -e
```

Add this line at the bottom (runs at 06:45 every morning, server local time):

```
45 6 * * * cd /root/LEAN && /root/LEAN/venv/bin/python digest.py >> /tmp/digest.log 2>&1
```

> The cron job calls the **venv's Python directly** — it never touches the system
> Python or any other project's environment.

Verify the entry was saved:

```bash
crontab -l
```

---

## 7. Check the logs

After the first scheduled run:

```bash
cat /tmp/digest.log
```

To watch a run in real time (if you trigger it manually):

```bash
tail -f /tmp/digest.log
```

The log file grows indefinitely. To rotate it weekly, add a second cron entry:

```
0 0 * * 0 truncate -s 0 /tmp/digest.log
```

---

## 8. Keeping the code up to date

When you push changes to GitHub:

```bash
cd /root/LEAN
git pull
/root/LEAN/venv/bin/pip install -r requirements.txt   # only needed if requirements changed
```

---

## 9. Isolation from other services

LEAN is a **run-and-exit script** — it opens no ports and listens on nothing.
It makes only outbound connections (RSS feeds over HTTPS, Anthropic API over
HTTPS, Gmail SMTP on port 587). It will not interact with, slow down, or
interfere with any other service running on the server.

The virtual environment at `/root/LEAN/venv/` is completely self-contained.
`apt`, system Python, and other projects are untouched.

---

## Optional: Claude Code on the server

If you want AI assistance directly on the server for debugging, you can install
Claude Code as a CLI. It uses the same `ANTHROPIC_API_KEY` you already have.

```bash
# Install Node.js 20 (LTS)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Install Claude Code
npm install -g @anthropic-ai/claude-code
```

Make the API key available to your shell sessions (Claude Code reads from the
environment, not from the `.env` file):

```bash
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.bashrc
source ~/.bashrc
```

Then use it from inside the project:

```bash
cd /root/LEAN
claude
```

This is safe — Claude Code is an interactive CLI process, opens no ports, and
will not affect any other service on the server.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `RuntimeError: Missing required configuration` | `.env` file missing or a key is blank | Check `/root/LEAN/.env` — all three keys must have values |
| `ModuleNotFoundError: No module named 'feedparser'` | Wrong Python called — not the venv | Make sure cron / your command uses `/root/LEAN/venv/bin/python` |
| `SMTPAuthenticationError` | Wrong Gmail App Password | Regenerate the App Password; check 2FA is enabled on the account |
| `No articles fetched` | RSS feeds unreachable | Run `curl -I https://www.timesofisrael.com/feed/` to test connectivity |
| Cron runs but no email and no log | Cron entry has a typo | Run `crontab -l` and verify the path; check `/var/log/syslog` for cron errors |
| `git pull` asks for credentials | Repo still private | Make the repo public on GitHub, or update the remote URL to include a PAT |
