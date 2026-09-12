# alphapay-python

SDK Python officiel pour l'API AlphaPay (agrégateur de paiement multi-gateway).

> **Statut : v0.1.0, non publié.** Couvre les ressources marchand
> principales (paiements, retraits, liens de paiement, checkout, clients,
> webhooks). Conçu en miroir des SDK [Node.js](../AlphaPaySDK-node) et
> [PHP](../AlphaPaySDK-php) — mêmes garanties, mêmes restrictions d'API
> découvertes en conditions réelles. Voir [CHECKLIST.md](./CHECKLIST.md)
> pour ce qui manque avant une publication PyPI.

Aucune dépendance runtime — uniquement la bibliothèque standard (`urllib`),
pas de `requests`. Python 3.8+.

## Installation

```bash
pip install alphapay
```

## Démarrage rapide

```python
import os
from alphapay import AlphaPayClient

alphapay = AlphaPayClient(os.environ["ALPHAPAY_SECRET_KEY"])  # sk_live_... ou sk_test_...

# Encaissement direct (push mobile money), sans page de checkout à suivre.
payment = alphapay.transactions.payin_initialize(
    amount=5000,
    currency="XOF",
    country="BJ",
    network="mtn_bj",
    customer={"email": "ayaba@exemple.com", "first_name": "Ayaba", "last_name": "Client", "phone": "+22900000000"},
    description="Commande #1234",
    idempotency_key=True,  # recommandé : évite un double push en cas de retry réseau
)

print(payment["status"])
```

### Options avancées des liens de paiement

`payment_links.create()`/`update()` acceptent aussi `require_phone`,
`facebook_pixel_id`, `google_ads_id`, `custom_fields`,
`show_confirmation_page` et `redirect_url`. `get_public()`/
`create_public_checkout()` sont les 2 seules méthodes de cette ressource qui
n'exigent PAS de clé secrète (page publique du lien) — ne les appelez jamais
depuis un front avec votre clé API en dur, seul `slug` doit y circuler.

```python
link = alphapay.payment_links.create(
    name="Facture #42",
    amount_type="FIXED",
    amount=5000,
    currency="XOF",
    google_ads_id="AW-123456789",
    custom_fields=[{"key": "reference_client", "label": "Référence client", "required": True}],
)

# Côté public (mobile/web), sans clé API :
public_link = alphapay.payment_links.get_public(link["slug"])
checkout = alphapay.payment_links.create_public_checkout(
    link["slug"],
    customer={"email": "client@exemple.com", "first_name": "Client", "last_name": "Test"},
    custom_field_values={"reference_client": "CMD-42"},
)
# checkout["slug"] est une CheckoutSession one-shot : pilotez la suite (réseau, push,
# statut) avec le SDK checkout public (mobile/web), jamais avec ce client à clé secrète.
```

## Sandbox vs live

L'environnement se déduit automatiquement du préfixe de la clé :

```python
sandbox = AlphaPayClient("sk_test_...")  # sandbox.environment == "sandbox"
live = AlphaPayClient("sk_live_...")     # live.environment == "live"
```

## Gestion des erreurs

Toute erreur API est normalisée en une sous-classe de `AlphaPayError` —
jamais un code HTTP brut à interpréter soi-même :

```python
from alphapay import AlphaPayValidationError, AlphaPayRateLimitError

try:
    alphapay.settlements.create(country="BJ", requested_amount=100, payout_method=method_id)
except AlphaPayValidationError as e:
    print(e.field_errors)  # {"requested_amount": ["Montant minimum : 500 XOF."]}
except AlphaPayRateLimitError as e:
    print(f"Réessayer dans {e.retry_after}s")
```

`AlphaPayAuthenticationError`, `AlphaPayPermissionError`,
`AlphaPayNotFoundError`, `AlphaPayIdempotencyError` (409 — clé
Idempotency-Key réutilisée avec un payload différent), `AlphaPayServerError`
et `AlphaPayConnectionError` (réseau/timeout, jamais atteint l'API)
couvrent le reste. Le client retente automatiquement (backoff exponentiel +
gigue) sur 429/5xx/erreur réseau — 2 tentatives supplémentaires par défaut,
configurable via `max_retries=` au constructeur.

## Pagination

`alphapay.paginate()` suit le lien `next` renvoyé par l'API (pas un numéro
de page recalculé côté SDK) — fonctionne aussi bien sur les ressources
paginées par page (`count` présent) que sur `transactions.list()`, paginée
par curseur (`TransactionListView` utilise `CreatedAtCursorPagination` côté
API, sans `count` ; y passer `page` n'a aucun effet) :

```python
from alphapay import paginate

for tx in paginate(alphapay.http, alphapay.transactions.list(status="SUCCESS")):
    print(tx["reference"], tx["amounts"]["net"])
```

## Vérifier un webhook reçu

Reproduit exactement le schéma de signature d'AlphaPayBack (HMAC-SHA256 de
`"<timestamp>.<corps>"`, comparaison en temps constant via
`hmac.compare_digest`, fenêtre anti-rejeu de 300s) :

```python
from alphapay import verify_signature, AlphaPayWebhookSignatureError

# Exemple Flask -- adapter selon le framework.
@app.route("/webhooks/alphapay", methods=["POST"])
def alphapay_webhook():
    try:
        event = verify_signature(
            payload=request.get_data(as_text=True),  # corps BRUT, jamais déjà décodé en JSON
            signature=request.headers["X-Webhook-Signature"],
            timestamp=request.headers["X-Webhook-Timestamp"],
            secret=os.environ["ALPHAPAY_WEBHOOK_SECRET"],
        )
    except AlphaPayWebhookSignatureError:
        return "", 400
    # traiter event["event"] / event["data"]
    return "", 200
```

## ⚠️ Sécurité — ce SDK est côté serveur uniquement

La clé API (`sk_live_.../sk_test_...`) donne un accès complet au compte
marchand (créer des paiements, déclencher des retraits, lire l'historique).
**Ne l'embarquez jamais dans du code exécuté côté client** (un notebook
partagé, un script de démo, une app desktop distribuée). Gardez-la dans une
variable d'environnement ou un secret manager, jamais en clair dans un
dépôt versionné.

## Ressources couvertes

| Ressource | Méthodes | Via clé API |
|---|---|---|
| `transactions` | `list`, `get`, `export`, `download_invoice`, `payin_initialize/payin_verify/payin_retry/payin_confirm_otp`, `payout_initialize/payout_verify` | ✅ |
| `payment_links` | `list`, `create`, `get`, `update`, `delete` | ✅ |
| `payment_links` | `get_public`, `create_public_checkout` | publiques (pas de clé requise) |
| `checkout_sessions` | `list`, `create`, `get`, `cancel` | ✅ |
| `customers` | `list`, `create`, `get`, `update`, `delete`, `transactions` | ✅ |
| `settlements` | `list`, `create`, `get`, `cancel` | ❌ dashboard-only |
| `wallet_transfers` | `list`, `create`, `get` | ❌ dashboard-only |
| `balances` | `list`, `get` | ✅ |
| `balances` | `ledger_entries` | ❌ dashboard-only |
| `api_keys` | `list`, `create`, `get`, `revoke`, `delete` | ❌ dashboard-only |
| `api_keys` | `ip_whitelist.{list,create,update,delete}` | ✅ |
| `webhook_endpoints` | `list`, `get`, `subscriptions.list`, `logs.{list,get}` | ✅ |
| `webhook_endpoints` | `create`, `update`, `rotate_secret`, `delete`, `subscriptions.{subscribe,unsubscribe}`, `logs.resend` | ❌ dashboard-only |

### La colonne "Via clé API"

Vérifié en conditions réelles (`api.alphapay.me`, appels en lecture, via le
SDK Node.js jumeau — même API, même restriction) : une partie de l'API est
**volontairement inaccessible à une clé API**, même en lecture — jamais un
bug, toujours `apps.core.mixins.forbid_api_key` côté AlphaPayBack :

```python
from alphapay import AlphaPayPermissionError

try:
    alphapay.settlements.list()
except AlphaPayPermissionError as e:
    if e.error_code == "dashboard_only":
        pass  # "La demande de retrait n'est possible que depuis le dashboard (compte utilisateur) — jamais via une clé API."
```

Logique : les retraits, l'historique détaillé du grand livre et la gestion
des clés API elles-mêmes exigent qu'un humain soit connecté au dashboard —
une clé compromise ne peut ni sortir d'argent, ni fabriquer d'autres clés
pour elle-même, ni consulter le détail comptable.

Pas encore couvert (endpoints existants côté API, absents du SDK pour l'instant) :
gestion d'équipe, KYC marchand, configs marchand, journal d'audit,
référentiels (pays/réseaux/taux de change), support.

## Développement

```bash
python -m unittest discover -s tests -v   # lance un vrai serveur HTTP local (tests/server.py, thread), aucun appel réseau réel vers AlphaPay
python -m py_compile src/alphapay/*.py src/alphapay/resources/*.py  # équivalent d'un lint syntaxique
```

## Licence

MIT
