from __future__ import annotations

import argparse
import requests
from dataclasses import dataclass, field
from datetime import date
from jinja2 import Environment, PackageLoader, select_autoescape
import logging

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
            display_name = dict.get("short_display_name", ""),
            start_date = date.fromisoformat(dict["start_date"]),
            results_posted = dict["results_posted_at"] is None,
            city = dict["city"],
            venue = dict["venue"],
            website = dict["website"],
        )

class CommandLine:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._log_option: str | None = None

    def execute(self) -> int:
        self.parse_arguments()
        logging.basicConfig(level=self.log_level)
        competitions = self.fetch_competitions()
        self.print_competitions(competitions)
        return 0
        
    def parse_arguments(self) -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument("query", type=str, help="query string", nargs='?', default=None)
        parser.add_argument("-c", "--country", type=str, help="country", default="US")
        parser.add_argument(
            "-L",
            "--log",
            choices=["debug", "info", "warning", "error"],
            default="warning",
            help="Set log level",
        )

        args = parser.parse_args()

        self.query = args.query
        self.country = args.country
        self._log_option = args.log
    
    def fetch_competitions(self) -> list[Competition]:
        # https://docs.worldcubeassociation.org/knowledge_base/v0_api.html
        url = "https://www.worldcubeassociation.org/api/v0/competitions"
        today = date.today().isoformat()
        payload = {"start": today}
        if self.query:
            payload["q"] = self.query
        if self.country:
            payload["country_iso2"] = self.country
        self.logger.info("Sending request to URL %r with payload %r", url, payload)
        response = requests.get(url, params=payload)
        self.logger.info("Got response %r", response)
        response.raise_for_status()
        json_competitions = response.json()
        competitions = [self.competition_from_dict(json_comp) for json_comp in json_competitions]
        return competitions
    
    def competition_from_dict(self, dict: dict) -> Competition:
        self.logger.debug("Converting competition:\n%r", dict)
        competition = Competition.from_dict(dict)
        self.logger.debug("Converted competition %r", competition)
        return competition
    
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
        
    @property
    def log_level(self) -> int:
        match self._log_option:
            case "debug":
                return logging.DEBUG

            case "info":
                return logging.INFO

            case "warning":
                return logging.WARNING

            case _:
                return logging.WARNING


    
def main() -> int:
    cli = CommandLine()
    return cli.execute()
