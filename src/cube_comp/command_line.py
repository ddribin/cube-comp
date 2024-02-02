import argparse
import inspect
import json
import logging
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape

from .competition import Competition
from .wca_service import WCAEndpoint


class CommandLine:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._log_option: str | None = None
        self.query: str | None = None
        self.country: str
        self.known_comps_file: str | None = None

    def execute(self) -> int:
        self.parse_arguments()
        logging.basicConfig(level=self.log_level)
        competitions = self.fetch_competitions()
        filtered_competitions = self.filter_competitions(competitions)
        self.print_competitions(filtered_competitions)
        return 0

    def parse_arguments(self) -> None:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "query", type=str, help="query string", nargs="?", default=None
        )
        parser.add_argument(
            "-c", "--country", type=str, help="ISO country code", default="US"
        )
        parser.add_argument(
            "-k",
            "--known",
            type=str,
            help="known competitions JSON file",
            metavar="FILE",
        )
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
        self.known_comps_file = args.known
        self._log_option = args.log

    def fetch_competitions(self) -> list[Competition]:
        service = WCAEndpoint()
        json_competitions = service.fetch_competitions(
            query=self.query, country=self.country
        )
        competitions = [
            self.competition_from_dict(json_comp) for json_comp in json_competitions
        ]
        return competitions

    def competition_from_dict(self, dict: dict[str, Any]) -> Competition:
        self.logger.debug("Converting competition:\n%r", dict)
        competition = Competition.from_dict(dict)
        self.logger.debug("Converted competition %r", competition)
        return competition

    def filter_competitions(self, competitions: list[Competition]) -> list[Competition]:
        if self.known_comps_file is None:
            return competitions

        known_comps = self.read_known_comps_file(self.known_comps_file)
        self.logger.debug("Known comps: %r" % known_comps)
        filtered_comps = [c for c in competitions if c.id not in known_comps]
        self.logger.debug("Filtered comps: %r" % filtered_comps)
        new_known_comps = [c.id for c in competitions]
        self.logger.debug("New known comps: %r" % new_known_comps)
        self.write_known_comps_file(self.known_comps_file, new_known_comps)
        return filtered_comps

    def read_known_comps_file(self, file: str) -> list[str]:
        self.logger.info("Reading known comps file: %r" % file)
        try:
            with open(file) as f:
                known_comps = json.load(f)
        except FileNotFoundError:
            known_comps = []

        return known_comps

    def write_known_comps_file(self, file: str, known_comps: list[str]) -> None:
        self.logger.info("Writing known comps file: %r" % file)
        with open(file, mode="w") as f:
            json.dump(known_comps, f, indent=2)

    def print_competitions(self, competitions: list[Competition]) -> None:
        env = Environment(
            loader=PackageLoader("cube_comp"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=False,
        )
        template = env.get_template("competitions.txt.j2")
        rendered = template.render(competitions=competitions)
        rendered = inspect.cleandoc(rendered)
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
