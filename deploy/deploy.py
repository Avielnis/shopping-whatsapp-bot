"""One-click deploy: runs the local tests, syncs source files to the
Raspberry Pi, and restarts the bot service there. Never touches the Pi's
data/ or .env - those hold the live WhatsApp session and shopping list.

Usage: double-click deploy.bat, or `python deploy/deploy.py` from a venv
that has requirements-dev.txt installed. Reads connection details from
deploy/deploy.env (copy deploy/deploy.env.example and fill it in first).
"""

import os
import subprocess
import sys
import tempfile
import time

import paramiko
from dotenv import dotenv_values

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deploy.env")

SYNC_FILES = [
    "main.py",
    "config.py",
    "requirements.txt",
    "README.md",
    ".env.example",
    ".gitignore",
    "deploy/shopping-bot.service",
]
SYNC_DIRS = ["core", "frontends", "tests"]

# Idempotent: safe to run on every deploy, only acts when something is missing.
ROOT_SETUP_SCRIPT = """set -e
if ! command -v cloudflared >/dev/null 2>&1; then
  mkdir -p --mode=0755 /usr/share/keyrings
  curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg -o /usr/share/keyrings/cloudflare-main.gpg
  echo 'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main' > /etc/apt/sources.list.d/cloudflared.list
  apt-get update -qq
  apt-get install -y cloudflared
fi
if [ ! -f /etc/sudoers.d/shopping-bot-reboot ]; then
  echo "{pi_user} ALL=NOPASSWD: /sbin/reboot" > /etc/sudoers.d/shopping-bot-reboot
  chmod 440 /etc/sudoers.d/shopping-bot-reboot
fi
cp {remote_path}/deploy/shopping-bot.service /etc/systemd/system/shopping-bot.service
systemctl daemon-reload
systemctl enable shopping-bot
"""


def collect_local_files():
    files = list(SYNC_FILES)
    for d in SYNC_DIRS:
        for name in sorted(os.listdir(os.path.join(PROJECT_ROOT, d))):
            if name.endswith(".py"):
                files.append(f"{d}/{name}")
    return files


def run_local_tests():
    print("Running local tests before deploying...")
    result = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=PROJECT_ROOT)
    if result.returncode != 0:
        print("\nTests failed - deploy aborted. Fix the tests and try again.")
        sys.exit(1)
    print("Tests passed.\n")


def run_remote(client, cmd, pty=False):
    _, stdout, stderr = client.exec_command(cmd, get_pty=pty, timeout=180)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    return exit_status, out, err


def main():
    if not os.path.exists(ENV_PATH):
        print(f"Missing {ENV_PATH}.")
        print("Copy deploy/deploy.env.example to deploy/deploy.env and fill in your Pi's details.")
        sys.exit(1)

    cfg = dotenv_values(ENV_PATH)
    host, user, password = cfg["PI_HOST"], cfg["PI_USER"], cfg["PI_PASSWORD"]
    remote_path = cfg["PI_PATH"]

    run_local_tests()

    print(f"Connecting to {user}@{host}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password, timeout=15)

    files = collect_local_files()
    print(f"Uploading {len(files)} source files (data/ and .env are never touched)...")
    sftp = client.open_sftp()
    for rel in files:
        sftp.put(os.path.join(PROJECT_ROOT, rel), f"{remote_path}/{rel}")
    sftp.close()

    print("Installing/updating Python dependencies on the Pi...")
    status, out, err = run_remote(
        client, f"cd {remote_path} && venv/bin/python -m pip install -q -r requirements.txt"
    )
    if status != 0:
        print("  pip install failed:")
        print(" ", err.strip() or out.strip())

    print("Ensuring one-time setup (cloudflared, sudoers, systemd unit)...")
    setup_script = ROOT_SETUP_SCRIPT.format(pi_user=user, remote_path=remote_path)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False, newline="\n") as f:
        f.write(setup_script)
        local_script_path = f.name
    remote_script = "/tmp/_deploy_root_setup.sh"
    sftp = client.open_sftp()
    sftp.put(local_script_path, remote_script)
    sftp.close()
    os.remove(local_script_path)
    status, out, err = run_remote(client, f"echo '{password}' | sudo -S bash {remote_script}", pty=True)
    run_remote(client, f"rm -f {remote_script}")
    if status != 0:
        print("  Setup script reported an error:")
        print(" ", err.strip() or out.strip())

    print("Restarting the bot service...")
    run_remote(client, f"echo '{password}' | sudo -S systemctl restart shopping-bot", pty=True)

    time.sleep(5)
    _, status_out, _ = run_remote(client, "systemctl is-active shopping-bot")
    status_out = status_out.strip()
    print(f"Service status: {status_out}")

    client.close()

    if status_out == "active":
        print("\nDeployed successfully.")
        print(f"  Admin page: http://{host}:8080")
        print(f"  List page:  http://{host}:8081")
    else:
        print("\nService did not report 'active' - check with:")
        print(f"  ssh {user}@{host} 'journalctl -u shopping-bot -n 50 --no-pager'")
        sys.exit(1)


if __name__ == "__main__":
    main()
