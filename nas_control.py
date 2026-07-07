import json
import socket
import subprocess
import sys
import time
from pathlib import Path

import paramiko

APP_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
CONFIG_PATH = APP_DIR / "config.json"

DEFAULT_CONFIG = {
    "nas_name": "Mon NAS",
    "nas_ip": "192.168.1.100",
    "nas_mac": "00-11-22-33-44-55",
    "ssh_port": 22,
    "ssh_user": "admin",
}


def load_config():
    config = DEFAULT_CONFIG.copy()
    if CONFIG_PATH.exists():
        config.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    return config


def save_config(config):
    CONFIG_PATH.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")


def _broadcast_address(nas_ip):
    parts = nas_ip.split(".")
    if len(parts) == 4:
        parts[3] = "255"
        return ".".join(parts)
    return "255.255.255.255"


def wake(config):
    mac_bytes = bytes.fromhex(config["nas_mac"].replace("-", "").replace(":", ""))
    magic_packet = b"\xff" * 6 + mac_bytes * 16
    broadcast = _broadcast_address(config["nas_ip"])
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        for _ in range(3):
            for target in (broadcast, "255.255.255.255"):
                sock.sendto(magic_packet, (target, 9))
            time.sleep(0.2)


def shutdown(config, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        config["nas_ip"],
        port=int(config["ssh_port"]),
        username=config["ssh_user"],
        password=password,
        timeout=10,
    )

    try:
        stdin, stdout, stderr = client.exec_command("sudo -S -p '' shutdown -h now")
        stdin.write(password + "\n")
        stdin.flush()
        try:
            exit_status = stdout.channel.recv_exit_status()
        except (EOFError, OSError):
            # La connexion a été coupée pendant l'extinction : comportement normal.
            return
        if exit_status not in (0, -1):
            err = stderr.read().decode(errors="ignore")
            raise RuntimeError(err or f"code de sortie {exit_status}")
    except (paramiko.SSHException, EOFError, OSError):
        # Le NAS a coupé la connexion en cours d'extinction : comportement normal.
        pass
    finally:
        client.close()


def is_online(config, timeout=1.5):
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", str(int(timeout * 1000)), config["nas_ip"]],
            capture_output=True,
            timeout=timeout + 1,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return result.returncode == 0
    except Exception:
        return False
