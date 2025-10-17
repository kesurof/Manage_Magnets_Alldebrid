# Manage_Magnets_Alldebrid

**Automatisation de la surveillance, relance et suppression des torrents AllDebrid en statut "expired" ou "error".**

## Présentation

Manage_Magnets_Alldebrid est un script Python conçu pour automatiser la gestion des torrents problématiques sur AllDebrid. Il surveille en continu vos magnets et intervient automatiquement lorsque des problèmes surviennent.

### Fonctionnalités

- **Surveillance périodique** : interroge l'API AllDebrid pour détecter les magnets en statut `expired` ou `error`
- **Compteur d'échecs intelligent** : chaque apparition d'un torrent en erreur incrémente un compteur persistant
- **Relance automatique** : tente de redémarrer automatiquement les torrents détectés en erreur
- **Suppression conditionnelle** : supprime définitivement les torrents après un nombre configurable d'échecs consécutifs
- **Notifications Discord** : envoie un webhook Discord lors de chaque suppression avec les détails du torrent
- **Multi-comptes** : gère plusieurs clés API AllDebrid simultanément
- **Persistance JSON** : historise l'état des torrents dans un fichier local pour survivre aux redémarrages

## Avantages

- **Simplicité** : configuration centralisée dans un seul fichier JSON, aucune base de données requise
- **Robustesse** : gestion des formats de réponse API variés (dict/list), logs détaillés via journald
- **Fiabilité** : service systemd avec redémarrage automatique en cas de crash
- **Notifications temps réel** : alertes Discord immédiates pour éviter l'accumulation de torrents irrécupérables
- **Maintenance aisée** : paramètres ajustables sans modification du code, supervision via `systemctl` et `journalctl`
- **ARM64 compatible** : testé sur Ubuntu ARM64

## Prérequis

- **Système** : Ubuntu/Debian (ARM64 ou x86_64)
- **Python** : version 3.8 ou supérieure
- **Dépendances** : `requests` (installé via pip)
- **Permissions** : accès root/sudo pour créer le service systemd
- **AllDebrid** : une ou plusieurs clés API valides
- **Discord** : URL de webhook (optionnel mais recommandé)

## Installation

### 1. Cloner le dépôt

```
git clone https://github.com/kesurof/Manage_Magnets_Alldebrid.git
cd Manage_Magnets_Alldebrid
```

### 2. Créer l'environnement virtuel

```
python3 -m venv venv
source venv/bin/activate
pip install requests
```

### 3. Configurer le fichier `config.json`

Créez le fichier de configuration avec vos paramètres :

```
{
  "api_keys": [
    "VOTRE_CLE_API_1",
    "VOTRE_CLE_API_2"
  ],
  "cycle_seconds": 1800,
  "max_retries": 5,
  "discord_webhook_url": "https://discord.com/api/webhooks/VOTRE_WEBHOOK",
  "log_level": "INFO"
}
```

**Paramètres** :
- `api_keys` : liste des clés API AllDebrid à surveiller
- `cycle_seconds` : intervalle en secondes entre chaque cycle de vérification (1800 = 30 minutes)
- `max_retries` : nombre d'apparitions en erreur avant suppression définitive
- `discord_webhook_url` : URL du webhook Discord pour les notifications
- `log_level` : niveau de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

### 4. Tester manuellement

Rendre le script exécutable et le lancer :

```
chmod +x manage_magnets.py
./manage_magnets.py
```

Vérifier que le script détecte correctement les torrents et que `retry_counts.json` est créé automatiquement.

### 5. Installer le service systemd

Créer le fichier de service (adapter les chemins si nécessaire) :

```
sudo tee /etc/systemd/system/manage-magnets.service > /dev/null << 'EOF'
[Unit]
Description=Manage_Magnets_Alldebrid Python Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=VOTRE_USER
WorkingDirectory=/chemin/vers/Manage_Magnets_Alldebrid
ExecStart=/chemin/vers/venv/bin/python3 /chemin/vers/manage_magnets.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

Remplacer `VOTRE_USER` et les chemins par vos valeurs réelles.

Activer et démarrer le service :

```
sudo systemctl daemon-reload
sudo systemctl enable --now manage-magnets.service
```

### 6. Vérifier le fonctionnement

```
sudo systemctl status manage-magnets.service
sudo journalctl -u manage-magnets.service -f
```

## Fonctionnement

### Logique de comptage

Le script fonctionne selon le principe suivant :

1. **Détection** : à chaque cycle, le script interroge l'API pour les statuts `expired` et `error`
2. **Comptage** : chaque fois qu'un torrent apparaît dans ces statuts, son compteur d'échecs s'incrémente
3. **Relance** : si le compteur est inférieur à `max_retries`, le script tente de redémarrer le torrent
4. **Suppression** : si le compteur atteint `max_retries`, le torrent est supprimé et une notification Discord est envoyée
5. **Persistance** : le compteur est sauvegardé dans `retry_counts.json` et survit aux redémarrages

**Important** : même si la relance technique réussit (l'API retourne un succès), si le torrent réapparaît en erreur au cycle suivant, cela compte comme un nouvel échec.

### Structure du fichier `retry_counts.json`

```
{
  "403207307": {
    "fails": 3,
    "last_status": "error"
  },
  "402623513": {
    "fails": 1,
    "last_status": "expired"
  }
}
```

## Maintenance

### Consulter les logs

Logs en temps réel :
```
sudo journalctl -u manage-magnets.service -f
```

Logs des dernières 24h :
```
sudo journalctl -u manage-magnets.service --since "24 hours ago"
```

### Redémarrer le service

```
sudo systemctl restart manage-magnets.service
```

### Arrêter le service

```
sudo systemctl stop manage-magnets.service
```

### Mettre à jour

1. Arrêter le service
2. Tirer les dernières modifications du dépôt
3. Redémarrer le service

```
sudo systemctl stop manage-magnets.service
git pull origin main
sudo systemctl start manage-magnets.service
```

### Modifier les paramètres

Éditer `config.json` puis redémarrer le service :

```
nano config.json
sudo systemctl restart manage-magnets.service
```

### Réinitialiser l'historique

Pour purger tous les compteurs d'échecs :

```
echo "{}" > retry_counts.json
sudo systemctl restart manage-magnets.service
```

### Tester le webhook Discord

```
curl -H "Content-Type: application/json" \
     -d '{"content":"[Manage_Magnets_Alldebrid] Test de notification Discord"}' \
     "VOTRE_WEBHOOK_URL"
```

## Dépannage

### Le service ne démarre pas

Vérifier les logs d'erreur :
```
sudo journalctl -u manage-magnets.service -n 50
```

Vérifier les permissions :
```
ls -la manage_magnets.py config.json
```

### Les torrents ne sont pas détectés

Vérifier la validité des clés API en testant manuellement :
```
curl -X POST "https://api.alldebrid.com/v4.1/magnet/status" \
     -H "Authorization: Bearer VOTRE_CLE_API" \
     -d "status=error"
```

### Le webhook Discord ne fonctionne pas

Vérifier l'URL et tester avec curl (voir section Maintenance)

### Le compteur ne s'incrémente pas

Vérifier que `retry_counts.json` est bien écrit après chaque cycle :
```
watch -n 5 cat retry_counts.json
```

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## Licence

MIT License - voir le fichier LICENSE pour plus de détails.

## Auteur

Développé pour automatiser la gestion des torrents AllDebrid dans l'écosystème DECYPHARR.

---

*Manage_Magnets_Alldebrid simplifie la gestion des torrents AllDebrid et prévient l'accumulation d'échecs redondants en automatisant la surveillance, la relance et la suppression intelligente.*
```

Ce README est complet, structuré et couvre tous les aspects du projet : présentation, installation détaillée, fonctionnement, maintenance et dépannage.