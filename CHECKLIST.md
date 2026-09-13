# Avant publication PyPI

Ce SDK est fonctionnel et testé (`python -m unittest discover -s tests` :
11/11 tests, contre un vrai serveur HTTP local — pas un mock, cf.
`tests/server.py`, lancé dans un thread du process de test).
`list()`/`get()` des 9 ressources ont aussi été vérifiés en lecture seule
contre une vraie clé LIVE sur `api.alphapay.me` — mêmes résultats que les
SDK Node.js et PHP jumeaux (mêmes formes de réponse, mêmes 403
`dashboard_only`, `transactions.list()` bien sans `count`). Le parsing
`urllib` (headers, `HTTPError`) fonctionne donc correctement en conditions
réelles, pas seulement contre le serveur de test local (thread, sans
latence réseau réelle). À faire avant `pip publish`/`twine upload` :

## Bloquant

- [x] **Tester contre une vraie clé live**, en lecture seule uniquement, sur
      `api.alphapay.me` — fait, résultats identiques aux SDK Node.js et PHP.
- [ ] Tester les écritures (create/update/rotate_secret) contre une clé
      sandbox — pas encore fait (pas de clé sandbox disponible, seulement
      une clé live testée en lecture seule pour ne rien déclencher de réel).
- [ ] Vérifier le nom exact des codes réseau (`network`) et méthodes de
      payout (`method`) attendus par l'API — documentés comme chaînes libres.
- [x] 2026-09-13 — Nom de package PyPI vérifié : **`alphapay`** (celui déjà
      dans `pyproject.toml`) est **disponible** — `GET
      https://pypi.org/pypi/alphapay/json` renvoie 404 (nom libre), pas de
      blocage équivalent au scope `@alphapay` déjà pris côté npm (voir
      CHECKLIST du SDK Node). Rien à renommer avant `twine upload`.
- [ ] `pyproject.toml` déclare `requires-python = ">=3.8"` — non testé sur
      autre chose que 3.10 dans cette session (seule version Python
      disponible ici). `from __future__ import annotations` couvre les
      types différés, mais à revalider sur 3.8/3.9 réels avant publication.

## Souhaitable avant v1.0.0

- [ ] Couvrir les ressources listées comme "pas encore couvertes" dans le
      README.
- [ ] CI (GitHub Actions) : tests sur 3.8/3.9/3.10/3.11/3.12 + `mypy`/`ruff`.
- [ ] Envisager `requests` en dépendance optionnelle pour de meilleures
      performances (connexions persistantes, HTTP/2) si des utilisateurs le
      demandent — volontairement stdlib-only pour l'instant (cohérent avec
      les SDK Node/PHP, 0 dépendance).
- [ ] Exemples d'intégration complets (`examples/flask_webhook.py`,
      `examples/django_webhook.py`) plutôt que les extraits du README.
- [ ] Publier des retours de type plus précis que `Dict[str, Any]` (TypedDict
      ou dataclasses) si des utilisateurs le demandent — actuellement chaque
      ressource renvoie un dict JSON brut, comme le SDK PHP, pour rester
      simple à maintenir en miroir des 2 autres SDK.

## Fait

- [x] Client HTTP (`urllib`, stdlib) : auth Bearer, détection sandbox/live,
      retries avec backoff sur 429/5xx/réseau, timeout configurable,
      Idempotency-Key optionnelle.
- [x] Enveloppe `{success, data, code}` déballée automatiquement ; erreurs
      mappées vers des exceptions typées (`AlphaPayValidationError.field_errors`,
      `AlphaPayRateLimitError.retry_after`, etc.).
- [x] `verify_signature()` — HMAC-SHA256 identique à
      `apps.webhooks.services.sign_payload`, comparaison en temps constant
      (`hmac.compare_digest`), fenêtre anti-rejeu de 300s.
- [x] `paginate()` — suit `next` (URL absolue), pas un numéro de page
      recalculé — même piège que celui trouvé et corrigé côté SDK Node sur
      `transactions.list()` (pagination par curseur, pas par page), corrigé
      dès l'écriture ici.
- [x] 9 ressources (voir tableau README), restrictions `dashboard_only`
      documentées par méthode dès l'écriture (reprises du SDK Node,
      vérifiées en conditions réelles côté Node).
- [x] 11 tests `unittest` verts, contre un vrai serveur HTTP local (thread,
      pas un mock) : enveloppe, erreurs de validation, retry 429, épuisement
      des retries, Idempotency-Key, pagination par curseur.
- [x] `list()`/`get()` des 9 ressources vérifiés en lecture seule contre une
      vraie clé live sur `api.alphapay.me` — formes de réponse et
      restrictions `dashboard_only` identiques aux SDK Node.js et PHP.
- [x] 2026-09-12 — synchronisé avec le SDK PHP (commit "Add public payment
      link features") : `payment_links.get_public()`/`create_public_checkout()`
      (les 2 seules méthodes de cette ressource qui n'exigent PAS de clé
      secrète — pensées pour un backend qui relaie ensuite le `slug` à un
      client, jamais un front avec la clé en dur), `create()`/`update()`
      étendus (`require_phone`, `facebook_pixel_id`, `google_ads_id`,
      `custom_fields`, `show_confirmation_page`, `redirect_url`),
      `webhook_endpoints.create()` + `payment_link`. 3 tests ajoutés
      (14 au total), contre le même serveur de test local, mêmes réponses
      que les tests PHP jumeaux. Au passage, clarifié en docstring (le SDK
      Python passe des `dict` non typés, donc rien à corriger dans le code
      lui-même) la forme exacte de `customer`/`recipient` sur
      `payin_initialize`/`payout_initialize` — un bug équivalent (mauvaise
      forme, `full_name` au lieu de `first_name`/`last_name`) a été trouvé
      et corrigé dans les *types* du SDK Node à cette occasion.
- [x] 2026-09-13 — `alphapay-python-demo` (`pip install -e
      ../AlphaPaySDK-python`) revérifié de bout en bout contre une vraie clé
      LIVE : `payment_links.create()` + `get_public()` (flux du demo
      lui-même), plus `balances.list()` et `checkout_sessions.create()` en
      complément (mêmes vérifications que côté SDK Node) — tout fonctionne,
      aucune régression après la synchronisation PHP.
- [x] 2026-09-13 — `EXAMPLES.md` créé : 9 exemples Python complets
      (checkout, softpay, lien de paiement, solde, clients, webhooks,
      reversements/transferts wallet, clés API/whitelist IP, gestion des
      erreurs) — syntaxe validée (`python -m py_compile`) et chaque chaîne
      d'attributs (`alphapay.<ressource>.<méthode>`) confirmée existante par
      introspection sur le vrai module installé, pas seulement relue.
