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
- [ ] Choisir le nom de package PyPI définitif (`alphapay` est optimiste --
      probablement déjà pris ; prévoir un repli type `alphapay-sdk` ou
      `alphapay-payments`).
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
