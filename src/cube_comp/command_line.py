import argparse
import inspect
import logging
import os
import smtplib
import sys
from email.message import EmailMessage
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape

from .competition import Competition
from .known_competitions import KnownCompetitions
from .wca_service import WCAEndpoint


class CommandError(Exception):
    pass


class CommandLine:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._log_option: str | None = None
        self.prog: str
        self.query: str | None = None
        self.country: str
        self.known_comps_file: str | None = None
        self.email_to: str | None = None
        self.email_from: str | None = None
        self.smtp_host = "localhost"
        self.smtp_port: int
        self.smtp_user: str | None = None
        self.smtp_password: str | None = None

    def execute(self) -> int:
        try:
            self.parse_arguments()
            self.run()
            return 0
        except CommandError as e:
            message = e.args[0]
            sys.stderr.write(f"{self.prog}: {message}\n")
            result = e.args[1] if len(e.args) == 2 else 1
            return result

    def run(self) -> None:
        logging.basicConfig(level=self.log_level)
        competitions = self.fetch_competitions()
        filtered_competitions = self.filter_competitions(competitions)
        self.output_competitions(filtered_competitions)

    def parse_arguments(self) -> None:
        parser = argparse.ArgumentParser()
        self.prog = parser.prog
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
            "--email-to", type=str, help="Email output to ADDRESS", metavar="ADDRESS"
        )
        parser.add_argument(
            "--email-from",
            type=str,
            help="Use ADDRESS as From address",
            metavar="ADDRESS",
        )
        parser.add_argument(
            "--smtp-host", type=str, help="SMTP server host", metavar="HOST"
        )
        parser.add_argument("--smtp-port", type=int, help="SMTP port", default=0)
        parser.add_argument("--smtp-user", type=str, help="SMTP user")

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

        self.email_to = args.email_to
        self.email_from = args.email_from

        if args.smtp_host is not None:
            self.smtp_host = args.smtp_host
        self.smtp_port = args.smtp_port
        if args.smtp_user is not None:
            self.smtp_user = args.smtp_user
            self.smtp_password = os.environ.get("CUBE_COMP_EMAIL_PASSWORD")
            if self.smtp_password is None:
                raise CommandError("Expected password in CUBE_COMP_EMAIL_PASSWORD")

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

        self.logger.info("Using known comps file: %r" % self.known_comps_file)
        with open(self.known_comps_file, "a+") as file_io:
            known_comps = KnownCompetitions(file_io)
            filtered_comps = known_comps.filter_competitions(competitions)
        return filtered_comps

    def output_competitions(self, competitions: list[Competition]) -> None:
        if self.email_to is None:
            self.print_competitions(competitions)
        else:
            self.email_competitions(competitions, self.email_to)

    def print_competitions(self, competitions: list[Competition]) -> None:
        rendered = self.render_competitions(competitions)
        print(rendered)

    def email_competitions(
        self, competitions: list[Competition], email_address: str
    ) -> None:
        if len(competitions) > 0:
            self.logger.info(
                "Emailing %r competitions to %r", len(competitions), email_address
            )
            self.send_email(competitions, email_address)
        else:
            self.logger.info("No competitions, so skipping email")

    def send_email(self, competitions: list[Competition], email_address: str) -> None:
        try:
            rendered = self.render_competitions(competitions)
            from_address = (
                self.email_from if self.email_from is not None else self.email_to
            )
            msg = EmailMessage()
            msg.set_content(rendered)
            msg["Subject"] = "WCA Competition Notification"
            msg["To"] = email_address
            msg["From"] = from_address

            s = smtplib.SMTP(self.smtp_host, port=self.smtp_port)
            if self.smtp_port == 587:
                s.starttls()
                if self.smtp_user is not None:
                    assert self.smtp_password is not None
                    s.login(self.smtp_user, self.smtp_password)
            s.send_message(msg)
            s.quit()
        except ConnectionRefusedError:
            raise CommandError(
                f"Cannot send email: Connection refused: {self.smtp_host}"
            )

    def render_competitions(self, competitions: list[Competition]) -> str:
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
        return rendered

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
