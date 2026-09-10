"""Itération automatique sur les ressources paginées."""

from __future__ import annotations

from typing import Any, Dict, Iterator

from .http import Http


def paginate(http: Http, first_page: Dict[str, Any]) -> Iterator[Any]:
    """Parcourt automatiquement toutes les pages d'une ressource paginée,
    qu'elle soit paginée par page (avec "count") ou par curseur (sans
    "count" -- ex. ``client.transactions.list()``).

    Suit le lien "next" renvoyé TEL QUEL par l'API plutôt que de recalculer
    un numéro de page soi-même : un curseur n'est pas un numéro de page
    (c'est un jeton opaque encodant une position dans le tri), l'incrémenter
    à la main ne ferait qu'interroger indéfiniment la même première page.

    :param http: ``client.http`` -- nécessaire pour requêter l'URL absolue "next".
    :param first_page: Le premier appel déjà résolu, ex.
        ``client.transactions.list(status="SUCCESS")``.

    :Example:

    >>> for tx in paginate(client.http, client.transactions.list(status="SUCCESS")):
    ...     print(tx["reference"])
    """
    page = first_page
    while True:
        for item in page["results"]:
            yield item
        next_url = page.get("next")
        if not next_url:
            return
        page = http.request("GET", next_url)
