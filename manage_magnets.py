#!/usr/bin/env python3
import os
import json
import time
import logging
import requests

# Chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
RETRY_COUNTS_PATH = os.path.join(BASE_DIR, 'retry_counts.json')

# Charger configuration
with open(CONFIG_PATH) as f:
    config = json.load(f)

API_KEYS = config['api_keys']
CYCLE_SECONDS = config.get('cycle_seconds', 1800)
MAX_RETRIES = config.get('max_retries', 5)
DISCORD_WEBHOOK_URL = config['discord_webhook_url']
LOG_LEVEL = config.get('log_level', 'INFO').upper()

# Initialiser logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# Charger ou initialiser retry_counts
try:
    with open(RETRY_COUNTS_PATH) as f:
        retry_counts = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    retry_counts = {}

def save_retry_counts():
    with open(RETRY_COUNTS_PATH, 'w') as f:
        json.dump(retry_counts, f, indent=2)

def get_magnets_by_status(api_key, status):
    url = 'https://api.alldebrid.com/v4.1/magnet/status'
    resp = requests.post(
        url,
        headers={'Authorization': f'Bearer {api_key}'},
        data={'status': status}
    )
    resp.raise_for_status()
    data = resp.json()
    items = data.get('data', {}).get('magnets')

    # Normaliser en liste
    if isinstance(items, dict):
        magnets = list(items.values())
    elif isinstance(items, list):
        magnets = items
    else:
        logging.error(
            f"[{api_key[:6]}…] Réponse inattendue pour status '{status}': {data}"
        )
        return []

    # Extraire les IDs
    return [m.get('id') for m in magnets if isinstance(m, dict) and 'id' in m]


def restart_magnet(api_key, magnet_id):
    url = 'https://api.alldebrid.com/v4/magnet/restart'
    resp = requests.post(
        url,
        headers={'Authorization': f'Bearer {api_key}'},
        data={'id': magnet_id}
    )
    resp.raise_for_status()
    return resp.json()

def delete_magnet(api_key, magnet_id):
    url = 'https://api.alldebrid.com/v4/magnet/delete'
    resp = requests.post(
        url,
        headers={'Authorization': f'Bearer {api_key}'},
        data={'id': magnet_id}
    )
    resp.raise_for_status()
    return resp.json()

def send_discord_notification(magnet_id, status, api_key):
    payload = {
        "content": (
            f"[Manage_Magnets_Alldebrid] Torrent supprimé après "
            f"{MAX_RETRIES} échecs: ID {magnet_id}, statut {status}, compte {api_key[:6]}…"
        )
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload).raise_for_status()
    except Exception as e:
        logging.error(f"Échec notification Discord pour ID {magnet_id}: {e}")

if __name__ == '__main__':
    logging.info('Démarrage Manage_Magnets_Alldebrid')
    while True:
        for api_key in API_KEYS:
            for status in ('expired', 'error'):
                try:
                    ids = get_magnets_by_status(api_key, status)
                except Exception as e:
                    logging.error(f"[{api_key[:6]}…] Erreur récupération status '{status}': {e}")
                    continue

                count = len(ids)
                logging.info(f"[{api_key[:6]}…] {count} magnet(s) '{status}' à traiter")

                for mid in ids:
                    entry = retry_counts.setdefault(mid, {'fails': 0, 'last_status': status})
                    try:
                        resp = restart_magnet(api_key, mid)
                        msg = resp.get('data', {}).get('message', 'No message')
                        logging.info(f"[{api_key[:6]}…] Succès ID {mid}: {msg}")
                        entry['fails'] = 0
                    except Exception as e:
                        entry['fails'] += 1
                        entry['last_status'] = status
                        logging.warning(
                            f"[{api_key[:6]}…] Échec ID {mid} "
                            f"({entry['fails']}/{MAX_RETRIES}): {e}"
                        )
                        if entry['fails'] >= MAX_RETRIES:
                            try:
                                delete_magnet(api_key, mid)
                                logging.error(
                                    f"[{api_key[:6]}…] ID {mid} supprimé "
                                    f"après {MAX_RETRIES} échecs"
                                )
                                send_discord_notification(mid, status, api_key)
                            except Exception as del_e:
                                logging.error(
                                    f"[{api_key[:6]}…] Erreur suppression ID {mid}: {del_e}"
                                )
                            retry_counts.pop(mid, None)

                save_retry_counts()

        logging.info(f"Cycle terminé, attente {CYCLE_SECONDS}s avant prochain cycle")
        time.sleep(CYCLE_SECONDS)
