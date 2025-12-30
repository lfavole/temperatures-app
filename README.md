# Températures

Projet Django minimal pour saisir la température chaque lundi (interface en français), créer des graphiques via Chart.js et envoyer des notifications push si la température du jour n'a pas été soumise.

## Installation rapide

1. Créez un environnement virtuel et installez les dépendances:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Migrer la base de données:

```bash
python manage.py migrate
```

3. Générer ou fournir des clefs VAPID et renseigner les variables d'environnement :

Méthode A — (recommandée) avec l'outil Node `web-push` :

```bash
# installer l'outil si nécessaire
npm install -g web-push

# générer les clés (JSON sortie)
web-push generate-vapid-keys --json > vapid.json

# exemple de sortie (vapid.json)
# {
#   "publicKey": "BP...",
#   "privateKey": "hG..."
# }

# exporter dans l'environnement
export VAPID_PUBLIC="$(jq -r .publicKey vapid.json)"
export VAPID_PRIVATE="$(jq -r .privateKey vapid.json)"
export VAPID_SUBJECT="mailto:you@example.com"
```

Méthode B — script Python (sans dépendance CLI) :

```bash
python - <<'PY'
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

key = ec.generate_private_key(ec.SECP256R1())
priv = key.private_numbers().private_value.to_bytes(32, 'big')
pub = key.public_key().public_numbers()
# Encodage base64 URL-safe requis par Push (utiliser une librairie pour formater proprement)
print('--- private (raw bytes) ---', priv.hex())
print('--- public numbers ---', pub.x, pub.y)
PY
```

Remarque : la méthode Python ci‑dessus est un exemple minimaliste ; utilisez de préférence `web-push` ou une librairie qui produit la clé publique au format Base64 URL-safe attendu par le navigateur.

Après génération, exportez les variables d'environnement `VAPID_PUBLIC`, `VAPID_PRIVATE` et `VAPID_SUBJECT` comme montré ci‑dessus.

4. Lancer le serveur:

```bash
python manage.py runserver
```

## Utilisation GitHub Actions

Le workflow `/.github/workflows/ping.yml` appelle toutes les heures l'URL définie dans le secret `PING_URL`. Configurez ce secret pour pointer vers votre instance déployée (par ex. `https://monserveur.example.com`). L'endpoint `/ping` vérifiera si la température d'aujourd'hui a été soumise et, si non, enverra une notification push aux abonnés enregistrés.

Pour ajouter le secret `PING_URL` dans GitHub :

1. Allez dans les `Settings` du dépôt → `Secrets and variables` → `Actions` → `New repository secret`.
2. Nom : `PING_URL` ; Valeur : l'URL publique de votre application (sans slash final), ex. `https://monserveur.example.com`.
