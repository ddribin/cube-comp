from __future__ import annotations

import requests
from dataclasses import dataclass, field
from datetime import date

@dataclass
class Competition:
    id: str
    name: str
    short_name: str
    display_name: str
    start_date: date
    results_posted: bool

    @classmethod
    def from_dict(cls, dict: dict) -> Competition:
        return cls(
            id = dict["id"],
            name = dict["name"],
            short_name = dict["short_name"],
            display_name = dict["displayName"],
            start_date = date.fromisoformat(dict["start_date"]),
            results_posted = dict["resultsPosted"],
        )

class CommandLine:
    def execute(self) -> int:
        # https://docs.worldcubeassociation.org/knowledge_base/v0_api.html
        url = "https://www.worldcubeassociation.org/api/v0/competitions"
        today = date.today().isoformat()
        payload = {"q": "Illinois", "country_iso2": "US", "start": today}
        r = requests.get(url, params=payload)
        r.raise_for_status()
        competitions = r.json()
        print(f"{len(competitions)}")
        if len(competitions) > 0:
            comp = Competition.from_dict(competitions[0])
            print(f"{comp}")

        for json_comp in competitions:
            comp = Competition.from_dict(json_comp)
            print(f"{comp}")

        return 0
    
def main() -> int:
    cli = CommandLine()
    return cli.execute()
