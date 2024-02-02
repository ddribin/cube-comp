import logging
from datetime import date
from typing import Any

import requests
from typing_extensions import Protocol


class WCAService(Protocol):
    def fetch_competitions(
        self, query: str | None, country: str | None, sort_desc=False
    ) -> list[dict[str, Any]]:
        "Fetches competitions with optional parameters"
        ...


# Basic documentation about the API:
# https://docs.worldcubeassociation.org/knowledge_base/v0_api.html
#
# Code for the `Competitions` endpoint:
# https://github.com/thewca/worldcubeassociation.org/blob/master/WcaOnRails/app/controllers/api/v0/competitions_controller.rb
#
# Code for the `Competition` model. The `search` method shows possible parameters:
# https://github.com/thewca/worldcubeassociation.org/blob/master/WcaOnRails/app/models/competition.rb
class WCAEndpoint(WCAService):
    def __init__(self) -> None:
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._base_url = "https://www.worldcubeassociation.org/api/v0"

    @property
    def _competitions_url(self) -> str:
        url = self._base_url + "/competitions"
        return url

    def fetch_competitions(
        self, query: str | None, country: str | None, sort_desc=False
    ) -> list[dict[str, Any]]:
        url = self._competitions_url
        today = date.today().isoformat()
        payload = {"start": today, "sort": "start_date"}
        if query:
            payload["q"] = query
        if country:
            payload["country_iso2"] = country
        self.logger.info("Sending request to URL %r with payload %r", url, payload)
        response = requests.get(url, params=payload)
        self.logger.info("Got response %r", response)
        response.raise_for_status()
        json_competitions = response.json()
        return json_competitions
