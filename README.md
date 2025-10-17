# Manage_Magnets_Alldebrid

**Automatisation de la relance, suppression et notification des torrents AllDebrid en statut “expired” ou “error”.**

## Présentation

Manage_Magnets_Alldebrid est un script Python simple et léger qui :

- Interroge périodiquement l’API AllDebrid pour détecter les magnets en statut **expired** ou **error**.  
- Relance automatiquement chaque torrent.  
- Historise localement le nombre de tentatives dans un fichier JSON.  
- Supprime les torrents après un nombre configurable de tentatives infructueuses.  
- Envoie une notification via webhook Discord lors de chaque suppression.

## Avantages

-  
  *Simplicité* : totalement en Python, avec un unique fichier JSON pour la persistance.  
-  
  *Robustesse* : gestion des formats de réponse variés, logs détaillés, redémarrage du service en cas de crash.  
-  
  *Notifications* : alerte Discord immédiate pour éviter d’accumuler des torrents injoignables.  
-  
  *Maintenance aisée* : paramètres centralisés dans `config.json`, service systemd pour supervision automatique.

## Installation

1. **Cloner le dépôt**  
   ```bash
   git clone <URL_GITHUB> Manage_Magnets_Alldebrid
   cd Manage_Magnets_Alldebrid
   ```

2. **Créer et activer le virtualenv**  
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install requests
   ```

3. **Configurer**  
   - Copier et adapter `config.json` :
     ```json
     {
       "api_keys": ["CLE_API1", "CLE_API2"],
       "cycle_seconds": 1800,
       "max_retries": 5,
       "discord_webhook_url": "https://discord.com/api/webhooks/…",
       "log_level": "INFO",
       "retry_counts_path": "./retry_counts.json"
     }
     ```
   - Initialiser le suivi des échecs :
     ```bash
     echo "{}" > retry_counts.json
     ```

4. **Rendre le script exécutable**  
   ```bash
   chmod +x manage_magnets.py
   ```

5. **Tester manuellement**  
   ```bash
   ./manage_magnets.py
   ```

6. **Installer le service systemd**  
   ```bash
   sudo tee /etc/systemd/system/manage-magnets.service > /dev/null << 'EOF'
   [Unit]
   Description=Manage_Magnets_Alldebrid Python Service
   After=network-online.target
   Wants=network-online.target

   [Service]
   Type=simple
   User=${USER}
   WorkingDirectory=$(pwd)
   ExecStart=$(pwd)/venv/bin/python3 $(pwd)/manage_magnets.py
   Restart=always
   RestartSec=30
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=multi-user.target
   EOF

   sudo systemctl daemon-reload
   sudo systemctl enable --now manage-magnets.service
   ```

## Maintenance

- **Logs & statut**  
  ```bash
  sudo journalctl -u manage-magnets.service -f
  sudo systemctl status manage-magnets.service
  ```

- **Mettre à jour**  
  1. Tirer les dernières modifications du dépôt.  
  2. Redémarrer le service :
     ```bash
     sudo systemctl restart manage-magnets.service
     ```

- **Paramètres**  
  - Modifier `config.json` pour ajuster `cycle_seconds`, `max_retries` ou `discord_webhook_url`.  
  - Réinitialiser `retry_counts.json` pour purger l’historique.

***

*Manage_Magnets_Alldebrid simplifie la gestion des torrents AllDebrid et prévient l’accumulation d’échecs redondants.*
