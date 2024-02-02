from __future__ import annotations

import argparse
import requests
from dataclasses import dataclass, field
from datetime import date
from jinja2 import Environment, PackageLoader, select_autoescape

@dataclass
class Competition:
    id: str
    name: str
    short_name: str
    display_name: str
    start_date: date
    results_posted: bool
    city: str
    venue: str
    website: str

    @classmethod
    def from_dict(cls, dict: dict) -> Competition:
        return cls(
            id = dict["id"],
            name = dict["name"],
            short_name = dict["short_name"],
            display_name = dict["displayName"],
            start_date = date.fromisoformat(dict["start_date"]),
            results_posted = dict["resultsPosted"],
            city = dict["city"],
            venue = dict["venue"],
            website = dict["website"],
        )

class CommandLine:
    def execute(self) -> int:
        self.parse_arguments()
        competitions = self.fetch_competitions()
        self.print_competitions(competitions)
        return 0
        
    def parse_arguments(self) -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument("query", type=str, help="query string", nargs='?', default=None)
        parser.add_argument("-c", "--country", type=str, help="country", default="US")

        args = parser.parse_args()

        self.query = args.query
        self.country = args.country
    
    def fetch_competitions(self) -> list[Competition]:
        # https://docs.worldcubeassociation.org/knowledge_base/v0_api.html
        url = "https://www.worldcubeassociation.org/api/v0/competitions"
        today = date.today().isoformat()
        payload = {"start": today}
        if self.query:
            payload["q"] = self.query
        if self.country:
            payload["country_iso2"] = self.country
        r = requests.get(url, params=payload)
        r.raise_for_status()
        json_competitions = r.json()
        competitions = [Competition.from_dict(json_comp) for json_comp in json_competitions]
        return competitions
    
    def print_competitions(self, competitions: list[Competition]) -> None:
        env = Environment(
            loader = PackageLoader("cube_comp"),
            autoescape = select_autoescape(),
            trim_blocks = True,
            lstrip_blocks = True,
            keep_trailing_newline = False,
        )
        template = env.get_template("competitions.txt.j2")
        rendered = template.render(competitions=competitions)
        print(rendered)

    
def main() -> int:
    cli = CommandLine()
    return cli.execute()
