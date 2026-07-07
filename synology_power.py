#!/usr/bin/env python3
import argparse
import getpass
import sys

import paramiko

import nas_control

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Allume/éteint le NAS Synology à distance.")
    parser.add_argument("action", choices=["on", "off"], help="on = Wake-on-LAN, off = extinction via SSH")
    args = parser.parse_args()

    config = nas_control.load_config()

    if args.action == "on":
        nas_control.wake(config)
        print(f"Paquet magique envoyé à {config['nas_mac']}.")
        return

    password = getpass.getpass(f"Mot de passe SSH pour {config['ssh_user']}@{config['nas_ip']}: ")
    try:
        nas_control.shutdown(config, password)
    except paramiko.AuthenticationException:
        print("Échec d'authentification SSH.", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Erreur lors de l'extinction : {exc}", file=sys.stderr)
        sys.exit(1)
    print("Commande d'extinction envoyée avec succès.")


if __name__ == "__main__":
    main()
